import pygame
import sys
import math
import random

pygame.init()

W, H = 520, 640
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("BOUNCE BALL")
clock = pygame.time.Clock()
FPS = 60

# ── 색상 ───────────────────────────────────────────────────────────────
BG         = (15,  12,  30)
COL_FLOOR  = (60,  60,  90)
COL_FLOOR2 = (80,  60, 110)
COL_SPIKE  = (220,  50,  50)
COL_JUMP   = ( 80, 220, 120)
COL_MOVE   = ( 80, 160, 220)
COL_ICE    = (160, 220, 255)
COL_COIN   = (255, 200,  40)
COL_GOAL   = (255, 180,  50)
WHITE      = (255, 255, 255)
CYAN       = ( 50, 200, 255)
PINK       = (255,  80, 140)
DARKGRAY   = ( 30,  30,  50)

def load_korean_font(size, bold=False):
    """한글 지원 폰트를 OS별로 탐색해서 로드"""
    candidates = [
        # Windows
        "malgun gothic", "맑은 고딕", "gulim", "dotum",
        # macOS
        "apple sd gothic neo", "applegothic",
        # Linux
        "nanum gothic", "nanumgothic", "noto sans cjk kr",
        "unifont",
    ]
    for name in candidates:
        try:
            f = pygame.font.SysFont(name, size, bold=bold)
            # 한글 렌더링 테스트
            test = f.render("가", True, (255, 255, 255))
            if test.get_width() > 4:
                return f
        except Exception:
            pass
    # 마지막 폴백: pygame 기본 폰트 (한글 깨지지만 크래시 방지)
    return pygame.font.Font(None, size + 6)

FONT_BIG = load_korean_font(40, bold=True)
FONT_MID = load_korean_font(22, bold=True)
FONT_SM  = load_korean_font(16)

# ══════════════════════════════════════════════════════════════════════
# 맵 데이터
# platform: [x, y, w, h, type]  type: normal|spike|jumppad|move|ice
# move 타입: [x, y, w, h, 'move', range_x1, range_x2]
# ══════════════════════════════════════════════════════════════════════
# 바운스 높이 기준:
#   일반 바운스: vy=10, gravity=0.6 → 최대 약 83px 상승
#   점프패드:   vy=18, gravity=0.6 → 최대 약 270px 상승
# 발판 간격은 반드시 70px 이내 (일반) 또는 점프패드로 연결

LEVELS = [
    # ── STAGE 1 : 계단식, 발판 간격 60px ─────────────────────────────
    {
        'name': 'STAGE 1',
        'bg': (15, 12, 30),
        'spawn': (55, 530),
        'goal': (440, 100, 36, 36),
        'platforms': [
            [0,   600, 520, 20, 'normal'],
            [0,   550,  90, 14, 'normal'],
            [110, 490, 100, 14, 'normal'],
            [250, 430, 100, 14, 'normal'],
            [370, 370,  90, 14, 'normal'],
            [210, 310, 100, 14, 'normal'],
            [ 60, 250, 100, 14, 'normal'],
            [210, 190, 110, 14, 'normal'],
            [360, 130, 130, 14, 'normal'],
            # 스파이크 (밟으면 안 됨, 옆으로 피해서 감)
            [250, 414,  26, 14, 'spike'],
            [370, 354,  26, 14, 'spike'],
        ],
        'coins': [
            (155, 465), (295, 405), (415, 345),
            (255, 285), (105, 225), (260, 165), (425, 105),
        ],
    },
    # ── STAGE 2 : 이동 발판 등장, 간격 60px ──────────────────────────
    {
        'name': 'STAGE 2',
        'bg': (10, 20, 35),
        'spawn': (40, 530),
        'goal': (435, 100, 36, 36),
        'platforms': [
            [0,   600, 520, 20, 'normal'],
            [0,   550, 110, 14, 'normal'],
            [150, 490, 100, 14, 'normal'],
            [300, 430,  90, 14, 'normal'],
            [ 20, 370,  80, 14, 'move',  10, 220],
            [220, 310,  80, 14, 'move', 180, 420],
            [350, 250,  80, 14, 'move', 280, 460],
            [ 60, 190,  90, 14, 'normal'],
            [210, 130, 100, 14, 'normal'],
            [370,  70, 120, 14, 'normal'],
            [300, 414,  26, 14, 'spike'],
            [150, 474,  26, 14, 'spike'],
        ],
        'coins': [
            (195, 465), (345, 405),
            (55,  345), (255, 285), (385, 225), (100, 165), (255, 105), (425,  45),
        ],
    },
    # ── STAGE 3 : 얼음 + 점프패드 ────────────────────────────────────
    # 점프패드(vy=18) → 최대 270px 상승, 이후 발판 간격 60px
    {
        'name': 'STAGE 3',
        'bg': (10, 25, 40),
        'spawn': (50, 530),
        'goal': (440, 80, 36, 36),
        'platforms': [
            [0,   600, 520, 20, 'normal'],
            [0,   550, 100, 14, 'normal'],
            # 점프패드 → 위로 270px (y=550 → y=280)
            [ 50, 550,  60, 12, 'jumppad'],
            [130, 490,  80, 14, 'ice'],
            [260, 430,  80, 14, 'ice'],
            [380, 370,  80, 14, 'normal'],
            # 점프패드 도달 지점
            [150, 280,  90, 14, 'normal'],
            [ 20, 220,  80, 14, 'ice'],
            [150, 160,  80, 14, 'normal'],
            [290, 100,  90, 14, 'normal'],
            [420,  40, 100, 14, 'normal'],
            # 스파이크
            [260, 414,  26, 14, 'spike'],
            [380, 354,  26, 14, 'spike'],
            [ 80, 204,  26, 14, 'spike'],
        ],
        'coins': [
            (170, 465), (300, 405), (420, 345),
            (190, 255), ( 55, 195), (185, 135), (330,  75), (460,  15),
        ],
    },
    # ── STAGE 4 : 함정 지대 + 이동발판 ──────────────────────────────
    {
        'name': 'STAGE 4',
        'bg': (25, 10, 30),
        'spawn': (30, 530),
        'goal': (450, 60, 36, 36),
        'platforms': [
            [0,   600, 520, 20, 'normal'],
            # 바닥 스파이크 통로
            [0,   550,  80, 14, 'normal'],
            [ 90, 550,  26, 14, 'spike'],
            [130, 550,  80, 14, 'normal'],
            [225, 550,  26, 14, 'spike'],
            [265, 550,  80, 14, 'normal'],
            [360, 550,  26, 14, 'spike'],
            [400, 550, 120, 14, 'normal'],
            # 2층 간격 60px
            [ 30, 490,  90, 14, 'normal'],
            [160, 490,  26, 14, 'spike'],
            [205, 490,  90, 14, 'normal'],
            [345, 490,  26, 14, 'spike'],
            [390, 490,  90, 14, 'normal'],
            # 이동발판 층
            [ 20, 430,  80, 14, 'move',  10, 200],
            [210, 370,  80, 14, 'move', 170, 400],
            [370, 310,  80, 14, 'move', 290, 470],
            # 얼음 층 (간격 60px)
            [ 40, 250,  70, 14, 'ice'],
            [160, 190,  70, 14, 'ice'],
            [280, 130,  70, 14, 'normal'],
            # 점프패드 → 마지막 발판
            [370, 130,  55, 12, 'jumppad'],
            [415,  80, 105, 14, 'normal'],
            # 스파이크
            [ 20, 234,  26, 14, 'spike'],
            [140, 174,  26, 14, 'spike'],
        ],
        'coins': [
            (155, 525), (300, 525),
            ( 70, 465), (248, 465), (432, 465),
            ( 55, 405), (248, 345), (405, 285),
            ( 70, 225), (190, 165), (310, 105), (460,  55),
        ],
    },
    # ── FINAL : 종합 ─────────────────────────────────────────────────
    {
        'name': 'FINAL STAGE',
        'bg': (20, 5, 25),
        'spawn': (35, 530),
        'goal': (450, 45, 36, 36),
        'platforms': [
            [0,   600, 520, 20, 'normal'],
            # 바닥 스파이크
            [0,   550,  70, 14, 'normal'],
            [ 80, 550,  26, 14, 'spike'],
            [120, 550,  70, 14, 'normal'],
            [205, 550,  26, 14, 'spike'],
            [245, 550,  70, 14, 'normal'],
            [330, 550,  26, 14, 'spike'],
            [370, 550, 150, 14, 'normal'],
            # 이동발판 층
            [  0, 490,  70, 14, 'move',   0, 160],
            [175, 490,  26, 14, 'spike'],
            [210, 490,  70, 14, 'move', 180, 380],
            [390, 490,  26, 14, 'spike'],
            [430, 490,  90, 14, 'normal'],
            # 얼음 층
            [ 40, 430,  70, 14, 'ice'],
            [160, 430,  26, 14, 'spike'],
            [200, 430,  70, 14, 'ice'],
            [320, 430,  26, 14, 'spike'],
            [360, 430,  90, 14, 'ice'],
            # 일반 층
            [ 20, 370,  80, 14, 'normal'],
            [155, 370,  26, 14, 'spike'],
            [200, 370,  80, 14, 'normal'],
            [355, 370,  26, 14, 'spike'],
            [400, 370,  80, 14, 'normal'],
            # 점프패드 → 위층 (y=370 → y~100)
            [ 25, 370,  55, 12, 'jumppad'],
            [  0,  95, 120, 14, 'normal'],
            [155,  95,  26, 14, 'spike'],
            [195,  95,  90, 14, 'normal'],
            [310, 130,  80, 14, 'move', 280, 450],
            [420,  65, 100, 14, 'normal'],
        ],
        'coins': [
            (150, 525), (290, 525), (445, 525),
            ( 35, 465), (245, 465),
            ( 70, 405), (230, 405), (390, 405),
            ( 55, 345), (235, 345), (435, 345),
            ( 55,  70), (235,  70), (465,  40),
        ],
    },
]

# ══════════════════════════════════════════════════════════════════════
# 파티클
# ══════════════════════════════════════════════════════════════════════
particles = []

def spawn_particles(x, y, color, n=10, speed=4):
    for _ in range(n):
        a = random.uniform(0, math.pi * 2)
        s = random.uniform(1, speed)
        particles.append({
            'x': x, 'y': y,
            'dx': math.cos(a) * s,
            'dy': math.sin(a) * s - 1,
            'life': 1.0, 'color': color,
            'r': random.uniform(2, 4)
        })

def update_draw_particles(surface):
    alive = []
    for p in particles:
        p['x'] += p['dx']
        p['y'] += p['dy']
        p['dy'] += 0.12
        p['life'] -= 0.035
        if p['life'] > 0:
            alive.append(p)
            r = max(1, int(p['r'] * p['life']))
            a = int(p['life'] * 220)
            s = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*p['color'], a), (r + 1, r + 1), r)
            surface.blit(s, (int(p['x']) - r - 1, int(p['y']) - r - 1))
    particles.clear()
    particles.extend(alive)

# ══════════════════════════════════════════════════════════════════════
# 플랫폼
# ══════════════════════════════════════════════════════════════════════
class Platform:
    def __init__(self, data):
        self.x = float(data[0])
        self.y = float(data[1])
        self.w = data[2]
        self.h = data[3]
        self.ptype = data[4]
        self.move_range = None
        self.move_dir = 1
        self.move_spd = 1.3
        if self.ptype == 'move' and len(data) >= 7:
            self.move_range = (data[5], data[6])

    def update(self):
        if self.ptype == 'move' and self.move_range:
            self.x += self.move_spd * self.move_dir
            if self.x < self.move_range[0]:
                self.x = float(self.move_range[0])
                self.move_dir = 1
            if self.x + self.w > self.move_range[1]:
                self.x = float(self.move_range[1] - self.w)
                self.move_dir = -1

    def get_rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def draw(self, surface):
        r = self.get_rect()
        if self.ptype == 'spike':
            self._draw_spike(surface, r)
        elif self.ptype == 'jumppad':
            self._draw_jumppad(surface, r)
        elif self.ptype == 'ice':
            self._draw_ice(surface, r)
        elif self.ptype == 'move':
            self._draw_move(surface, r)
        else:
            self._draw_normal(surface, r)

    def _draw_normal(self, surface, r):
        pygame.draw.rect(surface, COL_FLOOR2, r, border_radius=4)
        pygame.draw.rect(surface, (100, 90, 140), r, 2, border_radius=4)
        pygame.draw.line(surface, (140, 130, 180), (r.x + 4, r.y + 3), (r.x + r.w - 4, r.y + 3), 2)

    def _draw_ice(self, surface, r):
        pygame.draw.rect(surface, COL_ICE, r, border_radius=4)
        pygame.draw.rect(surface, (200, 240, 255), r, 2, border_radius=4)
        pygame.draw.line(surface, WHITE, (r.x + 4, r.y + 3), (r.x + 16, r.y + 3), 2)
        pygame.draw.line(surface, WHITE, (r.x + 4, r.y + 7), (r.x + 10, r.y + 7), 1)

    def _draw_move(self, surface, r):
        pygame.draw.rect(surface, COL_MOVE, r, border_radius=4)
        pygame.draw.rect(surface, (120, 200, 255), r, 2, border_radius=4)
        mid = r.centerx
        pygame.draw.polygon(surface, WHITE, [
            (mid - 10, r.y + 3), (mid + 10, r.y + 3),
            (mid + 14, r.centery), (mid + 10, r.y + r.h - 3),
            (mid - 10, r.y + r.h - 3), (mid - 14, r.centery)
        ])

    def _draw_spike(self, surface, r):
        n = max(1, r.w // 14)
        sw = r.w / n
        for i in range(n):
            sx = r.x + i * sw
            pts = [
                (sx, r.y + r.h),
                (sx + sw, r.y + r.h),
                (sx + sw / 2, r.y)
            ]
            pygame.draw.polygon(surface, COL_SPIKE, pts)
            pygame.draw.polygon(surface, PINK, pts, 1)

    def _draw_jumppad(self, surface, r):
        pygame.draw.rect(surface, (30, 180, 80), r, border_radius=3)
        pygame.draw.rect(surface, COL_JUMP, r, 2, border_radius=3)
        mx, my = r.centerx, r.centery
        pygame.draw.polygon(surface, WHITE, [
            (mx, r.y + 1), (mx - 7, my + 3), (mx + 7, my + 3)
        ])
        pygame.draw.line(surface, WHITE, (mx, my + 2), (mx, r.y + r.h - 2), 2)

# ══════════════════════════════════════════════════════════════════════
# 공
# ══════════════════════════════════════════════════════════════════════
GRAVITY  = 0.6
BOUNCE_VY = 10.0  # 일반 바운스 (최대 높이 약 83px)
MOVE_SPD = 4.0
BALL_R   = 11

class Ball:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.r  = BALL_R
        self.on_ground = False
        self.dead = False
        self.trail = []
        self.cur_friction = 0.85
        self.squash = 1.0
        self.squash_v = 0.0

    def reset(self, x, y):
        self.x, self.y = float(x), float(y)
        self.vx = self.vy = 0.0
        self.on_ground = False
        self.dead = False
        self.trail.clear()
        self.squash = 1.0
        self.squash_v = 0.0
        self.cur_friction = 0.85

    def update(self, keys, platforms):
        # 방향키 누를 때만 이동, 안 누르면 즉시 정지
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vx = -MOVE_SPD
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vx = MOVE_SPD
        else:
            self.vx = 0.0

        # 중력
        self.vy += GRAVITY
        if self.vy > 20:
            self.vy = 20  # 최대 낙하속도 제한

        # 트레일
        self.trail.append((self.x, self.y))
        if len(self.trail) > 14:
            self.trail.pop(0)

        # 찌그러짐 복원
        self.squash_v += (1.0 - self.squash) * 0.35
        self.squash_v *= 0.65
        self.squash += self.squash_v

        # ── X 이동 후 충돌 ────────────────────────────────────────────
        self.x += self.vx
        self._collide_x(platforms)

        # ── Y 이동 후 충돌 ────────────────────────────────────────────
        self.on_ground = False
        self.cur_friction = 0.85
        self.y += self.vy
        self._collide_y(platforms)

        # 화면 좌우 벽
        if self.x - self.r < 0:
            self.x = float(self.r)
            self.vx = abs(self.vx) * 0.5
        if self.x + self.r > W:
            self.x = float(W - self.r)
            self.vx = -abs(self.vx) * 0.5

        # 화면 아래로 떨어지면 사망
        if self.y - self.r > H + 40:
            self.dead = True

    def _collide_x(self, platforms):
        for p in platforms:
            if p.ptype in ('spike', 'jumppad'):
                continue
            r = p.get_rect()
            # 수직 범위 겹침 확인 (공 중심 기준, 약간 여유)
            if not (r.top + 2 < self.y + self.r * 0.85 and
                    self.y - self.r * 0.85 < r.bottom - 2):
                continue
            # 수평 겹침 확인
            if self.x + self.r > r.left and self.x - self.r < r.right:
                if self.vx > 0 and self.x < r.centerx:
                    self.x = float(r.left - self.r)
                    self.vx *= -0.3
                elif self.vx < 0 and self.x > r.centerx:
                    self.x = float(r.right + self.r)
                    self.vx *= -0.3

    def _collide_y(self, platforms):
        for p in platforms:
            r = p.get_rect()
            # X 범위 안에 있는지 먼저 확인
            if not (r.left - self.r * 0.8 < self.x < r.right + self.r * 0.8):
                continue

            # 스파이크: 위쪽 삼각형에 닿으면 즉사
            if p.ptype == 'spike':
                if (self.y + self.r > r.top and
                        self.y - self.r < r.bottom and
                        self.vy >= 0):
                    self.dead = True
                continue

            # ── 위에서 착지 ───────────────────────────────────────────
            prev_bottom = (self.y - self.vy) + self.r
            curr_bottom = self.y + self.r
            if self.vy > 0 and prev_bottom <= r.top + 2 and curr_bottom >= r.top:
                # 발판 위에 정확히 올려놓기
                self.y = float(r.top - self.r)
                self.on_ground = True

                if p.ptype == 'jumppad':
                    self.vy = -18.0
                    spawn_particles(self.x, self.y + self.r, COL_JUMP, 16, 7)
                    self.squash = 0.45
                    self.squash_v = 0.0
                    self.cur_friction = 0.85
                else:
                    # 항상 일정한 속도로 튀어오름 - 에너지 손실 없음
                    self.vy = -BOUNCE_VY
                    self.squash = 0.6
                    self.squash_v = 0.0
                    spawn_particles(self.x, self.y + self.r,
                                    COL_ICE if p.ptype == 'ice' else COL_FLOOR, 5, 3)
                    self.cur_friction = 0.97 if p.ptype == 'ice' else 0.80

            # ── 아래에서 천장 충돌 ────────────────────────────────────
            elif self.vy < 0:
                prev_top = (self.y - self.vy) - self.r
                curr_top = self.y - self.r
                if prev_top >= r.bottom - 1 and curr_top <= r.bottom:
                    self.y = float(r.bottom + self.r)
                    self.vy = abs(self.vy) * 0.2  # 천장에 살짝 튕김

    def draw(self, surface):
        for i, (tx, ty) in enumerate(self.trail):
            ratio = i / max(1, len(self.trail))
            a = int(160 * ratio ** 2)
            rad = max(1, int(self.r * 0.55 * ratio))
            s = pygame.Surface((rad * 2 + 2, rad * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*CYAN, a), (rad + 1, rad + 1), rad)
            surface.blit(s, (int(tx) - rad - 1, int(ty) - rad - 1))

        sx = self.r * (2.0 - self.squash)
        sy = self.r * self.squash
        bx, by = int(self.x), int(self.y)

        for g in (18, 12, 6):
            ga = 25 + g * 3
            gs = pygame.Surface((int(sx + g) * 2 + 4, int(sy + g) * 2 + 4), pygame.SRCALPHA)
            pygame.draw.ellipse(gs, (*CYAN, ga), (0, 0, int((sx + g) * 2 + 2), int((sy + g) * 2 + 2)))
            surface.blit(gs, (bx - int(sx + g) - 1, by - int(sy + g) - 1))

        surf = pygame.Surface((int(sx * 2) + 4, int(sy * 2) + 4), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, WHITE, (0, 0, int(sx * 2) + 2, int(sy * 2) + 2))
        pygame.draw.ellipse(surf, (*CYAN, 180),
                             (int(sx * 0.3), int(sy * 0.15), int(sx * 0.9), int(sy * 0.6)))
        surface.blit(surf, (bx - int(sx) - 1, by - int(sy) - 1))

# ══════════════════════════════════════════════════════════════════════
# 코인 / 골
# ══════════════════════════════════════════════════════════════════════
class Coin:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.alive = True
        self.t = random.uniform(0, math.pi * 2)

    def update(self):
        self.t += 0.06

    def draw(self, surface):
        if not self.alive:
            return
        bob = math.sin(self.t) * 3
        cx, cy = int(self.x), int(self.y + bob)
        gs = pygame.Surface((28, 28), pygame.SRCALPHA)
        pygame.draw.circle(gs, (*COL_COIN, 60), (14, 14), 13)
        surface.blit(gs, (cx - 14, cy - 14))
        pygame.draw.circle(surface, COL_COIN, (cx, cy), 9)
        pygame.draw.circle(surface, (255, 240, 180), (cx - 2, cy - 2), 4)

    def check(self, ball):
        if self.alive and math.hypot(self.x - ball.x, self.y - ball.y) < ball.r + 10:
            self.alive = False
            spawn_particles(self.x, self.y, COL_COIN, 12, 5)
            return True
        return False


class Goal:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
        self.t = 0.0

    def update(self):
        self.t += 0.05

    def draw(self, surface):
        pulse = abs(math.sin(self.t)) * 0.4 + 0.6
        c = (int(COL_GOAL[0] * pulse), int(COL_GOAL[1] * pulse), int(COL_GOAL[2] * pulse))
        for g in (20, 12, 5):
            ga = 40 + g * 4
            gs = pygame.Surface((self.rect.w + g * 2, self.rect.h + g * 2), pygame.SRCALPHA)
            pygame.draw.rect(gs, (*c, ga), (0, 0, self.rect.w + g * 2, self.rect.h + g * 2),
                             border_radius=8)
            surface.blit(gs, (self.rect.x - g, self.rect.y - g))
        pygame.draw.rect(surface, c, self.rect, border_radius=6)
        cx, cy = self.rect.centerx, self.rect.centery
        pts = []
        for i in range(10):
            a = math.pi / 2 + i * math.pi / 5
            r = 12 if i % 2 == 0 else 6
            pts.append((cx + math.cos(a) * r, cy - math.sin(a) * r))
        pygame.draw.polygon(surface, WHITE, pts)

    def check(self, ball):
        return self.rect.collidepoint(ball.x, ball.y)

# ══════════════════════════════════════════════════════════════════════
# 유틸
# ══════════════════════════════════════════════════════════════════════
def draw_text(surface, text, font, color, cx, cy, glow=None):
    if glow:
        for dx in (-2, 0, 2):
            for dy in (-2, 0, 2):
                if dx == dy == 0:
                    continue
                s = font.render(text, True, glow)
                surface.blit(s, s.get_rect(center=(cx + dx, cy + dy)))
    s = font.render(text, True, color)
    surface.blit(s, s.get_rect(center=(cx, cy)))

def load_level(idx):
    data = LEVELS[idx]
    platforms = [Platform(p) for p in data['platforms']]
    coins = [Coin(*c) for c in data['coins']]
    goal = Goal(*data['goal'])
    return platforms, coins, goal, data['spawn'], data['name'], data.get('bg', BG)

# ══════════════════════════════════════════════════════════════════════
# 메인
# ══════════════════════════════════════════════════════════════════════
def main():
    level_idx = 0
    score = 0
    total_coins = 0
    lives = 3
    state = 'idle'

    platforms, coins, goal, spawn, stage_name, bg_color = load_level(level_idx)
    ball = Ball(*spawn)
    death_timer = 0
    clear_timer = 0
    idle_t = 0
    shake = 0

    star_list = [(random.randint(0, W), random.randint(0, H),
                  random.uniform(0.4, 1.8), random.uniform(0, math.pi * 2))
                 for _ in range(100)]

    def restart_level():
        nonlocal platforms, coins, goal, spawn, stage_name, bg_color, shake
        platforms, coins, goal, spawn, stage_name, bg_color = load_level(level_idx)
        ball.reset(*spawn)
        shake = 0

    while True:
        clock.tick(FPS)
        keys = pygame.key.get_pressed()
        idle_t += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_r and state in ('dead', 'gameover'):
                    lives = 3
                    score = 0
                    total_coins = 0
                    level_idx = 0
                    restart_level()
                    state = 'playing'
                if event.key == pygame.K_SPACE and state == 'idle':
                    state = 'playing'

        # ── 업데이트 ──────────────────────────────────────────────────
        if state == 'playing':
            for p in platforms:
                p.update()
            for c in coins:
                c.update()
            goal.update()
            ball.update(keys, platforms)

            for c in coins:
                if c.check(ball):
                    score += 100
                    total_coins += 1

            if goal.check(ball):
                score += 500
                spawn_particles(ball.x, ball.y, COL_GOAL, 30, 8)
                if level_idx < len(LEVELS) - 1:
                    state = 'stageclear'
                    clear_timer = 110
                else:
                    state = 'allclear'
                    clear_timer = 200

            if ball.dead:
                lives -= 1
                shake = 18
                spawn_particles(ball.x, ball.y, PINK, 25, 7)
                if lives <= 0:
                    state = 'gameover'
                else:
                    state = 'dead'
                    death_timer = 60

        elif state == 'dead':
            death_timer -= 1
            if death_timer <= 0:
                restart_level()
                state = 'playing'

        elif state == 'stageclear':
            clear_timer -= 1
            goal.update()
            if clear_timer <= 0:
                level_idx += 1
                restart_level()
                state = 'playing'

        elif state == 'allclear':
            clear_timer -= 1
            if clear_timer <= 0:
                level_idx = 0
                score = 0
                total_coins = 0
                lives = 3
                restart_level()
                state = 'idle'

        if shake > 0:
            shake -= 1

        # ── 렌더링 ────────────────────────────────────────────────────
        ox = random.randint(-shake // 2, shake // 2) if shake > 1 else 0
        oy = random.randint(-shake // 2, shake // 2) if shake > 1 else 0

        buf = pygame.Surface((W, H))
        buf.fill(bg_color)

        for (sx, sy, sr, sp) in star_list:
            a = int((math.sin(idle_t * 0.015 * sp + sp) * 0.5 + 0.5) * 160 + 60)
            pygame.draw.circle(buf, (min(255, a), min(255, a + 15), min(255, a + 30)), (sx, sy), int(sr))

        for gx in range(0, W, 44):
            pygame.draw.line(buf, (25, 22, 45), (gx, 0), (gx, H))
        for gy in range(0, H, 44):
            pygame.draw.line(buf, (25, 22, 45), (0, gy), (W, gy))

        for p in platforms:
            p.draw(buf)
        for c in coins:
            c.draw(buf)
        goal.draw(buf)

        if state not in ('gameover', 'idle', 'allclear'):
            if not (state == 'dead' and death_timer % 8 < 4):
                ball.draw(buf)

        update_draw_particles(buf)

        # HUD
        draw_text(buf, f"SCORE  {score:06d}", FONT_SM, CYAN, W // 2, 14)
        draw_text(buf, stage_name, FONT_SM, (180, 160, 220), W // 2, 30)
        for i in range(3):
            col = PINK if i < lives else (50, 40, 70)
            pygame.draw.circle(buf, col, (W - 22 - i * 22, 15), 7)
        pygame.draw.circle(buf, COL_COIN, (18, 15), 7)
        draw_text(buf, f"x{total_coins}", FONT_SM, COL_COIN, 40, 15)

        if state == 'playing' and idle_t < 220:
            hint_a = max(0, 255 - (idle_t - 160) * 5) if idle_t > 160 else 255
            hs = FONT_SM.render("← → 키로 이동  |  점프패드(초록) 위에서 자동 점프!", True, (150, 140, 180))
            hs.set_alpha(hint_a)
            buf.blit(hs, hs.get_rect(center=(W // 2, H - 18)))

        # 오버레이
        if state == 'idle':
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((5, 5, 20, 185))
            buf.blit(ov, (0, 0))
            draw_text(buf, "BOUNCE BALL", FONT_BIG, WHITE, W // 2, H // 2 - 80, CYAN)
            draw_text(buf, "← → 키로 공을 굴려 골(별)까지!", FONT_SM, (190, 180, 230), W // 2, H // 2 - 10)
            draw_text(buf, "  점프패드(초록)  :  높이 튀어오름", FONT_SM, COL_JUMP, W // 2, H // 2 + 22)
            draw_text(buf, "  얼음(하늘색)    :  미끄러움", FONT_SM, COL_ICE, W // 2, H // 2 + 46)
            draw_text(buf, "  스파이크(빨강)  :  즉사!", FONT_SM, COL_SPIKE, W // 2, H // 2 + 70)
            draw_text(buf, "  이동발판(파랑)  :  좌우로 움직임", FONT_SM, COL_MOVE, W // 2, H // 2 + 94)
            if (idle_t // 40) % 2 == 0:
                draw_text(buf, "PRESS SPACE TO START", FONT_MID, CYAN, W // 2, H // 2 + 140)

        elif state == 'dead':
            alpha = max(0, 200 - death_timer * 3)
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((30, 0, 0, alpha))
            buf.blit(ov, (0, 0))
            draw_text(buf, f"남은 목숨  {lives}", FONT_MID, PINK, W // 2, H // 2, (80, 0, 0))

        elif state == 'stageclear':
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((0, 20, 0, 160))
            buf.blit(ov, (0, 0))
            draw_text(buf, "STAGE CLEAR!", FONT_BIG, COL_JUMP, W // 2, H // 2 - 40, (0, 80, 30))
            draw_text(buf, f"SCORE: {score:06d}", FONT_MID, WHITE, W // 2, H // 2 + 20)
            draw_text(buf, "다음 스테이지로...", FONT_SM, (150, 220, 150), W // 2, H // 2 + 55)

        elif state == 'gameover':
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((20, 0, 0, 200))
            buf.blit(ov, (0, 0))
            draw_text(buf, "GAME OVER", FONT_BIG, PINK, W // 2, H // 2 - 60, (80, 0, 20))
            draw_text(buf, f"SCORE: {score:06d}", FONT_MID, WHITE, W // 2, H // 2 + 10)
            draw_text(buf, f"코인: {total_coins}개", FONT_SM, COL_COIN, W // 2, H // 2 + 45)
            if (idle_t // 40) % 2 == 0:
                draw_text(buf, "R 키로 재시작", FONT_MID, CYAN, W // 2, H // 2 + 90)

        elif state == 'allclear':
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((20, 15, 0, 185))
            buf.blit(ov, (0, 0))
            draw_text(buf, "ALL CLEAR!!", FONT_BIG, COL_GOAL, W // 2, H // 2 - 70, (100, 70, 0))
            draw_text(buf, "모든 스테이지 클리어!", FONT_MID, WHITE, W // 2, H // 2 - 10)
            draw_text(buf, f"최종 스코어: {score:06d}", FONT_MID, COL_COIN, W // 2, H // 2 + 35)
            draw_text(buf, f"수집 코인: {total_coins}개", FONT_SM, COL_COIN, W // 2, H // 2 + 70)

        screen.blit(buf, (ox, oy))
        pygame.display.flip()

if __name__ == '__main__':
    main()