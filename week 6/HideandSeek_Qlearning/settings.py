# settings.py

GRID_SIZE = 10
CELL_SIZE  = 60

BOARD_WIDTH = GRID_SIZE * CELL_SIZE   # 600
INFO_HEIGHT = 230                      # 패널 높이 (버튼 포함 충분히)

WIDTH  = BOARD_WIDTH
HEIGHT = BOARD_WIDTH + INFO_HEIGHT

FPS = 30

# 색상
WHITE     = (245, 245, 245)
BLACK     = (30,  30,  30)
GRAY      = (180, 180, 180)
BLUE      = (70,  130, 255)
RED       = (220, 80,  80)
GREEN     = (80,  180, 120)
DARK_GRAY = (80,  80,  80)
PANEL_BG  = (238, 240, 245)

# 액션
ACTIONS = {
    0: ( 0, -1),  # up
    1: ( 0,  1),  # down
    2: (-1,  0),  # left
    3: ( 1,  0),  # right
    4: ( 0,  0),  # stay
}

ACTION_NAMES = {
    0: "UP", 1: "DOWN", 2: "LEFT", 3: "RIGHT", 4: "STAY",
}

MAX_STEPS  = 100

PRETRAIN_EPISODES        = 1000         # 초기 학습량 증가
TRAIN_EPISODES_PER_FRAME = 30           # T 키 누를 때 프레임당 학습량 증가