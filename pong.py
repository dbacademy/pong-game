import array
import math
import random
import sys

import pygame

# --- Constants ---
WIDTH, HEIGHT = 800, 600
FPS = 60
WINNING_SCORE = 7

# Colors
DARK_BG = (15, 15, 30)
WHITE = (240, 240, 240)
CYAN = (0, 230, 230)
MAGENTA = (230, 0, 230)
YELLOW = (255, 220, 0)
GRAY = (80, 80, 100)

PADDLE_WIDTH, PADDLE_HEIGHT = 12, 90
BALL_SIZE = 14
PADDLE_SPEED = 6
BALL_SPEED_INIT = 5
AI_SPEED = 5


def make_sound(frequency=440, duration_ms=80, volume=0.3, sample_rate=44100):
    """Generate a stereo sine-wave beep as a pygame.mixer.Sound."""
    n_samples = int(sample_rate * duration_ms / 1000)
    mono = array.array("h")
    for i in range(n_samples):
        val = int(volume * 32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
        mono.append(max(-32768, min(32767, val)))
    stereo = array.array("h")
    for s in mono:
        stereo.append(s)
        stereo.append(s)
    return pygame.mixer.Sound(buffer=stereo)


class Paddle:
    def __init__(self, x, y, color):
        self.rect = pygame.Rect(x, y, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.color = color
        self.score = 0

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect, border_radius=4)

    def move_up(self):
        self.rect.y = max(0, self.rect.y - PADDLE_SPEED)

    def move_down(self):
        self.rect.y = min(HEIGHT - PADDLE_HEIGHT, self.rect.y + PADDLE_SPEED)


class Ball:
    def __init__(self):
        self.reset()
        self.color = YELLOW

    def reset(self):
        self.rect = pygame.Rect(
            WIDTH // 2 - BALL_SIZE // 2,
            HEIGHT // 2 - BALL_SIZE // 2,
            BALL_SIZE,
            BALL_SIZE,
        )
        angle = random.uniform(-math.pi / 4, math.pi / 4)
        direction = random.choice([-1, 1])
        self.vx = direction * BALL_SPEED_INIT * math.cos(angle)
        self.vy = BALL_SPEED_INIT * math.sin(angle)

    def update(self):
        self.rect.x += int(self.vx)
        self.rect.y += int(self.vy)

    def draw(self, surface):
        pygame.draw.ellipse(surface, self.color, self.rect)


class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Pong – First to 7 Wins!")
        self.clock = pygame.time.Clock()

        self.font_large = pygame.font.SysFont("monospace", 72, bold=True)
        self.font_med = pygame.font.SysFont("monospace", 36, bold=True)
        self.font_small = pygame.font.SysFont("monospace", 24)

        # Sounds (created once and reused across resets)
        try:
            self.snd_hit = make_sound(520, 60, 0.35)
            self.snd_wall = make_sound(300, 50, 0.25)
            self.snd_score = make_sound(180, 250, 0.4)
            self.snd_win = make_sound(660, 500, 0.45)
            self.snd_bg = make_sound(55, 2000, 0.07)
        except Exception:
            self.snd_hit = self.snd_wall = self.snd_score = self.snd_win = self.snd_bg = None

        self._new_game()

    def _new_game(self):
        """Reset all mutable game state for a new game."""
        self.player = Paddle(30, HEIGHT // 2 - PADDLE_HEIGHT // 2, CYAN)
        self.ai = Paddle(WIDTH - 30 - PADDLE_WIDTH, HEIGHT // 2 - PADDLE_HEIGHT // 2, MAGENTA)
        self.ball = Ball()
        self.state = "playing"
        self.winner_text = ""
        self.pause_timer = 0
        # Start background hum
        if self.snd_bg:
            try:
                self.snd_bg.play(-1)
            except Exception:
                pass

    # ------------------------------------------------------------------
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if self.state == "winner" and event.key == pygame.K_r:
                    self._new_game()

    # ------------------------------------------------------------------
    def update(self):
        if self.state == "winner":
            return

        if self.pause_timer > 0:
            self.pause_timer -= 1
            return

        # Player input
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.player.move_up()
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.player.move_down()

        # AI movement – track ball with slight imperfection
        ball_center = self.ball.rect.centery
        ai_center = self.ai.rect.centery
        diff = ball_center - ai_center
        if abs(diff) > 4:
            step = min(AI_SPEED, abs(diff))
            self.ai.rect.y += step if diff > 0 else -step
            self.ai.rect.y = max(0, min(HEIGHT - PADDLE_HEIGHT, self.ai.rect.y))

        # Ball movement
        self.ball.update()

        # Wall bounce (top / bottom)
        if self.ball.rect.top <= 0:
            self.ball.rect.top = 0
            self.ball.vy = abs(self.ball.vy)
            self._play(self.snd_wall)
        elif self.ball.rect.bottom >= HEIGHT:
            self.ball.rect.bottom = HEIGHT
            self.ball.vy = -abs(self.ball.vy)
            self._play(self.snd_wall)

        # Paddle collisions
        for paddle in (self.player, self.ai):
            if self.ball.rect.colliderect(paddle.rect):
                # Reflect horizontal velocity
                if paddle is self.player:
                    self.ball.rect.left = paddle.rect.right
                    self.ball.vx = abs(self.ball.vx) * 1.05
                else:
                    self.ball.rect.right = paddle.rect.left
                    self.ball.vx = -abs(self.ball.vx) * 1.05

                # Add spin based on where ball hits paddle; enforce minimum vertical velocity
                relative_hit = (self.ball.rect.centery - paddle.rect.centery) / (PADDLE_HEIGHT / 2)
                self.ball.vy = relative_hit * abs(self.ball.vx)
                min_vy = BALL_SPEED_INIT * 0.2
                if abs(self.ball.vy) < min_vy:
                    self.ball.vy = math.copysign(min_vy, self.ball.vy if self.ball.vy != 0 else 1)

                # Cap speed
                speed = math.hypot(self.ball.vx, self.ball.vy)
                cap = BALL_SPEED_INIT * 2.5
                if speed > cap:
                    self.ball.vx *= cap / speed
                    self.ball.vy *= cap / speed

                self._play(self.snd_hit)

        # Scoring
        if self.ball.rect.right < 0:
            self.ai.score += 1
            self._play(self.snd_score)
            self._check_winner("Computer")
            if self.state != "winner":
                self.ball.reset()
                self.pause_timer = FPS
        elif self.ball.rect.left > WIDTH:
            self.player.score += 1
            self._play(self.snd_score)
            self._check_winner("Player")
            if self.state != "winner":
                self.ball.reset()
                self.pause_timer = FPS

    def _play(self, sound):
        if sound:
            try:
                sound.play()
            except Exception:
                pass

    def _check_winner(self, name):
        score = self.player.score if name == "Player" else self.ai.score
        if score >= WINNING_SCORE:
            self.state = "winner"
            self.winner_text = f"{name} Wins!"
            self._play(self.snd_win)
            if self.snd_bg:
                try:
                    self.snd_bg.stop()
                except Exception:
                    pass

    # ------------------------------------------------------------------
    def draw(self):
        self.screen.fill(DARK_BG)

        # Center dashed line
        for y in range(0, HEIGHT, 20):
            if (y // 20) % 2 == 0:
                pygame.draw.rect(self.screen, GRAY, (WIDTH // 2 - 2, y, 4, 12))

        # Paddles & ball
        self.player.draw(self.screen)
        self.ai.draw(self.screen)
        self.ball.draw(self.screen)

        # Scores
        p_surf = self.font_large.render(str(self.player.score), True, CYAN)
        a_surf = self.font_large.render(str(self.ai.score), True, MAGENTA)
        self.screen.blit(p_surf, (WIDTH // 4 - p_surf.get_width() // 2, 20))
        self.screen.blit(a_surf, (3 * WIDTH // 4 - a_surf.get_width() // 2, 20))

        # Labels
        lbl_p = self.font_small.render("PLAYER", True, CYAN)
        lbl_a = self.font_small.render("COMPUTER", True, MAGENTA)
        self.screen.blit(lbl_p, (WIDTH // 4 - lbl_p.get_width() // 2, 100))
        self.screen.blit(lbl_a, (3 * WIDTH // 4 - lbl_a.get_width() // 2, 100))

        # "First to 7" reminder at bottom
        hint = self.font_small.render("First to 7 wins  |  W/S or ↑/↓ to move  |  ESC to quit", True, GRAY)
        self.screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 30))

        # Winner overlay
        if self.state == "winner":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, 0))

            w_surf = self.font_large.render(self.winner_text, True, YELLOW)
            self.screen.blit(w_surf, (WIDTH // 2 - w_surf.get_width() // 2, HEIGHT // 2 - 60))

            r_surf = self.font_med.render("Press R to play again", True, WHITE)
            self.screen.blit(r_surf, (WIDTH // 2 - r_surf.get_width() // 2, HEIGHT // 2 + 30))

        pygame.display.flip()

    # ------------------------------------------------------------------
    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)


if __name__ == "__main__":
    Game().run()
