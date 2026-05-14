import sys, math, random
import numpy as np
import pygame

from env       import ParkingEnv
from dqn_agent import DQNAgent
from settings  import *


class ParkingApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("🚗 DQN 주차 시뮬레이터 (Ackermann)")
        self.clock  = pygame.time.Clock()

        self.fb = pygame.font.SysFont("malgungothic", 18, bold=True)
        self.fs = pygame.font.SysFont("malgungothic", 13)
        self.fq = pygame.font.SysFont("malgungothic", 11)

        self.env   = ParkingEnv()
        self.agent = DQNAgent()

        self.training  = False
        self.auto_play = False

        self.episode   = 0
        self.parked    = 0
        self.wall_cr   = 0
        self.npc_cr    = 0
        self.timeouts  = 0
        self.recent: list[int] = []

        self.demo_done   = False
        self.last_result = "READY"
        self.last_action = 6
        self.step_count  = 0
        self.last_step_t = 0
        self.state       = self.env.reset()

    def _train_episode(self):
        state = self.env.reset()
        done  = False
        info  = {"result": "running"}
        while not done:
            action = self.agent.select_action(state)
            ns, r, done, info = self.env.step(action)
            self.agent.push(state, action, r, ns, done)
            self.agent.learn()
            state = ns
        self.agent.decay_epsilon()
        self.episode += 1
        res = info["result"]
        win = 0
        if res == "parked":         self.parked  += 1; win = 1
        elif res == "wall_crash":   self.wall_cr += 1
        elif res == "npc_collision":self.npc_cr  += 1
        else:                       self.timeouts += 1
        self.recent.append(win)
        if len(self.recent) > 200:
            self.recent.pop(0)

    def reset_all(self):
        self.agent = DQNAgent()
        self.training = self.auto_play = False
        self.episode = self.parked = self.wall_cr = self.npc_cr = self.timeouts = 0
        self.recent  = []
        self.start_new_demo()

    def start_new_demo(self):
        self.state       = self.env.reset()
        self.demo_done   = False
        self.last_result = "RUNNING"
        self.last_action = 6
        self.step_count  = 0

    def run_demo_step(self):
        if self.demo_done:
            return
        eps_demo = max(0.05, self.agent.epsilon * 0.5)
        if random.random() < eps_demo:
            action = random.randrange(N_ACTIONS)
        else:
            action = self.agent.best_action(self.state)

        self.last_action = action
        ns, r, done, info = self.env.step(action)
        self.agent.push(self.state, action, r, ns, done)
        self.agent.learn()
        self.state       = ns
        self.demo_done   = done
        self.last_result = info["result"].upper()
        self.step_count += 1

    def _draw_q_overlay(self):
        q = self.agent.get_q_values(self.state)
        cx = int(self.env.car.x)
        cy = int(self.env.car.y)
        offsets = {
            0: ( 0,-28), 1: ( 0, 28),
            2: (-32,-18), 3: (32,-18),
            4: (-32, 18), 5: (32, 18),
            6: ( 0,   0),
        }
        max_q = float(np.max(q))
        for a, (ox, oy) in offsets.items():
            v = float(q[a])
            c = (0,160,70) if v > 0 else (200,40,40) if v < 0 else (130,130,130)
            if abs(v - max_q) < 1e-6 and len(set(q.tolist())) > 1:
                pygame.draw.circle(self.screen, (0,210,110), (cx+ox, cy+oy), 12, 2)
            lbl = self.fq.render(f"{v:.1f}", True, c)
            self.screen.blit(lbl, (cx+ox-12, cy+oy-7))

    def _bar(self, surf, x, y, w, h, ratio, fg, bg=(205,205,205)):
        pygame.draw.rect(surf, bg,  (x, y, w, h), border_radius=3)
        fw = max(0, int(w * min(ratio, 1.0)))
        if fw:
            pygame.draw.rect(surf, fg, (x, y, fw, h), border_radius=3)
        pygame.draw.rect(surf, (160,160,160), (x, y, w, h), 1, border_radius=3)

    def _txt(self, surf, text, x, y, font=None, color=(30,30,30)):
        if font is None: font = self.fs
        surf.blit(font.render(text, True, color), (x, y))

    def draw_panel(self):
        PAD  = 10
        COL  = WIDTH // 3
        H    = INFO_H
        ROW  = 17

        panel = pygame.Surface((WIDTH, H))
        panel.fill(PANEL_BG)
        pygame.draw.line(panel, (145,148,165), (0,0), (WIDTH,0), 2)

        total   = max(self.parked + self.wall_cr + self.npc_cr + self.timeouts, 1)
        park_r  = self.parked / total
        rec_r   = sum(self.recent) / max(len(self.recent), 1)

        x0 = PAD
        self._txt(panel, "📊 학습 통계", x0, 5,  self.fb, (45,48,80))
        self._txt(panel, f"에피소드: {self.episode:,}",     x0, 27)
        self._txt(panel, f"주차 성공: {self.parked:,}",     x0, 27+ROW,   color=(35,145,75))
        self._txt(panel, f"벽 충돌:  {self.wall_cr:,}",     x0, 27+ROW*2, color=(190,60,40))
        self._txt(panel, f"NPC 충돌: {self.npc_cr:,}",      x0, 27+ROW*3, color=(210,50,50))
        self._txt(panel, f"시간초과: {self.timeouts:,}",    x0, 27+ROW*4, color=(160,120,35))

        self._txt(panel, f"전체 성공률 {park_r*100:.1f}%",  x0, 27+ROW*5+4)
        self._bar(panel, x0, 27+ROW*6, COL-PAD*2, 9, park_r,
                  (65,185,105) if park_r > 0.3 else (200,95,65))
        self._txt(panel, f"최근200판 {rec_r*100:.1f}%",     x0, 27+ROW*7+4)
        self._bar(panel, x0, 27+ROW*8, COL-PAD*2, 9, rec_r,
                  (65,185,105) if rec_r > 0.3 else (200,95,65))

        x1 = COL + PAD
        pygame.draw.line(panel, (185,188,202), (COL,5), (COL,H-5), 1)
        self._txt(panel, "🎮 데모 상태", x1, 5, self.fb, (45,48,80))

        RC = {
            "PARKED":        (35,175,85),
            "WALL_CRASH":    (210,55,40),
            "NPC_COLLISION": (220,30,30),
            "TIMEOUT":       (185,135,25),
            "RUNNING":       (55,115,210),
            "READY":         (115,115,115),
        }
        self._txt(panel, self.last_result, x1, 27, self.fb, RC.get(self.last_result, BLACK))

        self._txt(panel, f"스텝: {self.step_count} / {MAX_STEPS}", x1, 50)
        sc = (195,75,65) if self.step_count/MAX_STEPS > 0.7 else (65,115,210)
        self._bar(panel, x1, 65, COL-PAD*2, 9, self.step_count/MAX_STEPS, sc)

        self._txt(panel, f"액션: {ACTION_NAMES[self.last_action]}", x1, 79)

        car = self.env.car
        tx, ty, ta = self.env.target
        dist = math.hypot(car.x - tx, car.y - ty)
        da   = abs(math.degrees(_norm_angle(car.angle - ta)))
        self._txt(panel, f"목표까지: {dist:.0f}px  각도차: {da:.1f}°", x1, 96, color=(75,75,75))
        self._txt(panel, f"속도: {car.speed:.1f}  조향: {math.degrees(car.steer):.1f}°", x1, 112, color=(75,75,75))

        min_npc = min(math.hypot(car.x-n.x, car.y-n.y) for n in self.env.npcs)
        nc = (210,55,55) if min_npc < 60 else (75,155,95)
        self._txt(panel, f"NPC 최근거리: {min_npc:.0f}px", x1, 128, color=nc)
        self._txt(panel, f"버퍼: {self.agent.buf_size:,} / {self.agent.buffer.buf.maxlen:,}", x1, 144, color=(75,75,75))
        self._txt(panel, f"avg Loss: {self.agent.avg_loss:.4f}", x1, 160, color=(75,75,75))

        x2 = COL*2 + PAD
        pygame.draw.line(panel, (185,188,202), (COL*2,5), (COL*2,H-5), 1)
        self._txt(panel, "🤖 DQN 에이전트", x2, 5, self.fb, (45,48,80))

        eps   = self.agent.epsilon
        eps_r = (eps - self.agent.epsilon_min) / max(1.0 - self.agent.epsilon_min, 1e-9)
        self._txt(panel, f"ε 탐험률: {eps:.4f}", x2, 27)
        self._bar(panel, x2, 42, COL-PAD*2, 9, eps_r, (210,145,45), bg=(65,175,105))
        self._txt(panel, "← 학습완료     탐험중 →", x2, 54, color=(125,125,125))

        self._txt(panel, f"Ackermann 물리 | WB={WHEEL_BASE}px", x2, 71, color=(75,75,75))
        self._txt(panel, f"상태 {STATE_DIM}차원 | 행동 {N_ACTIONS}개",   x2, 87, color=(75,75,75))
        self._txt(panel, f"NPC {NUM_NPC}대 (연속 이동)",              x2, 103, color=(175,55,55))
        self._txt(panel, f"Net: {STATE_DIM}→{HIDDEN1}→{HIDDEN2}→{N_ACTIONS}", x2, 119, color=(75,75,75))
        self._txt(panel, f"γ={GAMMA}  α={LR}  batch={BATCH_SIZE}",  x2, 135, color=(75,75,75))

        if self.training:
            pygame.draw.rect(panel, (255,238,195), (x2, 152, COL-PAD*2, 21), border_radius=4)
            self._txt(panel, "⚡ 학습 중...", x2+4, 155, color=(175,95,0))
        if self.auto_play:
            yy = 175 if self.training else 152
            pygame.draw.rect(panel, (215,238,255), (x2, yy, COL-PAD*2, 21), border_radius=4)
            self._txt(panel, "▶ 자동 플레이", x2+4, yy+3, color=(0,85,175))

        KEY_Y = H - 32
        pygame.draw.line(panel, (165,168,182), (0,KEY_Y-4), (WIDTH,KEY_Y-4), 1)
        keys = [("[T] 학습", self.training), ("[A] 자동", self.auto_play),
                ("[N] 한스텝", False), ("[D] 데모리셋", False), ("[R] 전체리셋", False)]
        btn_w = (WIDTH - PAD*2) // len(keys)
        for i, (label, active) in enumerate(keys):
            bx = PAD + i*btn_w
            bg = (175,228,190) if active else (212,212,220)
            fc = (28,125,65)   if active else (58,58,68)
            pygame.draw.rect(panel, bg,  (bx, KEY_Y, btn_w-4, 25), border_radius=5)
            pygame.draw.rect(panel, (155,158,172), (bx, KEY_Y, btn_w-4, 25), 1, border_radius=5)
            ts = self.fs.render(label, True, fc)
            tw, th = ts.get_size()
            panel.blit(ts, (bx+(btn_w-4-tw)//2, KEY_Y+(25-th)//2))

        self.screen.blit(panel, (0, int(WORLD_H)))

    def draw(self):
        self.env.render(self.screen)
        self._draw_q_overlay()
        self.draw_panel()
        pygame.display.flip()

    def run(self):
        while True:
            now = pygame.time.get_ticks()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if   event.key == pygame.K_t: self.training  = not self.training
                    elif event.key == pygame.K_a: self.auto_play = not self.auto_play
                    elif event.key == pygame.K_n:
                        if not self.training: self.run_demo_step()
                    elif event.key == pygame.K_d: self.start_new_demo()
                    elif event.key == pygame.K_r: self.reset_all()

            if self.training:
                for _ in range(TRAIN_EPISODES_PER_FRAME):
                    self._train_episode()
                if now - self.last_step_t > STEP_MS:
                    if self.demo_done: self.start_new_demo()
                    else:              self.run_demo_step()
                    self.last_step_t = now
            elif self.auto_play:
                if now - self.last_step_t > STEP_MS:
                    if self.demo_done: self.start_new_demo()
                    else:              self.run_demo_step()
                    self.last_step_t = now

            self.draw()
            self.clock.tick(FPS)


def _norm_angle(a):
    import math
    while a >  math.pi: a -= 2*math.pi
    while a < -math.pi: a += 2*math.pi
    return a


if __name__ == "__main__":
    ParkingApp().run()