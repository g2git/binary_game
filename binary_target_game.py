import pygame
import sys
import random
import math
import os

# Get the absolute path of the script
script_path = os.path.abspath(__file__)

# Get the directory of the script
script_dir = os.path.dirname(script_path)

# Change the current working directory to the script's directory
os.chdir(script_dir)

def load_best_stats():
    global best_time, best_final_score
    if os.path.exists(BEST_STATS_FILE):
        with open(BEST_STATS_FILE, "r") as f:
            lines = f.readlines()
            if len(lines) >= 2:
                best_time = float(lines[0].strip())
                best_final_score = int(lines[1].strip())

def save_best_stats(new_time, new_score):
    with open(BEST_STATS_FILE, "w") as f:
        f.write(f"{new_time}\n")
        f.write(f"{new_score}\n")

pygame.init()

# Intro music
pygame.mixer.init()
pygame.mixer.music.load("intro_theme.mp3")  # Or .ogg
pygame.mixer.music.set_volume(0.5)          # Optional: volume 0.0 - 1.0
pygame.mixer.music.play()                 # Input -1 to loop forever

# Screen setup
WIDTH, HEIGHT = 800, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bullseye Shooter")

BEST_STATS_FILE = "best_stats.txt"

load_best_stats()

clock = pygame.time.Clock()

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 100, 255)
BLACK = (0, 0, 0)
PURPLE = (128, 0, 128)
DARK_GRAY = (80, 80, 80)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

# Instructions
show_instructions = True

# Fonts
font = pygame.font.SysFont(None, 36)
big_font = pygame.font.SysFont(None, 72)

# Bullseye
bullseye_x = WIDTH // 2
bullseye_y = HEIGHT // 2
bullseye_speed = 5
bullseye_radius = 15

# Targets
target_radius = 20
normal_speed = 3
num_targets_per_wave = 5
targets = []
sniper_fired = False

# Sniper logic
sniper_fire_time = 4000  # ms
sniper_spawn_time = None

# Binairy number
current_binary = ""
binary_target = 0
current_sum = 0

# Game over
game_over_reason = ""

# Game won
wave_count = 0
you_win = False

# particle list
particles = []
last_firework_time = 0

# Timing trackers
game_start_time = 0
final_time = 0
final_score = 0
score_multiplier = 1.0

# Images
bg = pygame.image.load('bg.jpg')

# Default bests
best_time = None
best_final_score = 0

# Game state
score = 0
wave_time_limit = 10
wave_start_time = pygame.time.get_ticks()
game_over = False
fade_alpha = 0
sniper_killed_player = False  # tracks if sniper caused game over

flashing_text_time = 0  # to track time for flashing text
flash_interval = 500  # Flash interval in milliseconds
show_flash_text = True  # toggle visibility of flashing text

class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.dx = random.uniform(-3, 3)
        self.dy = random.uniform(-6, -2)
        self.color = random.choice([RED, GREEN, BLUE, PURPLE, YELLOW])
        self.life = 60  # frames until it fades out

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.dy += 0.2  # gravity
        self.life -= 1

    def draw(self, surface):
        if self.life > 0:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), 4)


def spawn_normal_target():
    speed = normal_speed
    return {
        "x": random.randint(target_radius, WIDTH - target_radius),
        "y": random.randint(target_radius, HEIGHT - target_radius),
        "dx": random.choice([-1, 1]) * speed,
        "dy": random.choice([-1, 1]) * speed,
        "type": "normal"
    }

def spawn_sniper_target():
    return {
        "x": random.randint(target_radius, WIDTH - target_radius),
        "y": random.randint(target_radius, HEIGHT - target_radius),
        "dx": 0,
        "dy": 0,
        "type": "sniper"
    }

def generate_binary_target():
    value = random.randint(1, 15)  # 4-bit binary (1 to 1111)
    return format(value, '04b'), value

def spawn_wave():
    global wave_start_time, sniper_spawn_time, sniper_fired, current_binary, binary_target, current_sum
    wave_start_time = pygame.time.get_ticks()
    sniper_fired = False
    sniper_spawn_time = None
    current_sum = 0

    # Create binary target
    current_binary, binary_target = generate_binary_target()

    t = []
    for i in range(6):
        target = spawn_normal_target()
        target["number"] = i + 1
        t.append(target)

    if random.random() < 0.5:
        sniper = spawn_sniper_target()
        t.append(sniper)
        sniper_spawn_time = pygame.time.get_ticks()

    return t

def reset_game():
    global score, targets, wave_start_time, sniper_spawn_time, sniper_killed_player, sniper_fired, game_over, bullseye_x, bullseye_y, fade_alpha, game_start_time, wave_count, you_win
    score = 0
    sniper_killed_player = False
    fade_alpha = 0
    bullseye_x = WIDTH // 2
    bullseye_y = HEIGHT // 2
    targets.clear()
    targets.extend(spawn_wave())
    game_over = False
    game_start_time = pygame.time.get_ticks()
    wave_count = 0
    you_win = False


# First wave
targets = spawn_wave()

# Game loop
running = True
while running:
    # Background image
    screen.blit(bg, (0,0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN and game_over and event.key == pygame.K_r:
            reset_game()

    keys = pygame.key.get_pressed()
    
    if keys[pygame.K_RETURN] and show_instructions:
        show_instructions = False
        pygame.mixer.music.stop()  # Stop intro music
        wave_count = 0
        score = 0
        current_sum = 0
        you_win = False
        game_over = False
        sniper_killed_player = False
        game_start_time = pygame.time.get_ticks()
        targets = spawn_wave()
        
    if show_instructions:
        screen.fill(WHITE)
        title = big_font.render("Binary Target Shooter", True, BLACK)
        rule1 = font.render("Shoot targets so their numbers match the 4-digit binary total", True, BLACK)
        rule2 = font.render("If your sum is too high or you run out of time — you lose", True, BLACK)
        rule3 = font.render("Sniper targets must be shot within 4 seconds!", True, RED)
        rule4 = font.render("Complete 8 waves to win", True, BLACK)
        control1 = font.render("Move bullseye with arrow keys", True, DARK_GRAY)
        control2 = font.render("Press SPACE to shoot", True, DARK_GRAY)
        start_msg = font.render("Press ENTER to Start", True, BLUE)

        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))
        screen.blit(rule1, (WIDTH // 2 - rule1.get_width() // 2, 150))
        screen.blit(rule2, (WIDTH // 2 - rule2.get_width() // 2, 190))
        screen.blit(rule3, (WIDTH // 2 - rule3.get_width() // 2, 230))
        screen.blit(rule4, (WIDTH // 2 - rule4.get_width() // 2, 270))
        screen.blit(control1, (WIDTH // 2 - control1.get_width() // 2, 330))
        screen.blit(control2, (WIDTH // 2 - control2.get_width() // 2, 370))
        screen.blit(start_msg, (WIDTH // 2 - start_msg.get_width() // 2, 450))

        pygame.display.flip()
        continue  # Skip rest of game loop until Enter is pressed

    if not game_over:
        # Movement
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            bullseye_x -= bullseye_speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            bullseye_x += bullseye_speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            bullseye_y -= bullseye_speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            bullseye_y += bullseye_speed

        bullseye_x = max(0, min(WIDTH, bullseye_x))
        bullseye_y = max(0, min(HEIGHT, bullseye_y))

        current_time = pygame.time.get_ticks()
        
        # Flashing text logic (500 ms interval)
        if current_time - flashing_text_time > flash_interval:
            show_flash_text = not show_flash_text
            flashing_text_time = current_time

        # Move & draw targets
        for target in targets:
            if target["type"] == "normal":
                # Normal target movement
                target["x"] += target["dx"]
                target["y"] += target["dy"]
                if target["x"] <= target_radius or target["x"] >= WIDTH - target_radius:
                    target["dx"] *= -1
                if target["y"] <= target_radius or target["y"] >= HEIGHT - target_radius:
                    target["dy"] *= -1
            
            # Handle bouncing between normal targets
            for i in range(len(targets)):
                for j in range(i + 1, len(targets)):
                    t1 = targets[i]
                    t2 = targets[j]

                    # Only normal targets bounce
                    if t1["type"] == "normal" and t2["type"] == "normal":
                        dx = t1["x"] - t2["x"]
                        dy = t1["y"] - t2["y"]
                        distance = math.hypot(dx, dy)

                        if distance < 2 * target_radius:
                            # Simple elastic collision: swap velocities
                            t1["dx"], t2["dx"] = t2["dx"], t1["dx"]
                            t1["dy"], t2["dy"] = t2["dy"], t1["dy"]

                            # Move them apart slightly so they don't stick
                            overlap = 2 * target_radius - distance
                            angle = math.atan2(dy, dx)
                            t1["x"] += math.cos(angle) * (overlap / 2)
                            t1["y"] += math.sin(angle) * (overlap / 2)
                            t2["x"] -= math.cos(angle) * (overlap / 2)
                            t2["y"] -= math.sin(angle) * (overlap / 2)

            # Choose color
            color = PURPLE if target["type"] == "sniper" else BLUE
            pygame.draw.circle(screen, color, (int(target["x"]), int(target["y"])), target_radius)

            # Flashing "SNIPER!!!" label
            if target["type"] == "sniper" and show_flash_text:
                sniper_text = font.render("SNIPER!!!", True, RED)
                screen.blit(sniper_text, (target["x"] - sniper_text.get_width() // 2, target["y"] - target_radius - 30))

            # Countdown timer in sniper
            if target["type"] == "sniper" and sniper_spawn_time and not sniper_fired:
                time_left = max(0, (sniper_fire_time - (current_time - sniper_spawn_time)) / 1000)
                timer_text = font.render(f"{time_left:.1f}", True, WHITE)
                screen.blit(timer_text, (target["x"] - timer_text.get_width() // 2, target["y"] - timer_text.get_height() // 2))

            # Draw target number (for normal targets)
            if target["type"] == "normal":
                number_text = font.render(str(target["number"]), True, WHITE)
                screen.blit(number_text, (
                    target["x"] - number_text.get_width() // 2,
                    target["y"] - number_text.get_height() // 2
                ))

        # Sniper fires if alive after 4s
        for target in targets:
            if target["type"] == "sniper" and not sniper_fired:
                if (current_time - sniper_spawn_time) >= sniper_fire_time:
                    sniper_fired = True
                    fade_alpha = 0  # trigger screen fade
                    print("SNIPER FIRED!")
                    break

        # Shooting
        if keys[pygame.K_SPACE]:
            destroyed = []
            for target in targets:
                dist = math.hypot(target["x"] - bullseye_x, target["y"] - bullseye_y)
                if dist < bullseye_radius + target_radius:
                    destroyed.append(target)
                    if target["type"] == "normal":
                        current_sum += target["number"]
                    elif target["type"] == "sniper":
                        score += 3
                    print(f"{target['type'].capitalize()} destroyed!")

            for target in destroyed:
                targets.remove(target)

            # Check if sum exceeds or matches binary target
            if current_sum > binary_target:
                game_over = True
                game_over_reason = "sum_too_high"
                print("Sum exceeded target — Game over!")
            elif current_sum == binary_target:
                wave_count += 1
                print(f"Wave {wave_count} complete!")

                if wave_count >= 8:
                    you_win = True
                    # Spawn particles on win
                    for _ in range(100):
                        px = random.randint(WIDTH // 4, WIDTH * 3 // 4)
                        py = random.randint(HEIGHT // 4, HEIGHT * 3 // 4)
                        particles.append(Particle(px, py))
                    game_over = True
                    final_time = pygame.time.get_ticks() - game_start_time  # total ms
                    time_seconds = final_time / 1000

                    # Example formula: 5.0x if under 20s, 1.0x if over 60s, linear in between
                    if time_seconds <= 20:
                        score_multiplier = 5.0
                    elif time_seconds >= 60:
                        score_multiplier = 1.0
                    else:
                        score_multiplier = 5.0 - ((time_seconds - 20) / 10)  # decrease 0.4x per 10s

                    final_score = int(score * score_multiplier)
                    
                    print("🎉 YOU WIN!")
                    print(f"Time: {time_seconds:.2f}s — Multiplier: {score_multiplier:.2f}")
                    
                    # Update best time and score
                    if best_time is None or final_time < best_time or final_score > best_final_score:
                        best_time = final_time
                        best_final_score = final_score
                        save_best_stats(final_time, final_score)

                else:
                    score += 1  # optional: give score
                    targets = spawn_wave()


        # Timer
        elapsed_time = (current_time - wave_start_time) / 1000
        remaining_time = max(0, wave_time_limit - elapsed_time)

        if remaining_time == 0 and current_sum != binary_target:
            game_over = True
            game_over_reason = "timeout"
            print("Time ran out — Game over!")

        # Draw bullseye
        pygame.draw.circle(screen, RED, (bullseye_x, bullseye_y), 15, 2)
        pygame.draw.circle(screen, RED, (bullseye_x, bullseye_y), 5)
        pygame.draw.line(screen, RED, (bullseye_x - 20, bullseye_y), (bullseye_x + 20, bullseye_y), 2)
        pygame.draw.line(screen, RED, (bullseye_x, bullseye_y - 20), (bullseye_x, bullseye_y + 20), 2)

        # UI
        score_text = font.render(f"Score: {score}", True, BLACK)
        timer_text = font.render(f"Time: {int(remaining_time)}s", True, BLACK)
        binary_text = font.render(f"Target Binary: {current_binary}", True, BLACK)
        sum_text = font.render(f"Current Sum: {current_sum}", True, BLACK)
        wave_text = font.render(f"Waves played: {wave_count}", True, BLACK)
        screen.blit(binary_text, (WIDTH // 2 - 100, 10))
        screen.blit(sum_text, (WIDTH // 2 - 100, 40))
        screen.blit(score_text, (10, 10))
        screen.blit(timer_text, (WIDTH - 150, 10))
        screen.blit(wave_text, (10, 40))

    else:
        # Game Over or Win screen
        if you_win:
            screen.fill((0, 180, 0))  # green background
            win_text = big_font.render("YOU WIN!", True, WHITE)
            base_score_text = font.render(f"Base Score: {score}", True, WHITE)
            time_text = font.render(f"Time: {final_time / 1000:.2f}s", True, WHITE)
            multiplier_text = font.render(f"Multiplier: x{score_multiplier:.2f}", True, WHITE)
            final_score_text = font.render(f"Final Score: {final_score}", True, WHITE)

            best_time_text = font.render(f"Best Time: {best_time / 1000:.2f}s", True, YELLOW)
            best_score_text = font.render(f"Best Score: {best_final_score}", True, YELLOW)

            restart_text = font.render("Press 'R' to Restart", True, WHITE)

            y_base = HEIGHT // 2 - 120
            screen.blit(win_text, (WIDTH // 2 - 140, y_base))
            screen.blit(base_score_text, (WIDTH // 2 - 90, y_base + 40))
            screen.blit(time_text, (WIDTH // 2 - 90, y_base + 70))
            screen.blit(multiplier_text, (WIDTH // 2 - 90, y_base + 100))
            screen.blit(final_score_text, (WIDTH // 2 - 90, y_base + 130))
            screen.blit(best_time_text, (WIDTH // 2 - 90, y_base + 170))
            screen.blit(best_score_text, (WIDTH // 2 - 90, y_base + 200))
            screen.blit(restart_text, (WIDTH // 2 - 130, y_base + 240))

            # 🎆 Animate particles
            current_time = pygame.time.get_ticks()
            if current_time - last_firework_time >= 1000:
                last_firework_time = current_time
                for _ in range(50):
                    px = random.randint(WIDTH // 4, WIDTH * 3 // 4)
                    py = random.randint(HEIGHT // 4, HEIGHT * 3 // 4)
                    particles.append(Particle(px, py))

            for p in particles[:]:
                p.update()
                p.draw(screen)
                if p.life <= 0:
                    particles.remove(p)

        else:
            screen.fill(PURPLE if sniper_killed_player else WHITE)

            game_over_text = big_font.render("Game Over!", True, WHITE if sniper_killed_player else RED)
            score_text = font.render(f"Final Score: {score}", True, WHITE if sniper_killed_player else BLACK)
            restart_text = font.render("Press 'R' to Restart", True, WHITE if sniper_killed_player else BLACK)

            screen.blit(game_over_text, (WIDTH // 2 - 160, HEIGHT // 2 - 100))
            screen.blit(score_text, (WIDTH // 2 - 90, HEIGHT // 2 - 40))

            # Reason for death
            if sniper_killed_player:
                cause_text = font.render("Sniper shot you!", True, WHITE)
                screen.blit(cause_text, (WIDTH // 2 - 110, HEIGHT // 2))
            elif game_over_reason == "sum_too_high":
                cause_text = font.render("Sum was too high!", True, RED)
                screen.blit(cause_text, (WIDTH // 2 - 110, HEIGHT // 2))
            elif game_over_reason == "timeout":
                cause_text = font.render("Time ran out!", True, RED)
                screen.blit(cause_text, (WIDTH // 2 - 100, HEIGHT // 2))

            screen.blit(restart_text, (WIDTH // 2 - 130, HEIGHT // 2 + 60))


    # If sniper fired, fade to purple and end game
    if sniper_fired and not game_over:
        fade_overlay = pygame.Surface((WIDTH, HEIGHT))
        fade_overlay.set_alpha(fade_alpha)
        fade_overlay.fill(PURPLE)
        screen.blit(fade_overlay, (0, 0))
        fade_alpha += 10
        if fade_alpha >= 255:
            game_over = True
            sniper_killed_player = True  # record sniper kill
            game_over_reason = "sniper"
            print("GAME OVER — Sniper shot you!")


    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
