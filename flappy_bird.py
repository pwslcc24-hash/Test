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
from typing import List, Tuple

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
        # Bird body
        pygame.draw.circle(surface, (255, 255, 0), (int(self.x), int(self.y)), BIRD_RADIUS)
        # Eye
        pygame.draw.circle(surface, (0, 0, 0), (int(self.x + 6), int(self.y - 5)), 4)
        # Beak triangle rotated based on angle
        beak_length = 12
        direction = pygame.Vector2(1, 0).rotate(-self.angle)
        tip = pygame.Vector2(self.x, self.y) + direction * (BIRD_RADIUS + beak_length)
        base_top = pygame.Vector2(self.x, self.y) + direction.rotate(90) * 4
        base_bottom = pygame.Vector2(self.x, self.y) + direction.rotate(-90) * 4
        pygame.draw.polygon(surface, (255, 165, 0), [tip, base_top, base_bottom])


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
        color = (34, 139, 34)
        pygame.draw.rect(surface, color, self.top_rect())
        pygame.draw.rect(surface, color, self.bottom_rect())
        # pipe edges
        pygame.draw.rect(surface, (0, 100, 0), self.top_rect(), 4)
        pygame.draw.rect(surface, (0, 100, 0), self.bottom_rect(), 4)


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


def main() -> None:
    os.environ.setdefault("SDL_VIDEO_CENTERED", "1")
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Flappy Bird")
    clock = pygame.time.Clock()

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

            if check_collision(bird, pipes):
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
