import math

WORLD_W     = 720.0
WORLD_H     = 576.0
INFO_H      = 220
WIDTH       = int(WORLD_W)
HEIGHT      = int(WORLD_H) + INFO_H
FPS         = 30
TRAIN_EPISODES_PER_FRAME = 5

WHITE       = (255, 255, 255)
BLACK       = (10,  10,  10)
GRAY        = (170, 170, 180)
PANEL_BG    = (238, 241, 248)
ROAD_C      = (195, 198, 210)
CURB_C      = (80,  82,  92)
SLOT_C      = (160, 215, 165)
TARGET_C    = (60,  195, 105)
TARGET_EDGE = (20,  140,  60)
CAR_C       = (55,  115, 220)
CAR_OK_C    = (25,  175,  75)
NPC_C       = (210,  65,  65)
ARROW_C     = (100, 180, 255)

CAR_L       = 36.0
CAR_W       = 18.0
WHEEL_BASE  = 24.0

STEER_DELTA = math.radians(20)
MAX_STEER   = math.radians(35)
SPEED_FWD   = 18.0
SPEED_REV   = 10.0

SLOT_W      = 48.0
SLOT_H      = 80.0

PARK_POS_TOL   = 18.0
PARK_ANG_TOL   = math.radians(15)

N_ACTIONS   = 7
ACTION_NAMES = ["전진", "후진", "전진+좌", "전진+우", "후진+좌", "후진+우", "정지"]

MAX_STEPS   = 600
PRETRAIN_EP = 0
TRAIN_PER_FRAME = 0
STEP_MS     = 80

STATE_DIM   = 12

HIDDEN1     = 128
HIDDEN2     = 128
LR          = 3e-4
GAMMA       = 0.97
EPSILON_START = 1.0
EPSILON_MIN   = 0.05
EPSILON_DECAY = 0.9985
BATCH_SIZE    = 64
REPLAY_CAP    = 30_000
TARGET_SYNC   = 200

R_PARK      = +300.0
R_CRASH     = -80.0
R_HIT_NPC   = -100.0
R_TIMEOUT   = -40.0
R_STEP      = -0.3
R_CLOSER    = +3.0
R_FARTHER   = -2.0
R_ALIGN     = +2.0
R_NPC_PROX  = -0.5
R_IDLE      = -1.0
R_WRONG_SLOT = -8.0

NUM_NPC     = 5
NPC_SPEED   = 30.0
NPC_MOVE_EVERY = 90