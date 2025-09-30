# main.py for Raspberry Pi Visual Schedule Clock (v7.1 - Logic Fix)

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
SCREEN_WIDTH = 1024; SCREEN_HEIGHT = 600; FULLSCREEN = False
CALENDAR_OVERRIDE_COLOR = (52, 168, 83); CALENDAR_REFRESH_INTERVAL = 600
CALENDAR_ID = "7c2f684e2d209402d42afa2c7e5f91aa2ae5213e19ddf66ed1b7f47fb2700cde@group.calendar.google.com"

# Colors
BLACK = (0, 0, 0); WHITE = (255, 255, 255); ORANGE = (255, 165, 0)
GREEN = (0, 255, 0); GRAY = (50, 50, 50); PURPLE = (81, 43, 133)

# --- SCHEDULE DEFINITIONS ---
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
todays_calendar_events = []
def fetch_calendar_events():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", ["https://www.googleapis.com/auth/calendar.readonly"])
    if not creds or not creds.valid:
        print("Google Calendar credentials not found or invalid. Please run quickstart.py again.")
        return []
    try:
        service = build("calendar", "v3", credentials=creds)
        now = datetime.now().astimezone()
        time_min = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        time_max = now.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat()
        print("Fetching today's calendar events...")
        events_result = service.events().list(calendarId=CALENDAR_ID, timeMin=time_min, timeMax=time_max, singleEvents=True, orderBy="startTime").execute()
        fetched_events = events_result.get("items", [])
        if fetched_events: print(f"Found {len(fetched_events)} event(s) for today.")
        return fetched_events
    except Exception as e:
        print(f"An error occurred fetching calendar events: {e}")
        return []

def get_next_ravens_game():
    try:
        # This function is restored from our previous version
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
                    return game_date
    except Exception as e:
        print(f"Could not fetch game schedule: {e}")
    return None

def get_current_and_next_activity(minute_of_day, schedule):
    # ** THIS IS THE CORRECTED FUNCTION **
    for i, activity in enumerate(schedule):
        if activity['start'] <= minute_of_day < activity['end']:
            current_activity = activity
            next_activity = schedule[(i + 1) % len(schedule)]
            return current_activity, next_activity
    # This line prevents the crash if a gap is found in the schedule
    return None, None

def get_next_upcoming_event(now_dt, events):
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        if 'dateTime' not in event['start']: continue
        event_start_time = datetime.fromisoformat(start).astimezone(None)
        if event_start_time > now_dt:
            return event
    return None

# --- MAIN PROGRAM ---
next_ravens_game_time = get_next_ravens_game()
last_calendar_refresh = 0
running = True
last_checked_minute = -1
active_schedule = WEEKDAY_SCHEDULE

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False

    current_timestamp = time.time()
    if current_timestamp - last_calendar_refresh > CALENDAR_REFRESH_INTERVAL:
        print("\n--- Refreshing Dynamic Data ---")
        todays_calendar_events = fetch_calendar_events()
        last_calendar_refresh = current_timestamp
        print("--- Refresh Complete ---\n")
            
    current_time_local = time.localtime()
    current_minute = current_time_local.tm_min
    if current_minute != last_checked_minute:
        last_checked_minute = current_minute
        
        day_of_week = current_time_local.tm_wday
        if day_of_week == 5: active_schedule = SATURDAY_SCHEDULE
        elif day_of_week == 6: active_schedule = SUNDAY_SCHEDULE
        else: active_schedule = WEEKDAY_SCHEDULE
        
        current_minute_of_day = current_time_local.tm_hour * 60 + current_minute
        current_act, next_base_act = get_current_and_next_activity(current_minute_of_day, active_schedule)
        
        if current_act:
            message, color = current_act['message'], current_act['color']
            now_dt_local = datetime.now().astimezone()

            next_event_message = next_base_act['message']; next_event_color = next_base_act['color']
            next_base_dt = now_dt_local.replace(hour=next_base_act['start'] // 60, minute=next_base_act['start'] % 60, second=0, microsecond=0)
            if next_base_dt < now_dt_local: next_base_dt += timedelta(days=1)
            soonest_event_time = next_base_dt
            
            next_cal_event = get_next_upcoming_event(now_dt_local, todays_calendar_events)
            if next_cal_event:
                cal_start_time = datetime.fromisoformat(next_cal_event['start'].get('dateTime')).astimezone(None)
                if cal_start_time < soonest_event_time:
                    soonest_event_time = cal_start_time
                    next_event_message = next_cal_event['summary']
                    next_event_color = CALENDAR_OVERRIDE_COLOR
            
            if next_ravens_game_time:
                game_time_local = next_ravens_game_time.astimezone(None)
                if now_dt_local < game_time_local < soonest_event_time:
                    next_event_message = "Ravens Game!"
                    next_event_color = PURPLE

            for event in todays_calendar_events:
                start = event['start'].get('dateTime'); end = event['end'].get('dateTime')
                if not start or not end: continue
                if datetime.fromisoformat(start).astimezone(None) <= now_dt_local < datetime.fromisoformat(end).astimezone(None):
                    message = event['summary']; color = CALENDAR_OVERRIDE_COLOR; break
            
            if next_ravens_game_time:
                game_start = next_ravens_game_time.astimezone(None)
                if game_start <= now_dt_local < game_start + timedelta(hours=3):
                    message = "Ravens Game!"; color = PURPLE

            progress_percent = (current_minute_of_day - current_act['start']) / (current_act['end'] - current_act['start']) if current_act['end'] > current_act['start'] else 0
            msg_surf = font_large.render(message, True, color)
            time_str = time.strftime("%#I:%M %p" if os.name == 'nt' else "%-I:%M %p", current_time_local)
            time_surf = font_medium.render(time_str, True, WHITE)
            next_label_surf = font_small.render("Next:", True, GRAY)
            next_msg_surf = font_medium.render(next_event_message, True, next_event_color)

            msg_rect = msg_surf.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 50))
            time_rect = time_surf.get_rect(center=(SCREEN_WIDTH / 2, 50))
            next_label_rect = next_label_surf.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 80))
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