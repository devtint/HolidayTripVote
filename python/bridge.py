"""
Holiday Destination Voting System - Python Bridge
Reads votes from Arduino via Serial and uploads to ThingSpeak

Usage: 
    python bridge.py           # Auto-detect Arduino port
    python bridge.py auto      # Explicitly auto-detect
    python bridge.py COM5      # Use specific port
"""

import serial
import serial.tools.list_ports
import requests
import time
import json
import csv
from datetime import datetime
import sys
import os
from dotenv import load_dotenv

# ========================================
# Load Environment Variables
# ========================================
# Load .env from project root (one level up from python/)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

# ========================================
# Configuration (from .env)
# ========================================
THINGSPEAK_WRITE_API_KEY = os.getenv("THINGSPEAK_WRITE_API_KEY")
THINGSPEAK_READ_API_KEY = os.getenv("THINGSPEAK_READ_API_KEY")
THINGSPEAK_CHANNEL_ID = os.getenv("THINGSPEAK_CHANNEL_ID")

# Validate required environment variables
if not all([THINGSPEAK_WRITE_API_KEY, THINGSPEAK_READ_API_KEY, THINGSPEAK_CHANNEL_ID]):
    print("[ERROR] Missing required environment variables!")
    print("        Please ensure .env file exists in project root with:")
    print("        - THINGSPEAK_WRITE_API_KEY")
    print("        - THINGSPEAK_READ_API_KEY")
    print("        - THINGSPEAK_CHANNEL_ID")
    sys.exit(1)

THINGSPEAK_WRITE_URL = "https://api.thingspeak.com/update"
THINGSPEAK_READ_URL = f"https://api.thingspeak.com/channels/{THINGSPEAK_CHANNEL_ID}/feeds/last.json"

# Serial Configuration
BAUD_RATE = 9600
DEFAULT_COM_PORT = os.getenv("DEFAULT_COM_PORT", "COM3")

# Upload Configuration
UPLOAD_INTERVAL = 15  # ThingSpeak free tier minimum (cannot go lower)
UPLOAD_AFTER_VOTE = True  # Upload immediately after vote (respecting interval)

# Candidate Names (for logging)
CANDIDATES = {
    1: "Japan",
    2: "Germany", 
    3: "Switzerland",
    4: "Norway"
}

# ========================================
# State
# ========================================
votes = {1: 0, 2: 0, 3: 0, 4: 0}
votes_since_last_upload = 0
last_upload_time = 0

# ========================================
# File Paths
# ========================================
VOTES_FILE = os.path.join(SCRIPT_DIR, "votes.json")
LOG_FILE = os.path.join(SCRIPT_DIR, "votes.csv")

# ========================================
# Arduino Auto-Detection
# ========================================
# Common Arduino/USB-Serial chip signatures
ARDUINO_SIGNATURES = [
    "CH340",      # Common clone chip (Arduino Nano, Uno clones)
    "CH341",      # Variant of CH340
    "FT232",      # FTDI chip (some Nanos, Pro Minis)
    "FT231",      # FTDI variant
    "Arduino",    # Original Arduino boards
    "USB Serial", # Generic USB-Serial adapters
    "USB-SERIAL", # Windows variant
    "ACM",        # Linux Arduino device
    "ttyUSB",     # Linux USB serial
    "ttyACM",     # Linux Arduino
]


def find_arduino_ports():
    """
    Scan all COM ports and return list of likely Arduino devices.
    Returns list of (device, description) tuples.
    """
    arduino_ports = []
    all_ports = serial.tools.list_ports.comports()
    
    for port in all_ports:
        desc_upper = port.description.upper()
        device_upper = port.device.upper()
        
        for signature in ARDUINO_SIGNATURES:
            if signature.upper() in desc_upper or signature.upper() in device_upper:
                arduino_ports.append((port.device, port.description))
                break
    
    return arduino_ports


def auto_select_port():
    """
    Automatically find and select Arduino port.
    Returns selected port name or None if not found.
    """
    print("[SCANNING] Looking for Arduino devices...")
    
    arduino_ports = find_arduino_ports()
    
    if not arduino_ports:
        # No Arduino found, show all available ports
        print("[WARN] No Arduino devices detected automatically.")
        all_ports = serial.tools.list_ports.comports()
        if all_ports:
            print("\nAvailable ports:")
            for i, port in enumerate(all_ports, 1):
                print(f"  {i}. {port.device}: {port.description}")
            print()
            
            # Let user choose
            try:
                choice = input("Enter port number to use (or press Enter to exit): ").strip()
                if choice:
                    idx = int(choice) - 1
                    if 0 <= idx < len(all_ports):
                        return all_ports[idx].device
            except (ValueError, IndexError):
                pass
        return None
    
    if len(arduino_ports) == 1:
        # Single Arduino found - auto select
        device, desc = arduino_ports[0]
        print(f"[FOUND] {device}: {desc}")
        return device
    
    # Multiple Arduinos found - let user choose
    print(f"[FOUND] {len(arduino_ports)} Arduino devices detected:\n")
    for i, (device, desc) in enumerate(arduino_ports, 1):
        print(f"  {i}. {device}: {desc}")
    print()
    
    try:
        choice = input(f"Select Arduino (1-{len(arduino_ports)}): ").strip()
        if choice:
            idx = int(choice) - 1
            if 0 <= idx < len(arduino_ports):
                return arduino_ports[idx][0]
    except (ValueError, IndexError):
        pass
    
    # Default to first one
    print(f"[DEFAULT] Using {arduino_ports[0][0]}")
    return arduino_ports[0][0]


# ========================================
# Functions
# ========================================
def fetch_votes_from_thingspeak():
    """Fetch current vote totals from ThingSpeak"""
    global votes
    try:
        url = f"{THINGSPEAK_READ_URL}?api_key={THINGSPEAK_READ_API_KEY}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data and 'field1' in data:
                votes[1] = int(data.get('field1') or 0)
                votes[2] = int(data.get('field2') or 0)
                votes[3] = int(data.get('field3') or 0)
                votes[4] = int(data.get('field4') or 0)
                print(f"[SYNCED] Loaded from ThingSpeak: {votes}")
                return True
            else:
                print("[INFO] No data on ThingSpeak yet, starting fresh")
        else:
            print(f"[WARN] Could not fetch from ThingSpeak: HTTP {response.status_code}")
    except Exception as e:
        print(f"[WARN] Could not fetch from ThingSpeak: {e}")
    
    # Fallback to local file
    load_votes_from_file()
    return False


def load_votes_from_file():
    """Load saved votes from local JSON file (fallback)"""
    global votes
    try:
        if os.path.exists(VOTES_FILE):
            with open(VOTES_FILE, 'r') as f:
                saved = json.load(f)
                votes = {int(k): v for k, v in saved.items()}
                print(f"[LOADED] From local file: {votes}")
    except Exception as e:
        print(f"[WARN] Could not load local votes: {e}")


def save_votes():
    """Save votes to JSON file"""
    try:
        with open(VOTES_FILE, 'w') as f:
            json.dump(votes, f)
    except Exception as e:
        print(f"[ERROR] Could not save votes: {e}")


def log_vote(candidate_id):
    """Append vote to CSV audit log"""
    try:
        timestamp = datetime.now().isoformat()
        candidate_name = CANDIDATES.get(candidate_id, f"Unknown-{candidate_id}")
        
        file_exists = os.path.exists(LOG_FILE)
        with open(LOG_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["timestamp", "candidate_id", "candidate_name"])
            writer.writerow([timestamp, candidate_id, candidate_name])
    except Exception as e:
        print(f"[ERROR] Could not log vote: {e}")


def upload_to_thingspeak():
    """Upload current vote totals to ThingSpeak"""
    global last_upload_time, votes_since_last_upload
    
    try:
        payload = {
            "api_key": THINGSPEAK_WRITE_API_KEY,
            "field1": votes[1],  # Japan
            "field2": votes[2],  # Germany
            "field3": votes[3],  # Switzerland
            "field4": votes[4]   # Norway
        }
        
        response = requests.post(THINGSPEAK_WRITE_URL, data=payload, timeout=10)
        
        if response.status_code == 200 and response.text != "0":
            print(f"[UPLOAD] Success! Entry #{response.text}")
            last_upload_time = time.time()
            votes_since_last_upload = 0
            return True
        else:
            print(f"[UPLOAD] Failed: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Upload failed: {e}")
        return False


def process_vote(line):
    """Process incoming vote from Arduino"""
    global votes_since_last_upload
    
    try:
        # Parse format: VOTE,X
        parts = line.strip().split(',')
        if len(parts) == 2 and parts[0] == "VOTE":
            candidate_id = int(parts[1])
            
            if candidate_id in votes:
                votes[candidate_id] += 1
                votes_since_last_upload += 1
                
                candidate_name = CANDIDATES.get(candidate_id, f"Candidate {candidate_id}")
                print(f"[VOTE] {candidate_name} | Total: {votes[candidate_id]}")
                
                # Log and save
                log_vote(candidate_id)
                save_votes()
                
                return True
    except ValueError:
        pass
    
    return False


def should_upload():
    """Determine if we should upload to ThingSpeak"""
    time_elapsed = time.time() - last_upload_time
    
    # Upload if enough time has passed AND there are new votes
    if time_elapsed >= UPLOAD_INTERVAL and votes_since_last_upload > 0:
        return True
    
    return False


def print_status():
    """Print current vote status"""
    total = sum(votes.values())
    print("\n" + "=" * 50)
    print("CURRENT VOTE TOTALS")
    print("=" * 50)
    for cid, name in CANDIDATES.items():
        pct = (votes[cid] / total * 100) if total > 0 else 0
        bar = "█" * int(pct / 5)
        print(f"  {name:15} | {votes[cid]:4} votes | {pct:5.1f}% {bar}")
    print(f"\n  {'TOTAL':15} | {total:4} votes")
    print("=" * 50 + "\n")


def main():
    global last_upload_time
    
    print("=" * 50)
    print("  HOLIDAY DESTINATION VOTING SYSTEM")
    print("  Python Bridge ")
    print("=" * 50)
    
    # Determine COM port
    if len(sys.argv) > 1 and sys.argv[1].lower() != "auto":
        # User specified a port explicitly
        com_port = sys.argv[1]
        print(f"  COM Port:    {com_port} (manual)")
    else:
        # Auto-detect Arduino
        com_port = auto_select_port()
        if not com_port:
            print("[ERROR] No Arduino found. Please connect Arduino and try again.")
            print("        Or specify port manually: python bridge.py COM5")
            sys.exit(1)
        print(f"  COM Port:    {com_port} (auto-detected)")
    
    print(f"  Baud Rate:   {BAUD_RATE}")
    print(f"  ThingSpeak:  Channel {THINGSPEAK_CHANNEL_ID}")
    print("=" * 50)
    print()
    
    # Generate frontend config.js from .env (not needed - frontend has hardcoded config)
    # generate_frontend_config()
    
    # Load votes from LOCAL file (source of truth)
    print("[LOADING] Reading votes from local storage...")
    load_votes_from_file()
    print_status()
    
    # Initialize upload time
    last_upload_time = time.time()
    
    # Try to connect to Arduino
    ser = None
    try:
        ser = serial.Serial(com_port, BAUD_RATE, timeout=1)
        print(f"[CONNECTED] {com_port} at {BAUD_RATE} baud")
        time.sleep(2)  # Wait for Arduino reset
        
    except Exception as e:
        print(f"[ERROR] Could not connect to {com_port}: {e}")
        print("\nAvailable ports:")
        ports = serial.tools.list_ports.comports()
        for port in ports:
            print(f"  - {port.device}: {port.description}")
        sys.exit(1)
    
    if ser is None:
        print("[ERROR] Serial connection failed")
        sys.exit(1)
    
    print("[READY] Waiting for votes... (Ctrl+C to exit)\n")
    
    try:
        while True:
            # Read from serial
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                
                if line:
                    if line == "READY":
                        print("[ARDUINO] Ready")
                    elif line.startswith("VOTE,"):
                        if process_vote(line):
                            pass  # Vote processed
                    else:
                        print(f"[DEBUG] {line}")
            
            # Check if we should upload
            if should_upload():
                print("\n[UPLOADING] Sending to ThingSpeak...")
                upload_to_thingspeak()
                print_status()
            
            time.sleep(0.1)  # Small delay to prevent CPU hogging
            
    except KeyboardInterrupt:
        print("\n\n[EXIT] Shutting down...")
        print_status()
        
        # Final upload
        if votes_since_last_upload > 0:
            print("[UPLOADING] Final upload...")
            upload_to_thingspeak()
        
        ser.close()
        print("[DONE] Goodbye!")


if __name__ == "__main__":
    main()
