import math, random
import pygame
from settings import *

RAW_MAP = [
    "WWWWWWWWWWWWWWWWWWWW",
    "WRRRRRRRRRRRRRRRRRRW",
    "WRSSSSSRRSSSSSRRSSSW",
    "WRSSSSSRRSSSSSRRSSSW",
    "WRRRRRRRRRRRRRRRRRRW",
    "WRSSSSSRRSSSSSRRSSSW",
    "WRSSSSSRRSSSSSRRSSSW",
    "WRRRRRRRRRRRRRRRRRRW",
    "WRSSSSSRRSSSSSRRSSSW",
    "WRSSSSSRRSSSSSRRSSSW",
    "WRRRRRRRRRRRRRRRRRRW",
    "WRSSSSSRRSSSSSRRSSSW",
    "WRSSSSSRRSSSSSRRSSSW",
    "WRRRRRRRRRRRRRRRRRRW",
    "WRRRRRRRRRRRRRRRRRRW",
    "WWWWWWWWWWWWWWWWWWWW",
]

assert len(RAW_MAP) == GRID_ROWS
assert all(len(r) == GRID_COLS for r in RAW_MAP)


def _parse_map():
    walls, slots = set(), []
    for r, row in enumerate(RAW_MAP):
        for c, ch in enumerate(row):
            if ch == 'W':
                walls.add((c, r))
            elif ch == 'S':
                slots.append((c, r))
    return walls, slots


WALLS, ALL_SLOTS = _parse_map()

ROAD_CELLS = [
    (c, r)
    for r, row in enumerate(RAW_MAP)
    for c, ch in enumerate(row)
    if ch == 'R'
]


class Car:
    def __init__(self, col: int, row: int):
        self.col = col
        self.row = row

    @property
    def pos(self):
        return (self.col, self.row)

    def pixel_center(self):
        return (self.col * CELL + CELL // 2, self.row * CELL + CELL // 2)

    def draw(self, screen, color):
        hw = CELL // 2 - 3
        px, py = self.pixel_center()
        body = pygame.Rect(px - hw, py - hw + 2, hw * 2, hw * 2 - 4)
        pygame.draw.rect(screen, color, body, border_radius=4)
        hood = pygame.Rect(px - hw // 2, py - hw + 2, hw, 5)
        pygame.draw.rect(screen, (255, 220, 80), hood, border_radius=2)
        for wx, wy in [(-hw+1, -hw+4), (hw-5, -hw+4), (-hw+1, hw-8), (hw-5, hw-8)]:
            pygame.draw.rect(screen, (20, 20, 20), pygame.Rect(px+wx, py+wy, 4, 6), border_radius=1)


class NPCCar:
    def __init__(self, col: int, row: int):
        self.col = col
        self.row = row
        self._step = 0

    @property
    def pos(self):
        return (self.col, self.row)

    def move(self, occupied: set):
        self._step += 1
        if self._step % NPC_MOVE_EVERY != 0:
            return
        neighbors = []
        for dc, dr in [(0,-1),(0,1),(-1,0),(1,0)]:
            nc, nr = self.col + dc, self.row + dr
            if (nc, nr) not in WALLS and (nc, nr) not in occupied \
               and 0 <= nc < GRID_COLS and 0 <= nr < GRID_ROWS:
                neighbors.append((nc, nr))
        if neighbors:
            nc, nr = random.choice(neighbors)
            self.col, self.row = nc, nr

    def draw(self, screen):
        hw = CELL // 2 - 4
        px = self.col * CELL + CELL // 2
        py = self.row * CELL + CELL // 2
        body = pygame.Rect(px - hw, py - hw + 2, hw * 2, hw * 2 - 4)
        pygame.draw.rect(screen, NPC_COLOR, body, border_radius=4)
        hood = pygame.Rect(px - hw // 2, py - hw + 2, hw, 5)
        pygame.draw.rect(screen, (255, 180, 60), hood, border_radius=2)
        for wx, wy in [(-hw+1, -hw+4), (hw-5, -hw+4), (-hw+1, hw-8), (hw-5, hw-8)]:
            pygame.draw.rect(screen, (20, 20, 20), pygame.Rect(px+wx, py+wy, 4, 6), border_radius=1)


class ParkingEnv:
    def __init__(self):
        self.walls  = WALLS
        self.slots  = ALL_SLOTS
        self.car    = Car(1, 14)
        self.target = (0, 0)
        self.npcs:  list[NPCCar] = []
        self.steps  = 0
        self._prev_dist = 0
        self.reset()

    def _spawn_npcs(self, exclude: set) -> list[NPCCar]:
        pool = [c for c in ROAD_CELLS if c not in exclude]
        random.shuffle(pool)
        npcs = []
        for pos in pool[:NUM_NPC_CARS]:
            npcs.append(NPCCar(pos[0], pos[1]))
        return npcs

    def reset(self) -> tuple:
        start_pool = [(c, r) for c, r in ROAD_CELLS if 12 <= r <= 14]
        sc = random.choice(start_pool)
        self.car = Car(sc[0], sc[1])

        candidates = [s for s in self.slots if s != sc]
        self.target = random.choice(candidates)

        exclude = {sc, self.target}
        self.npcs = self._spawn_npcs(exclude)

        self.steps      = 0
        self._prev_dist = self._manhattan()
        return self.get_state()

    def _npc_positions(self) -> set:
        return {n.pos for n in self.npcs}

    def get_state(self) -> tuple:
        tx, ty = self.target
        cx, cy = self.car.pos

        dx_b   = max(-4, min(4, tx - cx))
        dy_b   = max(-4, min(4, ty - cy))
        dist_b = min(5, self._manhattan() // 3)
        near_wall = int(self._near_wall())

        npc_positions = self._npc_positions()
        near_npc = int(any(
            (cx + dc, cy + dr) in npc_positions
            for dc, dr in [(0,-1),(0,1),(-1,0),(1,0),(0,0)]
        ))

        return (dx_b, dy_b, dist_b, near_wall, near_npc)

    def step(self, action: int):
        self.steps += 1
        dx, dy = ACTIONS[action]
        nx = self.car.col + dx
        ny = self.car.row + dy

        crashed  = False
        hit_npc  = False

        npc_pos = self._npc_positions()

        if (nx, ny) in self.walls or not (0 <= nx < GRID_COLS and 0 <= ny < GRID_ROWS):
            crashed = True
            nx, ny  = self.car.col, self.car.row
        elif (nx, ny) in npc_pos:
            hit_npc = True
            nx, ny  = self.car.col, self.car.row

        self.car.col = nx
        self.car.row = ny

        occupied = {self.car.pos} | npc_pos
        for npc in self.npcs:
            npc.move(occupied)
            occupied.add(npc.pos)

        reward, done, info = self._evaluate(crashed, hit_npc)
        self._prev_dist = self._manhattan()
        return self.get_state(), reward, done, info

    def _evaluate(self, crashed: bool, hit_npc: bool):
        cx, cy = self.car.pos

        if hit_npc:
            return R_HIT_NPC, True, {"result": "collision"}
        if crashed:
            return R_CRASH, False, {"result": "crash"}
        if (cx, cy) == self.target:
            return R_PARK_SUCCESS, True, {"result": "parked"}
        if self.steps >= MAX_STEPS:
            return R_TIMEOUT, True, {"result": "timeout"}

        if (cx, cy) in self.slots and (cx, cy) != self.target:
            reward = R_WRONG_ZONE
        else:
            reward = R_STEP

        cur_dist = self._manhattan()
        if cur_dist < self._prev_dist:
            reward += R_CLOSER
        elif cur_dist > self._prev_dist:
            reward += R_FARTHER

        return reward, False, {"result": "running"}

    def _manhattan(self) -> int:
        tx, ty = self.target
        cx, cy = self.car.pos
        return abs(tx - cx) + abs(ty - cy)

    def _near_wall(self) -> bool:
        cx, cy = self.car.pos
        return any((cx+dc, cy+dr) in self.walls for dc, dr in [(1,0),(-1,0),(0,1),(0,-1)])

    def render(self, screen: pygame.Surface):
        screen.fill(ROAD_COLOR)

        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                rect = pygame.Rect(c * CELL, r * CELL, CELL, CELL)
                if (c, r) in self.walls:
                    pygame.draw.rect(screen, WALL_COLOR, rect)
                elif (c, r) == self.target:
                    pygame.draw.rect(screen, SLOT_TARGET, rect)
                    font = pygame.font.SysFont("malgungothic", 14, bold=True)
                    lbl  = font.render("P", True, (20, 100, 40))
                    screen.blit(lbl, (c*CELL + CELL//2 - 5, r*CELL + CELL//2 - 8))
                elif (c, r) in self.slots:
                    pygame.draw.rect(screen, SLOT_EMPTY, rect)
                pygame.draw.rect(screen, (180, 180, 190), rect, 1)

        for npc in self.npcs:
            npc.draw(screen)

        parked = (self.car.pos == self.target)
        self.car.draw(screen, CAR_PARKED if parked else CAR_COLOR)
        self._draw_guide(screen)

    def _draw_guide(self, screen):
        cx, cy = self.car.pixel_center()
        tx_px  = self.target[0] * CELL + CELL // 2
        ty_px  = self.target[1] * CELL + CELL // 2
        dx     = tx_px - cx
        dy     = ty_px - cy
        dist   = max(1, math.hypot(dx, dy))
        if dist < 5:
            return
        steps = int(dist // 8)
        for i in range(steps):
            if i % 2 == 0:
                fx = cx + dx * i / steps
                fy = cy + dy * i / steps
                pygame.draw.circle(screen, (100, 180, 255), (int(fx), int(fy)), 2)