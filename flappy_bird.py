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


JUMP_SOUND: Optional[pygame.mixer.Sound] = None
HIT_SOUND: Optional[pygame.mixer.Sound] = None


@dataclass
class Bird:
    """Player controlled bird."""

    x: float
    y: float
    velocity: float = 0.0
    angle: float = 0.0
    alive: bool = True

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

    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - BIRD_RADIUS), int(self.y - BIRD_RADIUS), BIRD_RADIUS * 2, BIRD_RADIUS * 2)

    def draw(self, surface: pygame.Surface) -> None:
        bird_surface = pygame.Surface((BIRD_RADIUS * 2 + 12, BIRD_RADIUS * 2 + 12), pygame.SRCALPHA)
        center = (bird_surface.get_width() // 2, bird_surface.get_height() // 2)

        body_color = (255, 225, 70)
        belly_color = (255, 245, 180)
        outline_color = (190, 145, 0)
        wing_color = (255, 210, 60)
        wing_outline = (180, 130, 0)

        pygame.draw.circle(bird_surface, body_color, center, BIRD_RADIUS)
        pygame.draw.circle(bird_surface, belly_color, (center[0] - 5, center[1] + 4), BIRD_RADIUS - 6)
        pygame.draw.circle(bird_surface, outline_color, center, BIRD_RADIUS, 3)

        wing_rect = pygame.Rect(0, 0, BIRD_RADIUS + 8, BIRD_RADIUS)
        wing_rect.center = (center[0] - 4, center[1] + 2)
        pygame.draw.ellipse(bird_surface, wing_color, wing_rect)
        pygame.draw.ellipse(bird_surface, wing_outline, wing_rect, 2)

        eye_white = (255, 255, 255)
        eye_black = (0, 0, 0)
        eye_center = (center[0] + 8, center[1] - 6)
        pygame.draw.circle(bird_surface, eye_white, eye_center, 5)
        pygame.draw.circle(bird_surface, eye_black, (eye_center[0] + 1, eye_center[1]), 2)

        beak_color = (255, 170, 0)
        beak_rect = pygame.Rect(0, 0, 16, 10)
        beak_rect.center = (center[0] + BIRD_RADIUS - 4, center[1] + 2)
        beak_points = [
            (beak_rect.right, beak_rect.centery),
            (beak_rect.left, beak_rect.top),
            (beak_rect.left, beak_rect.bottom),
        ]
        pygame.draw.polygon(bird_surface, beak_color, beak_points)

        rotated_bird = pygame.transform.rotozoom(bird_surface, -self.angle, 1)
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

        # Drawing -----------------------------------------------------------------
        screen.fill(BACKGROUND_COLOR)

        # Draw background clouds
        draw_clouds(screen)

        for pipe in pipes:
            pipe.draw(screen)

        base.draw(screen)
        bird.draw(screen)

        draw_text(screen, str(score), 48, (WIDTH // 2, 80))

        if game_over:
            draw_text(screen, "Game Over", 48, (WIDTH // 2, HEIGHT // 2 - 40))
            draw_text(screen, "Press Space to Retry", 24, (WIDTH // 2, HEIGHT // 2 + 10))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


def draw_clouds(surface: pygame.Surface) -> None:
    cloud_color = (255, 255, 255)
    cloud_positions = [
        (50, 80, 60),
        (200, 120, 75),
        (320, 60, 55),
        (120, 200, 70),
    ]
    for x, y, radius in cloud_positions:
        pygame.draw.circle(surface, cloud_color, (x, y), radius)
        pygame.draw.circle(surface, cloud_color, (x + radius // 2, y + 10), radius - 10)
        pygame.draw.circle(surface, cloud_color, (x - radius // 2, y + 10), radius - 10)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pygame.quit()
        sys.exit()
