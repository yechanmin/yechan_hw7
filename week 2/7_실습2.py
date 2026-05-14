import pygame
import sys
import random

pygame.init()

WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("상속 예제")
clock = pygame.time.Clock()
font = pygame.font.SysFont("malgungothic", 20)

WHITE = (245, 245, 245)
BLACK = (30, 30, 30)
BLUE = (80, 80, 255)
RED = (230, 90, 90)
GREEN = (80, 255, 80)

#상속을 적용해보자!!
# Add Character Class!!
class Character:
    def __init__(self, x, y, speed, color, name):
        self.x = float(x)
        self.y = float(y)
        self.size = 50
        self.speed = speed
        self.color = color
        self.name = name

    def move(self, dx, dy):
        self.x += dx * self.speed
        self.y += dy * self.speed

        if self.x < 0: self.x = 0
        if self.y < 0: self.y = 0
        if self.x + self.size > WIDTH: self.x = WIDTH - self.size
        if self.y + self.size > HEIGHT: self.y = HEIGHT - self.size

    def draw(self, surface):
        pygame.draw.rect(surface, self.color,
                         (int(self.x), int(self.y), self.size, self.size))
        text = font.render(self.name, True, BLACK)
        surface.blit(text, (int(self.x), int(self.y) - 28))

class Player(Character):
    def __init__(self, x, y):
        super().__init__(x, y, 4, BLUE, "Player")

class Enemy(Character):
    def __init__(self, x, y):
        super().__init__(x, y, 2, RED, "Enemy")


class NPC(Character):
    def __init__(self, x, y):
        super().__init__(x, y, 2, GREEN, "NPC")
        self.dx = random.choice([-1, 0, 1])
        self.dy = random.choice([-1, 0, 1])

class Game:
    def __init__(self):
        self.player = Player(100, 250)
        self.enemy = Enemy(700, 100)
        self.npc = NPC(500, 400)

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    def update(self):
        # 방향키로 Player 이동
        keys = pygame.key.get_pressed()
        p_dx, p_dy = 0, 0
        if keys[pygame.K_LEFT]:
            p_dx = -1
        if keys[pygame.K_RIGHT]:
            p_dx = 1
        if keys[pygame.K_UP]:
            p_dy = -1
        if keys[pygame.K_DOWN]:
            p_dy = 1
        self.player.move(p_dx, p_dy)

        # Enemy는 Player를 따라가게~
        e_dx, e_dy = 0, 0

        if self.enemy.x < self.player.x:
            e_dx = 1
        elif self.enemy.x > self.player.x:
            e_dx = -1

        if self.enemy.y < self.player.y:
            e_dy = 1
        elif self.enemy.y > self.player.y:
            e_dy = -1
        self.enemy.move(e_dx, e_dy)

        # NPC는 랜덤 이동
        if random.random() < 0.02:
            self.npc.dx = random.choice([-1, 0, 1])
            self.npc.dy = random.choice([-1, 0, 1])
        self.npc.move(self.npc.dx, self.npc.dy)

    def draw(self, surface):
        surface.fill(WHITE)
        self.player.draw(surface)
        self.enemy.draw(surface)
        self.npc.draw(surface)


        info1 = font.render("Player: 방향키 이동", True, BLACK)
        info2 = font.render("Enemy: 플레이어 추적 / NPC: 랜덤 이동", True, BLACK)

        surface.blit(info1, (20, 20))
        surface.blit(info2, (20, 55))

game = Game()

while True:

    for event in pygame.event.get():
        game.handle_event(event)

    game.update()
    game.draw(screen)

    pygame.display.flip()
    clock.tick(60)