import pygame
import random
import math
from abc import ABC, abstractmethod

pygame.init()
WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Polymorphism Practice")
clock = pygame.time.Clock()

font = pygame.font.SysFont("arial", 22)
big_font = pygame.font.SysFont("arial", 32)

WHITE = (245, 245, 245)
BLACK = (30, 30, 30)
BLUE = (70, 130, 255)
RED = (220, 70, 70)
GREEN = (80, 200, 120)
GOLD = (255, 200, 0)
PURPLE = (170, 90, 220)

#Add to code hear
class GameObject(ABC):
    def __init__(self, x, y, radius, color):
        self.x = float(x)
        self.y = float(y)
        self.radius = radius
        self.color = color
        self.alive = True

    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def draw(self, surface):
        pass

    @abstractmethod
    def interact(self):
        pass

    def collides_with(self, other):
        distance = math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)
        return distance < (self.radius + other.radius)


class Player(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y, 22, BLUE)
        self.speed = 5
        self.hp = 3
        self.score = 0
        self.invincible = 0

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
        self.x = max(self.radius, min(WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(HEIGHT - self.radius, self.y))
        if self.invincible > 0:
            self.invincible -= 1

    def draw(self, surface):
        if self.invincible > 0 and self.invincible % 10 < 5:
            return
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, BLACK, (int(self.x), int(self.y)), self.radius, 3)
        # 눈 추가!!
        pygame.draw.circle(surface, BLACK, (int(self.x) - 5, int(self.y) - 4), 2)
        pygame.draw.circle(surface, BLACK, (int(self.x) + 5, int(self.y) - 4), 2)

    def interact(self, player):
        pass

    def __add__(self, other):
        if isinstance(other, Coin):
            self.score += other.value
            other.alive = False
            return f"Coin +{other.value}"
        elif isinstance(other, Power):
            self.hp += other.heal_amount
            other.alive = False
            return f"HP +{other.heal_amount}"
        return None



class Bullet(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y, 6, BLACK)
        self.speed = 8
        self.damage = 1

    def update(self):
        self.y -= self.speed
        if self.y < -10:
            self.alive = False

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)

    def interact(self, player):
        pass

    def __add__(self, other):
        if isinstance(other, (Enemy, Boss)):
            other.hp -= self.damage
            self.alive = False
            return f"Hit! Enemy HP: {max(0, other.hp)}"
        return None

class Enemy(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y, 18, RED)
        self.speed = random.uniform(1.5, 3.0)
        self.direction = random.choice([-1, 1])
        self.hp = 3

    def update(self):
        self.x += self.speed * self.direction
        if self.x <= self.radius or self.x >= WIDTH - self.radius:
            self.direction *= -1
        if self.hp <= 0:
            self.alive = False

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        hp_text = font.render(str(self.hp), True, WHITE)
        hp_rect = hp_text.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(hp_text, hp_rect)

    def interact(self, player):
        if player.invincible > 0:
            return None
        else :
            player.hp -= 1
            player.invincible = 90
            return "Ouch! HP -1"

class Coin(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y, 12, GOLD)
        self.value = 10
        self.angle = 0

    def update(self):
        self.angle += 0.08

    def draw(self, surface):
        animated_radius = self.radius + int(2 * math.sin(self.angle))
        pygame.draw.circle(
            surface,
            self.color,
            (int(self.x), int(self.y)),
            max(6, animated_radius)
        )
        pygame.draw.circle(surface, WHITE, (int(self.x) - 3, int(self.y) - 3), 3)

    def interact(self, player):
        return player + self

class Boss(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y, 40, PURPLE)
        self.hp = 20
        self.max_hp = 20
        self.speed = 1.5
        self.shoot_timer = 0
        self.shoot_interval = 70


    def update(self):
        global player
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.sqrt(dx**2 + dy**2)
        if dist > 0:
            self.x += self.speed * dx / dist
            self.y += self.speed * dy / dist

        self.shoot_timer += 1
        if self.shoot_timer >= self.shoot_interval:
            self.shoot_timer = 0
            angle = math.atan2(dy, dx)
            self.pending_shots = [
                (math.cos(angle - 0.5), math.sin(angle - 0.5)),
                (math.cos(angle), math.sin(angle)),
                (math.cos(angle + 0.5), math.sin(angle + 0.5)),
            ]
        else:
            self.pending_shots = []

        if self.hp <= 0:
            self.alive = False

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, BLACK, (int(self.x), int(self.y)), self.radius, 3)

        bar_width = 80
        bar_height = 8
        bar_x = int(self.x) - bar_width // 2
        bar_y = int(self.y) - self.radius - 16
        pygame.draw.rect(surface, RED, (bar_x, bar_y, bar_width, bar_height))
        hp_ratio = max(0, self.hp / self.max_hp)
        pygame.draw.rect(surface, GREEN, (bar_x, bar_y, int(bar_width * hp_ratio), bar_height))
        pygame.draw.rect(surface, BLACK, (bar_x, bar_y, bar_width, bar_height), 2)

        label = font.render("BOSS", True, WHITE)
        label_rect = label.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(label, label_rect)

    def interact(self, player):
        if player.invincible > 0:
            return None
        player.hp -= 3
        player.invincible = 90
        return "BOSS HIT! HP -3"

class BossBullet(GameObject):
    def __init__(self, x, y, dx, dy):
        super().__init__(x, y, 8, PURPLE)
        speed = 4
        dist = math.sqrt(dx**2 + dy**2)
        self.vx = speed * dx / dist  # x 방향 속도
        self.vy = speed * dy / dist  # y 방향 속도

    def update(self):
        self.x += self.vx
        self.y += self.vy
        # 화면 밖으로 나가면 제거
        if self.x < 0 or self.x > WIDTH or self.y < 0 or self.y > HEIGHT:
            self.alive = False

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)

    def interact(self, player):
        if player.invincible > 0:
            return None
        player.hp -= 1
        player.invincible = 90
        return "Boss bullet hit! HP -1"

class Power(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y, 14, GREEN)
        self.heal_amount = 1
        self.dy = 1
        self.base_y = y

    def update(self):
        self.y += self.dy
        if self.y > self.base_y + 10 or self.y < self.base_y - 10:
            self.dy *= -1

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.line(surface, WHITE, (int(self.x), int(self.y - 6)), (int(self.x), int(self.y + 6)), 2)
        pygame.draw.line(surface, WHITE, (int(self.x - 6), int(self.y)), (int(self.x + 6), int(self.y)), 2)

    def interact(self, player):
        return player + self


class MessageBox:
    def __init__(self):
        self.text = "Arrow keys: Move | Spacebar: Shoot"
        self.timer = 0

    def set_message(self, text):
        if text:
            self.text = text
            self.timer = 120

    def update(self):
        if self.timer > 0:
            self.timer -= 1

    def draw(self, surface):
        color = PURPLE if self.timer > 0 else BLACK
        text_img = font.render(self.text, True, color)
        surface.blit(text_img, (20, 20))

player = Player(WIDTH // 2, HEIGHT // 2)
message_box = MessageBox()

objects = []
bullets = []

for _ in range(5):
    objects.append(Enemy(random.randint(60, WIDTH - 60), random.randint(100, HEIGHT - 60)))

for _ in range(6):
    objects.append(Coin(random.randint(60, WIDTH - 60), random.randint(100, HEIGHT - 60)))

for _ in range(3):
    objects.append(Power(random.randint(60, WIDTH - 60), random.randint(100, HEIGHT - 60)))

running = True
game_over = False
game_clear = False
boss_spawned = False


while running:
    clock.tick(60)
    screen.fill(WHITE)

    # Event Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN and not game_over:
            if event.key == pygame.K_SPACE:
                bullets.append(Bullet(player.x, player.y - player.radius))
                message_box.set_message("Bullet fired!")

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q and (game_over or game_clear):
                running = False

    if not game_over and not game_clear:
        player.update()
        for obj in objects:
            obj.update()
        for bullet in bullets:
            bullet.update()

        message_box.update()

        for obj in objects:
            if obj.alive and player.collides_with(obj):
                result = obj.interact(player)
                message_box.set_message(result)

        for obj in objects:
            if isinstance(obj, BossBullet) and obj.alive and player.collides_with(obj):
                result = obj.interact(player)
                message_box.set_message(result)

        for obj in objects:
            if isinstance(obj, Boss) and hasattr(obj, 'pending_shots') and obj.pending_shots:
                for dx, dy in obj.pending_shots:
                    objects.append(BossBullet(obj.x, obj.y, dx, dy))
                message_box.set_message("Boss is shooting!")

        for bullet in bullets:
            if not bullet.alive:
                continue

            for obj in objects:
                if isinstance(obj, (Enemy, Boss)) and obj.alive and bullet.collides_with(obj):
                    result = bullet + obj
                    message_box.set_message(result)
                    break

        # 죽은 객체 제거
        objects = [obj for obj in objects if obj.alive]
        bullets = [bullet for bullet in bullets if bullet.alive]

        # 보스 스폰 조건
        enemy_count = sum(1 for obj in objects if isinstance(obj, Enemy))
        boss_count = sum(1 for obj in objects if isinstance(obj, Boss))

        if boss_spawned and boss_count == 0 and not game_over:
            game_clear = True

        if enemy_count == 0 and boss_count == 0 and not boss_spawned:
            objects.append(Boss(WIDTH // 2, 80))
            message_box.set_message("BOSS APPEARED!")
            boss_spawned = True

        if player.hp <= 0:
            game_over = True
            message_box.set_message("Game Over")

    else:
        message_box.update()

    drawables = [player] + objects + bullets + [message_box]

    for obj in drawables:
        obj.draw(screen)

    hp_text = font.render(f"HP: {player.hp}", True, BLACK)
    score_text = font.render(f"Score: {player.score}", True, BLACK)
    enemy_count = sum(1 for obj in objects if isinstance(obj, Enemy))
    enemy_text = font.render(f"Enemies: {enemy_count}", True, BLACK)

    screen.blit(hp_text, (20, 55))
    screen.blit(score_text, (20, 85))
    screen.blit(enemy_text, (20, 115))

    if game_over:
        # 어두운 반투명 오버레이
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        over_text = big_font.render("GAME OVER", True, RED)
        sub_text = font.render(f"Score: {player.score}  |  Press Q to Quit", True, WHITE)
        screen.blit(over_text, over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30)))
        screen.blit(sub_text, sub_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20)))

    elif game_clear:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        clear_text = big_font.render("YOU WIN!", True, GOLD)
        sub_text = font.render(f"Score: {player.score}  |  Press Q to Quit", True, WHITE)
        screen.blit(clear_text, clear_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30)))
        screen.blit(sub_text, sub_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20)))

    pygame.display.flip()

pygame.quit()