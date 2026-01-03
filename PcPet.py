# ======================================
# Imports and Globals
# ======================================
import threading
import sys
import random
import os  # <-- Added this
import numpy as np
import pygame
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw, ImageFont
import ctypes
user32 = ctypes.windll.user32
import ctypes.wintypes

running = True
tray_icon = None
window_visible = True

dragging = False
drag_offset_x = 0
drag_offset_y = 0

TRAY_SIZE = (64, 64)
TRAY_FONT_SIZE = None

# ======================================
# Animations (must be defined early for tray font calculation)
# ======================================
animations = {
    "idle": ["(O ◡ O)"] * 5,
    "red": ["(O = O)🍖", "(O 0 O)🍖", "(O = O)🍖", "(O 0 O)🍖", "(O = O)🍖"],
    "green": ["🫧(O o O)", "(O o O)🫧", "🫧(O o O)", "(O o O)🫧", "🫧(O o O)"],
    "blue": ["(O v O)", "(❤ v ❤)", "(O v O)", "(❤ v ❤)", "(O v O)"],
    "yellow": ["(⭐ o ⭐)", "(🌟 v 🌟)", "(⭐ o ⭐)", "(🌟 o 🌟)", "(⭐ o ⭐)"],
    "purple": ["💤(- 0 -)💤", "💤(- o -)💤", "💤(- 0 -)💤", "💤(- o -)💤", "💤(- 0 -)💤"],
    "orange": ["(O = O)🍬", "(O 0 O)🍬", "(O = O)🍬", "(⭐ v ⭐)", "(⭐ v ⭐)"],
    "hungry_idle": ["(O . O)🍖", "(O o O)🍖", "(O . O)🍖", "(O o O)🍖", "(O . O)🍖"],
    "dirty_idle": ["(O . O)💩", "(O o O)💩", "(O . O)💩", "(O o O)💩", "(O . O)💩"],
    "sleepy_idle": ["(O . O)💤", "(- . -)💤", "(O . O)💤", "(- . -)💤", "(- - -)💤"],
    "sad_idle": ["(- . -)", "(T . T)", "(- . -)", "(T . T)", "(- . -)"],
    "dead": ["(x . x)"] * 5,
}

# ======================================
# Tray Icon Helpers
# ======================================
def compute_tray_font_size():
    global TRAY_FONT_SIZE
    if TRAY_FONT_SIZE is not None:
        return TRAY_FONT_SIZE

    all_texts = [frame for anim in animations.values() for frame in anim]

    for size in range(48, 10, -2):  # Try from large down
        font = None
        for fname in ["seguiemj.ttf", "segoeuiemoji.ttf", "segoeui.ttf"]:
            try:
                font_path = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', fname)
                font = ImageFont.truetype(font_path, size)
                break
            except OSError:
                continue
        if font is None:
            continue

        draw = ImageDraw.Draw(Image.new("RGBA", (1,1)))
        max_w = max_h = 0
        for text in all_texts:
            bbox = draw.textbbox((0, 0), text, font=font)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            max_w = max(max_w, w)
            max_h = max(max_h, h)

        if max_w <= TRAY_SIZE[0] * 0.95 and max_h <= TRAY_SIZE[1] * 0.95:  # small margin
            TRAY_FONT_SIZE = size
            return size

    TRAY_FONT_SIZE = 28  # safe fallback
    return 28

def create_tray_image_from_text(text, size=TRAY_SIZE):
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_size = compute_tray_font_size()
    font = None
    for fname in ["seguiemj.ttf", "segoeuiemoji.ttf", "segoeui.ttf"]:
        try:
            font_path = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', fname)
            font = ImageFont.truetype(font_path, font_size)
            break
        except OSError:
            continue
    if font is None:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = (size[0] - w) / 2
    y = (size[1] - h) / 2
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
    return img

def update_tray_icon_frame(frame_text):
    global tray_icon
    if tray_icon is None:
        return
    try:
        tray_icon.icon = create_tray_image_from_text(frame_text)
    except Exception:
        pass

def toggle_window_visibility(icon=None, item=None):
    global window_visible
    hwnd = pygame.display.get_wm_info()["window"]
    if window_visible:
        user32.ShowWindow(hwnd, 0)  # SW_HIDE
        window_visible = False
    else:
        user32.ShowWindow(hwnd, 5)  # SW_SHOW
        user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002)  # always on top
        window_visible = True

def on_tray_quit(icon, item):
    global running
    running = False
    icon.stop()

def run_tray_icon(initial_frame="(O . O)"):
    global tray_icon
    img = create_tray_image_from_text(initial_frame)
    tray_icon = Icon(
        "ASCII Pet",
        img,
        "ASCII Pet",
        menu=Menu(
            MenuItem("Show/Hide window", toggle_window_visibility),
            MenuItem("Quit", on_tray_quit),
        ),
    )
    tray_icon.run()

# ======================================
# Pygame Setup
# ======================================
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.mixer.init()

WINDOW_W = 360
WINDOW_H = 240
screen = pygame.display.set_mode((WINDOW_W, WINDOW_H), pygame.NOFRAME)
pygame.display.set_caption("ASCII Pet")

hwnd = pygame.display.get_wm_info()["window"]
ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002)

# ======================================
# Fonts and Sounds
# ======================================
font = pygame.font.SysFont("segoe ui emoji", 36)
emoji_font = pygame.font.SysFont("segoe ui emoji", 28)
name_font = pygame.font.SysFont("consolas", 18)
score_font = pygame.font.SysFont("consolas", 18)
label_font = pygame.font.SysFont("consolas", 14)

def generate_beep(freq=600, duration=0.1, volume=0.5):
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = np.sin(freq * 2 * np.pi * t)
    audio = (wave * 32767).astype(np.int16)
    stereo = np.column_stack((audio, audio))
    sound = pygame.sndarray.make_sound(stereo)
    sound.set_volume(volume)
    return sound

button_sound = generate_beep(freq=900, duration=0.06, volume=0.6)
tick_sound = generate_beep(freq=600, duration=0.04, volume=0.5)

# ======================================
# Pet Data
# ======================================
pet_names = ["Mochi", "Pixel", "Noodle", "Sprout", "Ziggy", "Pebble", "Gizmo", "Biscuit", "Miso", "Pip", "Nova", "Bean", "Puddle", "Sushi", "Tater"]
pet_name = random.choice(pet_names)
name_surface = name_font.render(pet_name, True, (200, 200, 220))

rendered = {
    name: [font.render(f, True, (255, 255, 255)) for f in frames]
    for name, frames in animations.items()
}

current_anim = "idle"
frame_index = 0
frame_delay = 0.70
last_frame_time = pygame.time.get_ticks()
animating = False
dead = False
text_surface = rendered[current_anim][0]

# ======================================
# Bars and Care Logic
# ======================================
care_points = 0
hunger = 100
cleanliness = 100
sleepiness = 100

def compute_happiness():
    return max(0, min(100, (hunger + cleanliness + sleepiness) / 3.0))

now_ms = pygame.time.get_ticks()
next_hunger_tick = now_ms + random.randint(5_000, 10_000)
next_clean_tick = now_ms + random.randint(8_000, 12_000)
next_sleep_tick = now_ms + random.randint(10_000, 15_000)

def random_depletion(now):
    global hunger, cleanliness, sleepiness
    global next_hunger_tick, next_clean_tick, next_sleep_tick
    if now >= next_hunger_tick and hunger > 0:
        hunger = max(0, hunger - random.randint(1, 3))
        next_hunger_tick = now + random.randint(5_000, 10_000)
    if now >= next_clean_tick and cleanliness > 0:
        cleanliness = max(0, cleanliness - random.randint(1, 3))
        next_clean_tick = now + random.randint(8_000, 12_000)
    if now >= next_sleep_tick and sleepiness > 0:
        sleepiness = max(0, sleepiness - random.randint(1, 3))
        next_sleep_tick = now + random.randint(10_000, 15_000)

def get_current_need():
    if dead:
        return "dead"
    bars = {"hunger": hunger, "cleanliness": cleanliness, "sleepiness": sleepiness}
    lowest = min(bars, key=bars.get)
    lowest_val = bars[lowest]
    happiness = compute_happiness()
    if happiness < 50 and lowest_val < 50:
        return "sad_idle"
    if lowest_val < 50:
        if lowest == "hunger": return "hungry_idle"
        if lowest == "cleanliness": return "dirty_idle"
        if lowest == "sleepiness": return "sleepy_idle"
    return "idle"

def apply_button_effect(role):
    global hunger, cleanliness, sleepiness, care_points
    ADD = {"food": 10, "bath": 10, "sleep": 10, "love": 5, "cheer": 5, "treat": 5}
    TARGETS = {
        "food": ["hunger"], "bath": ["cleanliness"], "sleep": ["sleepiness"],
        "love": ["hunger", "cleanliness", "sleepiness"],
        "cheer": ["hunger", "cleanliness", "sleepiness"],
        "treat": ["hunger", "cleanliness", "sleepiness"],
    }
    amount = ADD[role]
    bars = TARGETS[role]
    at_least_one_good = False
    all_overfill = True
    for bar in bars:
        current = globals()[bar]
        if current < 100:
            all_overfill = False
        if current + amount <= 100:
            at_least_one_good = True
    if at_least_one_good:
        care_points += 1
    elif all_overfill:
        care_points = max(0, care_points - 1)
    for bar in bars:
        globals()[bar] = min(100, globals()[bar] + amount)

# ======================================
# Buttons
# ======================================
buttons = [
    {"emoji": "🍖", "anim": "red", "role": "food"},
    {"emoji": "🛁", "anim": "green", "role": "bath"},
    {"emoji": "❤", "anim": "blue", "role": "love"},
    {"emoji": "🌟", "anim": "yellow", "role": "cheer"},
    {"emoji": "💤", "anim": "purple", "role": "sleep"},
    {"emoji": "🍬", "anim": "orange", "role": "treat"},
]

button_data = []
def make_button_surf(emoji):
    return emoji_font.render(emoji, True, (255, 255, 255))

left_x = 40
right_x = WINDOW_W - 40
button_y_start = 55
button_y_gap = 60
for i in range(3):
    surf = make_button_surf(buttons[i]["emoji"])
    rect = surf.get_rect(center=(left_x, button_y_start + i * button_y_gap))
    button_data.append([surf, rect, buttons[i]["anim"], buttons[i]["role"], 0])
for i in range(3, 6):
    surf = make_button_surf(buttons[i]["emoji"])
    rect = surf.get_rect(center=(right_x, button_y_start + (i - 3) * button_y_gap))
    button_data.append([surf, rect, buttons[i]["anim"], buttons[i]["role"], 0])

# ======================================
# Animation and Drawing
# ======================================
def trigger_animation(anim_name):
    global current_anim, frame_index, animating, last_frame_time
    current_anim = anim_name
    frame_index = 0
    animating = True
    last_frame_time = pygame.time.get_ticks()

def update_animation(now):
    global frame_index, animating, current_anim, last_frame_time, text_surface
    if now - last_frame_time < frame_delay * 1000:
        return
    frame_index += 1
    last_frame_time = now
    if animating:
        tick_sound.play()
    frames = rendered[current_anim]
    if frame_index >= len(frames):
        if animating:
            animating = False
            current_anim = get_current_need()
            frame_index = 0
            frames = rendered[current_anim]
        else:
            frame_index = 0
    text_surface = frames[frame_index]
    update_tray_icon_frame(animations[current_anim][frame_index])

BAR_X = 70
BAR_W = 160
BAR_H = 10
BAR_Y_START = 120
BAR_GAP = 20

def draw_bar(label, value, x, y):
    label_surf = label_font.render(label, True, (255, 255, 255))
    screen.blit(label_surf, (x, y))
    bar_x = x + 60
    bar_y = y + 4
    pygame.draw.rect(screen, (60, 60, 60), (bar_x, bar_y, BAR_W, BAR_H))
    color = {
        "Hunger": (255, 80, 80),
        "Clean": (80, 255, 120),
        "Sleep": (80, 160, 255),
        "Happy": (255, 220, 80),
    }.get(label, (200, 200, 255))
    fill_w = int((value / 100) * BAR_W)
    pygame.draw.rect(screen, color, (bar_x, bar_y, fill_w, BAR_H))

def draw_everything():
    screen.fill((20, 20, 30))
    screen.blit(name_surface, (WINDOW_W // 2 - name_surface.get_width() // 2, 5))
    screen.blit(text_surface, (WINDOW_W // 2 - text_surface.get_width() // 2, 35))
    draw_bar("Hunger", hunger, BAR_X, BAR_Y_START)
    draw_bar("Clean", cleanliness, BAR_X, BAR_Y_START + BAR_GAP)
    draw_bar("Sleep", sleepiness, BAR_X, BAR_Y_START + BAR_GAP * 2)
    draw_bar("Happy", compute_happiness(), BAR_X, BAR_Y_START + BAR_GAP * 3)
    score_surf = score_font.render(f"Care: {care_points}", True, (255, 255, 255))
    screen.blit(score_surf, (5, 5))
    for surf, rect, _, _, shrink in button_data:
        if shrink > 0:
            shrunk = pygame.transform.scale(surf, (int(rect.width * 0.8), int(rect.height * 0.8)))
            shr_rect = shrunk.get_rect(center=rect.center)
            screen.blit(shrunk, shr_rect)
        else:
            screen.blit(surf, rect)

# ======================================
# Input Handling
# ======================================
def handle_button_press(pos):
    for i, (surf, rect, anim, role, shrink) in enumerate(button_data):
        if rect.collidepoint(pos):
            button_sound.play()
            trigger_animation(anim)
            apply_button_effect(role)
            button_data[i][4] = 3
            return

def update_shrink_effect():
    for i in range(len(button_data)):
        if button_data[i][4] > 0:
            button_data[i][4] -= 1

def handle_drag_events(event):
    global dragging, drag_offset_x, drag_offset_y
    hwnd = pygame.display.get_wm_info()["window"]
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        dragging = True
        mx, my = pygame.mouse.get_pos()
        rect = ctypes.wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        drag_offset_x = mx
        drag_offset_y = my
    elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
        dragging = False
    elif event.type == pygame.MOUSEMOTION and dragging:
        mx, my = pygame.mouse.get_pos()
        rect = ctypes.wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        new_x = rect.left + (mx - drag_offset_x)
        new_y = rect.top + (my - drag_offset_y)
        user32.SetWindowPos(hwnd, None, new_x, new_y, 0, 0, 0x0001)

def check_death():
    global dead, current_anim, animating, frame_index
    if hunger <= 0 and cleanliness <= 0 and sleepiness <= 0:
        dead = True
        current_anim = "dead"
        animating = False
        frame_index = 0

# ======================================
# Main Loop
# ======================================
tray_thread = threading.Thread(target=run_tray_icon, args=("(O . O)",), daemon=True)
tray_thread.start()

clock = pygame.time.Clock()
while running:
    now = pygame.time.get_ticks()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        handle_drag_events(event)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if window_visible:
                handle_button_press(event.pos)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p and pygame.key.get_mods() & (pygame.KMOD_LALT | pygame.KMOD_RALT):
                toggle_window_visibility()

    if not dead:
        random_depletion(now)
    check_death()
    update_animation(now)
    update_shrink_effect()

    if not animating and not dead:
        new_need = get_current_need()
        if new_need != current_anim:
            current_anim = new_need
            frame_index = 0
            text_surface = rendered[current_anim][0]
            update_tray_icon_frame(animations[current_anim][0])

    if window_visible:
        draw_everything()
        pygame.display.flip()

    clock.tick(60)

pygame.quit()
sys.exit()
