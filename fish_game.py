import pygame
import random
import sys

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
FISH_SPEED = 3
VISITOR_UPDATE_INTERVAL = 1.0  # Seconds
HUNGER_CHECK_INTERVAL = 10.0  # Seconds
FISH_BREED_AGE = 20.0  # Seconds

# Colors
BLUE = (0, 105, 148)  # Aquarium background
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (150, 150, 150)
YELLOW = (255, 215, 0)
GREEN = (50, 205, 50)
FISH_COLORS = {
    "Guppy": (255, 69, 0),  # Orange
    "Tetra": (255, 215, 0),  # Yellow
}

# Set up the display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Aquarium Game")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)  # Default font for text

# Fish class
class Fish:
    def __init__(self, type_, x, y):
        self.type = type_
        self.width = 30
        self.height = 15
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.color = FISH_COLORS[type_]
        self.speed_x = random.uniform(-FISH_SPEED, FISH_SPEED)
        self.speed_y = random.uniform(-FISH_SPEED, FISH_SPEED)
        self.age = 0.0  # Age in seconds
        self.hunger = 0.0  # Hunger level

    def update(self, dt):
        # Update age
        self.age += dt

        # Move the fish
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y

        # Bounce off the screen edges
        if self.rect.left < 0:
            self.speed_x = abs(self.speed_x)
        if self.rect.right > SCREEN_WIDTH:
            self.speed_x = -abs(self.speed_x)
        if self.rect.top < 0:
            self.speed_y = abs(self.speed_y)
        if self.rect.bottom > SCREEN_HEIGHT:
            self.speed_y = -abs(self.speed_y)

        # Randomly change direction occasionally
        if random.random() < 0.01:  # 1% chance per frame
            self.speed_x = random.uniform(-FISH_SPEED, FISH_SPEED)
            self.speed_y = random.uniform(-FISH_SPEED, FISH_SPEED)

    def scatter(self):
        # Scatter in a random direction
        self.speed_x = random.uniform(-FISH_SPEED * 2, FISH_SPEED * 2)
        self.speed_y = random.uniform(-FISH_SPEED * 2, FISH_SPEED * 2)

    def draw(self, surface):
        # Draw fish body
        pygame.draw.rect(surface, self.color, self.rect)
        
        # Draw hunger bar
        max_hunger = 10
        hunger_ratio = 1 - (min(self.hunger, max_hunger) / max_hunger)
        bar_width = int(self.rect.width * hunger_ratio)
        bar_color = (0, 255, 0) if hunger_ratio > 0.5 else (255, 255, 0) if hunger_ratio > 0.25 else (255, 0, 0)
        
        # Hunger bar positioning
        hunger_bar_rect = pygame.Rect(
            self.rect.x, 
            self.rect.y - 7,  # 5 pixels above fish + 2px padding
            bar_width,
            3  # Bar height
        )
        pygame.draw.rect(surface, bar_color, hunger_bar_rect)

# Seaweed class
class Seaweed:
    def __init__(self, x, y):
        self.width = 10
        self.height = 20
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.color = GREEN

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)

# Decoration class
class Decoration:
    def __init__(self, type_, x, y):
        self.type = type_
        self.width = 40
        self.height = 40
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.color = GRAY

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)

# Shop button class
class ShopButton:
    def __init__(self, x, y):
        self.width = 40
        self.height = 40
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.color = YELLOW

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)

# Game class
class AquariumGame:
    def __init__(self):
        self.coins = 100.0
        self.fish_list = []
        self.seaweed_list = []
        self.decorations = []
        self.visitor_count = 0
        self.visitor_income_rate = 0.1
        self.last_visitor_update = 0.0
        self.last_hunger_check = 0.0
        self.fish_sold = 0
        self.selected_fish = None
        self.shop_open = False
        self.fish_details_open = False
        self.seaweed_quantity = 1
        self.seaweed_areas = [
            (SCREEN_WIDTH // 4, SCREEN_HEIGHT - 50),
            (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50),
            (SCREEN_WIDTH * 3 // 4, SCREEN_HEIGHT - 50)
        ]
        self.current_area = 0

        # Initialize shop button
        self.shop_button = ShopButton(SCREEN_WIDTH - 60, 20)

    def update(self, dt):
        # Check for starved fish
        dead_fish = [fish for fish in self.fish_list if fish.hunger >= 10]
        for fish in dead_fish:
            self.fish_list.remove(fish)
            self.coins = max(0, self.coins - 5)  # Penalty for dead fish
            print(f"Fish died of hunger! -5 coins")

        # Update fish
        for fish in self.fish_list:
            fish.update(dt)
            fish.hunger += dt  # Increase hunger over time
            
            # Check for nearby seaweed
            for seaweed in self.seaweed_list[:]:
                if fish.rect.colliderect(seaweed.rect):
                    self.seaweed_list.remove(seaweed)
                    fish.hunger = 0  # Reset hunger when eating

        # Visitor income (simplified)
        fish_count = len(self.fish_list)
        base_income = 0.05
        self.coins += base_income * (fish_count ** 1.5) * dt

    def draw(self, surface):
        # Fill background
        surface.fill(BLUE)

        # Draw seaweed
        for seaweed in self.seaweed_list:
            seaweed.draw(surface)

        # Draw fish
        for fish in self.fish_list:
            fish.draw(surface)

        # Draw decorations
        for decoration in self.decorations:
            decoration.draw(surface)

        # Draw shop button
        self.shop_button.draw(surface)

        # Draw aquarium statistics
        income_rate = 0.05 * (len(self.fish_list) ** 1.5)
        stats = [
            f"Fish: {len(self.fish_list)}",
            f"Seaweed: {len(self.seaweed_list)}",
            f"Coins: {self.coins:.0f}",
            f"Income: {income_rate:.2f}/sec"
        ]
        for i, text in enumerate(stats):
            stat_text = font.render(text, True, WHITE)
            surface.blit(stat_text, (10, 10 + i * 30))

        # Draw shop menu
        if self.shop_open:
            pygame.draw.rect(surface, GRAY, (250, 200, 300, 200))
            pygame.draw.rect(surface, BLACK, (250, 200, 300, 200), 2)
            
            # Draw shop options
            shop_text = font.render("Buy Fish (10 coins)", True, BLACK)
            surface.blit(shop_text, (270, 220))
            shop_text = font.render("Buy Seaweed (5 coins)", True, BLACK)
            surface.blit(shop_text, (270, 280))
            shop_text = font.render("Close Shop", True, BLACK)
            surface.blit(shop_text, (270, 340))

        # Draw fish details if open
        if self.fish_details_open:
            if self.selected_fish:
                fish = self.selected_fish
                stage = "Baby" if fish.age < 5 else "Adult"
                can_sell = stage == "Adult"
                sell_price = 20.0 if fish.type == "Guppy" else 35.0

                # Draw fish details background
                details_rect = pygame.Rect(250, 200, 300, 200)
                pygame.draw.rect(surface, GRAY, details_rect)
                pygame.draw.rect(surface, BLACK, details_rect, 2)

                # Draw fish details
                details = [
                    f"{fish.type} Details",
                    f"Stage: {stage}",
                    f"Age: {fish.age:.1f}s",
                    f"Hunger: {10 - fish.hunger:.1f}s remaining"
                ]
                for i, text in enumerate(details):
                    detail_text = font.render(text, True, BLACK)
                    surface.blit(detail_text, (270, 220 + i * 30))

                # Draw sell button if applicable
                if can_sell:
                    sell_text = font.render(f"Sell for {sell_price} coins", True, BLACK)
                    sell_rect = sell_text.get_rect(topleft=(270, 310))
                    if sell_rect.collidepoint(pygame.mouse.get_pos()):
                        pygame.draw.rect(surface, WHITE, sell_rect.inflate(10, 10), 2)
                        if pygame.mouse.get_pressed()[0]:
                            self.sell_fish(fish)
                    surface.blit(sell_text, sell_rect)

                # Draw close button
                close_text = font.render("Close", True, BLACK)
                close_rect = close_text.get_rect(topleft=(270, 350))
                if close_rect.collidepoint(pygame.mouse.get_pos()):
                    pygame.draw.rect(surface, WHITE, close_rect.inflate(10, 10), 2)
                    if pygame.mouse.get_pressed()[0]:
                        self.fish_details_open = False
                        self.selected_fish = None
                surface.blit(close_text, close_rect)

    def buy_seaweed(self):
        if self.coins >= 5:
            self.coins -= 5
            # Cycle through predefined positions
            x, y = self.seaweed_areas[self.current_area]
            self.seaweed_list.append(Seaweed(x, y))
            self.current_area = (self.current_area + 1) % len(self.seaweed_areas)

    def buy_fish(self, type_):
        cost = 10 if type_ == "Guppy" else 15
        if self.coins >= cost:
            self.coins -= cost
            self.fish_list.append(Fish(type_, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))

    def buy_decoration(self, type_):
        if self.coins >= 20:
            self.coins -= 20
            self.decorations.append(Decoration(type_, SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60))

    def sell_fish(self, fish):
        sell_price = 20.0 if fish.type == "Guppy" else 35.0
        self.coins += sell_price
        self.fish_list.remove(fish)
        self.fish_sold += 1
        # Simple achievement system (print to console for now)
        if self.fish_sold == 1:
            print("Achievement Unlocked: First Sale")
        elif self.fish_sold == 10:
            print("Achievement Unlocked: Fish Seller")
        self.fish_details_open = False
        self.selected_fish = None

# Create game instance
game = AquariumGame()

# Game loop
running = True
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            
            # Shop button click
            if game.shop_button.rect.collidepoint(mouse_pos):
                game.shop_open = not game.shop_open
            
            # Shop menu interactions
            elif game.shop_open:
                # Buy Fish
                if pygame.Rect(250, 220, 300, 40).collidepoint(mouse_pos):
                    game.buy_fish("Guppy")
                # Buy Seaweed
                elif pygame.Rect(250, 280, 300, 40).collidepoint(mouse_pos):
                    game.buy_seaweed()
                # Close Shop
                elif pygame.Rect(250, 340, 300, 40).collidepoint(mouse_pos):
                    game.shop_open = False
            
            # Fish selection
            elif not game.shop_open and not game.fish_details_open:
                for fish in game.fish_list:
                    if fish.rect.collidepoint(mouse_pos):
                        game.selected_fish = fish
                        game.fish_details_open = True
                        break
                else:
                    # If no fish is clicked, scatter all fish
                    for fish in game.fish_list:
                        fish.scatter()

    # Update
    dt = clock.tick(FPS) / 1000.0  # Delta time in seconds
    game.update(dt)

    # Draw
    game.draw(screen)

    # Update the display
    pygame.display.flip()

# Quit Pygame
pygame.quit()
sys.exit()