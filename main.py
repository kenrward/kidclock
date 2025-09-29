# main.py for Raspberry Pi Visual Schedule Clock (v6 - Google Calendar)

import os
import sys
import pygame
import requests
import time
from datetime import datetime, timedelta, timezone

# --- GOOGLE CALENDAR IMPORTS ---
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# --- CONFIGURATION ---
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 600
FULLSCREEN = False
CALENDAR_OVERRIDE_COLOR = (52, 168, 83) # Google Green

# Colors
BLACK = (0, 0, 0); WHITE = (255, 255, 255); ORANGE = (255, 165, 0)
GREEN = (0, 255, 0); GRAY = (50, 50, 50); PURPLE = (81, 43, 133)

# --- SCHEDULE DEFINITIONS (BASE SCHEDULES) ---
WEEKDAY_SCHEDULE = [
    {'start': 0, 'end': 390, 'message': 'zZz ZzZ zZz', 'color': WHITE}, {'start': 390, 'end': 420, 'message': 'Breakfast!', 'color': ORANGE}, {'start': 420, 'end': 430, 'message': 'Get Ready!', 'color': ORANGE}, {'start': 430, 'end': 870, 'message': 'School Time', 'color': GREEN}, {'start': 870, 'end': 910, 'message': 'Homework', 'color': ORANGE}, {'start': 910, 'end': 1020, 'message': 'Free Time', 'color': GREEN}, {'start': 1020, 'end': 1200, 'message': 'Dinner Time', 'color': ORANGE}, {'start': 1200, 'end': 1260, 'message': 'Bedtime Soon', 'color': ORANGE}, {'start': 1260, 'end': 1440, 'message': 'zZz ZzZ zZz', 'color': WHITE},
]
SATURDAY_SCHEDULE = [
    {'start': 0, 'end': 540, 'message': 'zZz ZzZ zZz', 'color': WHITE}, {'start': 540, 'end': 600, 'message': 'Breakfast', 'color': ORANGE}, {'start': 600, 'end': 720, 'message': 'Play Time!', 'color': GREEN}, {'start': 720, 'end': 780, 'message': 'Lunch Time', 'color': ORANGE}, {'start': 780, 'end': 1020, 'message': 'Play Time!', 'color': GREEN}, {'start': 1020, 'end': 1200, 'message': 'Dinner Time', 'color': ORANGE}, {'start': 1200, 'end': 1320, 'message': 'Movie Night', 'color': GREEN}, {'start': 1320, 'end': 1440, 'message': 'zZz ZzZ zZz', 'color': WHITE},
]
SUNDAY_SCHEDULE = SATURDAY_SCHEDULE.copy()

# --- PYGAME & FONT SETUP ---
pygame.init()
font_large = pygame.font.Font(None, 120); font_medium = pygame.font.Font(None, 72); font_small = pygame.font.Font(None, 50)
flags = pygame.FULLSCREEN if FULLSCREEN else 0
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
pygame.display.set_caption("Kid Clock")
if not FULLSCREEN: pygame.mouse.set_visible(True)
else: pygame.mouse.set_visible(False)

# --- API & DYNAMIC DATA FUNCTIONS ---
next_ravens_game_time = None
todays_calendar_events = [] # A list to hold events fetched from Google Calendar

def fetch_calendar_events():
    """Connects to Google Calendar API and fetches events for today."""
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", ["https://www.googleapis.com/auth/calendar.readonly"])
    if not creds or not creds.valid:
        print("Google Calendar credentials not found or invalid. Please run quickstart.py again.")
        return []

    try:
        service = build("calendar", "v3", credentials=creds)
        
        # Get the start and end of today in the correct format
        now = datetime.now().astimezone()
        time_min = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        time_max = now.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat()

        print("Fetching today's calendar events...")
        events_result = service.events().list(
            calendarId="7c2f684e2d209402d42afa2c7e5f91aa2ae5213e19ddf66ed1b7f47fb2700cde@group.calendar.google.com",
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        
        fetched_events = events_result.get("items", [])
        if not fetched_events:
            print("No upcoming events found on the calendar for today.")
        
        return fetched_events

    except Exception as e:
        print(f"An error occurred fetching calendar events: {e}")
        return []

# (Other functions like get_next_ravens_game and get_current_and_next_activity remain the same)
def get_next_ravens_game():
    try:
        print("Fetching NFL schedule...")
        url = "http://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
        response = requests.get(url, timeout=10)
        data = response.json()
        now_utc = datetime.now(timezone.utc)
        for event in data['events']:
            game_date_str = event['date']
            game_date_naive = datetime.strptime(game_date_str, "%Y-%m-%dT%H:%MZ")
            game_date = game_date_naive.replace(tzinfo=timezone.utc)
            if game_date < now_utc: continue
            for team_data in event['competitions'][0]['competitors']:
                if team_data['team']['abbreviation'] == 'BAL':
                    print(f"Found next Ravens game: {game_date}")
                    return game_date
    except Exception as e:
        print(f"Could not fetch game schedule: {e}")
    return None

def get_current_and_next_activity(minute_of_day, schedule):
    for i, activity in enumerate(schedule):
        if activity['start'] <= minute_of_day < activity['end']:
            current_activity = activity
            next_activity = schedule[(i + 1) % len(schedule)]
            return current_activity, next_activity
    return None, None

# --- MAIN PROGRAM ---
# Fetch dynamic data once at startup
next_ravens_game_time = get_next_ravens_game()
todays_calendar_events = fetch_calendar_events()

running = True
last_checked_minute = -1
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False
            
    current_time_local = time.localtime()
    current_minute = current_time_local.tm_min
    if current_minute != last_checked_minute:
        last_checked_minute = current_minute
        
        day_of_week = current_time_local.tm_wday
        if day_of_week == 5: active_schedule = SATURDAY_SCHEDULE
        elif day_of_week == 6: active_schedule = SUNDAY_SCHEDULE
        else: active_schedule = WEEKDAY_SCHEDULE
        
        current_minute_of_day = current_time_local.tm_hour * 60 + current_minute
        current_act, next_act = get_current_and_next_activity(current_minute_of_day, active_schedule)
        
        if current_act:
            message, color = current_act['message'], current_act['color']
            
            # --- OVERRIDE LOGIC ---
            # 1. Check for Ravens Game (Highest Priority)
            if next_ravens_game_time:
                now_dt_local = datetime.now().astimezone()
                game_time_local = next_ravens_game_time.astimezone(None)
                game_end_time = game_time_local + timedelta(hours=3)
                if game_time_local <= now_dt_local < game_end_time:
                    message = "Ravens Game!"
                    color = PURPLE

            # 2. Check for Calendar Events
            for event in todays_calendar_events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                # Convert event start time to a local datetime object
                event_start_time = datetime.fromisoformat(start).astimezone(None)
                
                # All-day events won't have 'dateTime', handle them if needed, here we skip
                if 'dateTime' not in event['start']:
                    continue
                
                end = event['end'].get('dateTime', event['end'].get('date'))
                event_end_time = datetime.fromisoformat(end).astimezone(None)

                now_dt_local = datetime.now().astimezone()
                if event_start_time <= now_dt_local < event_end_time:
                    message = event['summary'] # Use the calendar event's title
                    color = CALENDAR_OVERRIDE_COLOR
                    break # Stop checking once a matching event is found

            # (The rest of the drawing code is unchanged)
            total_duration = current_act['end'] - current_act['start']
            elapsed_duration = current_minute_of_day - current_act['start']
            progress_percent = elapsed_duration / total_duration if total_duration > 0 else 0
            msg_surf = font_large.render(message, True, color)
            msg_rect = msg_surf.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 50))
            time_str = time.strftime("%#I:%M %p" if os.name == 'nt' else "%-I:%M %p", current_time_local)
            time_surf = font_medium.render(time_str, True, WHITE)
            time_rect = time_surf.get_rect(center=(SCREEN_WIDTH / 2, 50))
            next_label_surf = font_small.render("Next:", True, GRAY)
            next_label_rect = next_label_surf.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 80))
            next_msg_surf = font_medium.render(next_act['message'], True, next_act['color'])
            next_msg_rect = next_msg_surf.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 40))
            screen.fill(BLACK)
            screen.blit(msg_surf, msg_rect); screen.blit(time_surf, time_rect); screen.blit(next_label_surf, next_label_rect); screen.blit(next_msg_surf, next_msg_rect)
            bar_width = SCREEN_WIDTH * 0.8; bar_height = 40; bar_x = (SCREEN_WIDTH - bar_width) / 2; bar_y = SCREEN_HEIGHT / 2 + 50
            progress_width = bar_width * progress_percent
            pygame.draw.rect(screen, GRAY, (bar_x, bar_y, bar_width, bar_height), border_radius=10)
            pygame.draw.rect(screen, color, (bar_x, bar_y, progress_width, bar_height), border_radius=10)
            pygame.display.flip()

    time.sleep(1)
pygame.quit()