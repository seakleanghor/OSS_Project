"""
Global configuration for the pygame Minesweeper game.
"""

# Display settings
fps = 60

# Grid settings (Default)
cols = 16
rows = 16
num_mines = 40

# Cell size and margins
cell_size = 32
margin_left = 20
margin_top = 60
margin_right = 20
margin_bottom = 20

# Derived display dimension (Calculated dynamically in run.py, but defined here as default)
width = margin_left + cols * cell_size + margin_right
height = margin_top + rows * cell_size + margin_bottom

# Colors
color_bg = (24, 26, 27)
color_grid = (60, 64, 67)
color_cell_hidden = (40, 44, 52)
color_cell_revealed = (225, 228, 232)
color_cell_mine = (220, 0, 0)
color_flag = (255, 215, 0)
color_text = (20, 20, 20)
color_header_text = (240, 240, 240)
color_header = (32, 34, 36)
color_highlight = (70, 130, 180)
color_result = (242, 242, 0)

# Number colors for adjacent mines
number_colors = {
    1: (0, 0, 255),      # Blue
    2: (0, 128, 0),     # Green
    3: (255, 0, 0),     # Red
    4: (0, 0, 128),     # Navy
    5: (128, 0, 0),     # Maroon
    6: (0, 128, 128),   # Teal
    7: (0, 0, 0),       # Black
    8: (128, 128, 128)  # Gray
}

# Text / UI
font_name = None  # default pygame font
font_size = 22
header_font_size = 24
result_font_size = 64

# Input
mouse_left = 1
mouse_middle = 2
mouse_right = 3

# Highlight behavior
highlight_duration_ms = 600
result_overlay_alpha = 120

# Game Info
title = "Minesweeper"

# --- CRITICAL: Difficulty Settings (Fixes the AttributeError) ---
difficulties = {
    'easy': {'cols': 9, 'rows': 9, 'num_mines': 10},
    'medium': {'cols': 16, 'rows': 16, 'num_mines': 40},
    'hard': {'cols': 30, 'rows': 16, 'num_mines': 99}
}

current_difficulty = 'easy'