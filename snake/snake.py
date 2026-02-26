"""
Snake Game
~~~~~~~~~~~

A classic snake game implemented in Python using pygame.

Features:
- Smooth gameplay with controls
- Score tracking
- Game over detection
- High score system
- Playable with keyboard

Requirements:
    pip install pygame

Usage:
    python snake/snake.py

Controls:
    ↑ / w  : Move up
    ↓ / s  : Move down
    ← / a  : Move left
    → / d  : Move right
    p      : Pause game
    q      : Quit game
"""

import pygame
import sys
import os
from dataclasses import dataclass, field
from typing import List, Tuple

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRID_SIZE = 20
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE
SNAKE_SPEED = 15

# Colors
COLOR_BG = (0, 0, 0)
COLOR_SNAKE = (0, 255, 0)
COLOR_FOOD = (255, 0, 0)
COLOR_SCORE = (255, 255, 255)
COLOR_GAME_OVER = (255, 0, 0)
COLOR_PAUSE = (0, 0, 0)

@dataclass
class SnakeSegment:
    """Represents a single segment of the snake."""
    x: int
    y: int

@dataclass
class Position:
    """Represents a game position with x, y coordinates."""
    x: int
    y: int

class SnakeGame:
    """Main Snake game class handling all game logic."""

    def __init__(self):
        """Initialize the game."""
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Snake Game")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 24, bold=True)
        self.game_over_font = pygame.font.SysFont("Arial", 48, bold=True)

        # Game state
        self.snake: List[SnakeSegment] = []
        self.food: Position = Position(0, 0)
        self.direction: Position = Position(1, 0)
        self.next_direction: Position = Position(1, 0)
        self.score = 0
        self.high_score = self._load_high_score()
        self.game_over = False
        self.paused = False

        self._reset_game()

    def _load_high_score(self) -> int:
        """Load high score from file."""
        if os.path.exists("snake/highscore.txt"):
            try:
                with open("snake/highscore.txt", "r") as f:
                    return int(f.read())
            except (ValueError, IOError):
                return 0
        return 0

    def _save_high_score(self):
        """Save high score to file."""
        with open("snake/highscore.txt", "w") as f:
            f.write(str(self.high_score))

    def _reset_game(self) -> None:
        """Reset game state for a new round."""
        self.snake = [
            SnakeSegment(GRID_WIDTH // 2, GRID_HEIGHT // 2),
            SnakeSegment(GRID_WIDTH // 2 - 1, GRID_HEIGHT // 2),
            SnakeSegment(GRID_WIDTH // 2 - 2, GRID_HEIGHT // 2),
        ]
        self.direction = Position(1, 0)
        self.next_direction = Position(1, 0)
        self.score = 0
        self.game_over = False
        self.paused = False
        self._spawn_food()

    def _spawn_food(self) -> None:
        """Spawn food at a random position."""
        while True:
            self.food = Position(
                pygame.time.get_ticks() % GRID_WIDTH,
                (pygame.time.get_ticks() // 1000) % GRID_HEIGHT
            )
            # Ensure food doesn't spawn on snake
            if not any(segment.x == self.food.x and segment.y == self.food.y for segment in self.snake):
                break

    def _handle_input(self) -> None:
        """Handle user input."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.game_over:
                    self._reset_game()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()
                elif event.key == pygame.K_p and not self.game_over:
                    self.paused = not self.paused
                elif self.game_over:
                    self._reset_game()
                else:
                    # Update direction based on key press
                    if event.key in (pygame.K_UP, pygame.K_w) and self.direction.y != 1:
                        self.next_direction = Position(0, -1)
                    elif event.key in (pygame.K_DOWN, pygame.K_s) and self.direction.y != -1:
                        self.next_direction = Position(0, 1)
                    elif event.key in (pygame.K_LEFT, pygame.K_a) and self.direction.x != 1:
                        self.next_direction = Position(-1, 0)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d) and self.direction.x != -1:
                        self.next_direction = Position(1, 0)

    def _update(self) -> None:
        """Update game state."""
        if self.paused or self.game_over:
            return

        # Update direction
        self.direction = self.next_direction

        # Calculate new head position
        head_x = self.snake[0].x + self.direction.x
        head_y = self.snake[0].y + self.direction.y

        # Check for wall collision
        if head_x < 0 or head_x >= GRID_WIDTH or head_y < 0 or head_y >= GRID_HEIGHT:
            self._handle_game_over()
            return

        # Check for self collision
        if any(segment.x == head_x and segment.y == head_y for segment in self.snake):
            self._handle_game_over()
            return

        # Add new head
        self.snake.insert(0, SnakeSegment(head_x, head_y))

        # Check for food collision
        if head_x == self.food.x and head_y == self.food.y:
            self.score += 10
            self._update_high_score()
            self._spawn_food()
        else:
            # Remove tail if no food eaten
            self.snake.pop()

    def _handle_game_over(self) -> None:
        """Handle game over state."""
        self.game_over = True
        if self.score > self.high_score:
            self.high_score = self.score
            self._save_high_score()

    def _update_high_score(self) -> None:
        """Update high score if current score is new record."""
        if self.score > self.high_score:
            self.high_score = self.score

    def _draw(self) -> None:
        """Draw game elements."""
        self.screen.fill(COLOR_BG)

        # Draw snake
        for segment in self.snake:
            rect = pygame.Rect(
                segment.x * GRID_SIZE,
                segment.y * GRID_SIZE,
                GRID_SIZE - 2,
                GRID_SIZE - 2
            )
            pygame.draw.rect(self.screen, COLOR_SNAKE, rect)

        # Draw food
        food_rect = pygame.Rect(
            self.food.x * GRID_SIZE,
            self.food.y * GRID_SIZE,
            GRID_SIZE - 2,
            GRID_SIZE - 2
        )
        pygame.draw.rect(self.screen, COLOR_FOOD, food_rect)

        # Draw score and high score
        score_text = self.font.render(f"Score: {self.score}", True, COLOR_SCORE)
        high_score_text = self.font.render(f"High Score: {self.high_score}", True, COLOR_SCORE)
        self.screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 10))
        self.screen.blit(high_score_text, (SCREEN_WIDTH // 2 - high_score_text.get_width() // 2, 40))

        # Draw game over screen
        if self.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))

            game_over_text = self.game_over_font.render("GAME OVER", True, COLOR_GAME_OVER)
            score_msg = self.font.render(f"Final Score: {self.score}", True, COLOR_SCORE)
            high_score_msg = self.font.render(f"High Score: {self.high_score}", True, COLOR_SCORE)
            restart_msg = self.font.render("Click to restart or press any key", True, (150, 150, 150))

            self.screen.blit(
                game_over_text,
                (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, SCREEN_HEIGHT // 2 - 80)
            )
            self.screen.blit(
                score_msg,
                (SCREEN_WIDTH // 2 - score_msg.get_width() // 2, SCREEN_HEIGHT // 2 - 20)
            )
            self.screen.blit(
                high_score_msg,
                (SCREEN_WIDTH // 2 - high_score_msg.get_width() // 2, SCREEN_HEIGHT // 2 + 10)
            )
            self.screen.blit(
                restart_msg,
                (SCREEN_WIDTH // 2 - restart_msg.get_width() // 2, SCREEN_HEIGHT // 2 + 60)
            )

        # Draw pause screen
        if self.paused and not self.game_over:
            pause_text = self.game_over_font.render("PAUSED", True, COLOR_PAUSE)
            self.screen.blit(
                pause_text,
                (SCREEN_WIDTH // 2 - pause_text.get_width() // 2, SCREEN_HEIGHT // 2)
            )

        pygame.display.flip()

    def run(self) -> None:
        """Main game loop."""
        while True:
            self._handle_input()
            self._update()
            self._draw()
            self.clock.tick(SNAKE_SPEED)

if __name__ == "__main__":
    game = SnakeGame()
    game.run()