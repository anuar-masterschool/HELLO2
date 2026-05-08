import pygame
import sys
from enum import Enum

# ==================== CONSTANTS ====================
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 700
FPS = 30

# Colors
COLOR_BG = (20, 20, 30)
COLOR_GRID = (100, 100, 120)
COLOR_GRID_HIGHLIGHT = (200, 200, 220)
COLOR_FLY = (255, 50, 50)
COLOR_TEXT = (200, 200, 200)
COLOR_TITLE = (100, 200, 255)

# Cube parameters
CUBE_SIZE = 3
TILE_SIZE = 40
GRID_START_X = 250
GRID_START_Y = 100
LAYER_HEIGHT = 160

# ==================== CLASSES ====================

class GameState(Enum):
    PLAYING = 1
    GAME_OVER = 2


class Cube3D:
    """Manages the 3x3x3 cube state and fly position."""
    
    def __init__(self):
        self.fly_pos = [1, 1, 1]  # Center position: (x, y, z)
    
    def move_fly(self, dx, dy, dz):
        """
        Attempt to move the fly by (dx, dy, dz).
        Returns True if move is valid (within bounds), False if out of bounds.
        """
        new_x = self.fly_pos[0] + dx
        new_y = self.fly_pos[1] + dy
        new_z = self.fly_pos[2] + dz
        
        # Check bounds
        if not (0 <= new_x < CUBE_SIZE and 0 <= new_y < CUBE_SIZE and 0 <= new_z < CUBE_SIZE):
            return False  # Out of bounds - player loses
        
        # Valid move
        self.fly_pos = [new_x, new_y, new_z]
        return True
    
    def get_position(self):
        """Return current fly position as tuple."""
        return tuple(self.fly_pos)
    
    def reset(self):
        """Reset fly to center position."""
        self.fly_pos = [1, 1, 1]


class Game:
    """Manages game state, turns, and players."""
    
    def __init__(self, num_players=2):
        self.cube = Cube3D()
        self.num_players = num_players
        self.state = GameState.PLAYING
        self.last_move = None  # Display last movement made
        self.last_move_timer = 0
        self.show_help = False
        self.help_timer = 0
        self.out_timer = 0  # Timer for showing "you are out" message
    
    def move_fly(self, dx, dy, dz, move_name):
        """
        Process a fly movement.
        Returns True if move was valid, False if player loses.
        """
        if self.cube.move_fly(dx, dy, dz):
            # Valid move - display the movement
            self.last_move = move_name
            self.last_move_timer = 2000  # Show for 2 seconds
            return True
        else:
            # Invalid move - player loses, show "out" message temporarily
            self.last_move = f"{move_name} - OUT!"
            self.out_timer = 2000  # Show "you are out" for 2 seconds
            return False
    
    def restart(self):
        """Restart the game."""
        self.cube.reset()
        self.state = GameState.PLAYING
        self.last_move = None
        self.last_move_timer = 0
        self.out_timer = 0
    
    def toggle_help(self):
        """Toggle help display."""
        self.show_help = not self.show_help
        self.help_timer = 3000 if self.show_help else 0
    
    def update(self, dt):
        """Update game state (handle timers)."""
        if self.last_move_timer > 0:
            self.last_move_timer -= dt
            if self.last_move_timer <= 0:
                self.last_move = None
        
        if self.out_timer > 0:
            self.out_timer -= dt
            if self.out_timer <= 0:
                # Auto-continue: clear the out message and state
                self.out_timer = 0
        
        if self.show_help and self.help_timer > 0:
            self.help_timer -= dt
            if self.help_timer <= 0:
                self.show_help = False


class Renderer:
    """Handles all drawing operations."""
    
    def __init__(self, surface, font_small, font_large):
        self.surface = surface
        self.font_small = font_small
        self.font_large = font_large
    
    def cube_to_screen(self, x, y, z):
        """Convert 3D cube coordinates to 2D screen coordinates (layered grid view)."""
        # Each layer is positioned vertically
        # y is the height (0=bottom, 1=middle, 2=top)
        grid_x = GRID_START_X + x * TILE_SIZE
        grid_y = GRID_START_Y + y * LAYER_HEIGHT + z * TILE_SIZE
        return (grid_x, grid_y)
    
    def draw_grid(self):
        """Draw the 3x3x3 cube as three stacked 3x3 layers."""
        for y in range(CUBE_SIZE):
            # Draw layer label
            label = f"Layer {y}"
            label_text = self.font_small.render(label, True, COLOR_TITLE)
            self.surface.blit(label_text, (GRID_START_X, GRID_START_Y + y * LAYER_HEIGHT - 20))
            
            # Draw 3x3 grid for this layer
            for x in range(CUBE_SIZE):
                for z in range(CUBE_SIZE):
                    screen_x, screen_y = self.cube_to_screen(x, y, z)
                    rect = pygame.Rect(screen_x, screen_y, TILE_SIZE, TILE_SIZE)
                    pygame.draw.rect(self.surface, COLOR_GRID, rect, 2)
    
    def draw_fly(self, fly_pos):
        """Draw the fly at its current position."""
        x, y, z = fly_pos
        screen_x, screen_y = self.cube_to_screen(x, y, z)
        rect = pygame.Rect(screen_x, screen_y, TILE_SIZE, TILE_SIZE)
        pygame.draw.rect(self.surface, COLOR_FLY, rect)
        pygame.draw.rect(self.surface, COLOR_FLY, rect, 2)
    
    def draw_ui(self, fly_pos):
        """Draw UI elements: prompt and controls."""
        # Prompt
        prompt_text = self.font_large.render("please move", True, COLOR_TITLE)
        self.surface.blit(prompt_text, (20, 20))
        
        # Controls at bottom
        controls = [
            "Q=Up   W=Forward   E=Back",
            "A=Left   S=Down   D=Right",
            "H=Position   ESC=Quit"
        ]
        for i, control in enumerate(controls):
            text = self.font_small.render(control, True, COLOR_TEXT)
            self.surface.blit(text, (20, WINDOW_HEIGHT - 70 + i * 18))
    
    def draw_help(self, fly_pos):
        """Draw help overlay with current fly position."""
        x, y, z = fly_pos
        pos_text = self.font_large.render(f"Position: x={x} y={y} z={z}", True, COLOR_TITLE)
        text_rect = pos_text.get_rect(center=(WINDOW_WIDTH // 2, 30))
        self.surface.blit(pos_text, text_rect)
    
    def draw_last_move(self, last_move):
        """Draw the last move made."""
        if last_move:
            # Check if it's an out move
            is_out = "OUT!" in last_move
            color = (255, 100, 100) if is_out else COLOR_TITLE
            
            move_text = self.font_large.render(last_move, True, color)
            text_rect = move_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
            self.surface.blit(move_text, text_rect)
    
    def draw_game_over(self):
        """Draw game over screen."""
        # Semi-transparent overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(100)
        overlay.fill((0, 0, 0))
        self.surface.blit(overlay, (0, 0))
        
        # Game over text
        loser_text = self.font_large.render("you are out", True, (255, 100, 100))
        loser_rect = loser_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
        self.surface.blit(loser_text, loser_rect)
    
    def render(self, game):
        """Main render function."""
        self.surface.fill(COLOR_BG)
        
        # Draw cube grid and fly only when help is active
        if game.show_help:
            self.draw_grid()
            self.draw_fly(game.cube.get_position())
        
        # Draw UI
        self.draw_ui(game.cube.get_position())
        
        # Draw last move (movement or out)
        self.draw_last_move(game.last_move)
        
        # Draw "you are out" overlay if timer is active
        if game.out_timer > 0:
            self.draw_game_over()
        
        # Draw help if active
        if game.show_help:
            self.draw_help(game.cube.get_position())
        
        pygame.display.flip()


# ==================== MAIN GAME LOOP ====================

def main():
    """Main game loop."""
    pygame.init()
    
    # Setup display
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("La Mosquita - 3x3x3 Cube Game")
    clock = pygame.time.Clock()
    
    # Setup fonts
    font_small = pygame.font.Font(None, 20)
    font_large = pygame.font.Font(None, 36)
    
    # Initialize game and renderer
    game = Game(num_players=2)
    renderer = Renderer(screen, font_small, font_large)
    
    # Key-to-movement mapping
    key_to_move = {
        pygame.K_q: (0, 1, 0, "up"),
        pygame.K_w: (0, 0, 1, "forward"),
        pygame.K_e: (0, 0, -1, "back"),
        pygame.K_a: (-1, 0, 0, "left"),
        pygame.K_s: (0, -1, 0, "down"),
        pygame.K_d: (1, 0, 0, "right"),
    }
    
    running = True
    while running:
        dt = clock.tick(FPS)
        
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_h:
                    game.toggle_help()
                elif event.key in key_to_move:
                    # Process movement input
                    dx, dy, dz, move_name = key_to_move[event.key]
                    game.move_fly(dx, dy, dz, move_name)
        
        # Update game state
        game.update(dt)
        
        # Render
        renderer.render(game)
    
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
