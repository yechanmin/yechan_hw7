import pygame
import sys
import random
import math

pygame.init()

# ── Window ──────────────────────────────────────────────────────────────────
WIDTH, HEIGHT = 420, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("무한의 계단 🎮")
clock = pygame.time.Clock()
FPS = 60

# ── Colors ───────────────────────────────────────────────────────────────────
BG           = (10, 8, 28)
WHITE        = (255, 255, 255)
GRAY         = (145, 150, 168)
SCORE_C      = (95, 255, 148)
COIN_C       = (255, 215, 0)
WRONG_C      = (228, 55, 55)
BTN_TURN_ON  = (50, 100, 200)
BTN_TURN_OFF = (32, 38, 72)
BTN_CLIMB_ON = (45, 170, 70)
BTN_CLIMB_OFF= (30, 55, 38)
HP_GREEN     = (60, 208, 90)
HP_YELLOW    = (230, 192, 42)
HP_RED       = (215, 48, 48)
STAR_C       = (170, 182, 212)
STAIR = [
    ((82, 112, 200), (58, 84, 162), (36, 52, 105)),
    ((135, 165, 255),(105, 138, 238),(65, 90, 152)),
    ((108, 138, 228),(80, 108, 200),(50, 70, 130)),
]

# ── Geometry ─────────────────────────────────────────────────────────────────
SW   = 126
SH   = 20
SD   = 14
SXS  = 50
SYS  = 50
PLY  = int(HEIGHT * 0.62)

# ── Fonts ────────────────────────────────────────────────────────────────────
def _load_fonts():
    """
    한글 폰트 경로를 순서대로 시도합니다.
    모두 실패하면 pygame 내장 폰트(영문만 지원)로 대체합니다.
    한글이 깨진다면 아래 방법으로 폰트를 설치하세요:
      Ubuntu/Debian : sudo apt install fonts-nanum
      macOS         : brew install font-nanum (또는 .ttf 파일을 직접 지정)
      Windows       : C:/Windows/Fonts/malgunbd.ttf 경로 추가
    """
    candidates = [
        # Linux (Nanum)
        "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        # Linux (Noto CJK)
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        # macOS
        "/Library/Fonts/AppleGothic.ttf",
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        # Windows
        "C:/Windows/Fonts/malgunbd.ttf",
        "C:/Windows/Fonts/malgun.ttf",
        "C:/Windows/Fonts/gulim.ttc",
    ]
    # 스크립트와 같은 폴더에 NanumGothic.ttf 등을 직접 놓아도 동작합니다.
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    local_candidates = [
        os.path.join(script_dir, "NanumGothicBold.ttf"),
        os.path.join(script_dir, "NanumGothic.ttf"),
        os.path.join(script_dir, "malgunbd.ttf"),
    ]
    for path in local_candidates + candidates:
        try:
            fonts = [pygame.font.Font(path, s) for s in (52, 38, 26, 18)]
            print(f"[Font] Loaded: {path}")
            return fonts
        except Exception:
            pass
    # 한글 지원 폰트 없음 → pygame SysFont fallback (한글 깨질 수 있음)
    print("[Font] WARNING: 한글 폰트를 찾지 못했습니다. 'sudo apt install fonts-nanum' 으로 설치하세요.")
    return [pygame.font.SysFont("notosanscjk,applegothic,malgun gothic,gulim,arial", s)
            for s in (52, 38, 26, 18)]

F = _load_fonts()


# ── HP 회복량 (계단 1칸 오를 때마다) ─────────────────────────────────────────
HP_RECOVER = 3.5   # 조정 가능


# ── Particle ─────────────────────────────────────────────────────────────────
class Particle:
    def __init__(self, x, y, color):
        self.x, self.y   = float(x), float(y)
        self.vx          = random.uniform(-3.5, 3.5)
        self.vy          = random.uniform(-5.2, -0.6)
        self.life        = self.max_life = random.randint(22, 42)
        self.r           = random.randint(3, 6)
        self.color       = color

    def step(self):
        self.x  += self.vx
        self.y  += self.vy
        self.vy += 0.26
        self.life -= 1
        return self.life > 0

    def draw(self, surf):
        a = self.life / self.max_life
        c = tuple(int(ch * a) for ch in self.color)
        pygame.draw.circle(surf, c, (int(self.x), int(self.y)), self.r)


# ── Game ─────────────────────────────────────────────────────────────────────
class Game:
    def __init__(self):
        self.best  = 0
        self.state = 'menu'
        self.stars = [
            (random.randint(0, WIDTH), random.randint(0, HEIGHT), random.choice([1, 1, 2]))
            for _ in range(95)
        ]
        self.reset()

    def _add_stair(self):
        prev = self.st[-1]['d'] if self.st else 'R'
        if len(self.st) < 4:
            d = 'R'
        else:
            d = ('L' if prev == 'R' else 'R') if random.random() < 0.36 else prev
        coin = random.random() < 0.17 and len(self.st) > 4
        self.st.append({'d': d, 'coin': coin, 'got': False})

    def _refill(self):
        while len(self.st) < self.cur + 30:
            self._add_stair()

    def reset(self):
        self.score  = 0
        self.coins  = 0
        self.hp     = 100.0
        self.wflash = 0
        self.icd    = 0
        self.parts  = []
        self.st     = []
        for _ in range(40):
            self._add_stair()
        self.cur    = 4
        self.pd     = self.st[self.cur]['d']
        self.bounce = 0.0
        self.moving = False
        self.mv_t   = 0
        self.mv_dur = 9
        self.leg    = 0
        self.leg_t  = 0
        self.drain  = 4.0

    # ── HP 감소 속도 (높이 오를수록 훨씬 빠르게) ─────────────────────────────
    def _calc_drain(self):
        s = self.score
        if s < 20:   return 5.0
        if s < 50:   return 9.0
        if s < 100:  return 14.0
        if s < 200:  return 20.0
        if s < 350:  return 28.0
        return 38.0   # 350계단 이상 → 극한 압박

    def _need_turn(self):
        ni = self.cur + 1
        if ni >= len(self.st):
            return False
        return self.st[self.cur]['d'] != self.st[ni]['d']

    # ── 입력 처리 ─────────────────────────────────────────────────────────────
    def press(self, is_turn: bool):
        if self.state != 'playing' or self.moving or self.icd > 0:
            return
        correct = (is_turn == self._need_turn())
        if correct:
            ni = self.cur + 1
            self.cur    = ni
            self.score += 1
            self.pd     = self.st[self.cur]['d']
            self.moving = True
            self.mv_t   = 0

            # ── 계단 오를 때 HP 회복 ──────────────────────────────────────
            self.hp = min(100.0, self.hp + HP_RECOVER)

            s = self.st[self.cur]
            if s['coin'] and not s['got']:
                s['got'] = True
                self.coins += 1
                px, py = self._spos(self.cur)
                for _ in range(10):
                    self.parts.append(Particle(px, py - 30, COIN_C))
            self._refill()
            self.drain = self._calc_drain()
            self.icd   = 4
        else:
            # ── 틀리면 즉사 ───────────────────────────────────────────────
            self.hp    = 0.0
            self.wflash = 30
            self.icd   = 20
            px, py = self._spos(self.cur)
            for _ in range(14):
                self.parts.append(Particle(px, py - 20, WRONG_C))
            self._game_over()

    def _game_over(self):
        self.state = 'gameover'
        if self.score > self.best:
            self.best = self.score

    def update(self, dt):
        if self.state != 'playing':
            return
        self.hp -= self.drain * dt
        if self.hp <= 0:
            self.hp = 0
            self._game_over()
            return
        if self.icd    > 0: self.icd    -= 1
        if self.wflash > 0: self.wflash -= 1
        if self.moving:
            self.mv_t += 1
            t = self.mv_t / self.mv_dur
            self.bounce = -math.sin(t * math.pi) * 18
            if self.mv_t >= self.mv_dur:
                self.moving = False
                self.bounce = 0.0
        if self.moving:
            self.leg_t += 1
            if self.leg_t >= 5:
                self.leg_t = 0
                self.leg   = (self.leg + 1) % 4
        self.parts = [p for p in self.parts if p.step()]

    def _spos(self, idx):
        cx = WIDTH // 2
        x  = cx
        if idx > self.cur:
            for i in range(self.cur + 1, idx + 1):
                x += SXS if self.st[i]['d'] == 'R' else -SXS
        elif idx < self.cur:
            for i in range(self.cur, idx, -1):
                x -= SXS if self.st[i]['d'] == 'R' else -SXS
        y = PLY - (idx - self.cur) * SYS
        return x, y

    def _draw_stair(self, surf, x, y, tier):
        tc, fc, sc = STAIR[tier]
        hw = SW // 2
        pygame.draw.rect(surf, fc, (x - hw, y, SW, SH))
        pts_top  = [(x-hw, y), (x+hw, y),
                    (x+hw-SD//2, y-SD), (x-hw-SD//2, y-SD)]
        pygame.draw.polygon(surf, tc, pts_top)
        pts_side = [(x-hw, y), (x-hw, y+SH),
                    (x-hw-SD//2, y+SH-SD), (x-hw-SD//2, y-SD)]
        pygame.draw.polygon(surf, sc, pts_side)
        pygame.draw.line(surf, (190, 215, 255),
                         (x-hw-SD//2, y-SD), (x+hw-SD//2, y-SD), 1)
        pygame.draw.line(surf, (160, 192, 255), (x-hw, y), (x+hw, y), 1)

    def _draw_coin(self, surf, x, y):
        bob = int(math.sin(pygame.time.get_ticks() * 0.004 + x * 0.01) * 3)
        cy  = y + bob
        pygame.draw.circle(surf, COIN_C,           (x, cy), 9)
        pygame.draw.circle(surf, (255, 238, 88),   (x, cy), 7)
        pygame.draw.circle(surf, (255, 255, 195),  (x - 2, cy - 2), 3)

    def _draw_dir_arrow(self, surf, x, y, direction):
        ax = x + (22 if direction == 'R' else -22)
        ay = y - SD - 18
        t  = pygame.time.get_ticks()
        pulse = int(math.sin(t * 0.006) * 2)
        if direction == 'R':
            pts = [(ax+pulse, ay+6), (ax-10+pulse, ay), (ax-10+pulse, ay+12)]
        else:
            pts = [(ax-pulse, ay+6), (ax+10-pulse, ay), (ax+10-pulse, ay+12)]
        pygame.draw.polygon(surf, (255, 255, 100), pts)

    def _draw_player(self, surf, x, y):
        bx = x
        by = int(y + self.bounce)
        dx = 1 if self.pd == 'R' else -1
        ls = 0
        if self.moving:
            t  = self.mv_t / self.mv_dur
            ls = int(math.sin(t * math.pi * 2) * 6)
        pygame.draw.ellipse(surf, (7, 7, 24), (bx - 14, by + 18, 28, 7))
        LC = (52, 52, 112)
        pygame.draw.line(surf, LC, (bx - 4, by + 2), (bx - 4 + ls * dx, by + 16), 4)
        pygame.draw.line(surf, LC, (bx + 4, by + 2), (bx + 4 - ls * dx, by + 16), 4)
        SC = (22, 22, 42)
        pygame.draw.ellipse(surf, SC, (bx - 4 + ls * dx - 6, by + 13, 11, 5))
        pygame.draw.ellipse(surf, SC, (bx + 4 - ls * dx - 5, by + 13, 11, 5))
        BC = (50, 80, 180)
        pygame.draw.rect(surf, BC, (bx - 10, by - 18, 20, 20))
        pygame.draw.polygon(surf, (188, 42, 42),
                             [(bx-2, by-17), (bx+2, by-17),
                              (bx+1, by-5),  (bx, by-3), (bx-1, by-5)])
        asw = int(ls * 0.4)
        pygame.draw.line(surf, BC, (bx - 10, by - 14), (bx - 16 - asw * dx, by - 5), 4)
        pygame.draw.line(surf, BC, (bx + 10, by - 14), (bx + 16 + asw * dx, by - 5), 4)
        HC = (232, 188, 132)
        pygame.draw.circle(surf, HC, (bx - 16 - asw * dx, by - 4), 4)
        pygame.draw.circle(surf, HC, (bx + 16 + asw * dx, by - 4), 4)
        pygame.draw.circle(surf, HC, (bx, by - 28), 12)
        ex = bx + 5 * dx
        pygame.draw.circle(surf, (32, 20, 16), (ex, by - 28), 2)
        if not self.wflash:
            pygame.draw.arc(surf, (128, 72, 52),
                            (ex - 4, by - 26, 8, 5), math.pi, 2 * math.pi, 1)
        else:
            pygame.draw.arc(surf, (128, 72, 52),
                            (ex - 4, by - 23, 8, 5), 0, math.pi, 1)
        pygame.draw.rect(surf, (52, 36, 16), (bx - 11, by - 40, 22, 10))
        pygame.draw.rect(surf, (72, 50, 20), (bx - 13, by - 32, 26, 4))

    def _draw_hp(self, surf):
        bw, bh = 272, 19
        bx = (WIDTH - bw) // 2
        by = 18
        pygame.draw.rect(surf, (46, 12, 12), (bx-2, by-2, bw+4, bh+4), border_radius=5)
        pygame.draw.rect(surf, (65, 16, 16), (bx, by, bw, bh), border_radius=4)
        ratio = self.hp / 100.0
        fw    = int(bw * ratio)
        hc    = HP_GREEN if ratio > 0.6 else (HP_YELLOW if ratio > 0.3 else HP_RED)
        if fw > 0:
            pygame.draw.rect(surf, hc, (bx, by, fw, bh), border_radius=4)
        border_col = HP_RED if (self.hp < 30 and int(pygame.time.get_ticks() / 380) % 2) \
                     else (192, 212, 255)
        pygame.draw.rect(surf, border_col, (bx-2, by-2, bw+4, bh+4), 2, border_radius=5)
        t = F[3].render("HP", True, WHITE)
        surf.blit(t, (bx - 26, by + 1))

    def _draw_score(self, surf):
        t = F[1].render(str(self.score), True, SCORE_C)
        surf.blit(t, (WIDTH // 2 - t.get_width() // 2, 42))
        u = F[3].render("계단", True, GRAY)
        surf.blit(u, (WIDTH // 2 + t.get_width() // 2 + 4, 53))
        pygame.draw.circle(surf, COIN_C,           (15, 52), 9)
        pygame.draw.circle(surf, (255, 238, 88),   (15, 52), 7)
        pygame.draw.circle(surf, (255, 255, 195),  (13, 50), 3)
        ct = F[3].render(str(self.coins), True, COIN_C)
        surf.blit(ct, (27, 46))

    def _draw_buttons(self, surf):
        bw, bh = 150, 78
        by_    = HEIGHT - 102
        need   = self._need_turn()
        for is_turn in (True, False):
            rx = 8 if is_turn else WIDTH - 8 - bw
            on = (is_turn == need)
            bg = BTN_TURN_ON if (is_turn and on) else \
                 BTN_CLIMB_ON if (not is_turn and on) else \
                 BTN_TURN_OFF if is_turn else BTN_CLIMB_OFF
            bd = (165, 200, 255) if is_turn else (165, 255, 195)
            pygame.draw.rect(surf, bg, (rx, by_, bw, bh), border_radius=13)
            pygame.draw.rect(surf, bd, (rx, by_, bw, bh), 2, border_radius=13)
            cx_ = rx + bw // 2
            if is_turn:
                pygame.draw.polygon(surf, WHITE,
                    [(rx+38, by_+26), (rx+20, by_+39), (rx+38, by_+52)])
            else:
                pygame.draw.polygon(surf, WHITE,
                    [(cx_, by_+20), (cx_-12, by_+44), (cx_+12, by_+44)])
            key = F[3].render("[←]" if is_turn else "[→]", True,
                              (195, 215, 255) if is_turn else (195, 255, 205))
            lbl = F[2].render("방향전환" if is_turn else "올라가기", True, WHITE)
            surf.blit(key, (rx + bw//2 - key.get_width()//2, by_ + 5))
            surf.blit(lbl, (rx + bw//2 - lbl.get_width()//2, by_ + bh - 24))

    def _draw_game(self, surf):
        vis = [i for i in range(self.cur - 3, self.cur + 8)
               if 0 <= i < len(self.st)]
        for idx in sorted(vis, reverse=True):
            x, y = self._spos(idx)
            if y < -70 or y > HEIGHT + 70:
                continue
            tier = 1 if idx == self.cur else (2 if idx == self.cur + 1 else 0)
            self._draw_stair(surf, int(x), int(y), tier)
            st = self.st[idx]
            if st['coin'] and not st['got']:
                self._draw_coin(surf, int(x), int(y - SD - 8))
            if idx == self.cur + 1:
                self._draw_dir_arrow(surf, int(x), int(y), st['d'])
        px, py = self._spos(self.cur)
        self._draw_player(surf, int(px), int(py - SD + 2))
        for p in self.parts:
            p.draw(surf)
        if self.wflash > 0:
            ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            ov.fill((255, 0, 0, int(self.wflash / 30 * 88)))
            surf.blit(ov, (0, 0))

    def _draw_menu(self, surf):
        surf.fill(BG)
        for sx, sy, ss in self.stars:
            pygame.draw.circle(surf, STAR_C, (sx, sy), ss)
        t1 = F[0].render("무한의 계단", True, WHITE)
        surf.blit(t1, (WIDTH // 2 - t1.get_width() // 2, 120))
        t2 = F[2].render("Infinite Stairs", True, GRAY)
        surf.blit(t2, (WIDTH // 2 - t2.get_width() // 2, 178))
        pygame.draw.line(surf, (50, 55, 90), (40, 212), (WIDTH - 40, 212), 1)
        rules = [
            ("← 방향전환",              BTN_TURN_ON),
            ("다음 계단이 다른 방향일 때", GRAY),
            ("→ 올라가기",              BTN_CLIMB_ON),
            ("다음 계단이 같은 방향일 때", GRAY),
            ("",                        None),
            ("틀리면 즉사!",             WRONG_C),
            ("올라갈수록 HP 급격히 감소", GRAY),
            ("계단 1칸 = HP +{:.1f} 회복".format(HP_RECOVER), HP_GREEN),
            ("",                        None),
            ("SPACE / ENTER 시작",      (165, 192, 255)),
        ]
        y = 228
        for text, col in rules:
            if col is None:
                y += 14
                continue
            t = F[2].render(text, True, col)
            surf.blit(t, (WIDTH // 2 - t.get_width() // 2, y))
            y += 34
        if self.best > 0:
            b = F[1].render(f"최고 기록: {self.best}계단", True, COIN_C)
            surf.blit(b, (WIDTH // 2 - b.get_width() // 2, y + 6))

    def _draw_over(self, surf):
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 168))
        surf.blit(ov, (0, 0))
        go = F[0].render("GAME OVER", True, WRONG_C)
        surf.blit(go, (WIDTH // 2 - go.get_width() // 2, 198))
        sc = F[1].render(f"{self.score}계단", True, WHITE)
        surf.blit(sc, (WIDTH // 2 - sc.get_width() // 2, 265))
        if self.score > 0 and self.score == self.best:
            nr = F[1].render("★  신기록!  ★", True, COIN_C)
            surf.blit(nr, (WIDTH // 2 - nr.get_width() // 2, 312))
        ci = F[2].render(f"획득 코인: {self.coins}", True, COIN_C)
        surf.blit(ci, (WIDTH // 2 - ci.get_width() // 2, 360))
        dr = self._calc_drain()
        hint_text = "초당 HP 감소: {:.0f}  →  {}".format(
            dr,
            "극한 압박!" if dr >= 28 else ("엄청 빠름!" if dr >= 14 else ("빠름!" if dr >= 9 else "느림"))
        )
        ht = F[3].render(hint_text, True, GRAY)
        surf.blit(ht, (WIDTH // 2 - ht.get_width() // 2, 400))
        rs = F[2].render("다시 시작: SPACE / R", True, (158, 178, 255))
        surf.blit(rs, (WIDTH // 2 - rs.get_width() // 2, 435))
        mn = F[2].render("메뉴: ESC", True, GRAY)
        surf.blit(mn, (WIDTH // 2 - mn.get_width() // 2, 474))

    def draw(self, surf):
        if self.state == 'menu':
            self._draw_menu(surf)
            return
        surf.fill(BG)
        for sx, sy, ss in self.stars:
            pygame.draw.circle(surf, STAR_C, (sx, sy), ss)
        self._draw_game(surf)
        self._draw_hp(surf)
        self._draw_score(surf)
        self._draw_buttons(surf)
        if self.state == 'gameover':
            self._draw_over(surf)

    def handle(self, event):
        if event.type != pygame.KEYDOWN:
            return
        k = event.key
        if self.state == 'menu':
            if k in (pygame.K_SPACE, pygame.K_RETURN):
                self.state = 'playing'
            elif k == pygame.K_LEFT:
                self.state = 'playing'
                self.press(True)
            elif k == pygame.K_RIGHT:
                self.state = 'playing'
                self.press(False)
        elif self.state == 'playing':
            if k == pygame.K_LEFT:
                self.press(True)
            elif k == pygame.K_RIGHT:
                self.press(False)
            elif k == pygame.K_ESCAPE:
                self.state = 'menu'
        elif self.state == 'gameover':
            if k in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_r):
                self.reset()
                self.state = 'playing'
            elif k == pygame.K_ESCAPE:
                self.state = 'menu'

    def run(self):
        while True:
            dt = clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                self.handle(event)
            self.update(dt)
            self.draw(screen)
            pygame.display.flip()


if __name__ == '__main__':
    Game().run()