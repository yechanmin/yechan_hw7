#4_ex3.py
import pygame, sys, random
# -----------------------------
# 1. pygame 초기화
# -----------------------------
pygame.init()
W, H = 640, 360
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("OOP")
# FPS(프레임 속도) 제어용 Clock 객체
clock = pygame.time.Clock()

# -----------------------------
# 무작위 색상 생성 함수
# -----------------------------
def rand_color():
    #RGB 값을 40~230 사이에서 랜덤 생성
    return (random.randint(40, 230), random.randint(40, 230), random.randint(40, 230))

class Ball:
    # 객체 생성 시 실행되는 생성자
    def __init__(self, x, y, r=16):
        #공의 위치
        self.x = float(x)
        self.y = float(y)
        #공의 반지름
        self.r = int(r)
        #공의 색

        self.color = rand_color()
        #x 방향 속도
        self.vx = random.choice([-1, 1]) * random.uniform(2.0, 5.0)
        #y방향 속도
        self.vy = random.choice([-1, 1]) * random.uniform(2.0, 5.0)

    def update(self, w, h):
        self.x += self.vx
        self.y += self.vy

        #좌우 벽 충돌 검사
        if self.x - self.r <= 0 or self.x + self.r >= w:
            self.vx *= -1
        #상하 벽 충돌 검사
        if self.y - self.r <= 0 or self.y + self.r >= h:
            self.vy *= -1

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.r)

class Game:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        # 공 객체 리스트
        self.balls = [
            Ball(120, 120, 18),
            Ball(260, 160, 14),
            Ball(420, 220, 22),
        ]

# -----------------------------
# 이벤트 처리
# -----------------------------
    def handle_event(self, event):
        # 메시지 기반 상호작용: "공 추가"
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos #클릭 위치 얻기
            self.balls.append(Ball(mx, my, random.randint(12, 24))) # 해당 위치에 새로운 공 생성

# -----------------------------
# 게임 상태 업데이트
# -----------------------------
    def update(self):
        # Game은 '세계'로서 업데이트 흐름만 관리
        for b in self.balls:
            b.update(self.w, self.h)

# -----------------------------
# 화면 그리기
# -----------------------------
    def draw(self, surface):
        surface.fill((245, 245, 245))
        for b in self.balls:
            b.draw(surface)

        font = pygame.font.SysFont(None, 22)
        text = font.render(f"Balls: {len(self.balls)}  |  Left click: add ball", True, (30, 30, 30))
        surface.blit(text, (10, 10))

game = Game(W, H)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        # Game 객체에 이벤트 전달
        game.handle_event(event)

    ##### Add code Here!
    game.update()
    game.draw(screen)

    pygame.display.flip()
    clock.tick(60) # FPS 제한 (60프레임)