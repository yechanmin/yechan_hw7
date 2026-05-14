GRID_COLS   = 20
GRID_ROWS   = 16
CELL        = 36
BOARD_W     = GRID_COLS * CELL
BOARD_H     = GRID_ROWS * CELL
INFO_H      = 200
WIDTH       = BOARD_W
HEIGHT      = BOARD_H + INFO_H

FPS         = 30

WHITE       = (255, 255, 255)
BLACK       = (10,  10,  10)
GRAY        = (180, 180, 180)
PANEL_BG    = (240, 242, 248)
ROAD_COLOR  = (200, 200, 210)
WALL_COLOR  = (80,  80,  90)
SLOT_EMPTY  = (170, 220, 170)
SLOT_TARGET = (80,  200, 120)
CAR_COLOR   = (60,  120, 220)
CAR_PARKED  = (30,  180, 80)
NPC_COLOR   = (210,  70,  70)

ACTIONS = {
    0: ( 0, -1),
    1: ( 0,  1),
    2: (-1,  0),
    3: ( 1,  0),
    4: ( 0,  0),
}
ACTION_NAMES = ["위", "아래", "왼쪽", "오른쪽", "정지"]
N_ACTIONS    = len(ACTIONS)

MAX_STEPS               = 150
PRETRAIN_EPISODES       = 500
TRAIN_EPISODES_PER_FRAME = 20
STEP_DELAY_MS           = 320

ALPHA          = 0.15
GAMMA          = 0.95
EPSILON_START  = 1.0
EPSILON_MIN    = 0.05
EPSILON_DECAY  = 0.997

R_PARK_SUCCESS = +200.0
R_CRASH        = -60.0
R_HIT_NPC      = -80.0
R_STEP         = -0.5
R_CLOSER       = +2.0
R_FARTHER      = -1.5
R_TIMEOUT      = -30.0
R_WRONG_ZONE   = -5.0

NUM_NPC_CARS   = 10
NPC_MOVE_EVERY = 5