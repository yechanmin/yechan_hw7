#3_ex2.py
import pygame, sys

pygame.init()
W, H = 640, 360
screen = pygame.display.set_mode((W, H))
clock = pygame.time.Clock()

class Ball:
    def __init__(self, x, y, r, color, vx, vy):
        self.x = float(x)
        self.y = float(y)
        self.r = int(r)
        self.color = color
        self.vx = float(vx)
        self.vy = float(vy)

    def update(self, w, h):
        # 상태 변화(움직임)
        self.x += self.vx
        self.y += self.vy

        # 벽과 상호작용(충돌)
        if self.x - self.r <= 0 or self.x + self.r >= w:
            self.vx *= -1
        if self.y - self.r <= 0 or self.y + self.r >= h:
            self.vy *= -1

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.r)

# ball을 리스트로
balls = [
    Ball(100, 120, 20, (220, 50, 50), 3, 2),
    Ball(260, 200, 15, (50, 80, 220), -2.5, 3.2),
    Ball(420, 160, 25, (60, 180, 90), 2.2, -2.8),
]

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    screen.fill((245, 245, 245))

    # 모든 공 업데이트/그리기
    ##### Add code Here!.
    for b in balls:
        b.update(W, H)
        b.draw(screen)

    pygame.display.flip()
    clock.tick(60)

