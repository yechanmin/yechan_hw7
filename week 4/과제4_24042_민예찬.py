#  새로운 아이템/Enemy를 설계하여 추가하세요.
#조건
#1. GameObject를 상속받아 새 클래스를 만들것
#2. 기존 objects 리스트를 그대로 활용할 것
#3. 새로 만들 클래스의 인스턴스의 상태를 __변수와  @property 또는 메서드로 관리할 것(중요!!)
import pygame
import random
import sys
from abc import ABC, abstractmethod

pygame.init()

WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Encapsulation")
clock = pygame.time.Clock()
font = pygame.font.SysFont("malgungothic", 24)
big_font = pygame.font.SysFont("malgungothic", 40)

WHITE = (245, 245, 245)
BLACK = (30, 30, 30)
BLUE = (70, 130, 255)
RED = (220, 80, 80)
GOLD = (255, 210, 0)
GREEN = (80, 200, 120)
GRAY = (180, 180, 180)


class GameObject(ABC):
    def __init__(self):
        self._alive = True

    @property
    def is_alive(self):
        return self._alive

    def destroy(self):
        self._alive = False

    @property
    def can_collide_with_player(self):
        return False

    @property
    def can_collide_with_bullet(self):
        return False

    @property
    def is_bullet(self):
        return False

    @property
    @abstractmethod
    def rect(self):
        pass

    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def draw(self, surface):
        pass

    def on_player_collision(self, player):
        pass

    def on_bullet_collision(self, bullet, player):
        pass

class Player(GameObject):
    def __init__(self):
        super().__init__()
        self._x = 100
        self._y = 300
        self._size = 40
        self._speed = 5

        self._max_hp = 100
        self._hp = 100
        self._score = 0
        self.__invincible_timer = 0
        self.__invincible_duration = 30
        self.__shield_timer = 0

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        if isinstance(value, (int, float)):
            self._x = max(0, min(WIDTH - self._size, value))

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        if isinstance(value, (int, float)):
            self._y = max(0, min(HEIGHT - self._size, value))

    @property
    def hp(self):
        return self._hp

    @hp.setter
    def hp(self, value):
        if isinstance(value, (int, float)):
            self._hp = max(0, min(self._max_hp, int(value)))

    @property
    def max_hp(self):
        return self._max_hp

    @property
    def score(self):
        return self._score

    @score.setter
    def score(self, value):
        if isinstance(value, (int, float)):
            self._score = max(0, int(value))

    @property
    def is_dead(self):
        return not self.is_alive

    @property
    def is_shielded(self):
        return self.__shield_timer > 0

    @property
    def is_invincible(self):
        return self.__invincible_timer > 0 or self.is_shielded

    def activate_shield(self, duration=300):
        self.__shield_timer = duration

    @property
    def rect(self):
        return pygame.Rect(int(self._x), int(self._y), self._size, self._size)

    def shoot(self):
        cx = self._x + self._size
        cy = self._y + self._size // 2
        return [Bullet(cx, cy, -15), Bullet(cx, cy, 0), Bullet(cx, cy, 15)]

    def take_damage(self, amount):
        if amount >= 0 and self.is_alive and not self.is_invincible:
            self.hp -= amount
            if self._hp <= 0:
                self.destroy()
            else:
                self.__invincible_timer = self.__invincible_duration

    def add_score(self, amount):
        if amount >= 0:
            self.score += amount

    def update(self):
        if not self.is_alive:
            return

        if self.__invincible_timer > 0:
            self.__invincible_timer -= 1
        if self.__shield_timer > 0:
            self.__shield_timer -= 1

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.x -= self._speed
        if keys[pygame.K_RIGHT]:
            self.x += self._speed
        if keys[pygame.K_UP]:
            self.y -= self._speed
        if keys[pygame.K_DOWN]:
            self.y += self._speed

    def draw(self, surface):
        if self.is_dead:
            color = GRAY
        elif self.__invincible_timer > 0 and self.__invincible_timer % 6 < 3:
            color = WHITE
        else:
            color = BLUE
        pygame.draw.rect(surface, color, self.rect)
        if self.is_shielded:
            cx = int(self._x + self._size // 2)
            cy = int(self._y + self._size // 2)
            pygame.draw.circle(surface, (100, 200, 255), (cx, cy), self._size, 3)


class Enemy(GameObject):
    def __init__(self):
        super().__init__()
        self._radius = 20
        self._speed = random.choice([3, 4, 5, 6])
        self.reset()

    @property
    def can_collide_with_player(self):
        return True

    @property
    def can_collide_with_bullet(self):
        return True

    @property
    def rect(self):
        return pygame.Rect(
            int(self._x - self._radius),
            int(self._y - self._radius),
            self._radius * 2,
            self._radius * 2
        )

    def reset(self):
        self._x = WIDTH + self._radius
        self._y = random.randint(50, HEIGHT - 50)

    def update(self):
        self._x -= self._speed
        if self._x < -self._radius:
            self.reset()

    def draw(self, surface):
        pygame.draw.circle(surface, RED, (int(self._x), int(self._y)), self._radius)

    def on_player_collision(self, player):
        player.take_damage(10)

    def on_bullet_collision(self, bullet, player):
        if self.is_alive and bullet.is_alive:
            player.add_score(20)
            self.reset()
            bullet.destroy()

class Coin(GameObject):
    def __init__(self):
        super().__init__()
        self._radius = 12
        self._dy = 1
        self._direction = 1
        self.reset()

    @property
    def can_collide_with_player(self):
        return True

    @property
    def rect(self):
        return pygame.Rect(
            int(self._x - self._radius),
            int(self._y - self._radius),
            self._radius * 2,
            self._radius * 2
        )

    def reset(self):
        self._x = random.randint(100, WIDTH - 50)
        self._y = random.randint(50, HEIGHT - 50)

    def update(self):
        self._y += self._dy * self._direction
        if self._y > HEIGHT - 30 or self._y < 30:
            self._direction *= -1

    def draw(self, surface):
        pygame.draw.circle(surface, GOLD, (int(self._x), int(self._y)), self._radius)
        pygame.draw.circle(surface, BLACK, (int(self._x), int(self._y)), self._radius, 2)

    def on_player_collision(self, player):
        player.add_score(10)
        self.reset()

class Bullet(GameObject):
    def __init__(self, x, y, angle_offset=0):
        super().__init__()
        import math
        self._x = x
        self._y = y
        speed = 10
        angle = math.radians(angle_offset)
        self._vx = math.cos(angle) * speed
        self._vy = math.sin(angle) * speed
        self._radius = 5

    @property
    def is_bullet(self):
        return True

    @property
    def rect(self):
        return pygame.Rect(
            int(self._x - self._radius),
            int(self._y - self._radius),
            self._radius * 2,
            self._radius * 2
        )

    def update(self):
        self._x += self._vx
        self._y += self._vy
        if self._x > WIDTH + self._radius:
            self.destroy()

    def draw(self, surface):
        pygame.draw.circle(surface, BLACK, (int(self._x), int(self._y)), self._radius)


class EnemyBullet(GameObject):
    def __init__(self, x, y, target_x, target_y, angle_offset=0):
        super().__init__()
        self.__x = x
        self.__y = y
        self.__radius = 6
        self.__damage = 10
        speed = 4
        import math
        dx = target_x - x
        dy = target_y - y
        dist = max(1, (dx ** 2 + dy ** 2) ** 0.5)
        base_angle = math.atan2(dy, dx)
        angle = base_angle + math.radians(angle_offset)
        self.__vx = math.cos(angle) * speed
        self.__vy = math.sin(angle) * speed

    @property
    def can_collide_with_player(self):
        return True

    @property
    def rect(self):
        return pygame.Rect(
            int(self.__x - self.__radius),
            int(self.__y - self.__radius),
            self.__radius * 2,
            self.__radius * 2
        )

    def update(self):
        self.__x += self.__vx
        self.__y += self.__vy
        if self.__x < 0 or self.__x > WIDTH or self.__y < 0 or self.__y > HEIGHT:
            self.destroy()

    def draw(self, surface):
        pygame.draw.circle(surface, (255, 100, 0), (int(self.__x), int(self.__y)), self.__radius)

    def on_player_collision(self, player):
        player.take_damage(self.__damage)
        self.destroy()


class ShootingEnemy(GameObject):
    def __init__(self):
        super().__init__()
        self.__radius = 24
        self.__speed = random.choice([1, 2])
        self.__shoot_interval = 120
        self.__shoot_timer = random.randint(0, 120)
        self.__pending_bullets = []
        self.reset()

    @property
    def can_collide_with_player(self):
        return True

    @property
    def can_collide_with_bullet(self):
        return True

    @property
    def pending_bullets(self):
        bullets = self.__pending_bullets
        self.__pending_bullets = []
        return bullets

    @property
    def rect(self):
        return pygame.Rect(
            int(self._x - self.__radius),
            int(self._y - self.__radius),
            self.__radius * 2,
            self.__radius * 2
        )

    def reset(self):
        self._x = WIDTH + self.__radius
        self._y = random.randint(50, HEIGHT - 50)
        self.__shoot_timer = random.randint(0, self.__shoot_interval)

    def update(self, player=None):
        self._x -= self.__speed
        if self._x < -self.__radius:
            self.reset()

        self.__shoot_timer += 1
        if self.__shoot_timer >= self.__shoot_interval:
            self.__shoot_timer = 0
            if player is not None:
                for offset in [-20, 0, 20]:
                    self.__pending_bullets.append(EnemyBullet(
                        self._x - self.__radius,
                        self._y,
                        player.x,
                        player.y,
                        offset
                    ))

    def draw(self, surface):
        pygame.draw.circle(surface, (180, 0, 180), (int(self._x), int(self._y)), self.__radius)
        pygame.draw.circle(surface, BLACK, (int(self._x), int(self._y)), self.__radius, 2)

    def on_player_collision(self, player):
        player.take_damage(1)

    def on_bullet_collision(self, bullet, player):
        if self.is_alive and bullet.is_alive:
            player.add_score(40)
            self.reset()
            bullet.destroy()


class ShieldItem(GameObject):
    def __init__(self):
        super().__init__()
        self.__radius = 14
        self.__shield_duration = 150
        self.__bob_timer = 0
        self.reset()

    @property
    def can_collide_with_player(self):
        return True

    @property
    def rect(self):
        return pygame.Rect(
            int(self._x - self.__radius),
            int(self._y - self.__radius),
            self.__radius * 2,
            self.__radius * 2
        )

    def reset(self):
        self._x = random.randint(150, WIDTH - 100)
        self._y = random.randint(60, HEIGHT - 80)
        self.__bob_timer = 0

    def update(self):
        self.__bob_timer += 1

    def draw(self, surface):
        import math
        bob = math.sin(self.__bob_timer * 0.05) * 4
        cx = int(self._x)
        cy = int(self._y + bob)
        pygame.draw.circle(surface, (100, 200, 255), (cx, cy), self.__radius)
        pygame.draw.circle(surface, (50, 120, 220), (cx, cy), self.__radius, 3)
        pygame.draw.polygon(surface, WHITE, [
            (cx, cy - 7),
            (cx - 6, cy + 4),
            (cx + 6, cy + 4)
        ])

    def on_player_collision(self, player):
        player.activate_shield(self.__shield_duration)
        self.reset()


def draw_ui(surface, player):
    bar_x, bar_y = 20, 20
    bar_w, bar_h = 220, 24

    pygame.draw.rect(surface, GRAY, (bar_x, bar_y, bar_w, bar_h))
    current_w = bar_w * (player.hp / player.max_hp)
    pygame.draw.rect(surface, GREEN, (bar_x, bar_y, current_w, bar_h))
    pygame.draw.rect(surface, BLACK, (bar_x, bar_y, bar_w, bar_h), 2)

    hp_text = font.render(f"HP: {player.hp}/{player.max_hp}", True, BLACK)
    score_text = font.render(f"Score: {player.score}", True, BLACK)
    info_text = font.render("SPACE: Shoot   R: Restart   ESC: Quit", True, BLACK)

    surface.blit(hp_text, (20, 50))
    surface.blit(score_text, (20, 85))
    surface.blit(info_text, (20, 120))

    if player.is_shielded:
        shield_text = font.render("SHIELD ACTIVE", True, (100, 200, 255))
        surface.blit(shield_text, (20, 150))

def draw_game_over(surface, player):
    msg1 = big_font.render("GAME OVER", True, RED)
    msg2 = font.render(f"Final Score: {player.score}", True, BLACK)
    msg3 = font.render("R: Restart   ESC: Quit", True, BLACK)

    surface.blit(msg1, (WIDTH // 2 - msg1.get_width() // 2, 220))
    surface.blit(msg2, (WIDTH // 2 - msg2.get_width() // 2, 280))
    surface.blit(msg3, (WIDTH // 2 - msg3.get_width() // 2, 320))

def create_objects():
    player = Player()
    objects = [player]

    for _ in range(6):
        objects.append(Enemy())

    for _ in range(10):
        objects.append(Coin())

    for _ in range(3):
        objects.append(ShootingEnemy())

    for _ in range(2):
        objects.append(ShieldItem())

    return player, objects


player, objects = create_objects()
while True:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

            if not player.is_dead and event.key == pygame.K_SPACE:
                objects.extend(player.shoot())

            if player.is_dead and event.key == pygame.K_r:
                player, objects = create_objects()

    if not player.is_dead:
        new_bullets = []
        for obj in objects:
            if isinstance(obj, ShootingEnemy):
                obj.update(player)
                new_bullets.extend(obj.pending_bullets)
            else:
                obj.update()
        objects.extend(new_bullets)

        bullets = [obj for obj in objects if obj.is_bullet]
        player_targets = [
            obj for obj in objects
            if obj is not player and obj.can_collide_with_player
        ]
        bullet_targets = [
            obj for obj in objects
            if obj is not player and obj.can_collide_with_bullet
        ]

        for obj in player_targets:
            if obj.is_alive and player.rect.colliderect(obj.rect):
                obj.on_player_collision(player)

        for bullet in bullets:
            for obj in bullet_targets:
                if bullet.is_alive and obj.is_alive and bullet.rect.colliderect(obj.rect):
                    obj.on_bullet_collision(bullet, player)

        objects = [obj for obj in objects if obj.is_alive or obj is player]

    screen.fill(WHITE)

    for obj in objects:
        obj.draw(screen)

    draw_ui(screen, player)

    if player.is_dead:
        draw_game_over(screen, player)

    pygame.display.flip()