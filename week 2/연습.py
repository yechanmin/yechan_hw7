import pygame, sys
pygame.init()

W, H = 800, 600
screen = pygame.display.set_mode((W, H))
clock = pygame.time.Clock()

class Ball:
    def __init__(self, x, y, r, color, vx, vy):
        self.x = x
        self.y = y
        self.r = r
        self.color = color
        self.vx = vx
        self.vy = vy

    def update(self, w, h):
        self.x += self.vx
        self.y += self.vy

        if self.x - self.r <= 0 or self.x + self.r >= w:
            self.vx *= -1
        if self.y - self.r <= 0 or self.y + self.r >= h:
            self.vy *= -1

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.r)

B = Ball(300, 200, 20, (7, 62, 3), 10, 5)
C = Ball(150, 200, 30, (200, 2, 3), 20, 10)


while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    screen.fill((255, 255, 255))
    B.update(W, H)
    B.draw(screen)
    C.update(W, H)
    C.draw(screen)

    pygame.display.flip()
    clock.tick(60)
