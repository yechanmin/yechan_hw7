import math, random
import numpy as np
import pygame
from settings import *


def _norm_angle(a):
    while a >  math.pi: a -= 2 * math.pi
    while a < -math.pi: a += 2 * math.pi
    return a


SLOT_DEFS = []
for col in range(3):
    bx = 60 + col * 220
    for row in range(4):
        by = 40 + row * 120
        SLOT_DEFS.append((bx, by, 0.0))
        SLOT_DEFS.append((bx + SLOT_W + 10, by, 0.0))


WALL_RECTS = [
    pygame.Rect(0,   0,   WORLD_W, 10),
    pygame.Rect(0,   WORLD_H-10, WORLD_W, 10),
    pygame.Rect(0,   0,   10, WORLD_H),
    pygame.Rect(WORLD_W-10, 0, 10, WORLD_H),
]

ROAD_LANE_Y = [110, 230, 350, 470]


def _corners(x, y, angle, length=CAR_L, width=CAR_W):
    hl, hw = length / 2, width / 2
    ca,sa = math.cos(angle), math.sin(angle)
    pts = []
    for lx, ly in [(hl, hw), (hl, -hw), (-hl, -hw), (-hl, hw)]:
        pts.append((x + lx*ca - ly*sa, y + lx*sa + ly*ca))
    return pts


def _seg_intersect(p1, p2, p3, p4):
    d1 = (p2[0]-p1[0], p2[1]-p1[1])
    d2 = (p4[0]-p3[0], p4[1]-p3[1])
    cross = d1[0]*d2[1] - d1[1]*d2[0]
    if abs(cross) < 1e-10:
        return False
    t = ((p3[0]-p1[0])*d2[1] - (p3[1]-p1[1])*d2[0]) / cross
    u = ((p3[0]-p1[0])*d1[1] - (p3[1]-p1[1])*d1[0]) / cross
    return 0 <= t <= 1 and 0 <= u <= 1


def _poly_intersect(a_pts, b_pts):
    for poly in [a_pts, b_pts]:
        n = len(poly)
        for i in range(n):
            p1, p2 = poly[i], poly[(i+1)%n]
            for j in range(len(b_pts if poly is a_pts else a_pts)):
                q1 = (b_pts if poly is a_pts else a_pts)[j]
                q2 = (b_pts if poly is a_pts else a_pts)[(j+1)%len(b_pts if poly is a_pts else a_pts)]
                if _seg_intersect(p1, p2, q1, q2):
                    return True
    return False


class PlayerCar:
    def __init__(self, x, y, angle):
        self.x     = float(x)
        self.y     = float(y)
        self.angle = float(angle)
        self.steer = 0.0
        self.speed = 0.0

    def apply_action(self, action: int, dt: float):
        if   action == 0: self.speed =  SPEED_FWD; pass
        elif action == 1: self.speed = -SPEED_REV; pass
        elif action == 2: self.speed =  SPEED_FWD; self.steer = max(-MAX_STEER, self.steer - STEER_DELTA)
        elif action == 3: self.speed =  SPEED_FWD; self.steer = min( MAX_STEER, self.steer + STEER_DELTA)
        elif action == 4: self.speed = -SPEED_REV; self.steer = max(-MAX_STEER, self.steer - STEER_DELTA)
        elif action == 5: self.speed = -SPEED_REV; self.steer = min( MAX_STEER, self.steer + STEER_DELTA)
        elif action == 6: self.speed *= 0.7

        if abs(self.steer) > 0.001:
            turn_r = WHEEL_BASE / math.tan(self.steer)
            d_ang  = self.speed * dt / turn_r
        else:
            d_ang  = 0.0

        self.angle = _norm_angle(self.angle + d_ang)
        self.x    += self.speed * math.cos(self.angle) * dt
        self.y    += self.speed * math.sin(self.angle) * dt

        if action in (0, 1, 2, 3, 4, 5):
            self.steer *= 0.85

    def corners(self):
        return _corners(self.x, self.y, self.angle)

    def draw(self, screen, color=CAR_C):
        pts = [(int(p[0]), int(p[1])) for p in self.corners()]
        pygame.draw.polygon(screen, color, pts)
        pygame.draw.polygon(screen, BLACK, pts, 2)
        fx = self.x + (CAR_L/2 - 4) * math.cos(self.angle)
        fy = self.y + (CAR_L/2 - 4) * math.sin(self.angle)
        pygame.draw.circle(screen, (255, 220, 60), (int(fx), int(fy)), 5)


class NPCCar:
    def __init__(self, x, y, angle, speed):
        self.x     = float(x)
        self.y     = float(y)
        self.angle = float(angle)
        self.speed = float(speed)
        self._t    = 0

    def update(self, dt: float):
        self._t += dt
        self.angle = _norm_angle(self.angle + math.sin(self._t * 0.5) * 0.015)
        self.x    += self.speed * math.cos(self.angle) * dt
        self.y    += self.speed * math.sin(self.angle) * dt
        if self.x < 20:              self.angle = _norm_angle(-self.angle + math.pi * 0.1)
        if self.x > WORLD_W - 20:   self.angle = _norm_angle(-self.angle - math.pi * 0.1)
        if self.y < 20:              self.angle = _norm_angle(math.pi - self.angle)
        if self.y > WORLD_H - 20:   self.angle = _norm_angle(math.pi - self.angle)

    def corners(self):
        return _corners(self.x, self.y, self.angle)

    def draw(self, screen):
        pts = [(int(p[0]), int(p[1])) for p in self.corners()]
        pygame.draw.polygon(screen, NPC_C, pts)
        pygame.draw.polygon(screen, BLACK, pts, 2)
        fx = self.x + (CAR_L/2 - 4) * math.cos(self.angle)
        fy = self.y + (CAR_L/2 - 4) * math.sin(self.angle)
        pygame.draw.circle(screen, (255, 180, 50), (int(fx), int(fy)), 4)


def _spawn_npcs():
    npcs = []
    lanes = [110, 230, 350, 470]
    for i in range(NUM_NPC):
        lane_y = random.choice(lanes)
        x      = random.uniform(80, WORLD_W - 80)
        angle  = random.choice([0.0, math.pi])
        speed  = random.uniform(20, 50) * (1 if angle == 0 else -1)
        npcs.append(NPCCar(x, lane_y + random.uniform(-15, 15), angle, speed))
    return npcs


class ParkingEnv:
    def __init__(self):
        self.slots  = SLOT_DEFS
        self.car    = PlayerCar(WORLD_W/2, WORLD_H - 50, -math.pi/2)
        self.target = self.slots[0]
        self.npcs   = _spawn_npcs()
        self.steps  = 0
        self._prev_dist  = 0.0
        self._prev_align = 0.0
        self._idle_steps = 0
        self.reset()

    def reset(self) -> np.ndarray:
        sx = random.uniform(80, WORLD_W - 80)
        sy = random.uniform(WORLD_H - 100, WORLD_H - 30)
        sa = random.uniform(-math.pi/4, math.pi/4) - math.pi/2
        self.car    = PlayerCar(sx, sy, sa)
        self.target = random.choice(self.slots)
        self.npcs   = _spawn_npcs()
        self.steps       = 0
        self._idle_steps = 0
        self._prev_dist  = self._dist_to_target()
        self._prev_align = self._align_score()
        return self._get_state()

    def _dist_to_target(self) -> float:
        tx, ty, _ = self.target
        return math.hypot(self.car.x - tx, self.car.y - ty)

    def _align_score(self) -> float:
        _, _, ta = self.target
        da = abs(_norm_angle(self.car.angle - ta))
        return 1.0 - da / math.pi

    def _get_state(self) -> np.ndarray:
        tx, ty, ta = self.target
        dx  = (tx - self.car.x) / WORLD_W
        dy  = (ty - self.car.y) / WORLD_H
        dist = self._dist_to_target() / math.hypot(WORLD_W, WORLD_H)
        da   = _norm_angle(self.car.angle - ta) / math.pi
        speed_norm = self.car.speed / SPEED_FWD
        steer_norm = self.car.steer / MAX_STEER

        min_npc_dist = 1.0
        npc_dx = npc_dy = 0.0
        for npc in self.npcs:
            d = math.hypot(self.car.x - npc.x, self.car.y - npc.y)
            nd = d / math.hypot(WORLD_W, WORLD_H)
            if nd < min_npc_dist:
                min_npc_dist = nd
                npc_dx = (npc.x - self.car.x) / WORLD_W
                npc_dy = (npc.y - self.car.y) / WORLD_H

        wall_l = self.car.x / WORLD_W
        wall_r = (WORLD_W - self.car.x) / WORLD_W
        wall_t = self.car.y / WORLD_H
        wall_b = (WORLD_H - self.car.y) / WORLD_H

        return np.array([
            dx, dy, dist, da,
            speed_norm, steer_norm,
            min_npc_dist, npc_dx, npc_dy,
            wall_l, wall_r, wall_t,
        ], dtype=np.float32)

    def step(self, action: int, dt: float = 1/FPS):
        self.steps += 1
        prev_x, prev_y = self.car.x, self.car.y

        if action == 6:
            self._idle_steps += 1
        else:
            self._idle_steps = 0

        self.car.apply_action(action, dt)

        for npc in self.npcs:
            npc.update(dt)

        reward, done, info = self._evaluate(prev_x, prev_y)
        self._prev_dist  = self._dist_to_target()
        self._prev_align = self._align_score()
        return self._get_state(), reward, done, info

    def _wall_hit(self) -> bool:
        pts = self.car.corners()
        for p in pts:
            if p[0] < 8 or p[0] > WORLD_W-8 or p[1] < 8 or p[1] > WORLD_H-8:
                return True
        return False

    def _npc_hit(self) -> bool:
        cp = self.car.corners()
        for npc in self.npcs:
            if _poly_intersect(cp, npc.corners()):
                return True
        return False

    def _parked(self) -> bool:
        tx, ty, ta = self.target
        dist = math.hypot(self.car.x - tx, self.car.y - ty)
        da   = abs(_norm_angle(self.car.angle - ta))
        return dist < PARK_POS_TOL and da < PARK_ANG_TOL

    def _evaluate(self, prev_x, prev_y):
        if self._npc_hit():
            return R_HIT_NPC, True, {"result": "npc_collision"}

        if self._wall_hit():
            return R_CRASH, True, {"result": "wall_crash"}

        if self._parked():
            return R_PARK, True, {"result": "parked"}

        if self.steps >= MAX_STEPS:
            return R_TIMEOUT, True, {"result": "timeout"}

        reward = R_STEP

        cur_dist = self._dist_to_target()
        if cur_dist < self._prev_dist - 0.5:
            reward += R_CLOSER
        elif cur_dist > self._prev_dist + 0.5:
            reward += R_FARTHER

        cur_align = self._align_score()
        if cur_dist < 120 and cur_align > self._prev_align + 0.01:
            reward += R_ALIGN * (cur_align - self._prev_align) * 10

        min_npc = min(math.hypot(self.car.x - n.x, self.car.y - n.y) for n in self.npcs)
        if min_npc < 60:
            reward += R_NPC_PROX * (1 - min_npc / 60)

        if self._idle_steps > 5:
            reward += R_IDLE

        tx, ty, _ = self.target
        for sx, sy, _ in self.slots:
            if (sx, sy) != (tx, ty):
                if math.hypot(self.car.x - sx, self.car.y - sy) < PARK_POS_TOL:
                    reward += R_WRONG_SLOT

        return reward, False, {"result": "running"}

    def render(self, screen: pygame.Surface):
        screen.fill(ROAD_C)

        for wy in ROAD_LANE_Y:
            pygame.draw.rect(screen, (210, 210, 220),
                             pygame.Rect(0, wy - 40, WORLD_W, 80))
            for x in range(0, int(WORLD_W), 40):
                pygame.draw.rect(screen, (230, 230, 100),
                                 pygame.Rect(x, wy - 2, 20, 4))

        for sx, sy, sa in self.slots:
            tx, ty, _ = self.target
            is_tgt = (sx == tx and sy == ty)
            color  = TARGET_C if is_tgt else SLOT_C
            ca_, sa_ = math.cos(sa), math.sin(sa)
            corners = []
            for lx, ly in [(SLOT_H/2, SLOT_W/2),(SLOT_H/2,-SLOT_W/2),
                           (-SLOT_H/2,-SLOT_W/2),(-SLOT_H/2, SLOT_W/2)]:
                corners.append((int(sx + lx*ca_ - ly*sa_),
                                int(sy + lx*sa_ + ly*ca_)))
            pygame.draw.polygon(screen, color, corners)
            edge = TARGET_EDGE if is_tgt else (80, 150, 85)
            pygame.draw.polygon(screen, edge, corners, 2)
            if is_tgt:
                font = pygame.font.SysFont("malgungothic", 13, bold=True)
                lbl  = font.render("P", True, (20, 100, 40))
                screen.blit(lbl, (int(sx) - 5, int(sy) - 7))

        for wall in WALL_RECTS:
            pygame.draw.rect(screen, CURB_C, wall)

        for npc in self.npcs:
            npc.draw(screen)

        color = CAR_OK_C if self._parked() else CAR_C
        self.car.draw(screen, color)

        self._draw_guide(screen)

    def _draw_guide(self, screen):
        tx, ty, _ = self.target
        cx, cy = self.car.x, self.car.y
        dx, dy = tx - cx, ty - cy
        dist   = max(1, math.hypot(dx, dy))
        if dist < 5:
            return
        steps = int(dist // 12)
        for i in range(steps):
            if i % 2 == 0:
                fx = int(cx + dx * i / steps)
                fy = int(cy + dy * i / steps)
                pygame.draw.circle(screen, ARROW_C, (fx, fy), 2)