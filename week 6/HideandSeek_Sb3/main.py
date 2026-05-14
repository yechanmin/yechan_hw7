# main.py
import os
import sys
import pygame

from stable_baselines3 import DQN
from stable_baselines3.common.env_checker import check_env

from env import HideAndSeekEnv
from settings import *


class GameApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("SB3 Hide and Seek")
        self.clock = pygame.time.Clock()

        self.font_b = pygame.font.SysFont("malgungothic", 18, bold=True)
        self.font_s = pygame.font.SysFont("malgungothic", 13)

        self.train_env = HideAndSeekEnv()
        self.demo_env = HideAndSeekEnv()

        check_env(self.train_env, warn=True)

        if os.path.exists(MODEL_PATH):
            self.model = DQN.load(MODEL_PATH, env=self.train_env)
        else:
            self.model = DQN(
                policy="MlpPolicy",
                env=self.train_env,
                learning_rate=5e-4,
                buffer_size=100000,
                learning_starts=5000,
                batch_size=128,
                gamma=0.99,
                train_freq=4,
                target_update_interval=500,
                exploration_fraction=0.40,
                exploration_initial_eps=1.0,
                exploration_final_eps=0.05,
                policy_kwargs=dict(net_arch=[128, 128]),
                verbose=1,
            )

        self.total_trained_steps = 0

        self.auto_play = False
        self.demo_done = False
        self.last_result = "READY"
        self.last_action = 0
        self.step_count = 0
        self.step_delay = 220
        self.last_step_t = 0

        self.eval_episodes = 0
        self.wins = 0
        self.losses = 0
        self.timeouts = 0
        self.recent_results = []
        self.last_invalid = False

        self.obs = None
        self.start_new_demo()

    def train(self, timesteps):
        self.model.learn(total_timesteps=timesteps, reset_num_timesteps=False)
        self.model.save(MODEL_PATH)
        self.total_trained_steps += timesteps

    def reset_stats(self):
        self.eval_episodes = 0
        self.wins = 0
        self.losses = 0
        self.timeouts = 0
        self.recent_results = []

    def start_new_demo(self):
        self.obs, _ = self.demo_env.reset()
        self.demo_done = False
        self.last_result = "RUNNING"
        self.last_action = 0
        self.step_count = 0
        self.last_invalid = False

    def run_demo_step(self):
        if self.demo_done:
            return

        action, _ = self.model.predict(self.obs, deterministic=True)
        self.last_action = int(action)

        self.obs, reward, terminated, truncated, info = self.demo_env.step(action)
        self.last_invalid = info.get("invalid_move", False)
        self.demo_done = terminated or truncated
        self.last_result = info["result"].upper()
        self.step_count += 1

        if self.demo_done:
            self.eval_episodes += 1

            if info["result"] == "escaped":
                self.wins += 1
                self.recent_results.append(1)
            elif info["result"] == "caught":
                self.losses += 1
                self.recent_results.append(0)
            else:
                self.timeouts += 1
                self.recent_results.append(0)

            if len(self.recent_results) > 200:
                self.recent_results.pop(0)

    def _bar(self, surf, x, y, w, h, ratio, fg, bg=(205, 205, 205)):
        pygame.draw.rect(surf, bg, (x, y, w, h), border_radius=3)
        fw = max(0, int(w * max(0.0, min(ratio, 1.0))))
        if fw:
            pygame.draw.rect(surf, fg, (x, y, fw, h), border_radius=3)
        pygame.draw.rect(surf, (160, 160, 160), (x, y, w, h), 1, border_radius=3)

    def _txt(self, surf, text, x, y, font, color=(30, 30, 30)):
        surf.blit(font.render(text, True, color), (x, y))

    def _draw_action_arrow(self):
        if self.demo_done:
            return

        dx, dy = ACTIONS[self.last_action]
        hx, hy = self.demo_env.hider.pos
        cx = hx * CELL_SIZE + CELL_SIZE // 2
        cy = hy * CELL_SIZE + CELL_SIZE // 2
        end = (cx + dx * 20, cy + dy * 20)

        if dx or dy:
            pygame.draw.line(self.screen, BLACK, (cx, cy), end, 3)
            pygame.draw.circle(self.screen, BLACK, end, 4)

    def draw_info_panel(self):
        py = BOARD_WIDTH
        pad = 10
        col = WIDTH // 3
        h = INFO_HEIGHT

        panel = pygame.Surface((WIDTH, h))
        panel.fill(PANEL_BG)
        pygame.draw.line(panel, (150, 150, 160), (0, 0), (WIDTH, 0), 2)

        total = max(self.eval_episodes, 1)
        win_r = self.wins / total
        recent_r = sum(self.recent_results) / max(len(self.recent_results), 1)

        x0 = pad
        row = 18
        self._txt(panel, "📊 평가 통계", x0, 8, self.font_b, (50, 50, 80))
        self._txt(panel, f"평가 에피소드: {self.eval_episodes}", x0, 34, self.font_s)
        self._txt(panel, f"탈출: {self.wins}", x0, 34 + row, self.font_s, (40, 150, 80))
        self._txt(panel, f"잡힘: {self.losses}", x0, 34 + row * 2, self.font_s, (190, 60, 60))
        self._txt(panel, f"시간초과: {self.timeouts}", x0, 34 + row * 3, self.font_s, (160, 120, 40))
        self._txt(panel, f"전체 승률 {win_r * 100:.1f}%", x0, 34 + row * 4 + 2, self.font_s)
        self._bar(panel, x0, 34 + row * 5, col - pad * 2, 10, win_r, (70, 190, 110))
        self._txt(panel, f"최근 200판 {recent_r * 100:.1f}%", x0, 34 + row * 6 + 4, self.font_s)
        self._bar(panel, x0, 34 + row * 7 + 2, col - pad * 2, 10, recent_r, (70, 190, 110))

        x1 = col + pad
        pygame.draw.line(panel, (190, 190, 200), (col, 8), (col, h - 8), 1)
        self._txt(panel, "🎮 현재 데모", x1, 8, self.font_b, (50, 50, 80))
        self._txt(panel, self.last_result, x1, 34, self.font_b, (60, 120, 210))
        self._txt(panel, f"스텝: {self.step_count} / {MAX_STEPS}", x1, 58, self.font_s)
        self._bar(panel, x1, 76, col - pad * 2, 10, self.step_count / MAX_STEPS, (70, 120, 210))
        self._txt(panel, f"액션: {ACTION_NAMES[self.last_action]}", x1, 94, self.font_s)

        gdx, gdy, sdx, sdy, fov, dg, ds, bu, bd, bl, br = self.obs
        self._txt(panel, f"goal Δ({gdx:+.2f},{gdy:+.2f}) dist={dg:.2f}", x1, 114, self.font_s, (80, 80, 80))
        self._txt(panel, f"seek Δ({sdx:+.2f},{sdy:+.2f}) dist={ds:.2f}", x1, 132, self.font_s, (80, 80, 80))
        fov_c = (210, 60, 60) if fov >= 0.5 else (80, 160, 100)
        self._txt(panel, f"시야 노출: {'⚠ 위험!' if fov >= 0.5 else '✓ 안전'}", x1, 150, self.font_s, fov_c)
        self._txt(panel, f"막힌 이동: {'예' if self.last_invalid else '아니오'}", x1, 168, self.font_s)

        x2 = col * 2 + pad
        pygame.draw.line(panel, (190, 190, 200), (col * 2, 8), (col * 2, h - 8), 1)
        self._txt(panel, "🤖 SB3 DQN", x2, 8, self.font_b, (50, 50, 80))
        self._txt(panel, f"누적 학습 step: {self.total_trained_steps:,}", x2, 34, self.font_s)
        self._txt(panel, "T: 5만 step 학습", x2, 60, self.font_s)
        self._txt(panel, "A: 자동 재생", x2, 78, self.font_s)
        self._txt(panel, "N: 한 스텝", x2, 96, self.font_s)
        self._txt(panel, "D: 데모 리셋", x2, 114, self.font_s)
        self._txt(panel, "R: 통계 리셋", x2, 132, self.font_s)
        self._txt(panel, f"Auto play: {'ON' if self.auto_play else 'OFF'}", x2, 158, self.font_s)

        key_y = h - 34
        pygame.draw.line(panel, (170, 170, 185), (0, key_y - 6), (WIDTH, key_y - 6), 1)

        self.screen.blit(panel, (0, py))

    def draw(self):
        self.screen.fill(WHITE)
        self.demo_env.render_on(self.screen)
        self._draw_action_arrow()
        self.draw_info_panel()
        pygame.display.flip()

    def run(self):
        while True:
            now = pygame.time.get_ticks()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_t:
                        self.train(TRAIN_STEPS_PER_PRESS)
                    elif event.key == pygame.K_a:
                        self.auto_play = not self.auto_play
                    elif event.key == pygame.K_n:
                        if self.demo_done:
                            self.start_new_demo()
                        else:
                            self.run_demo_step()
                    elif event.key == pygame.K_d:
                        self.start_new_demo()
                    elif event.key == pygame.K_r:
                        self.reset_stats()

            if self.auto_play and now - self.last_step_t > self.step_delay:
                if self.demo_done:
                    self.start_new_demo()
                else:
                    self.run_demo_step()
                self.last_step_t = now

            self.draw()
            self.clock.tick(FPS)


if __name__ == "__main__":
    GameApp().run()