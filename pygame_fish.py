import pygame
import random
import math
import time
import os
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
RED = (255, 0, 0)
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
    def __init__(self, x, y, fish_type):
        self.base_width = 40
        self.base_height = 30
        self.type = fish_type
        self.hunger = 0
        self.stage = 1
        self.max_stage = 5
        self.size_multiplier = 1.0
        self.food_eaten = 0  # Track total amount of food eaten for growth
        self.food_needed = [2, 3, 4, 5, 6]  # Dynamic food requirement per stage
        self.rect = pygame.Rect(x, y, self.base_width, self.base_height)
        self.speed_x = random.uniform(-FISH_SPEED, FISH_SPEED)
        self.speed_y = random.uniform(-FISH_SPEED * 0.3, FISH_SPEED * 0.3)
        self.target_seaweed = None
        self.last_eat_time = time.time()  # Initialize with current time
        self.eat_cooldown = 5.0  # 5 seconds cooldown between eating
        self.animation_frame = 0
        self.animation_timer = 0
        self.animation_speed = 0.15  # Seconds per frame
        self.animation_frames = []
        self.current_row = 2  # Start with middle row for normal swimming
        
        # Load initial fish animation frames (guppy_baby for stage 1)
        self.load_animation_frames("guppy_baby")
        self.base_image = self.animation_frames[1][0]  # Middle row, first frame as default
        
        # Update image and rect based on initial orientation
        self.image = self.base_image
        self.rect = self.image.get_rect(center=(x, y)) if self.base_image else pygame.Rect(x - 25, y - 15, 50, 30)
        self.current_angle = 0  # Track current rotation angle
        self.is_paused = False

    def load_animation_frames(self, folder_name):
        """Load animation frames from the specified folder"""
        try:
            self.animation_frames = []
            for row in range(1, 4):
                row_frames = []
                for col in range(1, 4):
                    frame_path = f'assets/{folder_name}/row-{row}-column-{col}.png'
                    if not os.path.exists(frame_path):
                        print(f"Warning: Frame not found: {frame_path}")
                        if row == 1 and col == 1:
                            frame = pygame.Surface((50, 30), pygame.SRCALPHA)
                            pygame.draw.rect(frame, (255, 165, 0), (0, 0, 50, 30))
                        else:
                            frame = self.animation_frames[0][0] if self.animation_frames else pygame.Surface((50, 30), pygame.SRCALPHA)
                    else:
                        frame = pygame.image.load(frame_path).convert_alpha()
                    frame = pygame.transform.scale(frame, (int(50 * self.size_multiplier), int(30 * self.size_multiplier)))
                    row_frames.append(frame)
                self.animation_frames.append(row_frames)
        except Exception as e:
            print(f"Error loading {folder_name} images: {e}")
            self.base_image = None
            self.animation_frames = []
            fallback = pygame.Surface((50, 30), pygame.SRCALPHA)
            pygame.draw.rect(fallback, (255, 165, 0), (0, 0, 50, 30))
            self.base_image = fallback
            self.animation_frames = [[fallback for _ in range(3)] for _ in range(3)]

    def update(self, dt):
        # Update animation
        if self.animation_frames:
            self.animation_timer += dt
            if self.animation_timer >= self.animation_speed:
                self.animation_timer = 0
                self.animation_frame = (self.animation_frame + 1) % 3
                
                # Select row based on vertical movement
                if self.speed_y < -0.2:
                    target_row = 0
                elif self.speed_y > 0.2:
                    target_row = 2
                else:
                    target_row = 1
                
                # Smoothly transition between rows
                if target_row != self.current_row:
                    if target_row > self.current_row:
                        self.current_row = min(2, self.current_row + 1)
                    else:
                        self.current_row = max(0, self.current_row - 1)
                
                self.base_image = self.animation_frames[self.current_row][self.animation_frame]
        
        # Hunger increases based on stage
        self.hunger += dt * (0.5 + (self.stage - 1) * 0.125)

        # Aquarium-like movement
        if not hasattr(self, 'pause_timer'):
            self.pause_timer = 0
        if not hasattr(self, 'swim_duration'):
            self.swim_duration = random.uniform(2.0, 5.0)
        if not hasattr(self, 'pause_duration'):
            self.pause_duration = random.uniform(1.0, 3.0)
        if not hasattr(self, 'is_paused'):
            self.is_paused = False

        self.pause_timer += dt
        if self.is_paused:
            if self.pause_timer > self.pause_duration:
                self.is_paused = False
                self.pause_timer = 0
                self.swim_duration = random.uniform(2.0, 5.0)
                self.speed_x = random.uniform(-FISH_SPEED, FISH_SPEED)
                self.speed_y = random.uniform(-FISH_SPEED * 0.3, FISH_SPEED * 0.3)
        else:
            if self.pause_timer > self.swim_duration:
                self.is_paused = True
                self.pause_timer = 0
                self.pause_duration = random.uniform(1.0, 3.0)
                self.speed_x = 0
                self.speed_y = 0

        # Hunger behavior: move towards seaweed if hungry
        if self.hunger > 3 and self.target_seaweed:
            self.is_paused = False
            
            dx = self.target_seaweed.rect.centerx - self.rect.centerx
            dy = self.target_seaweed.rect.centery - self.rect.centery
            dist = math.hypot(dx, dy)
            
            if dist > 0:
                if not hasattr(self, 'target_speed_x'):
                    self.target_speed_x = 0
                    self.target_speed_y = 0
                    self.search_offset = 0
                
                if dist < 80:
                    self.search_offset = math.sin(time.time() * 1.5) * 20
                    dx += self.search_offset
                
                speed_factor = min(1.0, dist / 200.0) + 0.3
                desired_speed_x = (dx / dist) * FISH_SPEED * speed_factor
                desired_speed_y = (dy / dist) * FISH_SPEED * 0.3 * speed_factor
                
                wave_factor = math.sin(time.time() * 2.0) * 0.08
                desired_speed_y += wave_factor
                
                lerp_factor = 0.08 if dist > 100 else 0.15
                self.target_speed_x += (desired_speed_x - self.target_speed_x) * lerp_factor
                self.target_speed_y += (desired_speed_y - self.target_speed_y) * lerp_factor
                
                approach_factor = min(1.0, (dist - 20) / 100.0)
                approach_factor = max(0.2, approach_factor)
                self.speed_x = self.target_speed_x * approach_factor
                self.speed_y = self.target_speed_y * approach_factor
                
                random_scale = min(1.0, dist / 150.0) * 0.03
                self.speed_x += random.uniform(-random_scale, random_scale)
                self.speed_y += random.uniform(-random_scale * 0.5, random_scale * 0.5)
        else:
            if not self.is_paused and random.random() < 0.01:
                self.speed_x = random.uniform(-FISH_SPEED, FISH_SPEED)
                self.speed_y = random.uniform(-FISH_SPEED * 0.3, FISH_SPEED * 0.3)

        # Rotate fish based on movement direction
        if self.speed_x != 0 or self.speed_y != 0:
            movement_angle = math.degrees(math.atan2(-self.speed_y, abs(self.speed_x)))
            
            if abs(self.speed_y) < 0.1:
                target_angle = 0
            else:
                target_angle = max(min(movement_angle, 30), -30)
            
            if not hasattr(self, 'current_angle'):
                self.current_angle = target_angle
            else:
                self.current_angle += (target_angle - self.current_angle) * 0.15
            
            if self.base_image:
                flipped_image = pygame.transform.flip(self.base_image, self.speed_x < 0, False)
                rotation_angle = -self.current_angle if self.speed_x < 0 else self.current_angle
                self.image = pygame.transform.rotate(flipped_image, rotation_angle)
                self.rect = self.image.get_rect(center=self.rect.center)
        else:
            if self.base_image and hasattr(self, 'current_angle'):
                flipped_image = pygame.transform.flip(self.base_image, self.speed_x < 0 if hasattr(self, 'speed_x') else False, False)
                self.image = pygame.transform.rotate(flipped_image, self.current_angle)
                self.rect = self.image.get_rect(center=self.rect.center)

        # Update position
        base_speed = 0.5
        if self.hunger > 3 and self.target_seaweed:
            target_speed = 0.8 + (self.hunger * 0.03)
        else:
            target_speed = base_speed + (math.sin(time.time() * 0.5) * 0.1)
        
        size_factor = 1.0 + (1.0 - min(self.stage / 4, 1.0)) * 0.3
        target_speed *= size_factor
        
        if not hasattr(self, 'current_speed'):
            self.current_speed = target_speed
        else:
            self.current_speed += (target_speed - self.current_speed) * 0.1
        
        if not hasattr(self, 'movement_timer'):
            self.movement_timer = 0
            self.speed_variation = 1.0
        
        self.movement_timer += dt
        if self.movement_timer > random.uniform(0.8, 1.2):
            self.movement_timer = 0
            self.speed_variation = random.uniform(0.85, 1.15)
        
        effective_speed = self.current_speed * self.speed_variation
        
        self.rect.x += self.speed_x * effective_speed * 60 * dt
        self.rect.y += self.speed_y * effective_speed * 60 * dt
        
        # Boundary checks
        if self.rect.left < 0:
            self.rect.left = 0
            self.speed_x = abs(self.speed_x) * 0.8
        elif self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
            self.speed_x = -abs(self.speed_x) * 0.8
        if self.rect.top < 0:
            self.rect.top = 0
            self.speed_y = abs(self.speed_y) * 0.8
        elif self.rect.bottom > SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT
            self.speed_y = -abs(self.speed_y) * 0.8

    def update_orientation(self):
        if self.speed_x > 0:
            self.image = pygame.transform.flip(self.base_image, True, False)
            self.image = pygame.transform.scale(self.image, (self.rect.width, self.rect.height))
        else:
            self.image = pygame.transform.scale(self.base_image, (self.rect.width, self.rect.height))

        angle = 0
        if self.speed_y > 0.5:
            angle = -10
        elif self.speed_y < -0.5:
            angle = 10
        if angle != self.current_angle:
            self.image = pygame.transform.rotate(self.image, angle)
            self.current_angle = angle

    def scatter(self):
        self.speed_x = random.uniform(-FISH_SPEED * 2, FISH_SPEED * 2)
        self.speed_y = random.uniform(-FISH_SPEED * 2, FISH_SPEED * 2)

    def grow(self):
        if self.stage < self.max_stage and self.food_eaten >= self.food_needed[self.stage - 1]:
            self.stage += 1
            self.size_multiplier = 1.0 + (self.stage - 1) * 0.3
            print(f"Fish grew to stage {self.stage}! Size multiplier: {self.size_multiplier}")
            folder = "guppy" if self.stage >= 2 else "guppy_baby"
            self.load_animation_frames(folder)
            self.base_image = self.animation_frames[self.current_row][self.animation_frame]
            center = self.rect.center
            self.rect.size = (int(50 * self.size_multiplier), int(30 * self.size_multiplier))
            self.rect.center = center

    def eat_seaweed(self, seaweed):
        current_time = time.time()
        time_since_last_eat = current_time - self.last_eat_time
        if time_since_last_eat >= self.eat_cooldown:
            self.last_eat_time = current_time
            self.hunger = 0  # Fully reset hunger
            self.food_eaten += 1
            print(f"Fish ate seaweed! Type: {self.type}, Stage: {self.stage}, Food eaten: {self.food_eaten}, Hunger: {self.hunger}")
            self.grow()
            return True
        else:
            print(f"Fish can't eat yet. Time since last eat: {time_since_last_eat:.2f}/{self.eat_cooldown}, Hunger: {self.hunger}")
            return False

    def draw(self, surface):
        if self.image:
            center = self.rect.center
            surface.blit(self.image, self.image.get_rect(center=center))
        else:
            pygame.draw.rect(surface, FISH_COLORS[self.type], self.rect)

# Seaweed class
class Seaweed:
    def __init__(self, x, y):
        self.width = 10
        self.height = 20
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.color = GREEN

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)

# Button class
class Button:
    def __init__(self, x, y, width, height, text):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text

    def draw(self, surface):
        pygame.draw.rect(surface, (50, 50, 50), self.rect)
        text = font.render(self.text, True, WHITE)
        surface.blit(text, (self.rect.x + 10, self.rect.y + 10))

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
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Aquarium Game")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        
        # Game state
        self.coins = 20
        self.fish_list = []
        self.seaweed_list = []
        self.shop_items = {
            "Guppy": 8,
            "Seaweed": 3,
        }
        self.selected_item = None
        self.is_selling_mode = False
        self.fish_to_sell = []
        self.visitor_count = 0
        self.visitor_income_rate = 0.1
        self.last_visitor_update = 0.0
        self.seaweed_areas = [(100, 100), (200, 400), (600, 150), (700, 450), (400, 200)]
        self.current_area = 0
        self.shop_open = False
        self.sell_menu_open = False
        self.fish_details_open = False
        self.selected_fish = None
        self.auto_feed = False
        self.show_hunger_bar = True
        self.settings_open = False
        
        # Game control
        self.is_paused = False
        self.time_scale = 1.0
        
        # UI elements
        self.shop_button = Button(SCREEN_WIDTH - 100, 10, 90, 40, "Shop")
        self.settings_button = Button(SCREEN_WIDTH - 100, 60, 90, 40, "Settings")
        self.pause_button = Button(SCREEN_WIDTH - 100, 110, 90, 40, "Pause")
        self.speed_1x_button = Button(SCREEN_WIDTH - 100, 160, 50, 40, "1x")
        self.speed_3x_button = Button(SCREEN_WIDTH - 150, 160, 50, 40, "3x")
        self.speed_6x_button = Button(SCREEN_WIDTH - 200, 160, 50, 40, "6x")
        
        # Seaweed quantity prompt UI
        self.seaweed_quantity_prompt = False
        self.seaweed_quantity_input = ""
        self.confirm_button = Button(360, 370, 90, 40, "Confirm")
        self.cancel_button = Button(460, 370, 90, 40, "Cancel")
        
        # Button rectangles for shop UI
        self.guppy_btn = None
        self.seaweed_btn = None
        self.sell_mode_btn = None
        self.close_btn = None
        self.auto_feed_btn = None

    def update(self, dt):
        if self.is_paused:
            return
        
        scaled_dt = dt * self.time_scale
        
        dead_fish = [fish for fish in self.fish_list if fish.hunger >= 150 and not self.seaweed_list]
        for fish in dead_fish:
            self.fish_list.remove(fish)
            self.coins = max(0, self.coins - 5)
            print(f"Fish died of hunger! -5 coins, Hunger was: {fish.hunger}, Stage: {fish.stage}")

        targeted_seaweed = set(fish.target_seaweed for fish in self.fish_list if fish.target_seaweed)
        seaweed_counts = {sw: sum(1 for f in self.fish_list if f.target_seaweed == sw) for sw in targeted_seaweed}

        for fish in self.fish_list:
            if fish.hunger > 60 and self.seaweed_list:
                nearest = min(self.seaweed_list,
                            key=lambda s: ((s.rect.centerx - fish.rect.centerx)**2 +
                                         (s.rect.centery - fish.rect.centery)**2)**0.5 +
                                         (seaweed_counts.get(s, 0) * 50))
                fish.target_seaweed = nearest
            else:
                fish.target_seaweed = None
                
            fish.update(scaled_dt)
            
            for seaweed in self.seaweed_list[:]:
                fish_rect_expanded = fish.rect.inflate(20, 20)
                if fish_rect_expanded.colliderect(seaweed.rect):
                    if fish.eat_seaweed(seaweed):
                        self.seaweed_list.remove(seaweed)
                        fish.target_seaweed = None
                        next_food_needed = sum(fish.food_needed[:fish.stage])
                        print(f"Fish ate seaweed! Type: {fish.type}, Stage: {fish.stage}, Food eaten: {fish.food_eaten}/{next_food_needed}, Hunger: {fish.hunger}")
                        break

        # Updated income calculation with more pronounced stage scaling
        base_income = 0.02
        total_income = 0
        for fish in self.fish_list:
            # Income scales more noticeably with stage: 1x, 2x, 4x, 7x, 11x
            stage_multiplier = 1 + (fish.stage - 1) * (fish.stage / 2)
            total_income += base_income * stage_multiplier
        self.coins += total_income * scaled_dt

        if self.auto_feed:
            for fish in self.fish_list:
                if fish.hunger > 60 and not self.seaweed_list:
                    self.buy_seaweed(1)

    def draw(self, surface):
        surface.fill(BLUE)

        for seaweed in self.seaweed_list:
            seaweed.draw(surface)

        for fish in self.fish_list:
            fish.draw(surface)
            if self.is_selling_mode:
                sell_price = 3 * (1.0 + (fish.stage - 1) * 0.4)
                price_text = self.font.render(f"${sell_price:.1f}", True, WHITE)
                surface.blit(price_text, (fish.rect.centerx - 10, fish.rect.top - 20))
            elif self.show_hunger_bar:
                max_hunger = 120
                hunger_ratio = 1 - (min(fish.hunger, max_hunger) / max_hunger)
                bar_width = int(fish.rect.width * hunger_ratio)
                bar_color = (0, 255, 0) if hunger_ratio > 0.5 else (255, 255, 0) if hunger_ratio > 0.25 else (255, 0, 0)
                
                hunger_bar_rect = pygame.Rect(
                    fish.rect.x,
                    fish.rect.y - 7,
                    bar_width,
                    3
                )
                pygame.draw.rect(surface, bar_color, hunger_bar_rect)

        # Draw shop button
        pygame.draw.rect(surface, (0, 128, 0), self.shop_button.rect)
        shop_text = self.font.render("Shop", True, WHITE)
        surface.blit(shop_text, (self.shop_button.rect.x + 10, self.shop_button.rect.y + 10))

        self.settings_button.text = "Settings"
        self.settings_button.draw(surface)
        self.pause_button.text = "Play" if self.is_paused else "Pause"
        self.pause_button.draw(surface)
        self.speed_1x_button.draw(surface)
        self.speed_3x_button.draw(surface)
        self.speed_6x_button.draw(surface)

        base_income = 0.02
        total_income_rate = 0
        for fish in self.fish_list:
            stage_multiplier = 1 + (fish.stage - 1) * (fish.stage / 2)
            total_income_rate += base_income * stage_multiplier
        stats = [
            f"Fish: {len(self.fish_list)}",
            f"Seaweed: {len(self.seaweed_list)}",
            f"Coins: {int(self.coins)}",
            f"Income: {total_income_rate:.2f}/s",
            f"Speed: {self.time_scale}x"
        ]
        for i, stat in enumerate(stats):
            text = self.font.render(stat, True, WHITE)
            surface.blit(text, (10, 10 + i * 40))

        if self.shop_open:
            pygame.draw.rect(surface, (50, 50, 50, 200), (SCREEN_WIDTH // 4, SCREEN_HEIGHT // 4, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            title_text = self.font.render("Shop - Buy Items", True, WHITE)
            surface.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, SCREEN_HEIGHT // 4 + 20))
            
            guppy_btn = pygame.Rect(260, 220, 280, 40)
            guppy_color = GREEN if self.coins >= self.shop_items["Guppy"] else RED
            pygame.draw.rect(surface, guppy_color, guppy_btn)
            guppy_text = self.font.render(f"Buy Guppy ({self.shop_items['Guppy']} coins)", True, WHITE)
            surface.blit(guppy_text, (guppy_btn.x + 20, guppy_btn.y + 10))
            
            # Draw seaweed buttons with different quantities
            seaweed_cost = self.shop_items["Seaweed"]
            
            # 1 Seaweed button
            one_btn = pygame.Rect(260, 270, 80, 40)
            one_color = GREEN if self.coins >= seaweed_cost * 1 else RED
            pygame.draw.rect(surface, one_color, one_btn)
            one_text = self.font.render("1", True, WHITE)
            surface.blit(one_text, (one_btn.x + 30, one_btn.y + 10))
            
            # 10 Seaweed button
            ten_btn = pygame.Rect(350, 270, 80, 40)
            ten_color = GREEN if self.coins >= seaweed_cost * 10 else RED
            pygame.draw.rect(surface, ten_color, ten_btn)
            ten_text = self.font.render("10", True, WHITE)
            surface.blit(ten_text, (ten_btn.x + 25, ten_btn.y + 10))
            
            # 100 Seaweed button
            hundred_btn = pygame.Rect(440, 270, 100, 40)
            hundred_color = GREEN if self.coins >= seaweed_cost * 100 else RED
            pygame.draw.rect(surface, hundred_color, hundred_btn)
            hundred_text = self.font.render("100", True, WHITE)
            surface.blit(hundred_text, (hundred_btn.x + 25, hundred_btn.y + 10))
            
            # Auto Feed button
            auto_feed_btn = pygame.Rect(260, 320, 280, 40)
            auto_feed_color = GREEN if self.auto_feed else RED
            pygame.draw.rect(surface, auto_feed_color, auto_feed_btn)
            auto_feed_text = self.font.render("Auto Feed", True, WHITE)
            surface.blit(auto_feed_text, (auto_feed_btn.x + 20, auto_feed_btn.y + 10))
            
            # Seaweed cost label
            cost_text = self.font.render(f"Seaweed: {seaweed_cost} coins each", True, WHITE)
            surface.blit(cost_text, (260, 370))
            
            sell_mode_btn = pygame.Rect(260, 420, 280, 40)
            pygame.draw.rect(surface, (255, 165, 0), sell_mode_btn)
            sell_mode_text = self.font.render("Toggle Sell Mode", True, WHITE)
            surface.blit(sell_mode_text, (sell_mode_btn.x + 20, sell_mode_btn.y + 10))
            
            close_btn = pygame.Rect(260, 470, 280, 40)
            pygame.draw.rect(surface, RED, close_btn)
            close_text = self.font.render("Close Shop", True, WHITE)
            surface.blit(close_text, (close_btn.x + 20, close_btn.y + 10))

            # Store button rects for event handling
            self.guppy_btn = guppy_btn
            self.seaweed_buttons = {
                1: one_btn,
                10: ten_btn,
                100: hundred_btn
            }
            self.auto_feed_btn = auto_feed_btn
            self.sell_mode_btn = sell_mode_btn
            self.close_btn = close_btn
        elif self.sell_menu_open:
            pygame.draw.rect(surface, BLACK, (250, 200, 300, 300))
            pygame.draw.rect(surface, WHITE, (250, 200, 300, 300), 2)
            sell_text = self.font.render("Sell Fish", True, WHITE)
            surface.blit(sell_text, (400, 210))
            
            self.fish_to_sell = []
            y_offset = 250
            for fish in self.fish_list:
                btn_rect = pygame.Rect(260, y_offset, 280, 40)
                self.fish_to_sell.append(btn_rect)
                pygame.draw.rect(surface, GREEN, btn_rect)
                fish_text = self.font.render(f"Sell {fish.type} (Stage {fish.stage})", True, WHITE)
                surface.blit(fish_text, (btn_rect.x + 20, btn_rect.y + 10))
                y_offset += 50
            
            close_btn = pygame.Rect(260, 470, 280, 40)
            pygame.draw.rect(surface, RED, close_btn)
            close_text = self.font.render("Close", True, WHITE)
            surface.blit(close_text, (close_btn.x + 20, close_btn.y + 10))
        
        elif self.fish_details_open and self.selected_fish:
            pygame.draw.rect(surface, BLACK, (250, 200, 300, 200))
            pygame.draw.rect(surface, WHITE, (250, 200, 300, 200), 2)
            details_text = self.font.render("Fish Details", True, WHITE)
            surface.blit(details_text, (400, 210))
            
            type_text = self.font.render(f"Type: {self.selected_fish.type}", True, WHITE)
            surface.blit(type_text, (260, 240))
            stage_text = self.font.render(f"Stage: {self.selected_fish.stage}", True, WHITE)
            surface.blit(stage_text, (260, 270))
            hunger_text = self.font.render(f"Hunger: {int(self.selected_fish.hunger)}", True, WHITE)
            surface.blit(hunger_text, (260, 300))
            food_text = self.font.render(f"Food Eaten: {self.selected_fish.food_eaten}", True, WHITE)
            surface.blit(food_text, (260, 330))
            
            close_btn = pygame.Rect(260, 370, 280, 40)
            pygame.draw.rect(surface, RED, close_btn)
            close_text = self.font.render("Close", True, WHITE)
            surface.blit(close_text, (close_btn.x + 20, close_btn.y + 10))
        elif self.settings_open:
            pygame.draw.rect(surface, (50, 50, 50, 200), (SCREEN_WIDTH // 4, SCREEN_HEIGHT // 4, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            title_text = self.font.render("Settings", True, WHITE)
            surface.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, SCREEN_HEIGHT // 4 + 20))
            
            # Hunger bar toggle button
            hunger_bar_btn = pygame.Rect(260, 220, 280, 40)
            hunger_bar_color = GREEN if self.show_hunger_bar else RED
            pygame.draw.rect(surface, hunger_bar_color, hunger_bar_btn)
            hunger_bar_text = self.font.render("Show Hunger Bar", True, WHITE)
            surface.blit(hunger_bar_text, (hunger_bar_btn.x + 20, hunger_bar_btn.y + 10))
            
            # Close button
            close_btn = pygame.Rect(260, 270, 280, 40)
            pygame.draw.rect(surface, RED, close_btn)
            close_text = self.font.render("Close Settings", True, WHITE)
            surface.blit(close_text, (close_btn.x + 20, close_btn.y + 10))

            self.hunger_bar_btn = hunger_bar_btn
            self.close_settings_btn = close_btn

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            if self.shop_open:
                # Handle Seaweed buttons
                if self.seaweed_buttons:
                    for quantity, btn in self.seaweed_buttons.items():
                        if btn.collidepoint(mouse_pos):
                            try:
                                quantity = int(quantity)
                                if quantity > 0:
                                    self.buy_seaweed(quantity)
                                    self.shop_open = False
                                    return True
                            except ValueError:
                                print(f"Invalid quantity: {quantity}")
                # Buy Guppy
                if self.guppy_btn and self.guppy_btn.collidepoint(mouse_pos):
                    self.selected_item = "Guppy"
                    self.buy_fish("Guppy")
                    return True
                # Auto Feed
                if self.auto_feed_btn and self.auto_feed_btn.collidepoint(mouse_pos):
                    self.auto_feed = not self.auto_feed
                    return True
                # Toggle Selling Mode
                elif self.sell_mode_btn and self.sell_mode_btn.collidepoint(mouse_pos):
                    self.is_selling_mode = not self.is_selling_mode
                    self.shop_open = False
                    return True
                # Close Shop
                elif self.close_btn and self.close_btn.collidepoint(mouse_pos):
                    self.shop_open = False
                    return True
            elif self.sell_menu_open:
                for i, btn_rect in enumerate(self.fish_to_sell):
                    if btn_rect.collidepoint(mouse_pos):
                        if i < len(self.fish_list):
                            self.selected_fish = self.fish_list[i]
                            self.sell_fish(self.selected_fish)
                            self.sell_menu_open = False
                            return True
                close_btn = pygame.Rect(260, 470, 280, 40)
                if close_btn.collidepoint(mouse_pos):
                    self.sell_menu_open = False
                    return True
            elif self.fish_details_open:
                close_btn = pygame.Rect(260, 370, 280, 40)
                if close_btn.collidepoint(mouse_pos):
                    self.fish_details_open = False
                    self.selected_fish = None
                    return True
            elif self.settings_open:
                if self.hunger_bar_btn and self.hunger_bar_btn.collidepoint(mouse_pos):
                    self.show_hunger_bar = not self.show_hunger_bar
                    return True
                elif self.close_settings_btn and self.close_settings_btn.collidepoint(mouse_pos):
                    self.settings_open = False
                    return True
            else:
                if self.shop_button.rect.collidepoint(mouse_pos):
                    self.shop_open = True
                    return True
                elif self.settings_button.rect.collidepoint(mouse_pos):
                    self.settings_open = True
                    return True
                elif self.pause_button.rect.collidepoint(mouse_pos):
                    self.is_paused = not self.is_paused
                    return True
                elif self.speed_1x_button.rect.collidepoint(mouse_pos):
                    self.time_scale = 1.0
                    return True
                elif self.speed_3x_button.rect.collidepoint(mouse_pos):
                    self.time_scale = 3.0
                    return True
                elif self.speed_6x_button.rect.collidepoint(mouse_pos):
                    self.time_scale = 6.0
                    return True
                elif self.is_selling_mode:
                    for i, fish in enumerate(self.fish_list):
                        if fish.rect.collidepoint(mouse_pos):
                            self.selected_fish = fish
                            self.sell_fish(fish)
                            return True
                else:
                    for fish in self.fish_list:
                        if fish.rect.collidepoint(mouse_pos):
                            self.selected_fish = fish
                            self.fish_details_open = True
                            return True
        return True

    def buy_seaweed(self, quantity):
        total_cost = quantity * self.shop_items["Seaweed"]
        if self.coins >= total_cost:
            self.coins -= total_cost
            for _ in range(quantity):
                x, y = self.seaweed_areas[self.current_area]
                self.seaweed_list.append(Seaweed(x, y))
                self.current_area = (self.current_area + 1) % len(self.seaweed_areas)
            print(f"Bought {quantity} seaweed for {total_cost} coins")
        else:
            print(f"Not enough coins for {quantity} seaweed. Need {total_cost}, have {self.coins}")

    def buy_fish(self, type_):
        cost = 8 if type_ == "Guppy" else 12
        if self.coins >= cost:
            self.coins -= cost
            self.fish_list.append(Fish(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, type_))

    def sell_fish(self, fish):
        base_price = 3
        sell_price = base_price * (1.0 + (fish.stage - 1) * 0.4)
        self.coins += sell_price
        self.fish_list.remove(fish)
        print(f"Sold fish for {sell_price:.1f} coins! Stage: {fish.stage}")
        if not hasattr(self, 'fish_sold'):
            self.fish_sold = 0
        self.fish_sold += 1
        if self.fish_sold == 1:
            print("Achievement Unlocked: First Sale")
        elif self.fish_sold == 10:
            print("Achievement Unlocked: Fishmonger")
        elif self.fish_sold == 50:
            print("Achievement Unlocked: Aquarium Tycoon")
        self.fish_details_open = False
        self.selected_fish = None

# Create game instance
game = AquariumGame()

# Game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        game.handle_event(event)

    dt = clock.tick(FPS) / 1000.0
    game.update(dt)
    game.draw(screen)
    pygame.display.flip()

pygame.quit()
sys.exit()