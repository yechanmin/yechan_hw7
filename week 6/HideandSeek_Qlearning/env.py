# env.py
import random
import math
import pygame
from settings import *
from entities import Hider, Seeker, SafeZone

class HideAndSeekEnv:
    def __init__(self):
        self.grid_size = GRID_SIZE
        # 벽은 한 번만 생성 → 에피소드가 바뀌어도 유지
        self.walls = self._generate_fixed_walls()
        self.reset()

    # ── 벽 생성 (게임 시작 시 1회) ──────────────────────────
    def _generate_fixed_walls(self):
        """고정 미로 형태의 벽 배치 — 학습 안정성을 위해 매 에피소드 동일"""
        walls = set()
        patterns = [
            [(2, 1), (3, 1), (4, 1)],
            [(6, 3), (7, 3)],
            [(1, 5), (2, 5), (3, 5)],
            [(5, 6), (6, 6), (7, 6)],
            [(2, 8), (3, 8)],
            [(7, 8), (8, 8)],
            [(4, 3), (4, 4)],
            [(8, 1), (8, 2)],
            [(1, 7), (1, 8)],
            [(6, 4), (6, 5)],
        ]
        for group in patterns:
            for pos in group:
                walls.add(pos)
        return walls
    # 빈 위치를 랜덤으로 찾음.
    def _random_empty_pos(self, exclude=None):
        exclude = exclude or set()
        while True:
            pos = (random.randint(0, GRID_SIZE - 1),
                   random.randint(0, GRID_SIZE - 1))
            if pos not in self.walls and pos not in exclude:
                return pos

    # 에피소드 시작시 호출. 이전 거리값은 보상 계산용
    def reset(self):
        placed = set()
        hpos = self._random_empty_pos(placed); placed.add(hpos)
        spos = self._random_empty_pos(placed); placed.add(spos)
        gpos = self._random_empty_pos(placed)

        self.hider     = Hider(*hpos)
        self.seeker    = Seeker(*spos)
        self.safe_zone = SafeZone(*gpos)
        self.steps     = 0
        self._prev_dist_goal  = self._manhattan(self.hider.pos, self.safe_zone.pos)
        self._prev_dist_seek  = self._manhattan(self.hider.pos, self.seeker.pos)
        return self.get_state()

    @staticmethod
    def _manhattan(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def get_state(self):
        hx, hy = self.hider.pos
        sx, sy = self.seeker.pos
        gx, gy = self.safe_zone.pos

        gdx = gx - hx          # goal 상대 X (-9~9)
        gdy = gy - hy          # goal 상대 Y
        sdx = sx - hx          # seeker 상대 X
        sdy = sy - hy          # seeker 상대 Y
        in_fov = int(self._can_see())           # 시야 내 여부
        dist_g = min(self._manhattan(self.hider.pos, self.safe_zone.pos), 9)
        dist_s = min(self._manhattan(self.hider.pos, self.seeker.pos), 9)

        return (gdx, gdy, sdx, sdy, in_fov, dist_g, dist_s)

    # ── 이동 ───────────────────────────────────────────────
    def _move_hider(self, action):
        dx, dy = ACTIONS[action]
        x, y   = self.hider.pos
        nx = max(0, min(GRID_SIZE - 1, x + dx))
        ny = max(0, min(GRID_SIZE - 1, y + dy))
        if (nx, ny) not in self.walls:
            self.hider.set_pos(nx, ny)

    def _blocked(self, sx, sy, hx, hy):
        dx    = hx - sx
        dy    = hy - sy
        steps = max(abs(dx), abs(dy))
        for i in range(1, steps):
            x = round(sx + dx * i / steps)
            y = round(sy + dy * i / steps)
            if (x, y) in self.walls:
                return True
        return False
    #seeker가 hider를 볼 수 있는지 판단
    def _can_see(self):
        hx, hy = self.hider.pos
        sx, sy = self.seeker.pos
        dx, dy = self.seeker.direction
        vx = hx - sx
        vy = hy - sy
        dist = math.sqrt(vx * vx + vy * vy)
        if dist > 5:
            return False
        dot = vx * dx + vy * dy
        if dot <= 0:
            return False
        if dot / dist < 0.7:
            return False
        if self._blocked(sx, sy, hx, hy):
            return False
        return True
    # 보이면 추적, 안보이면 랜덤 행동.
    def _move_seeker(self):
        if self._can_see():
            self.seeker.chase(self.hider.pos, GRID_SIZE, self.walls)#hider를 추적함.
        else:
            sx, sy = self.seeker.pos
            moves  = [(1, 0), (-1, 0), (0, 1), (0, -1)]
            random.shuffle(moves)
            for dx, dy in moves:
                nx, ny = sx + dx, sy + dy
                if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                    if (nx, ny) not in self.walls:
                        self.seeker.set_pos(nx, ny)
                        return

    # action이 넘어 오면 hider 이동->종료 체크=> seeker이동->종료 체크-> 보상계산->(state, reward, done)반환
    def step(self, action):
        self.steps += 1
        self._move_hider(action)

        if self.hider.pos == self.safe_zone.pos:
            return self.get_state(), 200.0, True, {"result": "escaped"} #safezone 도달 200보장

        if self.steps % 2 == 0:
            self._move_seeker()

        if self.hider.pos == self.seeker.pos:
            return self.get_state(), -200.0, True, {"result": "caught"} #잡힘 -200

        if self.steps >= MAX_STEPS:
            return self.get_state(), -50.0, True, {"result": "timeout"} #시간 초과 -50

        # ── 보상 설계의 핵심 ──
        reward = -0.3   # 스텝 기본 시간 패널티 (빠른 이동 유도)

        # 1) goal 접근 보상 - 가까워지면 보상
        dist_g = self._manhattan(self.hider.pos, self.safe_zone.pos)
        reward += (self._prev_dist_goal - dist_g) * 3.0
        self._prev_dist_goal = dist_g

        # 2) seeker 회피 보상 - 멀어지면 보상
        dist_s = self._manhattan(self.hider.pos, self.seeker.pos)
        reward += (dist_s - self._prev_dist_seek) * 1.5
        self._prev_dist_seek = dist_s

        # 3) seeker 근접 패널티
        if dist_s <= 1:
            reward -= 10.0
        elif dist_s <= 2:
            reward -= 3.0

        # 4) 시야 노출 패널티
        if self._can_see():
            reward -= 5.0

        return self.get_state(), reward, False, {"result": "running"}

    def _ray_until_wall(self, sx, sy, angle, max_dist=5):
        step = 0.2
        dist = 0.0
        px   = sx + 0.5
        py   = sy + 0.5
        while dist < max_dist:
            px   += math.cos(angle) * step
            py   += math.sin(angle) * step
            dist += step
            gx = int(px); gy = int(py)
            if not (0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE):
                break
            if (gx, gy) in self.walls:
                break
        return px * CELL_SIZE, py * CELL_SIZE

    def _draw_fov(self, screen):
        sx, sy     = self.seeker.pos
        cx = sx * CELL_SIZE + CELL_SIZE // 2
        cy = sy * CELL_SIZE + CELL_SIZE // 2
        dx, dy     = self.seeker.direction
        base_angle = math.atan2(dy, dx)
        half_fov   = math.pi / 4
        ray_count  = 40
        points     = [(cx, cy)]
        for i in range(ray_count):
            t     = i / (ray_count - 1)
            angle = base_angle - half_fov + (2 * half_fov * t)
            ex, ey = self._ray_until_wall(sx, sy, angle)
            points.append((ex, ey))
        overlay = pygame.Surface((BOARD_WIDTH, BOARD_WIDTH), pygame.SRCALPHA)
        color   = (255, 120, 120, 90) if self._can_see() else (255, 230, 150, 90)
        pygame.draw.polygon(overlay, color, points)
        screen.blit(overlay, (0, 0))

    def render(self, screen):
        screen.fill(WHITE)
        for x in range(GRID_SIZE + 1):
            pygame.draw.line(screen, GRAY,
                             (x * CELL_SIZE, 0), (x * CELL_SIZE, BOARD_WIDTH))
        for y in range(GRID_SIZE + 1):
            pygame.draw.line(screen, GRAY,
                             (0, y * CELL_SIZE), (BOARD_WIDTH, y * CELL_SIZE))
        for wx, wy in self.walls:
            pygame.draw.rect(screen, DARK_GRAY,
                             (wx * CELL_SIZE, wy * CELL_SIZE, CELL_SIZE, CELL_SIZE))
            pygame.draw.rect(screen, (110, 110, 110),
                             (wx * CELL_SIZE + 2, wy * CELL_SIZE + 2,
                              CELL_SIZE - 4, CELL_SIZE - 4), 2)
        self._draw_fov(screen)
        self.safe_zone.draw(screen)
        self.seeker.draw(screen)
        self.hider.draw(screen)