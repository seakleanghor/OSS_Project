"""
Core game logic for Minesweeper.

This module contains pure domain logic without any pygame or pixel-level
concerns. It defines:
- CellState: the state of a single cell
- Cell: a cell positioned by (col,row) with an attached CellState
- Board: grid management, mine placement, adjacency computation, reveal/flag
"""

import random
from typing import List, Tuple


class CellState:
    """Mutable state of a single cell."""

    def __init__(self, is_mine: bool = False, is_revealed: bool = False, is_flagged: bool = False, adjacent: int = 0):
        self.is_mine = is_mine
        self.is_revealed = is_revealed
        self.is_flagged = is_flagged
        self.adjacent = adjacent


class Cell:
    """Logical cell positioned on the board by column and row."""

    def __init__(self, col: int, row: int):
        self.col = col
        self.row = row
        self.state = CellState()


class Board:
    """Minesweeper board state and rules."""

    def __init__(self, cols: int, rows: int, mines: int):
        self.cols = cols
        self.rows = rows
        self.num_mines = mines
        self.cells: List[Cell] = [Cell(c, r) for r in range(rows) for c in range(cols)]
        self._mines_placed = False
        self.revealed_count = 0
        self.game_over = False
        self.win = False

    def index(self, col: int, row: int) -> int:
        """Return the flat list index for (col,row)."""
        return row * self.cols + col

    def is_inbounds(self, col: int, row: int) -> bool:
        return 0 <= col < self.cols and 0 <= row < self.rows

    def neighbors(self, col: int, row: int) -> List[Tuple[int, int]]:
        deltas = [
            (-1, -1), (0, -1), (1, -1),
            (-1, 0), (1, 0),
            (-1, 1), (0, 1), (1, 1),
        ]
        result = []
        for dc, dr in deltas:
            new_col, new_row = col + dc, row + dr
            if self.is_inbounds(new_col, new_row):
                result.append((new_col, new_row))
        return result

    def place_mines(self, safe_col: int, safe_row: int) -> None:
        """Place mines ensuring the first click and its neighbors are safe."""
        all_positions = [(c, r) for r in range(self.rows) for c in range(self.cols)]
        # Forbidden set includes the clicked cell and all its immediate neighbors
        forbidden = {(safe_col, safe_row)} | set(self.neighbors(safe_col, safe_row))
        pool = [p for p in all_positions if p not in forbidden]
        
        # Guard against requested mine count exceeding available space
        actual_mines = min(self.num_mines, len(pool))
        mine_positions = random.sample(pool, actual_mines)
        
        for mc, mr in mine_positions:
            self.cells[self.index(mc, mr)].state.is_mine = True
            
        # Compute adjacency
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.cells[self.index(c, r)]
                if not cell.state.is_mine:
                    count = 0
                    for nc, nr in self.neighbors(c, r):
                        if self.cells[self.index(nc, nr)].state.is_mine:
                            count += 1
                    cell.state.adjacent = count

        self._mines_placed = True

    def reveal(self, col: int, row: int) -> None:
        """Reveal a cell and handle flood fill logic."""
        if not self.is_inbounds(col, row) or self.game_over or self.win:
            return
            
        idx = self.index(col, row)
        cell = self.cells[idx]
        
        if cell.state.is_revealed or cell.state.is_flagged:
            return
            
        if not self._mines_placed:
            self.place_mines(col, row)
            
        cell.state.is_revealed = True
        self.revealed_count += 1
        
        if cell.state.is_mine:
            self.game_over = True
            self._reveal_all_mines()
            return
            
        # Recursive flood fill for empty cells
        if cell.state.adjacent == 0:
            stack = [(col, row)]
            while stack:
                curr_col, curr_row = stack.pop()
                for n_col, n_row in self.neighbors(curr_col, curr_row):
                    n_idx = self.index(n_col, n_row)
                    n_cell = self.cells[n_idx]
                    if not n_cell.state.is_revealed and not n_cell.state.is_flagged:
                        n_cell.state.is_revealed = True
                        self.revealed_count += 1
                        if n_cell.state.adjacent == 0:
                            stack.append((n_col, n_row))

        self._check_win()

    def toggle_flag(self, col: int, row: int) -> None:
        if not self.is_inbounds(col, row) or self.game_over or self.win:
            return
        cell = self.cells[self.index(col, row)]
        if not cell.state.is_revealed:
            cell.state.is_flagged = not cell.state.is_flagged

    def flagged_count(self) -> int:
        return sum(1 for cell in self.cells if cell.state.is_flagged)

    def _reveal_all_mines(self) -> None:
        for cell in self.cells:
            if cell.state.is_mine:
                cell.state.is_revealed = True

    def _check_win(self) -> None:
        total_cells = self.cols * self.rows
        if self.revealed_count == total_cells - self.num_mines and not self.game_over:
            self.win = True

    def get_hint(self) -> Tuple[int, int] | None:
        """Issue #3: Returns a random unrevealed safe cell."""
        safe_unrevealed = [
            (cell.col, cell.row) for cell in self.cells
            if not cell.state.is_mine and not cell.state.is_revealed
        ]
        if safe_unrevealed:
            return random.choice(safe_unrevealed)
        return None