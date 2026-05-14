import pygame
import sys
import random
from abc import ABC, abstractmethod

pygame.init()

# 화면 설정
WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("ABC example")
clock = pygame.time.Clock()

# 색상
WHITE = (245, 245, 245)
BLACK = (30, 30, 30)
GREEN = (80, 200, 120)
RED = (230, 80, 80)
YELLOW = (255, 220, 70)
BLUE = (70, 130, 255)

font = pygame.font.SysFont("malgungothic", 24)

#Abstract Class
class GameObject(ABC):
    def __init__(self, x, y, color):
        self.x = float(x)
        self.y = float(y)
        self.color = color
        self.alive = True

    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def draw(self, surface):
        pass

    @abstractmethod
    def get_rect(self):
        pass

class Player(GameObject):
    def __init__(self, x, y, color):
        super().__init__(x, y, color)
        self.radius = 20
        self.speed = 5

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.x -= self.speed
        if keys[pygame.K_RIGHT]:
            self.x += self.speed
        if keys[pygame.K_UP]:
            self.y -= self.speed
        if keys[pygame.K_DOWN]:
            self.y += self.speed

        if self.x < self.radius:
            self.x = self.radius
        if self.x > WIDTH - self.radius:
            self.x = WIDTH - self.radius
        if self.y < self.radius:
            self.y = self.radius
        if self.y > HEIGHT - self.radius:
            self.y = HEIGHT - self.radius

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)

    def get_rect(self):
        return pygame.Rect(
            self.x - self.radius,
            self.y - self.radius,
            self.radius * 2,
            self.radius * 2
        )

class Enemy(GameObject):
    def __init__(self, x, y, color):
        super().__init__(x, y, color)
        self.size = 30
        self.speed = 2

    def update(self):
        self.y += self.speed

        if self.y > HEIGHT:
            self.y = -self.size

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, (int(self.x), int(self.y), self.size, self.size))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.size, self.size)


class Bullet(GameObject):
    def __init__(self, x, y, color):
        super().__init__(x, y, color)
        self.radius = 6
        self.speed = 7

    def update(self):
        self.y -= self.speed

        # 화면 위로 나가면 제거 표시
        if self.y < 0:
            self.alive = False

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)

    def get_rect(self):
        return pygame.Rect(
            self.x - self.radius,
            self.y - self.radius,
            self.radius * 2,
            self.radius * 2
        )

player = Player(WIDTH // 2, HEIGHT - 60, GREEN)

objects = [player]

for _ in range(6):
    x = random.randint(50, WIDTH - 50)
    y = random.randint(0, 200)
    objects.append(Enemy(x, y, RED))

bullet_cooldown = 0

running = True
while running:
    clock.tick(60)

    # 이벤트 처리
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # 스페이스바 누르면 총알 생성
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and bullet_cooldown == 0:
                bullet = Bullet(player.x, player.y - player.radius, YELLOW)
                objects.append(bullet)
                bullet_cooldown = 15

    if bullet_cooldown > 0:
        bullet_cooldown -= 1

    for obj1 in objects:
        if isinstance(obj1, Bullet):
            for obj2 in objects:
                if isinstance(obj2, Enemy):
                    if obj1.get_rect().colliderect(obj2.get_rect()): #colliderect 두개의 사각형이 겹치는지 검사
                        obj1.alive = False
                        obj2.alive = False

    for obj in objects:
        if isinstance(obj, Enemy):
            if player.get_rect().colliderect(obj.get_rect()):
                player.alive = False

    # 죽은 객체 제거
    objects = [obj for obj in objects if obj.alive]

    # 그리기
    screen.fill(WHITE)
    for obj in objects:
        obj.update()
        obj.draw(screen)

    info_text = font.render(
        "Arrow keys: Move / Spacebar: Shoot", True, BLACK
    )
    screen.blit(info_text, (20, 20))
    pygame.display.flip()

pygame.quit()
sys.exit()