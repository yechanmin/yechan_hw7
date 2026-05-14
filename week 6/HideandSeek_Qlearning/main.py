# main.py
import sys
import random
import pygame

from env import HideAndSeekEnv
from rl_agent import QLearningAgent
from settings import *

class GameApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("RL Hide and Seek")
        self.clock = pygame.time.Clock()

        self.font_b  = pygame.font.SysFont("malgungothic", 18, bold=True)
        self.font_m  = pygame.font.SysFont("malgungothic", 16)
        self.font_s  = pygame.font.SysFont("malgungothic", 13)
        self.font_q  = pygame.font.SysFont("malgungothic", 12)
        #환경 생성
        self.env   = HideAndSeekEnv()
        #agent 생성
        self.agent = QLearningAgent()

        self.training  = False
        self.auto_play = False

        self.episode  = 0
        self.wins     = 0
        self.losses   = 0
        self.timeouts = 0
        self.recent_results: list[int] = []   # 최근 200판

        self.demo_done    = False
        self.last_result  = "READY"
        self.last_action  = 4
        self.step_count   = 0
        self.step_delay   = 350
        self.last_step_t  = 0

        # 초기 학습
        for _ in range(PRETRAIN_EPISODES):
            self._train_one()
        self.start_new_demo()

    #episode 한번 학습
    def _train_one(self):
        state = self.env.reset()
        done  = False
        info  = {"result": "unknown"}
        while not done:
            action = self.agent.select_action(state) #다음 행동 고르기
            ns, reward, done, info = self.env.step(action) #환경이 상태와 보상 반환
            self.agent.learn(state, action, reward, ns, done) #agent가 학습하여 Q-table 갱신
            state = ns
        self.agent.decay_epsilon() #episode 끝나면 epsilon 감소시킴.
        self.episode += 1
        r = info["result"]
        if r == "escaped":
            self.wins += 1
            self.recent_results.append(1)
        elif r == "caught":
            self.losses += 1
            self.recent_results.append(0)
        else:
            self.timeouts += 1
            self.recent_results.append(0)
        if len(self.recent_results) > 200:
            self.recent_results.pop(0)
    #전체 학습 상태를 처음부터 다시 시작함. 초기화
    def reset_all(self):
        self.agent          = QLearningAgent()
        self.training       = self.auto_play = False
        self.episode        = self.wins = self.losses = self.timeouts = 0
        self.recent_results = []
        for _ in range(PRETRAIN_EPISODES):
            self._train_one()
        self.start_new_demo()
    #데모 한판을 새로 시작함.
    def start_new_demo(self):
        self.env.reset()
        self.demo_done   = False
        self.last_result = "RUNNING"
        self.last_action = 4
        self.step_count  = 0
    #데모에서 사용할 행동 결정. 10%확률로 일부러 무작위 탐험. 나머지는 best_action 으로 최선 행동 선택. 데모로 보여줄 행동 결정.
    def _demo_action(self, state):
        q = self.agent.get_q_values(state)
        if all(v == 0 for v in q):
            return random.randint(0, 3)
        if random.random() < 0.10:
            return random.randint(0, 3)
        return self.agent.best_action(state)
    #데모 한 step 결정.
    def run_demo_step(self):
        if self.demo_done:
            return
        state             = self.env.get_state()
        self.last_action  = self._demo_action(state)
        _, _, done, info  = self.env.step(self.last_action)
        self.demo_done    = done
        self.last_result  = info["result"].upper()
        self.step_count  += 1

    def _draw_action_arrow(self):
        if self.demo_done:
            return
        dx, dy = ACTIONS[self.last_action]
        hx, hy = self.env.hider.pos
        cx = hx * CELL_SIZE + CELL_SIZE // 2
        cy = hy * CELL_SIZE + CELL_SIZE // 2
        end = (cx + dx * 20, cy + dy * 20)
        if dx or dy:
            pygame.draw.line(self.screen, BLACK, (cx, cy), end, 3)
            pygame.draw.circle(self.screen, BLACK, end, 4)
    # 현재 위치에서 각 행동의 Q값 표기
    def _draw_q_overlay(self):
        state = self.env.get_state()
        q     = self.agent.get_q_values(state)
        hx, hy = self.env.hider.pos
        cx = hx * CELL_SIZE + CELL_SIZE // 2
        cy = hy * CELL_SIZE + CELL_SIZE // 2
        offsets = {0:(0,-22), 1:(0,22), 2:(-26,0), 3:(26,0), 4:(0,0)}
        max_q   = max(q)
        for a, (ox, oy) in offsets.items():
            v = q[a]
            color = (0, 150, 70) if v > 0 else (190, 30, 30) if v < 0 else (120,120,120)
            # 최선 액션 강조
            if abs(v - max_q) < 1e-9 and v != 0:
                pygame.draw.circle(self.screen, (0,200,100),
                                   (cx+ox, cy+oy), 11, 2)
            txt = self.font_q.render(f"{v:.1f}", True, color)
            self.screen.blit(txt, (cx + ox - 10, cy + oy - 7))

    def _bar(self, surf, x, y, w, h, ratio, fg, bg=(205,205,205)):
        pygame.draw.rect(surf, bg,  (x, y, w, h), border_radius=3)
        fw = max(0, int(w * min(ratio, 1.0)))
        if fw:
            pygame.draw.rect(surf, fg, (x, y, fw, h), border_radius=3)
        pygame.draw.rect(surf, (160,160,160), (x,y,w,h), 1, border_radius=3)

    def _txt(self, surf, text, x, y, font, color=(30,30,30)):
        surf.blit(font.render(text, True, color), (x, y))

    def draw_info_panel(self):
        PY   = BOARD_WIDTH
        PAD  = 10
        COL  = WIDTH // 3   # 각 열 너비 = 200px
        H    = INFO_HEIGHT

        panel = pygame.Surface((WIDTH, H))
        panel.fill(PANEL_BG)
        pygame.draw.line(panel, (150,150,160), (0,0), (WIDTH,0), 2)

        total   = max(self.wins + self.losses + self.timeouts, 1)
        win_r   = self.wins / total
        recent_r = sum(self.recent_results) / max(len(self.recent_results), 1)

        # ══ 열 0: 학습 통계 (x=0) ══
        x0 = PAD
        ROW = 18   # 행 간격

        self._txt(panel, "📊 학습 통계", x0, 6,  self.font_b, (50,50,80))
        self._txt(panel, f"에피소드: {self.episode:,}", x0, 28, self.font_s)
        self._txt(panel, f"탈출(승): {self.wins:,}",   x0, 28+ROW, self.font_s, (40,150,80))
        self._txt(panel, f"잡힘(패): {self.losses:,}", x0, 28+ROW*2, self.font_s, (190,60,60))
        self._txt(panel, f"시간초과: {self.timeouts:,}",x0, 28+ROW*3, self.font_s, (160,120,40))

        # 전체 승률 바
        self._txt(panel, f"전체 승률 {win_r*100:.1f}%", x0, 28+ROW*4+4, self.font_s)
        self._bar(panel, x0, 28+ROW*5+2, COL-PAD*2, 10, win_r,
                  (70,190,110) if win_r > 0.5 else (200,100,70))

        # 최근 200판 승률
        self._txt(panel, f"최근200판 {recent_r*100:.1f}%", x0, 28+ROW*6+6, self.font_s)
        self._bar(panel, x0, 28+ROW*7+4, COL-PAD*2, 10, recent_r,
                  (70,190,110) if recent_r > 0.5 else (200,100,70))

        # ══ 열 1: 데모 상태 (x=COL) ══
        x1 = COL + PAD
        pygame.draw.line(panel, (190,190,200), (COL, 6), (COL, H-6), 1)

        self._txt(panel, "🎮 데모 상태", x1, 6, self.font_b, (50,50,80))

        RESULT_COLOR = {
            "ESCAPED": (40,180,90), "CAUGHT": (210,60,60),
            "TIMEOUT": (190,140,30), "RUNNING": (60,120,210), "READY": (120,120,120),
        }
        rc = RESULT_COLOR.get(self.last_result, BLACK)
        self._txt(panel, self.last_result, x1, 28, self.font_b, rc)

        self._txt(panel, f"스텝: {self.step_count} / {MAX_STEPS}", x1, 52, self.font_s)
        step_c = (200,80,70) if self.step_count/MAX_STEPS > 0.7 else (70,120,210)
        self._bar(panel, x1, 68, COL-PAD*2, 10, self.step_count/MAX_STEPS, step_c)

        self._txt(panel, f"액션: {ACTION_NAMES[self.last_action]}", x1, 84, self.font_s)

        # 상태 벡터 표시
        state = self.env.get_state()
        gdx,gdy,sdx,sdy,fov,dg,ds = state
        self._txt(panel, f"goal Δ({gdx:+d},{gdy:+d}) dist={dg}", x1, 104, self.font_s, (80,80,80))
        self._txt(panel, f"seek Δ({sdx:+d},{sdy:+d}) dist={ds}", x1, 120, self.font_s, (80,80,80))
        fov_c = (210,60,60) if fov else (80,160,100)
        self._txt(panel, f"시야 노출: {'⚠ 위험!' if fov else '✓ 안전'}", x1, 136, self.font_s, fov_c)

        # ══ 열 2: 에이전트 (x=COL*2) ══
        x2 = COL*2 + PAD
        pygame.draw.line(panel, (190,190,200), (COL*2, 6), (COL*2, H-6), 1)

        self._txt(panel, "🤖 에이전트", x2, 6, self.font_b, (50,50,80))

        eps = self.agent.epsilon
        eps_r = (eps - self.agent.epsilon_min) / (1.0 - self.agent.epsilon_min)
        self._txt(panel, f"ε 탐험률: {eps:.4f}", x2, 28, self.font_s)
        self._bar(panel, x2, 44, COL-PAD*2, 10, eps_r, (210,150,50), bg=(70,180,110))
        self._txt(panel, "← 학습완료   탐험중 →", x2, 57, self.font_s, (130,130,130))

        q_size = len(self.agent.q_table)
        self._txt(panel, f"Q-table: {q_size:,} 상태",  x2, 74,  self.font_s)
        self._txt(panel, f"α={self.agent.alpha}  γ={self.agent.gamma}", x2, 90, self.font_s)

        # 학습 중 표시
        if self.training:
            pygame.draw.rect(panel, (255,240,200), (x2, 108, COL-PAD*2, 22), border_radius=4)
            self._txt(panel, "⚡ 학습 중...", x2+4, 112, self.font_s, (180,100,0))
        if self.auto_play:
            pygame.draw.rect(panel, (220,240,255), (x2, 108 if not self.training else 132,
                                                     COL-PAD*2, 22), border_radius=4)
            self._txt(panel, "▶ 자동 플레이", x2+4,
                      112 if not self.training else 136, self.font_s, (0,90,180))

        # ══ 하단 키 안내 (전체 너비) ══
        KEY_Y  = H - 34
        pygame.draw.line(panel, (170,170,185), (0, KEY_Y-4), (WIDTH, KEY_Y-4), 1)

        keys = [
            ("[T] 학습",     self.training),
            ("[A] 자동",     self.auto_play),
            ("[N] 한스텝",   False),
            ("[D] 데모리셋", False),
            ("[R] 전체리셋", False),
        ]
        btn_w = (WIDTH - PAD*2) // len(keys)
        for i, (label, active) in enumerate(keys):
            bx = PAD + i * btn_w
            by = KEY_Y
            bg = (180, 230, 195) if active else (215, 215, 222)
            fc = (30, 130, 70)   if active else (60, 60, 70)
            pygame.draw.rect(panel, bg,  (bx, by, btn_w-4, 26), border_radius=5)
            pygame.draw.rect(panel, (160,160,175), (bx, by, btn_w-4, 26), 1, border_radius=5)
            ts = self.font_s.render(label, True, fc)
            tw, th = ts.get_size()
            panel.blit(ts, (bx + (btn_w-4-tw)//2, by + (26-th)//2))

        self.screen.blit(panel, (0, PY))


    def draw(self):
        self.screen.fill(WHITE)
        self.env.render(self.screen)
        self._draw_action_arrow()
        self._draw_q_overlay()
        self.draw_info_panel()
        pygame.display.flip()

    def run(self):
        while True:
            now = pygame.time.get_ticks()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if   event.key == pygame.K_t:
                        self.training  = not self.training
                    elif event.key == pygame.K_a:
                        self.auto_play = not self.auto_play
                    elif event.key == pygame.K_n:
                        if not self.training:
                            self.run_demo_step()
                    elif event.key == pygame.K_d:
                        self.start_new_demo()
                    elif event.key == pygame.K_r:
                        self.reset_all()

            if self.training:
                for _ in range(TRAIN_EPISODES_PER_FRAME):
                    self._train_one()
                # 학습 중에도 데모 자동 진행
                if now - self.last_step_t > self.step_delay:
                    if self.demo_done:
                        self.start_new_demo()
                    else:
                        self.run_demo_step()
                    self.last_step_t = now
            else:
                if self.auto_play:
                    if now - self.last_step_t > self.step_delay:
                        if self.demo_done:
                            self.start_new_demo()
                        else:
                            self.run_demo_step()
                        self.last_step_t = now

            self.draw()
            self.clock.tick(FPS)


if __name__ == "__main__":
    GameApp().run()