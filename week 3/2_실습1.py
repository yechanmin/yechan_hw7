import pygame
import random
import sys
import math

pygame.init()

WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Polymorphism Example")
clock = pygame.time.Clock()

WHITE = (245,245,245)
BLACK = (30,30,30)
RED = (230,80,80)
GREEN = (30,150,100)
PURPLE = (150,50,200)
BLUE = (70,130,255)

font = pygame.font.SysFont("malgungothic", 22)

class Enemy:
    def __init__(self, x, y, color):
        self.x = float(x)
        self.y = float(y)
        self.radius = 18
        self.color = color

    def update(self):
        pass

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)

#직선(위에서 아래로)
class StraightEnemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, RED)
        self.speed = random.uniform(2,4)

    def update(self):
        self.y += self.speed
        if self.y > HEIGHT:
            self.y = -20
            self.x = random.randint(20, WIDTH-20)

#일정 범위를 왔다갔다 하도록
class ZigzagEnemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, PURPLE)
        self.speed = 2.5
        self.angle = random.uniform(0, math.pi*2)

    def update(self):
        self.y += self.speed
        self.angle += 0.1
        self.x += math.sin(self.angle) * 5
        if self.y > HEIGHT:
            self.y = -20
            self.x = random.randint(20, WIDTH-20)

#Add to code here
#SpiralEnemy 추가하기
class SpiralEnemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, GREEN)
        self.speed = 2.0
        self.angle = random.uniform(0, math.pi * 2)

    def update(self):
        self.angle += 0.1
        self.y += self.speed
        self.x += math.sin(self.angle) * 5
        self.y += math.cos(self.angle) * 5

        if self.y > HEIGHT:
            self.y = -20
            self.x = random.randint(20, WIDTH-20)


class Player:
    def __init__(self):
        self.x = WIDTH//2
        self.y = HEIGHT-80
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
        self.x = max(self.radius, min(WIDTH-self.radius, self.x))
        self.y = max(self.radius, min(HEIGHT-self.radius, self.y))

    def draw(self, surface):
        pygame.draw.circle(surface, BLUE, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, BLACK, (int(self.x), int(self.y)), self.radius, 3)
        # 눈 추가!!
        pygame.draw.circle(surface, BLACK, (int(self.x) - 5, int(self.y) - 4), 2)
        pygame.draw.circle(surface, BLACK, (int(self.x) + 5, int(self.y) - 4), 2)

player = Player()
enemies = []

for _ in range(4):
    enemies.append(StraightEnemy(random.randint(40,860), random.randint(0,200)))

for _ in range(3):
    enemies.append(ZigzagEnemy(random.randint(40,860), random.randint(0,200)))

#Add to code here
#SpiralEnemy 객체 생성하기(3개)
for _ in range(3):
    enemies.append(SpiralEnemy(random.randint(100, WIDTH-100), random.randint(0, 200)))


while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    player.update()
    # 다형성! 여기 for문은 수정하지 않기
    for enemy in enemies:
        enemy.update()

    screen.fill(WHITE)

    player.draw(screen)
    # 다형성! 여기 for문은 수정하지 않기
    for enemy in enemies:
        enemy.draw(screen)

    text1 = font.render("red: straight / purple: zigzag", True, BLACK)
    screen.blit(text1,(20,20))

    pygame.display.flip()
    clock.tick(60)
