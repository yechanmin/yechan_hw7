# 상속 적용
import pygame
import random
import math
import sys

pygame.init()

WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("상속")
clock = pygame.time.Clock()
font = pygame.font.SysFont("malgungothic", 20)

# color
BLUE = (70, 70, 255)
RED = (230, 80, 80)
GOLD = (255, 200, 0)
GREEN = (80, 200, 120)
WHITE = (245, 245, 245)
BLACK = (30, 30, 30)

# Parent - 공통 데이터와 기능을 가지고 있음
class GameObject:
    def __init__(self, x, y, radius, color):
        self.x = float(x)
        self.y = float(y)
        self.radius = radius
        self.color = color
        self.alive = True

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)

    def update(self):
        # 자식클래스에서 필요한 대로 각기 구현됨 --> 오버라이딩
        pass

    def distance_to(self, other):
        return math.hypot(self.x - other.x, self.y - other.y)

    def collides_with(self, other):
        return self.distance_to(other) < self.radius + other.radius

# Child  - Player, Enemy, Coin은 GameObject 클래스로부터 상속받음.
class Player(GameObject):
    def __init__(self, x, y):
        # 부모의 공통 초기화 재사용
        super().__init__(x, y, radius=20, color=BLUE)
        self.speed = 5
        self.score = 0
        self.hp = 3
        self.invincible = False
        self.invincible_timer = 0
        self.invincible_duration = 120

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


        # 화면 밖으로 못 나가게 처리
        self.x = max(self.radius, min(WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(HEIGHT - self.radius, self.y))

        if self.invincible:
            self.invincible_timer -= 1
            if self.invincible_timer <= 0:
                self.invincible = False

    def draw(self, surface):
        if self.invincible and self.invincible_timer % 10 < 5:
            return
        super().draw(surface)
        # 테두리 추가
        pygame.draw.circle(surface, BLACK, (int(self.x), int(self.y)), self.radius, 3)
        # 눈추가
        pygame.draw.circle(surface, BLACK, (int(self.x) - 5, int(self.y) - 4), 2)
        pygame.draw.circle(surface, BLACK, (int(self.x) + 5, int(self.y) - 4), 2)


class Enemy(GameObject):
    def __init__(self, x, y, stage=1):
        super().__init__(x, y, radius=18, color=RED)
        self.speed = random.uniform(1.2, 2.0) + stage*0.3

    def update(self, player):
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)

        if dist != 0:
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

    def draw(self, surface):
        super().draw(surface)
        # 눈 추가!!
        pygame.draw.circle(surface, BLACK, (int(self.x) - 5, int(self.y) - 4), 2)
        pygame.draw.circle(surface, BLACK, (int(self.x) + 5, int(self.y) - 4), 2)


class Coin(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y, radius=12, color=GOLD)
        self.base_radius = 12
        self.t = 0

    def update(self):
        # 크기가 살짝 커졌다 작아졌다 하도록
        self.t += 0.12
        self.radius = int(self.base_radius + math.sin(self.t) * 2)

    def draw(self, surface):
        super().draw(surface)
        pygame.draw.circle(surface, WHITE, (int(self.x) - 3, int(self.y) - 3), 3)

class HP(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y, radius=12, color=GREEN)
        self.base_radius = 12
        self.t = 0

    def update(self):
        self.t += 0.12
        self.radius = int(self.base_radius + math.sin(self.t) * 2)

    def draw(self, surface):
        super().draw(surface)
        # + 모양 그리기
        pygame.draw.rect(surface, WHITE, (int(self.x) - 8, int(self.y) - 3, 16, 6))
        pygame.draw.rect(surface, WHITE, (int(self.x) - 3, int(self.y) - 8, 6, 16))



def random_position(margin=40):
    x = random.randint(margin, WIDTH - margin)
    y = random.randint(margin, HEIGHT - margin)
    return x, y

def draw_text(text, x, y, color=BLACK):
    img = font.render(text, True, color)
    screen.blit(img, (x, y))


class Game:
    def __init__(self):
        self.player = Player(WIDTH // 2, HEIGHT // 2)
        self.enemies = []
        self.coins = []
        self.hps = []
        self.hps.append(HP(*random_position()))
        for _ in range(5):
            self.enemies.append(Enemy(*random_position(), 1))
        for _ in range(8):
            self.coins.append(Coin(*random_position()))
        self.running = True
        self.game_over = False
        self.stage = 1

    # 이벤트 처리
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    # 게임 업데이트
    def update(self):
        if self.game_over:
            return
        self.player.update()
        for enemy in self.enemies:
            enemy.update(self.player)
        for coin in self.coins:
            coin.update()
        self.check_collisions()
        for hp in self.hps:
            hp.update()

    # 충돌 처리
    def check_collisions(self):
        # 코인 먹기
        for coin in self.coins:
            if coin.alive and self.player.collides_with(coin):
                coin.alive = False
                self.player.score += 1
        #먹힌 코인 제거
        self.coins = [c for c in self.coins if c.alive]
        #코인이 다 없어지면 새로 생성하자
        # if len(self.coins) == 0:
        #     for _ in range(8):
        #         self.coins.append(Coin(*random_position()))
        if len(self.coins) == 0:
            self.stage += 1  # 스테이지 증가
            enemy_count = 4 + self.stage  # 스테이지마다 적 증가
            for _ in range(8):
                self.coins.append(Coin(*random_position()))
            self.enemies = [Enemy(*random_position(), self.stage) for _ in range(enemy_count)]
            self.hps.append(HP(*random_position()))

        for hp in self.hps:
            if hp.alive and self.player.collides_with(hp):
                hp.alive = False
                self.player.hp += 1
        self.hps = [hp for hp in self.hps if hp.alive]
        if len(self.hps) == 0:
            self.hps.append(HP(*random_position()))

        # 적 충돌
        for enemy in self.enemies:
            if self.player.collides_with(enemy):
                if not self.player.invincible:  # 무적 아닐 때만 데미지
                    self.player.hp -= 1
                    self.player.invincible = True
                    self.player.invincible_timer = self.player.invincible_duration
                    self.player.x = WIDTH // 2
                    self.player.y = HEIGHT // 2
                    self.enemies = [Enemy(*random_position()) for _ in range(5)]
                    if self.player.hp <= 0:
                        self.game_over = True
                break


    # 화면 그리기
    def draw(self):
        screen.fill(WHITE)
        # 공통 부모 덕분에 모든 객체를 같은 방식으로 다룰 수 있음
        all_objects = [self.player] + self.enemies + self.coins + self.hps

        for obj in all_objects:
            obj.draw(screen)

        draw_text(f"점수: {self.player.score}", 20, 20)
        draw_text(f"체력(적과 충돌하면 줄어듬): {self.player.hp}", 20, 55)
        draw_text(f"스테이지: {self.stage}", 20, 90, BLUE)
        draw_text("방향키로 이동", 20, 125, RED)

        if self.game_over:
            draw_text("GAME OVER", WIDTH // 2 - 80, HEIGHT // 2 - 20, RED)
        pygame.display.flip()

    # 메인 루프를 메서드로 넣어보자.
    def run(self):
        while self.running:
            clock.tick(60)
            self.handle_events()
            self.update()
            self.draw()


game = Game()
game.run()

pygame.quit()
sys.exit()



