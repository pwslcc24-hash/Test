"""Flappy Bird style game implemented with Pygame.

Run with:
    python flappy_bird.py

Use the space bar or up arrow to flap the bird. Press escape to quit.
"""
from __future__ import annotations

import os
import random
import sys
from dataclasses import dataclass
from typing import List, Optional, Tuple

import pygame

# Constants --------------------------------------------------------------------
WIDTH, HEIGHT = 400, 600
FPS = 60
PIPE_GAP = 160
PIPE_WIDTH = 70
PIPE_SPEED = 3
BIRD_RADIUS = 18
BIRD_X = 80
GRAVITY = 0.35
FLAP_STRENGTH = -7.5
BASE_HEIGHT = 80
FONT_NAME = "freesansbold.ttf"
BACKGROUND_COLOR = (135, 206, 235)  # sky blue
BIRD_ANIMATION_SPEED = 5
CLOUD_SIZE_SCALE = 1.35


JUMP_SOUND: Optional[pygame.mixer.Sound] = None
HIT_SOUND: Optional[pygame.mixer.Sound] = None


def create_smooth_bird_frames() -> List[pygame.Surface]:
    """Create stylized Flappy Bird inspired frames with kissy lips and big wings."""

    body_color = (255, 228, 92)
    shadow_color = (232, 172, 53)
    highlight_color = (255, 248, 180)
    outline_color = (216, 140, 32)
    wing_color = (255, 255, 255)
    wing_shadow = (230, 230, 230)
    lip_color = (210, 40, 72)
    lip_highlight = (255, 110, 140)

    width, height = 42, 32
    body_rect = pygame.Rect(6, 8, 28, 18)
    eye_center = (25, 16)
    eye_radius = 7
    pupil_radius = 4
    lip_rect = pygame.Rect(28, 15, 10, 8)

    wing_offsets = (-4, 0, 4)
    frames: List[pygame.Surface] = []

    for offset in wing_offsets:
        surface = pygame.Surface((width, height), pygame.SRCALPHA)

        pygame.draw.ellipse(surface, body_color, body_rect)
        inner = body_rect.inflate(-10, -6).move(2, 2)
        pygame.draw.ellipse(surface, shadow_color, inner)
        highlight = body_rect.inflate(-18, -10).move(-2, -3)
        pygame.draw.ellipse(surface, highlight_color, highlight)
        pygame.draw.ellipse(surface, outline_color, body_rect, 2)

        wing_rect = pygame.Rect(10, 12 + offset, 12, 9)
        pygame.draw.ellipse(surface, wing_shadow, wing_rect.inflate(2, 1))
        pygame.draw.ellipse(surface, wing_color, wing_rect)
        pygame.draw.ellipse(surface, outline_color, wing_rect, 1)

        pygame.draw.circle(surface, (255, 255, 255), eye_center, eye_radius)
        pygame.draw.circle(surface, (0, 0, 0), eye_center, pupil_radius)
        pygame.draw.circle(surface, highlight_color, (eye_center[0] - 2, eye_center[1] - 2), 2)

        pygame.draw.ellipse(surface, lip_color, lip_rect)
        inner_lip = lip_rect.inflate(-4, -3).move(1, 0)
        pygame.draw.ellipse(surface, lip_highlight, inner_lip)
        pygame.draw.ellipse(surface, outline_color, lip_rect, 1)

        frames.append(surface)

    return frames


BIRD_FRAMES = create_smooth_bird_frames()


@dataclass
class Bird:
    """Player controlled bird."""

    x: float
    y: float
    velocity: float = 0.0
    angle: float = 0.0
    alive: bool = True
    frame_index: int = 0
    frame_counter: int = 0

    def flap(self) -> None:
        if self.alive:
            self.velocity = FLAP_STRENGTH
            if JUMP_SOUND:
                JUMP_SOUND.play()

    def update(self) -> None:
        self.velocity += GRAVITY
        self.y += self.velocity
        # limit fall speed to keep gameplay manageable
        self.velocity = min(self.velocity, 10)
        # Tilt bird based on movement
        if self.velocity < 0:
            self.angle = max(-25, self.angle - 5)
        else:
            self.angle = min(90, self.angle + 3)

        if self.alive:
            self.frame_counter += 1
            if self.frame_counter >= BIRD_ANIMATION_SPEED:
                self.frame_counter = 0
                self.frame_index = (self.frame_index + 1) % len(BIRD_FRAMES)

    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - BIRD_RADIUS), int(self.y - BIRD_RADIUS), BIRD_RADIUS * 2, BIRD_RADIUS * 2)

    def draw(self, surface: pygame.Surface) -> None:
        current_frame = BIRD_FRAMES[self.frame_index]
        rotated_bird = pygame.transform.rotozoom(current_frame, -self.angle, 1)
        rect = rotated_bird.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rotated_bird, rect)


@dataclass
class Pipe:
    """A pair of top and bottom pipes."""

    x: float
    gap_y: float
    passed: bool = False

    def top_rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), 0, PIPE_WIDTH, int(self.gap_y - PIPE_GAP / 2))

    def bottom_rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.gap_y + PIPE_GAP / 2), PIPE_WIDTH, HEIGHT - BASE_HEIGHT - int(self.gap_y + PIPE_GAP / 2))

    def update(self) -> None:
        self.x -= PIPE_SPEED

    def is_offscreen(self) -> bool:
        return self.x + PIPE_WIDTH < 0

    def draw(self, surface: pygame.Surface) -> None:
        body_color = (76, 187, 23)
        shade_color = (56, 145, 18)
        highlight_color = (140, 227, 96)
        rim_color = (96, 207, 43)
        rim_height = 20

        top_rect = self.top_rect()
        bottom_rect = self.bottom_rect()

        pygame.draw.rect(surface, body_color, top_rect)
        pygame.draw.rect(surface, body_color, bottom_rect)

        top_shade = pygame.Rect(top_rect.x + top_rect.width - 14, top_rect.y, 14, top_rect.height)
        bottom_shade = pygame.Rect(bottom_rect.x + bottom_rect.width - 14, bottom_rect.y, 14, bottom_rect.height)
        pygame.draw.rect(surface, shade_color, top_shade)
        pygame.draw.rect(surface, shade_color, bottom_shade)

        top_highlight = pygame.Rect(top_rect.x + 6, top_rect.y, 8, top_rect.height)
        bottom_highlight = pygame.Rect(bottom_rect.x + 6, bottom_rect.y, 8, bottom_rect.height)
        pygame.draw.rect(surface, highlight_color, top_highlight)
        pygame.draw.rect(surface, highlight_color, bottom_highlight)

        top_rim = pygame.Rect(top_rect.x - 6, top_rect.bottom - rim_height, PIPE_WIDTH + 12, rim_height)
        bottom_rim = pygame.Rect(bottom_rect.x - 6, bottom_rect.y, PIPE_WIDTH + 12, rim_height)
        pygame.draw.rect(surface, rim_color, top_rim)
        pygame.draw.rect(surface, rim_color, bottom_rim)

        pygame.draw.rect(surface, shade_color, top_rim, 3, border_radius=4)
        pygame.draw.rect(surface, shade_color, bottom_rim, 3, border_radius=4)

        pygame.draw.rect(surface, shade_color, top_rect, 3, border_radius=2)
        pygame.draw.rect(surface, shade_color, bottom_rect, 3, border_radius=2)


class Base:
    """Scrolling ground at the bottom of the screen."""

    def __init__(self, y: int) -> None:
        self.y = y
        self.x1 = 0
        self.x2 = WIDTH
        self.speed = PIPE_SPEED

    def update(self) -> None:
        self.x1 -= self.speed
        self.x2 -= self.speed
        if self.x1 + WIDTH < 0:
            self.x1 = self.x2 + WIDTH
        if self.x2 + WIDTH < 0:
            self.x2 = self.x1 + WIDTH

    def draw(self, surface: pygame.Surface) -> None:
        color = (222, 184, 135)
        pygame.draw.rect(surface, color, pygame.Rect(int(self.x1), self.y, WIDTH, BASE_HEIGHT))
        pygame.draw.rect(surface, color, pygame.Rect(int(self.x2), self.y, WIDTH, BASE_HEIGHT))
        pygame.draw.rect(surface, (139, 69, 19), pygame.Rect(0, self.y, WIDTH, 8))


@dataclass
class Cloud:
    """Soft, layered cloud that scrolls slowly across the sky."""

    x: float
    y: float
    base_radius: float
    speed: float
    offsets: List[Tuple[float, float, float, float]]

    @property
    def width(self) -> float:
        return self.base_radius * 4.5

    def update(self) -> None:
        self.x -= self.speed
        if self.x < -self.width:
            self.x = WIDTH + random.uniform(20, 120)
            self.y = random.uniform(40, 240)

    def draw(self, surface: pygame.Surface) -> None:
        cloud_surface_width = int(self.base_radius * 4.6)
        cloud_surface_height = int(self.base_radius * 2.9)
        cloud_surface = pygame.Surface((cloud_surface_width, cloud_surface_height), pygame.SRCALPHA)
        center_x = cloud_surface_width // 2
        center_y = cloud_surface_height // 2

        for index, (dx, dy, width, height) in enumerate(self.offsets):
            rect = pygame.Rect(0, 0, int(width), int(height))
            rect.center = (int(center_x + dx), int(center_y + dy))
            alpha = max(180, 220 - index * 15)
            main_color = (255, 255, 255, alpha)
            accent_color = (255, 255, 255, max(170, alpha - 20))
            pygame.draw.ellipse(cloud_surface, main_color, rect)
            inner = rect.inflate(-rect.width * 0.25, -rect.height * 0.3)
            if inner.width > 0 and inner.height > 0:
                pygame.draw.ellipse(cloud_surface, accent_color, inner)

        surface.blit(
            cloud_surface,
            (int(self.x - cloud_surface_width / 2), int(self.y - cloud_surface_height / 2)),
        )


CLOUDS: List[Cloud] = []


def create_cloud_offsets(base_radius: float) -> List[Tuple[float, float, float, float]]:
    offsets: List[Tuple[float, float, float, float]] = []
    centers = (-0.75, 0.0, 0.75)
    for index, factor in enumerate(centers):
        dx = factor * base_radius + random.uniform(-8, 8)
        dy = random.uniform(-8, 8)
        width = base_radius * random.uniform(1.4, 1.8) if index == 1 else base_radius * random.uniform(1.1, 1.5)
        height = base_radius * random.uniform(0.65, 0.9)
        offsets.append((dx, dy, width, height))
    return offsets


def initialize_clouds() -> None:
    if CLOUDS:
        return
    layers = (
        (0.25, 56.0, 60),
        (0.4, 48.0, 110),
        (0.65, 36.0, 160),
    )
    for speed, base_radius, base_y in layers:
        for _ in range(3):
            radius = random.uniform(base_radius * 0.85, base_radius * 1.15) * CLOUD_SIZE_SCALE
            x = random.uniform(0, WIDTH)
            y = random.uniform(base_y - 20, base_y + 40)
            offsets = create_cloud_offsets(radius)
            CLOUDS.append(Cloud(x=x, y=y, base_radius=radius, speed=speed, offsets=offsets))


def spawn_pipe() -> Pipe:
    margin = 70
    gap_center = random.randint(margin + PIPE_GAP // 2, HEIGHT - BASE_HEIGHT - margin - PIPE_GAP // 2)
    return Pipe(x=WIDTH, gap_y=float(gap_center))


def check_collision(bird: Bird, pipes: List[Pipe]) -> bool:
    if bird.y - BIRD_RADIUS <= 0 or bird.y + BIRD_RADIUS >= HEIGHT - BASE_HEIGHT:
        return True
    bird_rect = bird.rect()
    for pipe in pipes:
        if bird_rect.colliderect(pipe.top_rect()) or bird_rect.colliderect(pipe.bottom_rect()):
            return True
    return False


def draw_text(surface: pygame.Surface, text: str, size: int, pos: Tuple[int, int], color=(255, 255, 255), shadow=True) -> None:
    font = pygame.font.Font(FONT_NAME, size)
    label = font.render(text, True, color)
    rect = label.get_rect(center=pos)
    if shadow:
        shadow_label = font.render(text, True, (0, 0, 0))
        shadow_rect = shadow_label.get_rect(center=(pos[0] + 2, pos[1] + 2))
        surface.blit(shadow_label, shadow_rect)
    surface.blit(label, rect)


def reset_game() -> Tuple[Bird, List[Pipe], int, Base]:
    bird = Bird(x=float(BIRD_X), y=HEIGHT / 2)
    pipes = [spawn_pipe()]
    score = 0
    base = Base(HEIGHT - BASE_HEIGHT)
    return bird, pipes, score, base


def load_sounds() -> Tuple[Optional[pygame.mixer.Sound], Optional[pygame.mixer.Sound]]:
    jump_sound: Optional[pygame.mixer.Sound] = None
    hit_sound: Optional[pygame.mixer.Sound] = None

    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        base_path = os.path.dirname(os.path.abspath(__file__))
        try:
            jump_sound = pygame.mixer.Sound(os.path.join(base_path, "jump.wav"))
        except (pygame.error, FileNotFoundError):
            jump_sound = None
        try:
            hit_sound = pygame.mixer.Sound(os.path.join(base_path, "hit.wav"))
        except (pygame.error, FileNotFoundError):
            hit_sound = None
    except pygame.error:
        jump_sound = None
        hit_sound = None

    return jump_sound, hit_sound


def main() -> None:
    os.environ.setdefault("SDL_VIDEO_CENTERED", "1")
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Flappy Bird")
    clock = pygame.time.Clock()

    global JUMP_SOUND, HIT_SOUND
    JUMP_SOUND, HIT_SOUND = load_sounds()

    bird, pipes, score, base = reset_game()
    running = True
    game_over = False
    high_score = 0

    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_UP):
                    if not game_over:
                        bird.flap()
                    else:
                        bird, pipes, score, base = reset_game()
                        game_over = False
                elif event.key == pygame.K_ESCAPE:
                    running = False

        if not game_over:
            bird.update()
            for pipe in pipes:
                pipe.update()
            base.update()

            # spawn new pipes
            if pipes[-1].x < WIDTH - 200:
                pipes.append(spawn_pipe())

            # remove offscreen pipes
            pipes = [pipe for pipe in pipes if not pipe.is_offscreen()]

            # scoring
            for pipe in pipes:
                if not pipe.passed and pipe.x + PIPE_WIDTH < bird.x:
                    pipe.passed = True
                    score += 1

            if bird.alive and check_collision(bird, pipes):
                if HIT_SOUND:
                    HIT_SOUND.play()
                bird.alive = False
                game_over = True
                if score > high_score:
                    high_score = score

        # Drawing -----------------------------------------------------------------
        screen.fill(BACKGROUND_COLOR)

        # Draw background clouds
        draw_clouds(screen)

        for pipe in pipes:
            pipe.draw(screen)

        base.draw(screen)
        bird.draw(screen)

        draw_text(screen, str(score), 48, (WIDTH // 2, 80))
        draw_text(screen, f"HI {high_score}", 24, (WIDTH - 70, 40))

        if game_over:
            draw_text(screen, "Game Over", 48, (WIDTH // 2, HEIGHT // 2 - 40))
            draw_text(screen, "Press Space to Retry", 24, (WIDTH // 2, HEIGHT // 2 + 10))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


def draw_clouds(surface: pygame.Surface) -> None:
    if not CLOUDS:
        initialize_clouds()
    for cloud in CLOUDS:
        cloud.update()
        cloud.draw(surface)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pygame.quit()
        sys.exit()
