"""
Utility program made by Gemini, which allows me to easily create walls from a given background image
"""

import pygame
import sys
import os

# --- Configuration ---
SCREEN_WIDTH, SCREEN_HEIGHT = 1024, 1024
BACKGROUND_FILE = 'maps/map1/background.png'  # ASSUME THIS PATH based on your main.py
OUTPUT_FILE = 'maps/map1/walls.txt'

# --- Initialization ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pygame Wall Editor Tool (S: Save, C: Clear)")
clock = pygame.time.Clock()

# --- Load Background ---
try:
    # Attempt to load the background map (adjust path if needed)
    background_surface = pygame.image.load(BACKGROUND_FILE).convert()
except pygame.error:
    print(f"Warning: Could not load background image from '{BACKGROUND_FILE}'.")
    print("Using a placeholder screen size.")
    # Fallback to a solid gray surface if the file is missing
    background_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    background_surface.fill((50, 50, 50))


# --- Data Structures ---
drawn_rects = []
current_rect = None
drawing = False
start_pos = (0, 0)

# --- Colors ---
WALL_COLOR = (255, 0, 0)
PREVIEW_COLOR = (255, 150, 0)


def save_rects(rectangles):
    """Saves the list of Pygame Rect objects to a text file."""
    try:
        with open(OUTPUT_FILE, 'w') as f:
            for r in rectangles:
                # Format: x, y, height, width (as used in your MapLoader)
                line = f"{r.x},{r.y},{r.w},{r.h}\n"
                f.write(line)
        print(f"\n--- Saved {len(rectangles)} walls to {OUTPUT_FILE} ---")
    except Exception as e:
        print(f"\n--- ERROR saving file: {e} ---")

def adjust_rect(pos1, pos2):
    """Creates a Rect object from two corners, handling reverse drawing."""
    x = min(pos1[0], pos2[0])
    y = min(pos1[1], pos2[1])
    width = abs(pos1[0] - pos2[0])
    height = abs(pos1[1] - pos2[1])
    # Ensure minimum size to prevent zero-area rects
    width = max(1, width)
    height = max(1, height)
    return pygame.Rect(x, y, width, height)

# --- Main Loop ---
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # --- Mouse Input for Drawing ---
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click to start drawing
                drawing = True
                start_pos = event.pos
                current_rect = adjust_rect(start_pos, start_pos)
        
        elif event.type == pygame.MOUSEMOTION:
            if drawing:
                # Update the current preview rect as the mouse moves
                current_rect = adjust_rect(start_pos, event.pos)
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and drawing:  # Left click release to finish
                drawing = False
                final_rect = adjust_rect(start_pos, event.pos)
                drawn_rects.append(final_rect)
                current_rect = None # Reset preview
        
        # --- Keyboard Input for Control ---
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:
                save_rects(drawn_rects)
            elif event.key == pygame.K_c:
                drawn_rects = []
                print("--- Cleared all drawn walls ---")

    # --- Drawing ---
    screen.blit(background_surface, (0, 0))

    # 1. Draw existing saved rects (solid red)
    for rect in drawn_rects:
        pygame.draw.rect(screen, WALL_COLOR, rect)

    # 2. Draw current rect being drawn (transparent orange preview)
    if current_rect:
        # Use an overlay surface to draw a transparent rectangle
        overlay = pygame.Surface((current_rect.width, current_rect.height), pygame.SRCALPHA)
        overlay.fill(PREVIEW_COLOR + (128,)) # R, G, B, A (128 = 50% opacity)
        screen.blit(overlay, current_rect.topleft)
        pygame.draw.rect(screen, WALL_COLOR, current_rect, 1) # Draw border


    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()