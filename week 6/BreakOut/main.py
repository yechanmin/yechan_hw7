import pygame
import random
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import collections

# --- 전역 설정 ---
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 850  # 하단 UI 영역 확보
FPS = 60

COLORS = {
    "bg": (15, 15, 25),
    "paddle": (0, 255, 200),
    "ball": (255, 255, 255),
    "text": (240, 240, 240),
    "accent": (255, 0, 150),
    "bricks": [(255, 50, 50), (255, 150, 50), (255, 255, 50), (50, 255, 50), (50, 50, 255)]
}


# --- [RL 모델 정의] ---
class DQN(nn.Module):
    def __init__(self, input_dim, output_dim):
        super(DQN, self).__init__()
        self.fc = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, output_dim)
        )

    def forward(self, x):
        return self.fc(x)


class DQNAgent:
    def __init__(self, state_dim, action_dim):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = DQN(state_dim, action_dim).to(self.device)
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.0005)
        self.memory = collections.deque(maxlen=20000)
        self.batch_size = 64
        self.gamma = 0.99
        self.epsilon = 1.0
        self.epsilon_min = 0.02
        self.epsilon_decay = 0.998
        self.loss = 0

    def act(self, state, train=True):
        if train and random.random() < self.epsilon:
            return random.randint(0, 2)
        state_t = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        with torch.no_grad():
            return self.model(state_t).argmax().item()

    def train_step(self):
        if len(self.memory) < self.batch_size: return
        batch = random.sample(self.memory, self.batch_size)
        s, a, r, ns, d = zip(*batch)
        s, a, r, ns, d = map(lambda x: torch.FloatTensor(np.array(x)).to(self.device), [s, a, r, ns, d])

        curr_q = self.model(s).gather(1, a.long().unsqueeze(1))
        next_q = self.model(ns).max(1)[0].unsqueeze(1)
        target_q = r.unsqueeze(1) + (self.gamma * next_q * (1 - d.unsqueeze(1)))

        loss = nn.MSELoss()(curr_q, target_q)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        self.loss = loss.item()

    def save(self):
        torch.save(self.model.state_dict(), "breakout_model.pth")

    def load(self):
        try:
            self.model.load_state_dict(torch.load("breakout_model.pth", map_location=self.device))
        except:
            pass


# --- [게임 엔진 클래스] ---
class BreakoutEngine:
    def __init__(self):
        self.paddle_w, self.paddle_h = 100, 15
        self.reset()

    def reset(self):
        self.px = (SCREEN_WIDTH - self.paddle_w) // 2
        self.bx, self.by = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        self.bdx, self.bdy = random.choice([-5, 5]), -5
        self.bricks = [pygame.Rect(5 + c * 60, 60 + r * 25, 55, 20) for r in range(5) for c in range(10)]
        self.score = 0
        self.done = False
        return self.get_state()

    def get_state(self):
        return np.array([self.px / 600, self.bx / 600, self.by / 800, self.bdx / 10, self.bdy / 10], dtype=np.float32)

    def step(self, action):
        reward = 0.1
        if action == 1 and self.px > 0:
            self.px -= 10
        elif action == 2 and self.px < SCREEN_WIDTH - self.paddle_w:
            self.px += 10

        self.bx += self.bdx
        self.by += self.bdy

        if self.bx <= 0 or self.bx >= SCREEN_WIDTH - 12: self.bdx *= -1
        if self.by <= 0: self.bdy *= -1

        br = pygame.Rect(self.bx, self.by, 12, 12)
        pr = pygame.Rect(self.px, SCREEN_HEIGHT - 100, self.paddle_w, self.paddle_h)

        if br.colliderect(pr) and self.bdy > 0:
            self.bdy *= -1
            self.bdx = ((self.bx - (self.px + 50)) / 50) * 6
            reward = 2.0

        hit_idx = br.collidelist(self.bricks)
        if hit_idx != -1:
            self.bdy *= -1
            self.bricks.pop(hit_idx)
            self.score += 10
            reward = 5.0

        if self.by > SCREEN_HEIGHT - 80:
            self.done = True
            reward = -10.0

        return self.get_state(), reward, self.done


# --- [메인 어플리케이션] ---
class BreakoutApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font_main = pygame.font.SysFont("malgungothic", 40)
        self.font_sub = pygame.font.SysFont("malgungothic", 20)

        self.env = BreakoutEngine()
        self.agent = DQNAgent(5, 3)
        self.agent.load()

        self.state = "MENU"  # MENU, PLAYING
        self.mode = 1  # 1:Human, 2:AI, 3:Train
        self.paused = False
        self.speed = 1
        self.episode = 0

    def draw_text(self, text, x, y, color=COLORS["text"], center=False):
        surf = self.font_main.render(text, True, color) if y < 400 else self.font_sub.render(text, True, color)
        rect = surf.get_rect(center=(x, y)) if center else surf.get_rect(topleft=(x, y))
        self.screen.blit(surf, rect)

    def run(self):
        running = True
        while running:
            if self.state == "MENU":
                running = self.handle_menu()
            elif self.state == "PLAYING":
                running = self.handle_game()
            pygame.display.flip()
        pygame.quit()

    def handle_menu(self):
        self.screen.fill(COLORS["bg"])
        self.draw_text("BREAKOUT AI TRAINER", SCREEN_WIDTH // 2, 200, COLORS["accent"], True)
        self.draw_text("[1] HUMAN PLAY", SCREEN_WIDTH // 2, 350, center=True)
        self.draw_text("[2] AI TEST (Load Saved Model)", SCREEN_WIDTH // 2, 400, center=True)
        self.draw_text("[3] REINFORCEMENT LEARNING", SCREEN_WIDTH // 2, 450, center=True)
        self.draw_text("Controls: ESC(Back), P(Pause), S(Save), Up/Down(Speed)", SCREEN_WIDTH // 2, 750, center=True)

        for event in pygame.event.get():
            if event.type == pygame.QUIT: return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1: self.mode, self.state = 1, "PLAYING"
                if event.key == pygame.K_2: self.mode, self.state = 2, "PLAYING"
                if event.key == pygame.K_3: self.mode, self.state = 3, "PLAYING"
                if self.state == "PLAYING":
                    self.env.reset()
                    self.speed = 1
        return True

    def handle_game(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: self.state = "MENU"
                if event.key == pygame.K_p: self.paused = not self.paused
                if event.key == pygame.K_s and self.mode == 3: self.agent.save()
                if event.key == pygame.K_UP: self.speed = min(self.speed * 10, 1000)
                if event.key == pygame.K_DOWN: self.speed = max(self.speed // 10, 1)

        if not self.paused:
            for _ in range(self.speed):
                obs = self.env.get_state()
                if self.mode == 1:
                    keys = pygame.key.get_pressed()
                    action = 1 if keys[pygame.K_LEFT] else 2 if keys[pygame.K_RIGHT] else 0
                else:
                    action = self.agent.act(obs, train=(self.mode == 3))

                next_obs, reward, done = self.env.step(action)

                if self.mode == 3:
                    self.agent.memory.append((obs, action, reward, next_obs, done))
                    self.agent.train_step()

                if done:
                    self.episode += 1
                    if self.mode == 3: self.agent.epsilon = max(0.02, self.agent.epsilon * 0.995)
                    self.env.reset()
                    break

        # 렌더링 (최적화: 너무 빠를 땐 10프레임마다 그림)
        if self.speed < 100 or self.episode % 5 == 0:
            self.screen.fill(COLORS["bg"])
            pygame.draw.rect(self.screen, COLORS["paddle"],
                             (self.env.px, SCREEN_HEIGHT - 100, self.env.paddle_w, self.env.paddle_h))
            pygame.draw.rect(self.screen, COLORS["ball"], (self.env.bx, self.env.by, 12, 12))
            for b in self.env.bricks:
                color = COLORS["bricks"][(b.y - 60) // 25 % 5]
                pygame.draw.rect(self.screen, color, b)

            # UI 정보 표시
            mode_str = ["HUMAN", "AI PLAY", "TRAINING"][self.mode - 1]
            info = f"MODE: {mode_str} | SCORE: {self.env.score} | SPEED: {self.speed}x"
            self.draw_text(info, 20, 10)
            if self.mode == 3:
                rl_info = f"EP: {self.episode} | EPS: {self.agent.epsilon:.2f} | LOSS: {self.agent.loss:.4f}"
                self.draw_text(rl_info, 20, 810)
            if self.paused:
                self.draw_text("PAUSED", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, COLORS["accent"], True)

        if self.speed == 1: self.clock.tick(FPS)
        return True


if __name__ == "__main__":
    BreakoutApp().run()