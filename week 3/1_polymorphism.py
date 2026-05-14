import pygame
import sys
#1. 초기화
pygame.init()
#2. 화면설정
WIDTH = 800
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))#800x600크기의 윈도우생성
pygame.display.set_caption("Polymorphism") #화면제목설정
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)

class GameObject():
    def update(self):
        pass
    def draw(self, surface):
        pass


class Player(GameObject):
    def update(self):
        print("플레이어 업데이트")
    def draw(self, suface):
        print("플레이어 그리기")

class Enemy(GameObject):
    def update(self):
        print("적 업데이트")
    def draw(self, suface):
        print("적 그리기")

class Coin(GameObject):
    def update(self):
        print("코인 업데이트")
    def draw(self, suface):
        print("코인 그리기")

class Power(GameObject):
    def update(self):
        print("파워 업데이트")
    def draw(self, suface):
        print("파워 그리기")

objects = []
for _ in range(10):
    objects += [Player(), Enemy(), Coin(), Power()]

for obj in objects:
    obj.update()
    obj.draw(screen)

players = []
enemies = []
coins = []
powers = []

for _ in range(10):
    players.append(Player())
    enemies.append(Enemy())
    coins.append(Coin())
    powers.append(Power())

#3.메인 루프
running = True
while running:
    for event in pygame.event.get(): #이벤트처리
        if event.type == pygame.QUIT:
            running = False
    #화면그리기
    screen.fill(WHITE) #이전화면지우기(배경흰색)

    for player in players:
        player.update()
        player.draw(screen)

    for enemy in enemies:
        enemy.update()
        enemy.draw(screen)

    for coin in coins:
        coin.update()
        coin.draw(screen)

    for power in powers:
        power.update()
        power.draw(screen)

    pygame.display.flip()#메모리에 있는 걸 실제로 화면에 그림
#4.종료
pygame.quit()
sys.exit()
