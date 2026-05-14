import math
import random
from collections import deque

import gymnasium as gym
import numpy as np
import pygame
from gymnasium import spaces

from entities import Hider, SafeZone, Seeker
from settings import *


class HideAndSeekEnv(gym.Env):
    metadata = {"render_modes": ["human"], "render_fps": FPS}

    def __init__(self, render_mode=None):
        super().__init__()
        self.grid_size = GRID_SIZE
        self.render_mode = render_mode

        self.action_space = spaces.Discrete(len(ACTIONS))

        # 관측값:
        # 0: goal dx
        # 1: goal dy
        # 2: seeker dx
        # 3: seeker dy
        # 4: in_fov
        # 5: goal shortest-path distance
        # 6: seeker manhattan distance
        # 7: blocked_up
        # 8: blocked_down
        # 9: blocked_left
        # 10: blocked_right
        self.observation_space = spaces.Box(
            low=-1.0,
            high=1.0,
            shape=(11,),
            dtype=np.float32,
        )

        self.walls = self._generate_fixed_walls()
        self.screen = None
        self.clock = None

        self.reset()

    def _generate_fixed_walls(self):
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

    def _random_empty_pos(self, exclude=None):
        exclude = exclude or set()
        while True:
            pos = (
                random.randint(0, GRID_SIZE - 1),
                random.randint(0, GRID_SIZE - 1),
            )
            if pos not in self.walls and pos not in exclude:
                return pos

    @staticmethod
    def _manhattan(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _is_valid_pos(self, x, y):
        return 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE and (x, y) not in self.walls

    def _shortest_path_distance(self, start, goal):
        if start == goal:
            return 0

        q = deque([(start, 0)])
        visited = {start}

        while q:
            (x, y), dist = q.popleft()

            for dx, dy in ACTIONS.values():
                nx, ny = x + dx, y + dy

                if not self._is_valid_pos(nx, ny):
                    continue
                if (nx, ny) in visited:
                    continue
                if (nx, ny) == goal:
                    return dist + 1

                visited.add((nx, ny))
                q.append(((nx, ny), dist + 1))

        return GRID_SIZE * GRID_SIZE

    def _blocked(self, sx, sy, hx, hy):
        dx = hx - sx
        dy = hy - sy
        steps = max(abs(dx), abs(dy))

        for i in range(1, steps):
            x = round(sx + dx * i / steps)
            y = round(sy + dy * i / steps)
            if (x, y) in self.walls:
                return True
        return False

    def _can_see(self):
        hx, hy = self.hider.pos
        sx, sy = self.seeker.pos
        dx, dy = self.seeker.direction

        vx = hx - sx
        vy = hy - sy
        dist = math.sqrt(vx * vx + vy * vy)

        if dist == 0:
            return True
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

    def _get_obs(self):
        hx, hy = self.hider.pos
        sx, sy = self.seeker.pos
        gx, gy = self.safe_zone.pos

        gdx = (gx - hx) / 9.0
        gdy = (gy - hy) / 9.0
        sdx = (sx - hx) / 9.0
        sdy = (sy - hy) / 9.0
        in_fov = float(self._can_see())

        bfs_goal_dist = self._shortest_path_distance(self.hider.pos, self.safe_zone.pos)
        dist_g = min(bfs_goal_dist, 18) / 18.0

        dist_s = min(self._manhattan(self.hider.pos, self.seeker.pos), 9) / 9.0

        blocked_up = 0.0 if self._is_valid_pos(hx, hy - 1) else 1.0
        blocked_down = 0.0 if self._is_valid_pos(hx, hy + 1) else 1.0
        blocked_left = 0.0 if self._is_valid_pos(hx - 1, hy) else 1.0
        blocked_right = 0.0 if self._is_valid_pos(hx + 1, hy) else 1.0

        return np.array(
            [
                gdx,
                gdy,
                sdx,
                sdy,
                in_fov,
                dist_g,
                dist_s,
                blocked_up,
                blocked_down,
                blocked_left,
                blocked_right,
            ],
            dtype=np.float32,
        )

    def _get_info(self, result="running", invalid_move=False):
        return {"result": result, "invalid_move": invalid_move}

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)

        placed = set()

        hpos = self._random_empty_pos(placed)
        placed.add(hpos)

        spos = self._random_empty_pos(placed)
        placed.add(spos)

        gpos = self._random_empty_pos(placed)

        self.hider = Hider(*hpos)
        self.seeker = Seeker(*spos)
        self.safe_zone = SafeZone(*gpos)

        self.steps = 0
        self._prev_dist_goal = self._shortest_path_distance(self.hider.pos, self.safe_zone.pos)
        self._prev_dist_seek = self._manhattan(self.hider.pos, self.seeker.pos)

        self._invalid_streak = 0
        self._same_pos_streak = 0

        return self._get_obs(), self._get_info("running")

    def _move_hider(self, action):
        dx, dy = ACTIONS[int(action)]
        x, y = self.hider.pos
        nx = x + dx
        ny = y + dy

        if self._is_valid_pos(nx, ny):
            self.hider.set_pos(nx, ny)
            return False

        return True

    def _move_seeker(self):
        if self._can_see():
            self.seeker.chase(self.hider.pos, GRID_SIZE, self.walls)
        else:
            sx, sy = self.seeker.pos
            moves = [(1, 0), (-1, 0), (0, 1), (0, -1)]
            random.shuffle(moves)

            for dx, dy in moves:
                nx, ny = sx + dx, sy + dy
                if self._is_valid_pos(nx, ny):
                    self.seeker.set_pos(nx, ny)
                    self.seeker.direction = (dx, dy)
                    return

    def step(self, action):
        self.steps += 1
        prev_pos = self.hider.pos

        invalid_move = self._move_hider(action)

        if invalid_move:
            self._invalid_streak += 1
        else:
            self._invalid_streak = 0

        if self.hider.pos == prev_pos:
            self._same_pos_streak += 1
        else:
            self._same_pos_streak = 0

        if self.hider.pos == self.safe_zone.pos:
            return self._get_obs(), 500.0, True, False, self._get_info("escaped", invalid_move)

        if self.steps % 2 == 0:
            self._move_seeker()

        if self.hider.pos == self.seeker.pos:
            return self._get_obs(), -250.0, True, False, self._get_info("caught", invalid_move)

        if self.steps >= MAX_STEPS:
            return self._get_obs(), -80.0, False, True, self._get_info("timeout", invalid_move)

        reward = -0.5

        dist_g = self._shortest_path_distance(self.hider.pos, self.safe_zone.pos)
        reward += (self._prev_dist_goal - dist_g) * 18.0
        self._prev_dist_goal = dist_g

        dist_s = self._manhattan(self.hider.pos, self.seeker.pos)
        reward += (dist_s - self._prev_dist_seek) * 0.2
        self._prev_dist_seek = dist_s

        if dist_s <= 1:
            reward -= 15.0
        elif dist_s <= 2:
            reward -= 6.0

        if self._can_see():
            reward -= 2.5

        if invalid_move:
            reward -= 8.0 + min(self._invalid_streak, 4) * 6.0
        else:
            reward += 1.5

        if self.hider.pos == prev_pos:
            reward -= 2.0 + min(self._same_pos_streak, 4) * 3.0

        return self._get_obs(), reward, False, False, self._get_info("running", invalid_move)

    def _ray_until_wall(self, sx, sy, angle, max_dist=5):
        step = 0.2
        dist = 0.0
        px = sx + 0.5
        py = sy + 0.5

        while dist < max_dist:
            px += math.cos(angle) * step
            py += math.sin(angle) * step
            dist += step
            gx = int(px)
            gy = int(py)

            if not (0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE):
                break
            if (gx, gy) in self.walls:
                break

        return px * CELL_SIZE, py * CELL_SIZE

    def _draw_fov(self, screen):
        sx, sy = self.seeker.pos
        cx = sx * CELL_SIZE + CELL_SIZE // 2
        cy = sy * CELL_SIZE + CELL_SIZE // 2
        dx, dy = self.seeker.direction

        base_angle = math.atan2(dy, dx)
        half_fov = math.pi / 4
        ray_count = 40
        points = [(cx, cy)]

        for i in range(ray_count):
            t = i / (ray_count - 1)
            angle = base_angle - half_fov + (2 * half_fov * t)
            ex, ey = self._ray_until_wall(sx, sy, angle)
            points.append((ex, ey))

        overlay = pygame.Surface((BOARD_WIDTH, BOARD_WIDTH), pygame.SRCALPHA)
        color = (255, 120, 120, 90) if self._can_see() else (255, 230, 150, 90)
        pygame.draw.polygon(overlay, color, points)
        screen.blit(overlay, (0, 0))

    def render_on(self, screen):
        board = pygame.Surface((BOARD_WIDTH, BOARD_WIDTH))
        board.fill(WHITE)

        for x in range(GRID_SIZE + 1):
            pygame.draw.line(board, GRAY, (x * CELL_SIZE, 0), (x * CELL_SIZE, BOARD_WIDTH))
        for y in range(GRID_SIZE + 1):
            pygame.draw.line(board, GRAY, (0, y * CELL_SIZE), (BOARD_WIDTH, y * CELL_SIZE))

        for wx, wy in self.walls:
            pygame.draw.rect(board, DARK_GRAY, (wx * CELL_SIZE, wy * CELL_SIZE, CELL_SIZE, CELL_SIZE))
            pygame.draw.rect(
                board,
                (110, 110, 110),
                (wx * CELL_SIZE + 6, wy * CELL_SIZE + 6, CELL_SIZE - 12, CELL_SIZE - 12),
                border_radius=4,
            )

        self._draw_fov(board)
        self.safe_zone.draw(board)
        self.hider.draw(board)
        self.seeker.draw(board)

        screen.blit(board, (0, 0))