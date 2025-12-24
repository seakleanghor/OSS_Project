"""
Pygame presentation layer for Minesweeper.

This module owns:
- Renderer: all drawing of cells, header, and result overlays
- InputController: translate mouse input to board actions and UI feedback
- Game: orchestration of loop, timing, state transitions, and composition
"""
import json
import os
import sys
import pygame
import config
from components import Board
from pygame.locals import Rect

class Renderer:
    """Draws the Minesweeper UI."""

    def __init__(self, screen: pygame.Surface, board: Board):
        self.screen = screen
        self.board = board
        self.font = pygame.font.Font(config.font_name, config.font_size)
        self.header_font = pygame.font.Font(config.font_name, config.header_font_size)
        self.result_font = pygame.font.Font(config.font_name, config.result_font_size)

    def cell_rect(self, col: int, row: int) -> Rect:
        """Return the rectangle in pixels for the given grid cell."""
        x = config.margin_left + col * config.cell_size
        y = config.margin_top + row * config.cell_size
        return Rect(x, y, config.cell_size, config.cell_size)

    def draw_cell(self, col: int, row: int, highlighted: bool) -> None:
        """Draw a single cell, respecting revealed/flagged state and highlight."""
        cell = self.board.cells[self.board.index(col, row)]
        rect = self.cell_rect(col, row)
        
        if cell.state.is_revealed:
            pygame.draw.rect(self.screen, config.color_cell_revealed, rect)
            if cell.state.is_mine:
                pygame.draw.circle(self.screen, config.color_cell_mine, rect.center, rect.width // 4)
            elif cell.state.adjacent > 0:
                # Issue #1: Color coded numbers from config
                color = config.number_colors.get(cell.state.adjacent, config.color_text)
                label = self.font.render(str(cell.state.adjacent), True, color)
                self.screen.blit(label, label.get_rect(center=rect.center))
        else:
            base_color = config.color_highlight if highlighted else config.color_cell_hidden
            pygame.draw.rect(self.screen, base_color, rect)
            if cell.state.is_flagged:
                # Simple flag drawing
                pygame.draw.polygon(self.screen, (200, 0, 0), [
                    (rect.left + 10, rect.top + 5), 
                    (rect.right - 10, rect.centery - 5), 
                    (rect.left + 10, rect.centery)
                ])
        pygame.draw.rect(self.screen, config.color_grid, rect, 1)

    def draw_header(self, remaining_mines: int, time_text: str, high_score: int | None) -> None:
        """Draw remaining mines, timer, and high score in the header."""
        screen_w = self.screen.get_width()
        pygame.draw.rect(
            self.screen,
            config.color_header,
            Rect(0, 0, screen_w, config.margin_top - 4),
        )
        
        hs_text = f"Best: {high_score}s" if high_score is not None else "Best: --"
        
        left_label = self.header_font.render(f"Mines: {remaining_mines}", True, config.color_header_text)
        center_label = self.header_font.render(hs_text, True, config.color_header_text)
        right_label = self.header_font.render(f"Time: {time_text}", True, config.color_header_text)
        
        self.screen.blit(left_label, (10, 12))
        self.screen.blit(center_label, (screen_w // 2 - center_label.get_width() // 2, 12))
        self.screen.blit(right_label, (screen_w - right_label.get_width() - 10, 12))

    def draw_result_overlay(self, text: str | None) -> None:
        """Draw a semi-transparent overlay with centered result text."""
        if not text:
            return
        screen_w, screen_h = self.screen.get_size()
        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, config.result_overlay_alpha))
        self.screen.blit(overlay, (0, 0))
        label = self.result_font.render(text, True, config.color_result)
        rect = label.get_rect(center=(screen_w // 2, screen_h // 2))
        self.screen.blit(label, rect)


class InputController:
    """Translates input events into game and board actions."""

    def __init__(self, game: "Game"):
        self.game = game

    def pos_to_grid(self, x: int, y: int):
        """Convert pixel coordinates to grid indices."""
        col = (x - config.margin_left) // config.cell_size
        row = (y - config.margin_top) // config.cell_size
        if 0 <= col < self.game.board.cols and 0 <= row < self.game.board.rows:
            return int(col), int(row)
        return -1, -1

    def handle_mouse(self, pos, button) -> None:
        col, row = self.pos_to_grid(pos[0], pos[1])
        if col == -1:
            return
        game = self.game
        
        # Issue #5: Start timer only on first valid click (Left or Right)
        if not game.started and button in (1, 3):
            game.started = True
            game.start_ticks_ms = pygame.time.get_ticks()

        if button == 1: # Left Click
            game.highlight_targets.clear()
            game.board.reveal(col, row)
        elif button == 3: # Right Click
            game.highlight_targets.clear()
            game.board.toggle_flag(col, row)
        elif button == 2: # Middle Click (Highlight)
            neighbors = game.board.neighbors(col, row)
            game.highlight_targets = {
                (nc, nr) for (nc, nr) in neighbors
                if not game.board.cells[game.board.index(nc, nr)].state.is_revealed
            }
            game.highlight_until_ms = pygame.time.get_ticks() + 500


class Game:
    """Main application object orchestrating loop and high-level state."""

    def __init__(self):
        pygame.init()
        self.difficulty = 'easy'
        self.high_score_file = "high_scores.json"
        self.high_scores = self.load_high_scores()
        
        # Initial settings
        settings = config.difficulties[self.difficulty]
        self.cols, self.rows, self.num_mines = settings['cols'], settings['rows'], settings['num_mines']
        
        width = config.margin_left + config.margin_right + self.cols * config.cell_size
        height = config.margin_top + config.margin_bottom + self.rows * config.cell_size
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Minesweeper")
        
        self.board = Board(self.cols, self.rows, self.num_mines)
        self.renderer = Renderer(self.screen, self.board)
        self.input = InputController(self)
        
        self.highlight_targets = set()
        self.highlight_until_ms = 0
        self.started = False
        self.start_ticks_ms = 0
        self.end_ticks_ms = 0
        self.score_saved = False
        self.clock = pygame.time.Clock()

    def load_high_scores(self):
        if os.path.exists(self.high_score_file):
            try:
                with open(self.high_score_file, "r") as f:
                    return json.load(f)
            except: pass
        return {"easy": None, "medium": None, "hard": None}

    def save_high_score(self):
        current_time_sec = self._elapsed_ms() // 1000
        best = self.high_scores.get(self.difficulty)
        if best is None or current_time_sec < best:
            self.high_scores[self.difficulty] = current_time_sec
            with open(self.high_score_file, "w") as f:
                json.dump(self.high_scores, f)

    def reset(self, diff_name=None):
        """Issue #2: Reset game with optional difficulty change."""
        if diff_name:
            self.difficulty = diff_name
            settings = config.difficulties[self.difficulty]
            self.cols, self.rows, self.num_mines = settings['cols'], settings['rows'], settings['num_mines']
            width = config.margin_left + config.margin_right + self.cols * config.cell_size
            height = config.margin_top + config.margin_bottom + self.rows * config.cell_size
            self.screen = pygame.display.set_mode((width, height))
            self.renderer.screen = self.screen

        self.board = Board(self.cols, self.rows, self.num_mines)
        self.renderer.board = self.board
        self.highlight_targets.clear()
        self.started = False
        self.start_ticks_ms = 0
        self.end_ticks_ms = 0
        self.score_saved = False

    def _elapsed_ms(self) -> int:
        """Timer logic - stops when game ends."""
        if not self.started:
            return 0
        current = self.end_ticks_ms if self.end_ticks_ms else pygame.time.get_ticks()
        return current - self.start_ticks_ms

    def _format_time(self, ms: int) -> str:
        total_sec = ms // 1000
        return f"{total_sec // 60:02d}:{total_sec % 60:02d}"

    def draw(self):
        self.screen.fill(config.color_bg)
        remaining = max(0, self.num_mines - self.board.flagged_count())
        time_text = self._format_time(self._elapsed_ms())
        
        self.renderer.draw_header(remaining, time_text, self.high_scores.get(self.difficulty))
        
        now = pygame.time.get_ticks()
        for r in range(self.board.rows):
            for c in range(self.board.cols):
                is_high = (now <= self.highlight_until_ms) and ((c, r) in self.highlight_targets)
                self.renderer.draw_cell(c, r, is_high)
        
        res = "GAME OVER" if self.board.game_over else "GAME CLEAR" if self.board.win else None
        self.renderer.draw_result_overlay(res)
        pygame.display.flip()

    def run_step(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r: self.reset()
                elif event.key == pygame.K_h: # Hint
                    hint = self.board.get_hint()
                    if hint: self.board.reveal(*hint)
                elif event.key == pygame.K_1: self.reset('easy')
                elif event.key == pygame.K_2: self.reset('medium')
                elif event.key == pygame.K_3: self.reset('hard')
            
            if event.type == pygame.MOUSEBUTTONDOWN and not (self.board.game_over or self.board.win):
                self.input.handle_mouse(event.pos, event.button)

        # Handle game end
        if (self.board.game_over or self.board.win) and self.started and not self.end_ticks_ms:
            self.end_ticks_ms = pygame.time.get_ticks()
            if self.board.win and not self.score_saved:
                self.save_high_score()
                self.score_saved = True

        self.draw()
        self.clock.tick(config.fps)
        return True

def main():
    game = Game()
    while game.run_step():
        pass
    pygame.quit()

if __name__ == "__main__":
    main()