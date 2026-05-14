# entities.py
from abc import ABC, abstractmethod
import pygame
import math
from settings import CELL_SIZE, BLUE, RED, GREEN

class GameObject(ABC):
    def __init__(self, x, y):
        self._x = x
        self._y = y

    @property
    def pos(self):
        return self._x, self._y

    def set_pos(self, x, y):
        self._x = x
        self._y = y

    @abstractmethod
    def draw(self, surface):
        pass


class Hider(GameObject):

    def draw(self, surface):
        cx = self._x * CELL_SIZE + CELL_SIZE // 2
        cy = self._y * CELL_SIZE + CELL_SIZE // 2

        # 몸통 (파란 닌자복)
        body_rect = pygame.Rect(cx - 10, cy - 6, 20, 18)
        pygame.draw.ellipse(surface, (50, 110, 220), body_rect)

        # 머리
        pygame.draw.circle(surface, (255, 220, 180), (cx, cy - 14), 10)

        # 두건 (닌자 마스크)
        pygame.draw.arc(surface, (30, 60, 160),
                        pygame.Rect(cx - 11, cy - 25, 22, 20),
                        0, math.pi, 5)
        # 마스크 (코 아래 가리기)
        pygame.draw.rect(surface, (30, 60, 160), (cx - 10, cy - 14, 20, 8))

        # 눈만 보임
        pygame.draw.circle(surface, (255, 255, 255), (cx - 4, cy - 16), 3)
        pygame.draw.circle(surface, (255, 255, 255), (cx + 4, cy - 16), 3)
        pygame.draw.circle(surface, (20, 20, 20), (cx - 4, cy - 16), 1)
        pygame.draw.circle(surface, (20, 20, 20), (cx + 4, cy - 16), 1)

        # 팔
        pygame.draw.line(surface, (50, 110, 220), (cx - 10, cy - 2), (cx - 16, cy + 6), 3)
        pygame.draw.line(surface, (50, 110, 220), (cx + 10, cy - 2), (cx + 16, cy + 6), 3)

        # 다리
        pygame.draw.line(surface, (30, 60, 160), (cx - 5, cy + 12), (cx - 7, cy + 22), 3)
        pygame.draw.line(surface, (30, 60, 160), (cx + 5, cy + 12), (cx + 7, cy + 22), 3)


class Seeker(GameObject):
    """찾는 캐릭터 - 탐정 로봇 스타일"""

    def __init__(self, x, y):
        super().__init__(x, y)
        self.direction = (1, 0)
        self._anim_tick = 0

    def draw(self, surface):
        self._anim_tick += 1
        cx = self._x * CELL_SIZE + CELL_SIZE // 2
        cy = self._y * CELL_SIZE + CELL_SIZE // 2

        # 몸통 (둥근 사각형)
        body_color = (200, 60, 60)
        pygame.draw.rect(surface, body_color, (cx - 12, cy - 8, 24, 20), border_radius=5)

        # 머리 (원형 로봇 헬멧)
        pygame.draw.circle(surface, (180, 50, 50), (cx, cy - 16), 13)
        pygame.draw.circle(surface, (220, 80, 80), (cx, cy - 16), 11)

        # 탐지 스캐너 눈 (깜빡임)
        blink = (self._anim_tick // 15) % 5 == 0
        eye_h = 1 if blink else 4

        pygame.draw.ellipse(surface, (255, 255, 100),
                            pygame.Rect(cx - 8, cy - 20, 6, eye_h))
        pygame.draw.ellipse(surface, (255, 255, 100),
                            pygame.Rect(cx + 2, cy - 20, 6, eye_h))

        # 안테나
        pygame.draw.line(surface, (220, 80, 80), (cx, cy - 27), (cx, cy - 33), 2)
        pulse = abs(math.sin(self._anim_tick * 0.15)) * 2
        pygame.draw.circle(surface, (255, 80, 80), (cx, cy - 33), int(3 + pulse))

        # 팔
        pygame.draw.line(surface, (180, 50, 50), (cx - 12, cy - 2), (cx - 18, cy + 5), 3)
        pygame.draw.line(surface, (180, 50, 50), (cx + 12, cy - 2), (cx + 18, cy + 5), 3)

        # 다리
        pygame.draw.rect(surface, (150, 40, 40), (cx - 10, cy + 12, 7, 9), border_radius=2)
        pygame.draw.rect(surface, (150, 40, 40), (cx + 3, cy + 12, 7, 9), border_radius=2)

    def chase(self, target_pos, grid_size, walls):
        tx, ty = target_pos
        sx, sy = self.pos
        dx = tx - sx
        dy = ty - sy

        if abs(dx) > abs(dy):
            self.direction = (1 if dx > 0 else -1, 0)
        else:
            self.direction = (0, 1 if dy > 0 else -1)

        nx = sx + self.direction[0]
        ny = sy + self.direction[1]
        if 0 <= nx < grid_size and 0 <= ny < grid_size:
            if (nx, ny) not in walls:
                self.set_pos(nx, ny)


class SafeZone(GameObject):

    def __init__(self, x, y):
        super().__init__(x, y)
        self._tick = 0

    def draw(self, surface):
        self._tick += 1
        px = self._x * CELL_SIZE + CELL_SIZE // 2
        py = self._y * CELL_SIZE + CELL_SIZE // 2

        # 외곽 후광 (펄스)
        pulse = abs(math.sin(self._tick * 0.08)) * 6
        glow_surf = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (100, 255, 160, 40),
                           (CELL_SIZE // 2, CELL_SIZE // 2), int(18 + pulse))
        surface.blit(glow_surf, (self._x * CELL_SIZE, self._y * CELL_SIZE))

        # 별 모양 (6각)
        for i in range(6):
            angle = math.radians(i * 60 + self._tick * 1.5)
            ex = px + math.cos(angle) * 14
            ey = py + math.sin(angle) * 14
            pygame.draw.line(surface, (80, 200, 120), (px, py), (int(ex), int(ey)), 2)

        # 중심 원
        pygame.draw.circle(surface, (60, 200, 100), (px, py), 8)
        pygame.draw.circle(surface, (180, 255, 200), (px, py), 4)

        # "SAFE" 라벨
        font = pygame.font.SysFont("malgungothic", 9)
        label = font.render("SAFE", True, (60, 180, 90))
        surface.blit(label, (px - 10, py + 12))