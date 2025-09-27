# main.py for Pico W Visual Schedule Clock

import hub75
import network
import ntptime
import time
import secrets # Import the new secrets file
# --- CONFIGURATION ---
# Wi-Fi Credentials
WIFI_SSID = secrets.WIFI_SSID
WIFI_PASS = secrets.WIFI_PASS

# HUB75 Panel Configuration (update PINS if your board is different)
WIDTH = 64
HEIGHT = 64
matrix = hub75.Hub75(WIDTH, HEIGHT, stb_invert=False)

# --- SCHEDULE DEFINITION (Hour of day: Message) ---
# Using 24-hour format.
SCHEDULE = {
    7: "Breakfast!",    # 7:00 AM - 7:59 AM
    8: "Get Ready!",    # 8:00 AM - 8:59 AM
    9: "School Time",   # 9:00 AM - 2:59 PM (handled by default below)
    15: "Homework",     # 3:00 PM - 3:59 PM
    16: "Free Time",    # 4:00 PM - 5:59 PM
    18: "Dinner Time",  # 6:00 PM - 6:59 PM
    20: "Bedtime Soon"  # 8:00 PM - 8:59 PM
}
DEFAULT_MESSAGE = "School Time"
NIGHT_MESSAGE = "zZz ZzZ zZz"

# --- FUNCTIONS ---
def connect_wifi():
    """Connects the Pico W to your Wi-Fi network."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASS)
    
    # Wait for connection
    max_wait = 10
    print("Connecting to Wi-Fi...")
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        time.sleep(1)
        
    if wlan.status() != 3:
        raise RuntimeError('Network connection failed')
    else:
        print('Connected!')
        print('IP:', wlan.ifconfig()[0])

def sync_time():
    """Syncs the Pico's internal clock with an NTP server."""
    print("Syncing time...")
    ntptime.settime()
    print("Time synced!")

# --- MAIN PROGRAM ---

# 1. Start Graphics & Connect
matrix.start()
matrix.clear()
matrix.text("Connecting...", 1, 1, matrix.color(200, 200, 200))
time.sleep(2)

try:
    connect_wifi()
    sync_time()
    matrix.clear()
    matrix.text("Ready!", 10, 28, matrix.color(0, 255, 0))
    time.sleep(2)
except Exception as e:
    matrix.clear()
    matrix.text("Error!", 15, 28, matrix.color(255, 0, 0))
    print(e)
    # The program will stop here on an error

# 2. Main Loop
while True:
    # Get the current time
    # UTC time is returned, so we adjust for EDT (-4 hours)
    current_hour_utc = time.localtime()[3]
    current_hour_local = (current_hour_utc - 4) % 24
    
    # Determine the message
    message = SCHEDULE.get(current_hour_local, DEFAULT_MESSAGE)
    
    # Override for night hours
    if current_hour_local >= 21 or current_hour_local < 7:
        message = NIGHT_MESSAGE
        
    # Display the message
    matrix.clear()
    matrix.text(message, 1, 1, matrix.color(255, 165, 0)) # Orange text
    
    # Wait before checking the time again
    time.sleep(60) # Update every minute