import pygame
import sys
import random
import math

pygame.init()

WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("클래스 생성 예제")
clock = pygame.time.Clock()
font = pygame.font.SysFont("malgungothic", 20)

WHITE = (245, 245, 245)
BLACK = (30, 30, 30)
BLUE = (80, 80, 255)
RED = (230, 90, 90)
GREEN = (80, 255, 80)

class Player:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.size = 50
        self.speed = 10
        self.color = BLUE

    def move(self, dx, dy):
        self.x += dx * self.speed
        self.y += dy * self.speed

        if self.x < 0:
            self.x = WIDTH - self.size
        if self.y < 0:
            self.y = HEIGHT - self.size
        if self.x + self.size > WIDTH:
            self.x = 0
        if self.y + self.size > HEIGHT:
            self.y = 0

    def draw(self, surface):
        #파란색 사각형 그리기
        pygame.draw.rect(surface, self.color,
                         (int(self.x), int(self.y), self.size, self.size))
        #Player라는 텍스트를 이미지로 만드기
        text = font.render("Player", True, BLACK)
        #surface에 text 이미지를 붙여넣기
        surface.blit(text, (int(self.x), int(self.y) - 28))

class Enemy:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.size = 50
        self.speed = 1
        self.color = RED

    def move(self, dx, dy):
        self.x += dx * self.speed
        self.y += dy * self.speed

        if self.x < 0:
            self.x = 0
        if self.y < 0:
            self.y = 0
        if self.x + self.size > WIDTH:
            self.x = WIDTH - self.size
        if self.y + self.size > HEIGHT:
            self.y = HEIGHT - self.size

    def draw(self, surface):
        pygame.draw.rect(surface, self.color,
                         (int(self.x), int(self.y), self.size, self.size))

        text = font.render("Enemy", True, BLACK)
        surface.blit(text, (int(self.x), int(self.y) - 28))

class Bullet:
    def __init__(self, x, y, dx, dy):
        self.x = float(x)
        self.y = float(y)
        self.size = 10
        self.speed = 10
        self.dx = dx  # 방향
        self.dy = dy
        self.color = (255, 165, 0)  # 주황색

    def move(self):
        self.x += self.dx * self.speed
        self.y += self.dy * self.speed

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.size)

    def is_out(self):
        return self.x < 0 or self.x > WIDTH or self.y < 0 or self.y > HEIGHT

class NPC:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.size = 50
        self.speed = 2
        self.color = GREEN

        self.dx = random.choice([-1, 0, 1])
        self.dy = random.choice([-1, 0, 1])

    def move(self, dx, dy):
        self.x += dx * self.speed
        self.y += dy * self.speed

        if self.x < 0:
            self.x = 0
        if self.y < 0:
            self.y = 0
        if self.x + self.size > WIDTH:
            self.x = WIDTH - self.size
        if self.y + self.size > HEIGHT:
            self.y = HEIGHT - self.size

    #Add code here
    def draw(self, surface):
        pygame.draw.rect(surface, self.color,
                         (int(self.x), int(self.y), self.size, self.size))

        text = font.render("Npc", True, BLACK)
        surface.blit(text, (int(self.x), int(self.y) - 28))
    #method 추가해보자
    # 1. 초록색 사각형 그리기
    # 2. NPC 텍스트를 이미지로 만들기
    # 3. 사각형 위에 텍스트 보이기(이미지를 surface에 붙여넣기)

#player, enemy, npc를 관리하는 클래스
class Game:
    def __init__(self):
        self.player = Player(100, 250)
        self.enemy = Enemy(700, 100)
        self.npc = NPC(500, 400)
        self.bullets = []
        self.shoot_timer = 0
        self.game_over = False

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    def update(self):
        if self.game_over:  # ← 추가: 게임오버면 업데이트 중단
            return
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
        # 객체간 메시지 교환(메서드 호출)으로 상호작용.
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
        # 객체간 메시지 교환(메서드 호출)으로 상호작용.
        self.enemy.move(e_dx, e_dy)

        # NPC는 랜덤 이동
        if random.random() < 0.02:
            self.npc.dx = random.choice([-1, 0, 1])
            self.npc.dy = random.choice([-1, 0, 1])
        # 객체간 메시지 교환(메서드 호출)으로 상호작용.
        self.npc.move(self.npc.dx, self.npc.dy)

        self.shoot_timer += 1
        if self.shoot_timer >= 20:
            self.shoot_timer = 0
            # Player 방향으로 총알 발사
            dx = self.player.x - self.enemy.x
            dy = self.player.y - self.enemy.y
            dist = math.sqrt(dx ** 2 + dy ** 2)
            if dist != 0:
                dx /= dist  # 단위벡터로 정규화
                dy /= dist
            bullet = Bullet(self.enemy.x, self.enemy.y, dx, dy)
            self.bullets.append(bullet)

        # ← 추가: 총알 이동 및 충돌 체크
        for bullet in self.bullets[:]:
            bullet.move()
            if bullet.is_out():
                self.bullets.remove(bullet)
                continue
            # Player와 충돌 체크 (사각형 충돌)
            if (self.player.x < bullet.x < self.player.x + self.player.size and
                    self.player.y < bullet.y < self.player.y + self.player.size):
                self.game_over = True  # 게임오버!

    def draw(self, surface):
        surface.fill(WHITE)
        self.player.draw(surface)
        self.enemy.draw(surface)
        self.npc.draw(surface)
        #Add code here
        #NPC 클래스에 추가한 Method 호출
        for bullet in self.bullets:
            bullet.draw(surface)

        if self.game_over:
            go_font = pygame.font.SysFont("malgungothic", 60)
            go_text = go_font.render("GAME OVER", True, RED)
            surface.blit(go_text, (WIDTH // 2 - go_text.get_width() // 2, HEIGHT // 2 - 40))

        info1 = font.render("Player: 방향키로 이동", True, BLACK)
        info2 = font.render("Enemy: 플레이어 추적 / NPC: 랜덤 이동", True, BLACK)

        surface.blit(info1, (20, 20))
        surface.blit(info2, (20, 55))

# 관리하는 객체 생성
game = Game()
while True:
    for event in pygame.event.get():
        game.handle_event(event)
    #관리하는 객체에게 메모리에 상태를 업데이트하고 화면에 그리도록 요청
    game.update()
    game.draw(screen)

    pygame.display.flip()
    clock.tick(60)