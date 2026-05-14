import pygame
import sys

pygame.init()

WIDTH, HEIGHT = 900, 500
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Encapsulation")
clock = pygame.time.Clock()

font = pygame.font.SysFont("arial", 28)
small_font = pygame.font.SysFont("arial", 22)
big_font = pygame.font.SysFont("arial", 40)

WHITE = (245, 245, 245)
BLACK = (30, 30, 30)
BLUE = (70, 130, 255)
RED = (220, 80, 80)
GREEN = (80, 180, 120)
GOLD = (255, 200, 0)
GRAY = (180, 180, 180)

class Player:
    def __init__(self, name):
        self.name = name
        self.__hp = 100  #체력
        self.score = 0 #점수
        self.x = 200
        self.y = 150
        self.radius = 35

    @property
    def hp(self):
        return self.__hp

    @hp.setter
    def hp(self, value):
        self.__hp = max(0, min(100, value))

    def draw(self, surface):
        pygame.draw.circle(surface, BLUE, (self.x, self.y), self.radius)
        name_text = small_font.render(self.name, True, BLACK)
        surface.blit(name_text, (self.x - 25, self.y - 60))



class Enemy:
    def __init__(self, name, damage):
        self.name = name
        self.damage = damage
        self.x = 650
        self.y = 150
        self.radius = 35

    def attack(self, player):
        player.hp = player.hp - self.damage
        return f"{self.name} attacks {player.name}! (-{self.damage} HP)"

    def draw(self, surface):
        pygame.draw.circle(surface, RED, (self.x, self.y), self.radius)
        name_text = small_font.render(self.name, True, BLACK)
        surface.blit(name_text, (self.x - 30, self.y - 60))

def draw_bar(surface, x, y, value, max_value, width, height, color):
    pygame.draw.rect(surface, GRAY, (x, y, width, height))
    ratio = max(0, value) / max_value if max_value > 0 else 0
    pygame.draw.rect(surface, color, (x, y, int(width * ratio), height))
    pygame.draw.rect(surface, BLACK, (x, y, width, height), 2)

def reset_game():
    return Player("Player"), Enemy("Enemy", 30), "Press SPACE to attack"

player, enemy, message = reset_game()
running = True
while running:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                message = enemy.attack(player)
            elif event.key == pygame.K_h:
                player.hp += 20 # 직접 접근 (문제)
                message = "Someone changed Player's HP directly: +20"
            elif event.key == pygame.K_j:
                player.hp -= 200 # 직접 접근 (문제)
                message = "Someone changed Player's HP directly: -200"
            elif event.key == pygame.K_s:
                player.score += 1000 # 직접 접근 (문제)
                message = "Someone changed Player's score directly: +1000"
            elif event.key == pygame.K_r:
                player, enemy, message = reset_game()

    screen.fill(WHITE)

    player.draw(screen)
    enemy.draw(screen)

    hp_text = font.render(f"HP: {player.hp}", True, BLACK)
    score_text = font.render(f"Score: {player.score}", True, BLACK)
    screen.blit(hp_text, (100, 300))
    screen.blit(score_text, (100, 340))

    draw_bar(screen, 100, 270, player.hp, 100, 250, 25, GREEN if player.hp > 30 else RED)
    message_text = small_font.render(message, True, BLACK)
    screen.blit(message_text, (100, 400))

    guide1 = small_font.render("SPACE: Enemy attacks", True, BLACK)
    guide2 = small_font.render("H: HP +20 directly   J: HP -200 directly", True, BLACK)
    guide3 = small_font.render("S: Score +1000 directly   R: Reset", True, BLACK)

    screen.blit(guide1, (500, 270))
    screen.blit(guide2, (500, 305))
    screen.blit(guide3, (500, 340))

    pygame.display.flip()

pygame.quit()
sys.exit()