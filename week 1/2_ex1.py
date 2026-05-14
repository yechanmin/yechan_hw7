#2_ex1.py
import pygame, sys

pygame.init()
W, H = 640, 360
screen = pygame.display.set_mode((W, H))
clock = pygame.time.Clock()

# 전역 상태(절차지향의 전형)
x, y = 120.0, 120.0
vx, vy = 4.0, 2.5
r = 18
x2, y2 = 300.0, 200.0
vx2, vy2 = -3.0, 2.0
r2 = 18
color2 = (50, 80, 220)
color = (220, 50, 50)
PINK = (255, 105, 180)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # 업데이트(계산)
    x += vx
    y += vy
    x2 += vx2
    y2 += vy2

    # 충돌(벽)
    if x - r <= 0 or x + r >= W:
        vx *= -1
    if y - r <= 0 or y + r >= H:
        vy *= -1
    if x2 - r2 <= 0 or x2 + r2 >= W:
        vx2 *= -1
    if y2 - r2 <= 0 or y2 + r2 >= H:
        vy2 *= -1

    # 그리기(출력)
    screen.fill((245, 245, 245))
    pygame.draw.circle(screen, color, (int(x), int(y)), r)
    pygame.draw.circle(screen, PINK, (int(x2), int(y2)), r2)
    pygame.display.flip()
    clock.tick(60)