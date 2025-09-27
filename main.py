# main.py for Raspberry Pi Visual Schedule Clock (v2)

import os
import pygame
import requests
import time

# --- CONFIGURATION ---
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 600
FULLSCREEN = False # Set to True for production

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
ORANGE = (255, 165, 0)
GREEN = (0, 255, 0)
GRAY = (50, 50, 50) # For the progress bar background

# --- SCHEDULE DEFINITION (NEW FORMAT) ---
# List of dictionaries, must be in chronological order by 'start' hour (24-hour format)
SCHEDULE = [
    {'start': 0,  'end': 7,  'message': 'zZz ZzZ zZz', 'color': WHITE},
    {'start': 7,  'end': 8,  'message': 'Breakfast!',  'color': ORANGE},
    {'start': 8,  'end': 9,  'message': 'Get Ready!',  'color': ORANGE},
    {'start': 9,  'end': 15, 'message': 'School Time', 'color': GREEN},
    {'start': 15, 'end': 16, 'message': 'Homework',    'color': ORANGE},
    {'start': 16, 'end': 18, 'message': 'Free Time',   'color': GREEN},
    {'start': 18, 'end': 20, 'message': 'Dinner Time', 'color': ORANGE},
    {'start': 20, 'end': 21, 'message': 'Bedtime Soon','color': ORANGE},
    {'start': 21, 'end': 24, 'message': 'zZz ZzZ zZz', 'color': WHITE},
]

# --- PYGAME SETUP ---
pygame.init()
flags = pygame.FULLSCREEN if FULLSCREEN else 0
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
pygame.display.set_caption("Kid Clock")
if not FULLSCREEN:
    pygame.mouse.set_visible(True)
else:
    pygame.mouse.set_visible(False)

# Create different font sizes
font_large = pygame.font.Font(None, 120)
font_medium = pygame.font.Font(None, 72)
font_small = pygame.font.Font(None, 50)

def get_current_and_next_activity(hour):
    """Finds the current and next activity from the schedule."""
    for i, activity in enumerate(SCHEDULE):
        if activity['start'] <= hour < activity['end']:
            current_activity = activity
            # Get next activity, wrapping around to the first if it's the last one
            next_activity = SCHEDULE[(i + 1) % len(SCHEDULE)]
            return current_activity, next_activity
    return None, None # Should not happen with a complete schedule

# --- MAIN PROGRAM ---
running = True
last_checked_minute = -1

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False

    current_time = time.localtime()
    current_minute = current_time.tm_min
    
    # Only update the screen when the minute changes to save resources
    if current_minute != last_checked_minute:
        last_checked_minute = current_minute
        
        local_hour = current_time.tm_hour
        
        # --- GET SCHEDULE INFO ---
        current_act, next_act = get_current_and_next_activity(local_hour)
        
        if current_act:
            # --- CALCULATE PROGRESS ---
            start_minute_of_day = current_act['start'] * 60
            end_minute_of_day = current_act['end'] * 60
            current_minute_of_day = local_hour * 60 + current_minute

            total_duration = end_minute_of_day - start_minute_of_day
            elapsed_duration = current_minute_of_day - start_minute_of_day
            progress_percent = elapsed_duration / total_duration if total_duration > 0 else 0

            # --- PREPARE TEXT ---
            # Main Activity Text
            msg_surf = font_large.render(current_act['message'], True, current_act['color'])
            msg_rect = msg_surf.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 50))
            
            # Digital Clock Text
            time_str = time.strftime("%-I:%M %p", current_time) # %-I removes leading zero
            time_surf = font_medium.render(time_str, True, WHITE)
            time_rect = time_surf.get_rect(center=(SCREEN_WIDTH / 2, 50))
            
            # Upcoming Activity Text
            next_label_surf = font_small.render("Next:", True, GRAY)
            next_label_rect = next_label_surf.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 80))
            
            next_msg_surf = font_medium.render(next_act['message'], True, next_act['color'])
            next_msg_rect = next_msg_surf.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 40))

            # --- DRAW EVERYTHING ---
            screen.fill(BLACK)
            
            # Draw Text
            screen.blit(msg_surf, msg_rect)
            screen.blit(time_surf, time_rect)
            screen.blit(next_label_surf, next_label_rect)
            screen.blit(next_msg_surf, next_msg_rect)

            # Draw Progress Bar
            bar_width = SCREEN_WIDTH * 0.8
            bar_height = 40
            bar_x = (SCREEN_WIDTH - bar_width) / 2
            bar_y = SCREEN_HEIGHT / 2 + 50
            
            progress_width = bar_width * progress_percent

            pygame.draw.rect(screen, GRAY, (bar_x, bar_y, bar_width, bar_height), border_radius=10)
            pygame.draw.rect(screen, current_act['color'], (bar_x, bar_y, progress_width, bar_height), border_radius=10)
            
            # Update the entire display
            pygame.display.flip()

    time.sleep(1) # Sleep briefly to prevent high CPU usage

pygame.quit()