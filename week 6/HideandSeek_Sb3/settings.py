# settings.py

GRID_SIZE = 10
CELL_SIZE = 60

BOARD_WIDTH = GRID_SIZE * CELL_SIZE
INFO_HEIGHT = 280

WIDTH = BOARD_WIDTH
HEIGHT = BOARD_WIDTH + INFO_HEIGHT

FPS = 30

WHITE = (245, 245, 245)
BLACK = (30, 30, 30)
GRAY = (180, 180, 180)
BLUE = (70, 130, 255)
RED = (220, 80, 80)
GREEN = (80, 180, 120)
DARK_GRAY = (80, 80, 80)
PANEL_BG = (238, 240, 245)

# STAY 행동을 제거해서 hider가 반드시 이동 방향을 선택하도록 수정
ACTIONS = {
    0: (0, -1),
    1: (0, 1),
    2: (-1, 0),
    3: (1, 0),
}

ACTION_NAMES = {
    0: "UP",
    1: "DOWN",
    2: "LEFT",
    3: "RIGHT",
}

MAX_STEPS = 100

MODEL_PATH = "sb3_hider_dqn_no_stay.zip"
TRAIN_STEPS_PER_PRESS = 50000
