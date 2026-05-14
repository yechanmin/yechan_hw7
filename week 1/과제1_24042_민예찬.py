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
        #공의 반지름, 질량
        self.r = int(r)
        self.m = self.r * self.r
        #공의 색
        self.color = rand_color()
        #x 방향 속도
        self.vx = random.choice([-1, 1]) * random.uniform(2.0, 5.0)
        #y방향 속도
        self.vy = random.choice([-1, 1]) * random.uniform(2.0, 5.0)

    def update(self, w, h, g=0.25, bounce=0.9, friction=0.995):
        #중력
        self.vy += g

        #이동
        self.x += self.vx
        self.y += self.vy

        #좌우 벽 충돌 검사
        if self.x - self.r <= 0:
            self.x = self.r
            self.vx *= -bounce
        elif self.x + self.r >= w:
            self.x = w - self.r
            self.vx *= -bounce
        #상하 벽 충돌 검사
        if self.y + self.r >= h:
            self.y = h - self.r
            self.vy *= -bounce
            self.vx *= friction  # 바닥에서 살짝 미끄러지며 감속
            if abs(self.vy) < 0.6:  # 너무 작게 떨면 정지
                self.vy = 0.0
        elif self.y - self.r <= 0:
            self.y = self.r
            self.vy *= -bounce

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
        self.g = 0.25
        self.bounce = 0.9
        self.friction = 0.995

# -----------------------------
# 이벤트 처리
# -----------------------------
    def handle_event(self, event):
        # 메시지 기반 상호작용: "공 추가"
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos #클릭 위치 얻기
            self.balls.append(Ball(mx, my, random.randint(12, 24))) # 해당 위치에 새로운 공 생성
        if event.type == pygame.KEYDOWN: # 위아래 방향키로 중력 조정
            if event.key == pygame.K_UP:
                self.g += 0.05
            elif event.key == pygame.K_DOWN:
                self.g -= 0.05

# -----------------------------
# 충돌
# -----------------------------
    def resolve_collisions(self):
        n = len(self.balls)
        for i in range(n):
            for j in range(i + 1, n):
                a = self.balls[i]
                b = self.balls[j]

                dx = b.x - a.x
                dy = b.y - a.y
                rr = a.r + b.r
                d2 = dx * dx + dy * dy
                if d2 == 0:
                    dx, dy = 1.0, 0.0
                    d2 = 1.0

                if d2 <= rr * rr:
                    dist = (d2) ** 0.5
                    nx, ny = dx / dist, dy / dist

                    # 겹침 해소(먼저 떼어내기)
                    overlap = rr - dist
                    a.x -= nx * overlap / 2
                    a.y -= ny * overlap / 2
                    b.x += nx * overlap / 2
                    b.y += ny * overlap / 2


                    # 간단 탄성 충돌(동질량 가정): 법선 방향 속도 성분만 교환
                    avn = a.vx * nx + a.vy * ny
                    bvn = b.vx * nx + b.vy * ny

                    # 서로 멀어지는 중이면 스킵
                    if avn - bvn <= 0:
                        continue

                    m1 = a.m
                    m2 = b.m

                    new_avn = (avn * (m1 - m2) + 2 * m2 * bvn) / (m1 + m2)
                    new_bvn = (bvn * (m2 - m1) + 2 * m1 * avn) / (m1 + m2)

                    a.vx += (new_avn - avn) * nx
                    a.vy += (new_avn - avn) * ny
                    b.vx += (new_bvn - bvn) * nx
                    b.vy += (new_bvn - bvn) * ny

                    # 전체적으로 속도 감소
                    a.vx *= 0.995
                    a.vy *= 0.995
                    b.vx *= 0.995
                    b.vy *= 0.995

# -----------------------------
# 게임 상태 업데이트
# -----------------------------
    def update(self):
        # Game은 '세계'로서 업데이트 흐름만 관리
        for b in self.balls:
            b.update(self.w, self.h, self.g, self.bounce, self.friction)
        self.resolve_collisions()

# -----------------------------
# 화면 그리기
# -----------------------------
    def draw(self, surface):
        surface.fill((245, 245, 245))
        for b in self.balls:
            b.draw(surface)

        font = pygame.font.SysFont(None, 22)
        text = font.render(
            f"Balls: {len(self.balls)} | Gravity: {self.g:.2f} | Left click: add ball",
            True,
            (30, 30, 30)
        )
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