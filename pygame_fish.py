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
    _id_counter = 0  # Class-level counter for unique IDs

    def __init__(self, game, x, y, fish_type="Guppy", stage=1):
        pygame.sprite.Sprite.__init__(self)
        self.id = Fish._id_counter  # Assign unique ID
        Fish._id_counter += 1
        self.game = game
        self.type = fish_type
        self.stage = stage
        self.max_stage = 5
        self.gender = random.choice(["male", "female"])
        self.hunger = 0
        self.food_eaten = 0
        self.food_needed = [3, 5, 7, 10, 0]
        self.breeding_partner = None
        self.collision_start_time = 0
        self.breed_timer = 0
        self.is_fertilized = False
        self.last_breed_time = time.time()
        self.breed_cooldown = 600  # 10 minutes
        self.breed_delay = 120  # 2 minutes
        self.required_collision_time = 2
        self.base_width = 40
        self.base_height = 30
        self.size_multiplier = 1.0 + (self.stage - 1) * 0.2
        self.speed_x = random.uniform(-FISH_SPEED, FISH_SPEED) or FISH_SPEED
        self.speed_y = random.uniform(-FISH_SPEED * 0.3, FISH_SPEED * 0.3)
        self.rect = pygame.Rect(x, y, self.base_width, self.base_height)
        self.last_eat_time = time.time()
        self.eat_cooldown = 5.0
        self.animation_frame = 0
        self.animation_timer = 0
        self.animation_speed = 0.15
        self.animation_frames = []
        self.current_row = 2
        self.current_angle = 0
        self.is_paused = False
        self.time_scale = 1.0
        # Feeding and movement attributes from provided code
        self.target_seaweed = None
        self.is_hungry = False
        self.pause_timer = 0
        self.swim_duration = random.uniform(2.0, 5.0)
        self.pause_duration = random.uniform(1.0, 3.0)
        self.current_speed = 0.5
        self.movement_timer = 0
        self.speed_variation = 1.0

        # Load animation frames
        if self.type == "Guppy":
            if self.stage == 1:
                self.load_animation_frames("guppy_baby")
            else:
                folder = "guppy_female" if self.gender == "female" else "guppy"
                self.load_animation_frames(folder)
        else:
            self.load_animation_frames(f"{self.type.lower()}_baby")

        self.base_image = self.animation_frames[1][0] if self.animation_frames else None
        if self.base_image:
            self.image = self.base_image
            self.rect = self.image.get_rect(center=(x, y))
        else:
            self.image = None
            self.rect = pygame.Rect(x - 25, y - 15, 50, 30)

        print(f"Created fish ID {self.id}, Type: {self.type}, Stage: {self.stage}, Gender: {self.gender}")

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
            self.animation_frames = []
            fallback = pygame.Surface((50, 30), pygame.SRCALPHA)
            pygame.draw.rect(fallback, (255, 165, 0), (0, 0, 50, 30))
            self.animation_frames = [[fallback for _ in range(3)] for _ in range(3)]

    def update(self, dt):
        if self.is_paused:
            print(f"Fish ID {self.id} is paused")
            return

        scaled_dt = max(dt * self.time_scale, 0.001)

        # Check for death due to hunger
        if self.hunger >= 150 and not self.game.seaweed_list:
            print(f"Fish ID {self.id} should die: Hunger {self.hunger}")
            self.game.fish_list.remove(self)
            self.game.coins = max(0, self.game.coins - 5)
            return

        # Handle breeding movement
        if self.breeding_partner and self.collision_start_time > 0:
            current_time = time.time()
            collision_duration = current_time - self.collision_start_time

            if collision_duration >= self.required_collision_time:
                if self.gender == "female":
                    self.is_fertilized = True
                    self.breed_timer = self.breed_delay
                self.last_breed_time = current_time
                self.breeding_partner.last_breed_time = current_time
                print(f"Breeding complete for Fish ID {self.id} with Partner ID {self.breeding_partner.id}")
                self.game.breeding_in_progress = False
                self.game.selected_fish_1 = None
                self.game.selected_fish_2 = None
                self.breeding_partner.breeding_partner = None
                self.breeding_partner = None
                self.collision_start_time = 0
                # Resume normal movement
                self.speed_x = random.uniform(-FISH_SPEED, FISH_SPEED) or FISH_SPEED
                self.speed_y = random.uniform(-FISH_SPEED * 0.3, FISH_SPEED * 0.3)
            else:
                dx = self.breeding_partner.rect.centerx - self.rect.centerx
                dy = self.breeding_partner.rect.centery - self.rect.centery
                dist = math.hypot(dx, dy)
                if dist > 5:
                    self.speed_x = (dx / dist) * FISH_SPEED * 0.5
                    self.speed_y = (dy / dist) * FISH_SPEED * 0.5
                else:
                    self.speed_x = 0
                    self.speed_y = 0
        else:
            # Movement logic from provided code
            self.pause_timer += scaled_dt
            if self.pause_timer > self.swim_duration:
                self.pause_timer = 0
                self.swim_duration = random.uniform(2.0, 5.0)
                self.pause_duration = random.uniform(1.0, 3.0)
                if self.is_hungry:
                    self.speed_x = random.uniform(-FISH_SPEED * 0.7, FISH_SPEED * 0.7)
                    self.speed_y = random.uniform(-FISH_SPEED * 0.2, FISH_SPEED * 0.2)
                else:
                    self.speed_x = random.uniform(-FISH_SPEED, FISH_SPEED) or FISH_SPEED
                    self.speed_y = random.uniform(-FISH_SPEED * 0.3, FISH_SPEED * 0.3)
            elif self.pause_timer > self.swim_duration - 1.0:
                self.speed_x *= 0.9
                self.speed_y *= 0.9

            # Move toward seaweed if hungry
            if self.is_hungry and self.target_seaweed:
                dx = self.target_seaweed.rect.centerx - self.rect.centerx
                dy = self.target_seaweed.rect.centery - self.rect.centery
                dist = math.hypot(dx, dy)
                if dist > 5:
                    hunger_speed_boost = min(1.3, 1.0 + (self.hunger - 30) / 70)
                    self.speed_x = (dx / dist) * (FISH_SPEED * 0.7) * hunger_speed_boost
                    self.speed_y = (dy / dist) * (FISH_SPEED * 0.3) * hunger_speed_boost
                else:
                    self.speed_x = 0
                    self.speed_y = 0

            # Speed variation
            base_speed = 0.5
            if self.hunger > 30 and self.target_seaweed:
                target_speed = 0.8 + (self.hunger * 0.03)
            else:
                target_speed = base_speed + (math.sin(time.time() * 0.5) * 0.1)
            size_factor = 1.0 + (1.0 - min(self.stage / 4, 1.0)) * 0.3
            target_speed *= size_factor
            self.current_speed += (target_speed - self.current_speed) * 0.1
            self.movement_timer += scaled_dt
            if self.movement_timer > random.uniform(0.8, 1.2):
                self.movement_timer = 0
                self.speed_variation = random.uniform(0.85, 1.15)
            effective_speed = self.current_speed * self.speed_variation

            # Update position
            self.rect.x += self.speed_x * effective_speed * 60 * scaled_dt
            self.rect.y += self.speed_y * effective_speed * 60 * scaled_dt

            # Boundary checks
            if self.rect.left < 0:
                self.rect.left = 0
                self.speed_x = abs(self.speed_x) * 0.8
                print(f"Fish ID {self.id} hit left boundary")
            elif self.rect.right > SCREEN_WIDTH:
                self.rect.right = SCREEN_WIDTH
                self.speed_x = -abs(self.speed_x) * 0.8
                print(f"Fish ID {self.id} hit right boundary")
            if self.rect.top < 0:
                self.rect.top = 0
                self.speed_y = abs(self.speed_y) * 0.8
                print(f"Fish ID {self.id} hit top boundary")
            elif self.rect.bottom > SCREEN_HEIGHT:
                self.rect.bottom = SCREEN_HEIGHT
                self.speed_y = -abs(self.speed_y) * 0.8
                print(f"Fish ID {self.id} hit bottom boundary")

        # Animation updates
        if self.animation_frames:
            self.animation_timer += scaled_dt
            if self.animation_timer >= self.animation_speed:
                self.animation_timer = 0
                self.animation_frame = (self.animation_frame + 1) % 3
                if self.speed_y < -0.2:
                    target_row = 0
                elif self.speed_y > 0.2:
                    target_row = 2
                else:
                    target_row = 1
                if target_row != self.current_row:
                    self.current_row = target_row
                self.base_image = self.animation_frames[self.current_row][self.animation_frame]

        # Update hunger
        self.hunger += scaled_dt * (0.5 + (self.stage - 1) * 0.125)
        print(f"Fish ID {self.id} hunger updated to {self.hunger}")

        # Update breeding timer
        if self.breed_timer > 0:
            self.breed_timer -= scaled_dt

        # Update image and rotation
        if self.speed_x != 0 or self.speed_y != 0:
            movement_angle = math.degrees(math.atan2(-self.speed_y, abs(self.speed_x)))
            target_angle = 0 if abs(self.speed_y) < 0.1 else max(min(movement_angle, 30), -30)
            self.current_angle += (target_angle - self.current_angle) * 0.15
        if self.base_image:
            flipped_image = pygame.transform.flip(self.base_image, self.speed_x < 0, False)
            rotation_angle = -self.current_angle if self.speed_x < 0 else self.current_angle
            self.image = pygame.transform.rotate(flipped_image, rotation_angle)
            self.rect = self.image.get_rect(center=self.rect.center)

    def collide_with_fish(self, other_fish):
        """Handle collision only for selected breeding pairs"""
        current_time = time.time()
        if not (self.game.selected_fish_1 and self.game.selected_fish_2):
            return

        if not (self == self.game.selected_fish_1 and other_fish == self.game.selected_fish_2 or
                self == self.game.selected_fish_2 and other_fish == self.game.selected_fish_1):
            return

        can_breed = (
            self.stage == 5 and
            other_fish.stage == 5 and
            self.gender != other_fish.gender and
            current_time - self.last_breed_time >= self.breed_cooldown and
            current_time - other_fish.last_breed_time >= other_fish.breed_cooldown
        )

        if can_breed:
            if self.collision_start_time == 0:
                self.collision_start_time = current_time
                self.breeding_partner = other_fish
                other_fish.breeding_partner = self
                other_fish.collision_start_time = current_time
                print(f"Breeding collision started: Fish ID {self.id} with Fish ID {other_fish.id}")

    def spawn_babies(self):
        """Spawn baby fish when breeding timer is complete"""
        current_time = time.time()
        if (
            self.stage == 5 and
            self.gender == "female" and
            self.is_fertilized and
            self.breed_timer <= 0
        ):
            num_babies = random.randint(3, 6)
            babies = []
            for _ in range(num_babies):
                baby_x = self.rect.centerx + random.uniform(-50, 50)
                baby_y = self.rect.centery + random.uniform(-50, 50)
                baby = Fish(self.game, baby_x, baby_y, "Guppy")
                babies.append(baby)
            self.is_fertilized = False
            self.breed_timer = self.breed_delay
            self.last_breed_time = current_time
            print(f"Fish ID {self.id} spawned {num_babies} babies")
            return babies
        return []

    def scatter(self):
        self.speed_x = random.uniform(-FISH_SPEED * 2, FISH_SPEED * 2) or FISH_SPEED
        self.speed_y = random.uniform(-FISH_SPEED * 2, FISH_SPEED * 2)
        print(f"Fish ID {self.id} scattered")

    def grow(self):
        """Increase the fish's stage if it has eaten enough food"""
        if self.stage < self.max_stage and self.food_eaten >= self.food_needed[self.stage - 1]:
            self.stage += 1
            self.size_multiplier = 1.0 + (self.stage - 1) * 0.2
            self.food_eaten = 0
            if self.type == "Guppy":
                if self.stage == 1:
                    self.load_animation_frames("guppy_baby")
                else:
                    folder = "guppy_female" if self.gender == "female" else "guppy"
                    self.load_animation_frames(folder)
            else:
                self.load_animation_frames(f"{self.type.lower()}")
            self.base_image = self.animation_frames[1][0] if self.animation_frames else None
            if self.base_image:
                self.image = self.base_image
                self.rect = self.image.get_rect(center=self.rect.center)
            else:
                self.image = None
                self.rect = pygame.Rect(self.rect.x - 25, self.rect.y - 15, 50, 30)
            print(f"Fish ID {self.id} grew to stage {self.stage}")

    def eat_seaweed(self, seaweed):
        """Eat seaweed on collision if cooldown allows"""
        current_time = time.time()
        time_since_last_eat = current_time - self.last_eat_time
        if time_since_last_eat >= self.eat_cooldown:
            self.last_eat_time = current_time
            self.hunger = 0
            self.food_eaten += 1
            print(f"Fish ID {self.id} ate seaweed! Stage: {self.stage}, Food eaten: {self.food_eaten}")
            self.grow()
            return True
        return False

    def draw(self, surface):
        if self.image:
            center = self.rect.center
            surface.blit(self.image, self.image.get_rect(center=center))
        else:
            pygame.draw.rect(surface, FISH_COLORS[self.type], self.rect)

    def clear_breeding_state(self):
        """Clear breeding-related state"""
        if self.breeding_partner:
            self.breeding_partner.breeding_partner = None
            self.breeding_partner.collision_start_time = 0
        self.breeding_partner = None
        self.collision_start_time = 0
        self.speed_x = random.uniform(-FISH_SPEED, FISH_SPEED) or FISH_SPEED
        self.speed_y = random.uniform(-FISH_SPEED * 0.3, FISH_SPEED * 0.3)

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

# BreedButton class
class BreedButton:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 90, 40)
        self.text = "Breed"
        self.active = False

    def draw(self, surface):
        color = GREEN if self.active else (100, 100, 100)
        pygame.draw.rect(surface, color, self.rect)
        text = font.render(self.text, True, WHITE)
        surface.blit(text, (self.rect.x + 10, self.rect.y + 10))

# ShopButton class
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
        self.coins = 200
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
        self.is_paused = False
        self.time_scale = 1.0
        self.selected_fish_1 = None
        self.selected_fish_2 = None
        self.breeding_in_progress = False
        self.shop_button = Button(SCREEN_WIDTH - 100, 10, 90, 40, "Shop")
        self.breed_button = BreedButton(SCREEN_WIDTH - 100, 210)
        self.settings_button = Button(SCREEN_WIDTH - 100, 60, 90, 40, "Settings")
        self.pause_button = Button(SCREEN_WIDTH - 100, 110, 90, 40, "Pause")
        self.speed_1x_button = Button(SCREEN_WIDTH - 100, 160, 50, 40, "1x")
        self.speed_3x_button = Button(SCREEN_WIDTH - 150, 160, 50, 40, "3x")
        self.speed_6x_button = Button(SCREEN_WIDTH - 200, 160, 50, 40, "6x")
        self.seaweed_quantity_prompt = False
        self.seaweed_quantity_input = ""
        self.confirm_button = Button(360, 370, 90, 40, "Confirm")
        self.cancel_button = Button(460, 370, 90, 40, "Cancel")
        self.guppy_btn = None
        self.seaweed_btn = None
        self.sell_mode_btn = None
        self.close_btn = None
        self.auto_feed_btn = None

    def update(self, dt):
        if self.is_paused:
            return

        scaled_dt = max(dt * self.time_scale, 0.001)

        # Update fish
        for fish in self.fish_list[:]:
            # Feeding and targeting from provided code
            if fish.hunger > 30 and self.seaweed_list:
                targeted_seaweed = set(f.target_seaweed for f in self.fish_list if f.target_seaweed)
                seaweed_counts = {sw: sum(1 for f in self.fish_list if f.target_seaweed == sw) for sw in targeted_seaweed}
                nearest = min(self.seaweed_list,
                              key=lambda s: ((s.rect.centerx - fish.rect.centerx)**2 +
                                            (s.rect.centery - fish.rect.centery)**2)**0.5 * 0.7 +
                                            (seaweed_counts.get(s, 0) * 30))
                fish.target_seaweed = nearest
                fish.is_hungry = True
            else:
                fish.target_seaweed = None
                fish.is_hungry = False

            fish.update(scaled_dt)

            # Check for seaweed collisions
            for seaweed in self.seaweed_list[:]:
                fish_rect_expanded = fish.rect.inflate(20, 20)
                if fish_rect_expanded.colliderect(seaweed.rect):
                    if fish.eat_seaweed(seaweed):
                        self.seaweed_list.remove(seaweed)
                        fish.target_seaweed = None
                        next_food_needed = sum(fish.food_needed[:fish.stage])
                        print(f"Fish ID {fish.id} ate seaweed! Type: {fish.type}, Stage: {fish.stage}, Food eaten: {fish.food_eaten}/{next_food_needed}")
                        break

            # Check for breeding collisions
            if self.breeding_in_progress and fish.breeding_partner:
                dx = fish.rect.centerx - fish.breeding_partner.rect.centerx
                dy = fish.rect.centery - fish.breeding_partner.rect.centery
                distance = math.hypot(dx, dy)
                if distance <= 50:
                    fish.collide_with_fish(fish.breeding_partner)

            # Spawn babies
            if fish.gender == "female" and fish.is_fertilized and fish.breed_timer <= 0:
                new_babies = fish.spawn_babies()
                self.fish_list.extend(new_babies)

        # Update coins
        base_income = 0.02
        total_income = sum(base_income * (1 + (fish.stage - 1) * (fish.stage / 2)) for fish in self.fish_list)
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

        self.breed_button.active = (self.selected_fish_1 and self.selected_fish_2 and
                                   not self.breeding_in_progress and
                                   self.selected_fish_1.stage == 5 and
                                   self.selected_fish_2.stage == 5 and
                                   self.selected_fish_1.gender != self.selected_fish_2.gender)
        self.breed_button.draw(surface)

        if self.selected_fish_1:
            pygame.draw.rect(surface, (0, 255, 0), self.selected_fish_1.rect, 2)
        if self.selected_fish_2:
            pygame.draw.rect(surface, (255, 255, 0), self.selected_fish_2.rect, 2)

        base_income = 0.02
        total_income_rate = sum(base_income * (1 + (fish.stage - 1) * (fish.stage / 2)) for fish in self.fish_list)
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
            
            seaweed_cost = self.shop_items["Seaweed"]
            one_btn = pygame.Rect(260, 270, 80, 40)
            one_color = GREEN if self.coins >= seaweed_cost * 1 else RED
            pygame.draw.rect(surface, one_color, one_btn)
            one_text = self.font.render("1", True, WHITE)
            surface.blit(one_text, (one_btn.x + 30, one_btn.y + 10))
            
            ten_btn = pygame.Rect(350, 270, 80, 40)
            ten_color = GREEN if self.coins >= seaweed_cost * 10 else RED
            pygame.draw.rect(surface, ten_color, ten_btn)
            ten_text = self.font.render("10", True, WHITE)
            surface.blit(ten_text, (ten_btn.x + 25, ten_btn.y + 10))
            
            hundred_btn = pygame.Rect(440, 270, 100, 40)
            hundred_color = GREEN if self.coins >= seaweed_cost * 100 else RED
            pygame.draw.rect(surface, hundred_color, hundred_btn)
            hundred_text = self.font.render("100", True, WHITE)
            surface.blit(hundred_text, (hundred_btn.x + 25, hundred_btn.y + 10))
            
            auto_feed_btn = pygame.Rect(260, 320, 280, 40)
            auto_feed_color = GREEN if self.auto_feed else RED
            pygame.draw.rect(surface, auto_feed_color, auto_feed_btn)
            auto_feed_text = self.font.render("Auto Feed", True, WHITE)
            surface.blit(auto_feed_text, (auto_feed_btn.x + 20, auto_feed_btn.y + 10))
            
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
            
            hunger_bar_btn = pygame.Rect(260, 220, 280, 40)
            hunger_bar_color = GREEN if self.show_hunger_bar else RED
            pygame.draw.rect(surface, hunger_bar_color, hunger_bar_btn)
            hunger_bar_text = self.font.render("Show Hunger Bar", True, WHITE)
            surface.blit(hunger_bar_text, (hunger_bar_btn.x + 20, hunger_bar_btn.y + 10))
            
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
                if self.guppy_btn and self.guppy_btn.collidepoint(mouse_pos):
                    self.selected_item = "Guppy"
                    self.buy_fish("Guppy")
                    return True
                if self.auto_feed_btn and self.auto_feed_btn.collidepoint(mouse_pos):
                    self.auto_feed = not self.auto_feed
                    return True
                elif self.sell_mode_btn and self.sell_mode_btn.collidepoint(mouse_pos):
                    self.is_selling_mode = not self.is_selling_mode
                    self.shop_open = False
                    return True
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
                elif self.breed_button.rect.collidepoint(mouse_pos) and self.breed_button.active:
                    if self.selected_fish_1 and self.selected_fish_2:
                        self.breeding_in_progress = True
                        self.selected_fish_1.breeding_partner = self.selected_fish_2
                        self.selected_fish_2.breeding_partner = self.selected_fish_1
                        self.selected_fish_1.collision_start_time = time.time()
                        self.selected_fish_2.collision_start_time = time.time()
                        print(f"Breeding initiated: Fish ID {self.selected_fish_1.id} with Fish ID {self.selected_fish_2.id}")
                    return True
                else:
                    for fish in self.fish_list:
                        if fish.rect.collidepoint(mouse_pos):
                            if fish.stage == 5:
                                if not self.selected_fish_1:
                                    self.selected_fish_1 = fish
                                    print(f"Selected Fish ID {fish.id} ({fish.gender})")
                                elif not self.selected_fish_2 and fish != self.selected_fish_1:
                                    self.selected_fish_2 = fish
                                    print(f"Selected Fish ID {fish.id} ({fish.gender})")
                                    if self.selected_fish_1.gender == self.selected_fish_2.gender:
                                        print(f"Same gender: Fish ID {self.selected_fish_1.id} and ID {self.selected_fish_2.id}")
                                        self.selected_fish_1.scatter()
                                        self.selected_fish_2.scatter()
                                        self.selected_fish_1 = None
                                        self.selected_fish_2 = None
                                elif fish == self.selected_fish_1:
                                    self.selected_fish_1 = None
                                    print(f"Unselected Fish ID {fish.id}")
                                elif fish == self.selected_fish_2:
                                    self.selected_fish_2 = None
                                    print(f"Unselected Fish ID {fish.id}")
                            else:
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
            self.fish_list.append(Fish(self, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, type_))

    def sell_fish(self, fish):
        base_price = 3
        sell_price = base_price * (1.0 + (fish.stage - 1) * 0.4)
        self.coins += sell_price
        self.fish_list.remove(fish)
        print(f"Sold Fish ID {fish.id} for {sell_price:.1f} coins! Stage: {fish.stage}")
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

game = AquariumGame()

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