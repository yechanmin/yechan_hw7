import pygame, sys, math, random
from abc import ABC, abstractmethod

pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)

TILE         = 40
COLS         = 15
ROWS         = 12
TOP_BAR      = 60
W            = COLS * TILE
H            = ROWS * TILE + TOP_BAR
FPS          = 60
BASE_INTERVAL = 180

# ─── 색상 ────────────────────────────────────────────────
GRID_DARK   = (100, 182, 60)
GRID_LIGHT  = (111, 196, 67)
SNAKE_HEAD  = (71,  117, 213)
SNAKE_BODY  = (71,  117, 213)
SNAKE_SHINE = (120, 160, 255)
APPLE_RED   = (220,  50,  50)
APPLE_DARK  = (170,  20,  20)
APPLE_LEAF  = ( 60, 160,  60)
GOLDEN_YELLOW = (255, 215, 0)
GOLDEN_DARK   = (210, 170, 20)
WHITE       = (255, 255, 255)
BLACK       = ( 20,  20,  20)

# ─── 방향 ────────────────────────────────────────────────
UP    = ( 0, -1); DOWN  = ( 0,  1)
LEFT  = (-1,  0); RIGHT = ( 1,  0)
OPPOSITE = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}

# ─── 사운드 ──────────────────────────────────────────────
def _make_snd(freq, ms, vol=0.25):
    rate = 44100; n = int(rate * ms / 1000)
    buf = bytearray(n * 2)
    for i in range(n):
        fade = min(1.0, (n - i) / max(1.0, n * 0.1))
        v = int(32767 * vol * fade * math.sin(2 * math.pi * freq * i / rate))
        v = max(-32768, min(32767, v))
        buf[2*i] = v & 0xFF; buf[2*i+1] = (v >> 8) & 0xFF
    try:   return pygame.mixer.Sound(buffer=bytes(buf))
    except: return None

SND_EAT = _make_snd(880, 80,  0.25)
SND_DIE = _make_snd(220, 400, 0.30)

# ─── 폰트 ────────────────────────────────────────────────
def _font(size, bold=False):
    for name in ["Nunito","Segoe UI","Arial Rounded MT Bold","Helvetica Neue","Arial"]:
        try:   return pygame.font.SysFont(name, size, bold=bold)
        except: pass
    return pygame.font.Font(None, size)

F_BIG = _font(38, True); F_MED = _font(24, True); F_SM = _font(18)

def tile_rect(c, r):
    return pygame.Rect(c * TILE, TOP_BAR + r * TILE, TILE, TILE)

def rrect(surf, color, rect, radius=8, bw=0, bc=None):
    pygame.draw.rect(surf, color, rect, border_radius=radius)
    if bw and bc:
        pygame.draw.rect(surf, bc, rect, bw, border_radius=radius)

def random_empty(occupied):
    while True:
        p = (random.randint(0, COLS-1), random.randint(0, ROWS-1))
        if p not in occupied: return p

def move_interval(score):
    return max(60, BASE_INTERVAL - (score // 50) * 10)


class Entity(ABC):
    @abstractmethod
    def update(self): ...

    @abstractmethod
    def draw(self, surf: pygame.Surface): ...


class Food(Entity, ABC):
    def __init__(self, pos: tuple):
        self._pos  = pos
        self._tick = 0
        self.alive = True

    @property
    def pos(self) -> tuple:
        return self._pos

    @abstractmethod
    def on_eat(self, game) -> None:
        ...

    def apply_effect(self, game, points, cnt):
        game.score += points
        game.best = max(game.best, game.score)
        game.eat_anim = 8
        if SND_EAT:
            SND_EAT.play()
        rect = tile_rect(*self._pos)
        for _ in range(cnt):
            game.particles.append(Particle(rect.centerx, rect.centery))
        self.alive = False

    def draw_apple(self, surf: pygame.Surface, main, dark, shine):
        rect = tile_rect(*self._pos)
        cx, cy = rect.centerx, rect.centery
        bob = int(math.sin(self._tick * 0.08) * 2)
        r = TILE // 2 - 4

        pygame.draw.circle(surf, dark, (cx, cy + bob), r)
        pygame.draw.circle(surf, main, (cx, cy + bob - 1), r - 1)
        pygame.draw.circle(surf, shine, (cx - r//3, cy + bob - r//3), r // 4)
        pygame.draw.line(surf, (100, 60, 20),
                         (cx, cy + bob - r), (cx, cy + bob - r - 5), 2)
        pygame.draw.polygon(surf, APPLE_LEAF, [
            (cx,     cy + bob - r - 2),
            (cx + 7, cy + bob - r - 7),
            (cx + 3, cy + bob - r - 1),
        ])

    def update(self):
        self._tick += 1

    def draw(self, surf: pygame.Surface):
        self.draw_apple(surf, APPLE_RED, APPLE_DARK, (255, 140, 140))


class Apple(Food):
    def on_eat(self, game) -> None:
        self.apply_effect(game, 10, 18)


class GoldenApple(Food):
    def on_eat(self, game) -> None:
        self.apply_effect(game, 30, 28)

    def draw(self, surf: pygame.Surface):
        self.draw_apple(surf, GOLDEN_YELLOW, GOLDEN_DARK, (255, 245, 180))


class Snake(Entity):
    def __init__(self):
        self.reset()

    def reset(self):
        mc, mr = COLS // 2, ROWS // 2
        self._body      = [(mc, mr), (mc-1, mr), (mc-2, mr)]
        self._body_set  = set(self._body)
        self._direction = RIGHT
        self._next_dir  = RIGHT
        self._eat_anim  = 0

    @property
    def head(self) -> tuple:    return self._body[0]
    @property
    def body_set(self) -> set:  return self._body_set

    def set_direction(self, d: tuple):
        if d != OPPOSITE.get(self._direction):
            self._next_dir = d

    def trigger_eat_anim(self):
        self._eat_anim = 8

    def step(self) -> str:
        self._direction = self._next_dir
        hx, hy = self._body[0]
        new_head = (hx + self._direction[0], hy + self._direction[1])

        if not (0 <= new_head[0] < COLS and 0 <= new_head[1] < ROWS):
            return 'wall'
        tail = self._body[-1]
        if new_head in (self._body_set - {tail}):
            return 'body'

        self._body.insert(0, new_head)
        self._body_set.add(new_head)
        removed = self._body.pop()
        self._body_set.discard(removed)
        return 'ok'

    def grow(self):
        self._body.append(self._body[-1])
        self._body_set.add(self._body[-1])

    def update(self):
        if self._eat_anim > 0: self._eat_anim -= 1

    def draw(self, surf: pygame.Surface):
        for i, (cx, cy) in enumerate(self._body):
            inner = tile_rect(cx, cy).inflate(-6, -6)
            rrect(surf, SNAKE_BODY, inner, radius=7)
            if i == 0:
                sh = inner.inflate(-inner.width//2, -inner.height//2)
                sh.topleft = (inner.left + 4, inner.top + 4)
                pygame.draw.ellipse(surf, SNAKE_SHINE, sh)
                if self._eat_anim > 0:
                    scale = 1 + 0.15 * (self._eat_anim / 8)
                    big   = inner.inflate(int(inner.width*(scale-1)),
                                          int(inner.height*(scale-1)))
                    rrect(surf, SNAKE_HEAD, big, radius=9)

                dx, dy = self._direction
                ex = inner.centerx + dx*6 + dy*5
                ey = inner.centery + dy*6 + dx*5
                pygame.draw.circle(surf, WHITE, (ex, ey), 4)
                pygame.draw.circle(surf, BLACK, (ex+dx, ey+dy), 2)


class Particle(Entity):
    def __init__(self, x, y):
        ang = random.uniform(0, 2*math.pi)
        spd = random.uniform(2, 6)
        self._x    = float(x); self._y = float(y)
        self._vx   = math.cos(ang)*spd
        self._vy   = math.sin(ang)*spd - 2
        self._life = random.randint(20, 40)
        self._max  = self._life
        self._col  = random.choice([APPLE_RED, (255,200,50), (255,255,100)])
        self._size = random.randint(3, 7)

    @property
    def alive(self): return self._life > 0

    def update(self):
        self._x += self._vx; self._y += self._vy
        self._vy += 0.3;    self._life -= 1

    def draw(self, surf: pygame.Surface):
        a = int(255 * self._life / self._max)
        r, g, b = self._col
        s = pygame.Surface((self._size*2, self._size*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (r, g, b, a), (self._size, self._size), self._size)
        surf.blit(s, (int(self._x)-self._size, int(self._y)-self._size))


def draw_grid(surf):
    for r in range(ROWS):
        for c in range(COLS):
            col = GRID_DARK if (r+c)%2==0 else GRID_LIGHT
            pygame.draw.rect(surf, col, (c*TILE, TOP_BAR+r*TILE, TILE, TILE))

def draw_panel(surf, score, best, level):
    pygame.draw.rect(surf, (40, 80, 170), (0, 0, W, TOP_BAR))
    pygame.draw.line(surf, (30, 60, 140), (0, TOP_BAR-2), (W, TOP_BAR-2), 2)

    surf.blit(F_BIG.render("SNAKE GAME", True, WHITE), (16, TOP_BAR//2 - 19))

    lv_col = (255, 220, 80) if level > 1 else (180, 210, 255)
    surf.blit(F_SM.render("LEVEL",  True, lv_col),         (W-280, 8))
    surf.blit(F_BIG.render(str(level), True, lv_col),       (W-280, 22))
    surf.blit(F_SM.render("SCORE",  True, (180, 210, 255)), (W-200, 8))
    surf.blit(F_BIG.render(str(score), True, WHITE),         (W-200, 22))
    surf.blit(F_SM.render("BEST",   True, (255, 230, 100)), (W-95, 8))
    surf.blit(F_BIG.render(str(best),  True, (255, 230, 100)), (W-95, 22))

def draw_gameover(surf, score, best):
    ov = pygame.Surface((W, H), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 150)); surf.blit(ov, (0,0))
    box = pygame.Rect((W-340)//2, (H-240)//2, 340, 240)
    rrect(surf, (30, 50, 140), box, radius=18)
    rrect(surf, (30, 50, 140), box, radius=18, bw=3, bc=(100, 150, 255))

    def _c(t, dy): surf.blit(t, (box.centerx - t.get_width()//2, box.top + dy))
    _c(F_BIG.render("GAME OVER", True, (255, 100, 100)), 45)
    _c(F_MED.render(f"SCORE: {score}", True, WHITE), 110)
    if score > 0 and score >= best:
        _c(F_MED.render("BEST SCORE!", True, (255, 230, 80)), 140)
    else:
        _c(F_MED.render(f"BEST: {best}", True, (255, 230, 80)), 140)
    _c(F_MED.render("SPACE / ENTER  TO RESTART", True, (200, 220, 255)), 175)

def draw_start(surf, tick):
    surf.fill((40, 80, 170))
    gs = pygame.Surface((W, H-TOP_BAR), pygame.SRCALPHA)
    for r in range(ROWS):
        for c in range(COLS):
            col = (80,130,220,60) if (r+c)%2==0 else (60,110,200,60)
            pygame.draw.rect(gs, col, (c*TILE, r*TILE, TILE, TILE))
    surf.blit(gs, (0, TOP_BAR))
    pulse = abs(math.sin(tick * 0.04))
    sc = (int(255*pulse+200*(1-pulse)), int(230*pulse+180*(1-pulse)), 80)

    def _c(t, y): surf.blit(t, (W//2 - t.get_width()//2, y))
    base = H//2 - 60
    _c(F_BIG.render("SNAKE GAME",                             True, WHITE),           base)
    _c(F_MED.render("Control the snake with the arrow keys.", True, (180,210,255)), base+50)
    _c(F_MED.render("SPACE / ENTER  TO START",                True, sc),             base+84)
    _c(F_SM.render("Every 50 points will speed up!",              True, (140,180,255)), base+120)


class SnakeGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("SNAKE GAME")
        self.clock  = pygame.time.Clock()
        self.best   = 0
        self.state  = "start"
        self.tick   = 0
        self.snake  = Snake()
        self._init_vars()

    def _init_vars(self):
        self.score      = 0
        self.move_timer = 0
        self.eat_anim   = 0
        self.particles: list[Particle] = []
        self.foods: list[Food]         = []
        self.snake.reset()
        self._spawn_food()

    def _spawn_food(self):
        pos = random_empty(self.snake.body_set | {f.pos for f in self.foods})
        if random.random() < 0.2:
            self.foods.append(GoldenApple(pos))
        else:
            self.foods.append(Apple(pos))

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                k = event.key
                if self.state == "start":
                    if k in (pygame.K_SPACE, pygame.K_RETURN):
                        self._init_vars(); self.state = "play"
                elif self.state == "play":
                    if   k in (pygame.K_UP,    pygame.K_w): self.snake.set_direction(UP)
                    elif k in (pygame.K_DOWN,  pygame.K_s): self.snake.set_direction(DOWN)
                    elif k in (pygame.K_LEFT,  pygame.K_a): self.snake.set_direction(LEFT)
                    elif k in (pygame.K_RIGHT, pygame.K_d): self.snake.set_direction(RIGHT)
                elif self.state == "over":
                    if k in (pygame.K_SPACE, pygame.K_RETURN):
                        self._init_vars(); self.state = "play"

    def update(self, dt):
        self.tick += 1
        if self.state != "play": return

        self.snake.update()
        for f in self.foods:   f.update()
        for p in self.particles: p.update()
        self.particles = [p for p in self.particles if p.alive]

        self.move_timer += dt
        if self.move_timer >= move_interval(self.score):
            self.move_timer -= move_interval(self.score)
            result = self.snake.step()

            if result in ('wall', 'body'):
                self.best = max(self.best, self.score)
                if SND_DIE: SND_DIE.play()
                self.state = "over"
                return

            head = self.snake.head
            for food in self.foods:
                if food.pos == head and food.alive:
                    food.on_eat(self)
                    self.snake.grow()
                    self.snake.trigger_eat_anim()
                    break

            self.foods = [f for f in self.foods if f.alive]
            if not self.foods:
                self._spawn_food()

    def draw(self):
        surf = self.screen
        if self.state == "start":
            draw_start(surf, self.tick)
        else:
            draw_grid(surf)
            for f in self.foods:     f.draw(surf)
            self.snake.draw(surf)
            for p in self.particles: p.draw(surf)
            level = self.score // 50 + 1
            draw_panel(surf, self.score, self.best, level)
            if self.state == "over":
                draw_gameover(surf, self.score, self.best)
        pygame.display.flip()

    def run(self):
        while True:
            dt = self.clock.tick(FPS)
            self.handle_input()
            self.update(dt)
            self.draw()


if __name__ == "__main__":
    SnakeGame().run()