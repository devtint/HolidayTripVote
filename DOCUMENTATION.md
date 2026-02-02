# 🗳️ Holiday Destination Voting System
## Complete Project Documentation

**Course:** 525 Final Project  
**Date:** February 2026  
**Repository:** [github.com/devtint/HolidayTripVote](https://github.com/devtint/HolidayTripVote)

---

## 📋 Table of Contents

1. [Project Overview](#-project-overview)
2. [System Architecture](#-system-architecture)
3. [Hardware Components](#-hardware-components)
4. [Software Components](#-software-components)
5. [Data Flow Diagram](#-data-flow-diagram)
6. [Setup Instructions](#-setup-instructions)
7. [How to Run](#-how-to-run)
8. [ThingSpeak Configuration](#-thingspeak-configuration)
9. [Security Considerations](#-security-considerations)
10. [Troubleshooting](#-troubleshooting)

---

## 🎯 Project Overview

This is an **IoT-based voting system** that allows users to vote for their preferred holiday destination using physical buttons connected to an Arduino. The votes are processed by a Python bridge script and uploaded to **ThingSpeak** cloud platform for real-time visualization.

### Voting Options
| Button | Destination |
|--------|-------------|
| 1 | 🇯🇵 Japan |
| 2 | 🇩🇪 Germany |
| 3 | 🇨🇭 Switzerland |
| 4 | 🇳🇴 Norway |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        VOTING SYSTEM ARCHITECTURE                    │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────┐     Serial      ┌──────────────┐     HTTP      ┌──────────────┐
│              │     (USB)       │              │    (REST)     │              │
│   ARDUINO    │ ──────────────► │    PYTHON    │ ────────────► │  THINGSPEAK  │
│   UNO/NANO   │    VOTE,X       │    BRIDGE    │   POST/GET    │    CLOUD     │
│              │                 │              │               │              │
└──────────────┘                 └──────────────┘               └──────────────┘
       │                                │                              │
       │                                │                              │
       ▼                                ▼                              ▼
  ┌─────────┐                    ┌─────────────┐               ┌─────────────┐
  │ 4 Push  │                    │ votes.json  │               │   Channel   │
  │ Buttons │                    │ votes.csv   │               │   Fields    │
  └─────────┘                    └─────────────┘               └─────────────┘
                                                                      │
                                                                      │
                                                                      ▼
                                                               ┌─────────────┐
                                                               │  WEB        │
                                                               │  DASHBOARD  │
                                                               │ (index.html)│
                                                               └─────────────┘
```

---

## 🔧 Hardware Components

### Required Components
| Component | Quantity | Purpose |
|-----------|----------|---------|
| Arduino Uno/Nano | 1 | Microcontroller |
| Push Buttons | 4 | Vote input (one per candidate) |
| LED | 1 | Vote confirmation indicator |
| Buzzer (Piezo) | 1 | Audio feedback on vote |
| 7-Segment Display | 1 | Shows voted candidate number (1-4) |
| Resistors (220Ω) | 7 | Current limiting for 7-segment |
| Breadboard | 1 | Circuit prototyping |
| USB Cable | 1 | Power & serial communication |
| Jumper Wires | ~30 | Connections |

### Hardware Feedback System
| Component | Trigger | Duration | Purpose |
|-----------|---------|----------|--------|
| LED (Pin 13) | On vote | 500ms | Notifies button was pressed |
| Buzzer (Pin 11) | On vote | 100ms | Audio confirmation beep |
| 7-Segment | On vote | 2000ms | Shows which candidate (1-4) was voted |

### Wiring Diagram
```
Arduino Pin Configuration:
══════════════════════════════════════════════════════════════

  BUTTONS (INPUT_PULLUP):
  ─────────────────────────
  Pin 2  ──► Button 1 (Japan)        ──► GND
  Pin 3  ──► Button 2 (Germany)      ──► GND
  Pin 4  ──► Button 3 (Switzerland)  ──► GND
  Pin 5  ──► Button 4 (Norway)       ──► GND

  7-SEGMENT DISPLAY (Common Cathode):
  ─────────────────────────
  Pin 6  ──► Segment A
  Pin 7  ──► Segment B
  Pin 8  ──► Segment C
  Pin 9  ──► Segment D
  Pin 10 ──► Segment E
  Pin A0 ──► Segment F
  Pin A1 ──► Segment G
  GND    ──► Common Cathode

  OUTPUT INDICATORS:
  ─────────────────────────
  Pin 11 ──► Buzzer (+)  ──► GND
  Pin 13 ──► LED (+)     ──► 220Ω ──► GND

══════════════════════════════════════════════════════════════
```

---

## 💻 Software Components

### 1. Arduino Firmware (`arduino/voting_system/voting_system.ino`)
- Monitors 4 button inputs with INPUT_PULLUP
- Software debouncing (200ms) to avoid false triggers
- Sends `VOTE,X` command via Serial (9600 baud)
- **LED feedback:** Lights up for 500ms on vote
- **Buzzer feedback:** Beeps (1000Hz, 100ms) on vote
- **7-Segment display:** Shows candidate number for 2 seconds

### 2. Python Bridge (`python/bridge.py`)
- Reads Serial data from Arduino
- Processes votes and maintains count
- Uploads to ThingSpeak every 15 seconds
- Logs votes to CSV file for audit
- Saves state to JSON for recovery

### 3. Web Dashboard (`index.html`, `style.css`, `script.js`)
- Real-time vote display
- Auto-refresh from ThingSpeak
- Visual bar chart of results
- Responsive design

---

## 🔄 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         DATA FLOW                                │
└─────────────────────────────────────────────────────────────────┘

1. USER PRESSES BUTTON
         │
         ▼
2. ARDUINO DETECTS BUTTON PRESS
         │
         ├── Debounce check (200ms)
         ├── LED lights up (500ms)
         ├── Buzzer beeps (100ms)
         ├── 7-Segment shows candidate number (2s)
         │
         ▼
3. ARDUINO SENDS "VOTE,X" VIA SERIAL
         │
         ▼
4. PYTHON BRIDGE RECEIVES DATA
         │
         ├── Parse vote (VOTE,1 → Japan)
         ├── Increment local counter
         ├── Log to votes.csv (audit trail)
         └── Save to votes.json (backup)
         │
         ▼
5. PYTHON UPLOADS TO THINGSPEAK (every 15s)
         │
         ├── POST request with API key
         ├── field1 = Japan votes
         ├── field2 = Germany votes
         ├── field3 = Switzerland votes
         └── field4 = Norway votes
         │
         ▼
6. WEB DASHBOARD READS FROM THINGSPEAK
         │
         ├── GET request with Read API key
         ├── Parse JSON response
         └── Update UI (bars, percentages)
         │
         ▼
7. USER SEES REAL-TIME RESULTS
```

---

## 📦 Setup Instructions

### Prerequisites
- Python 3.8+
- Arduino IDE
- Git
- Web browser

### Step 1: Clone Repository
```bash
git clone https://github.com/devtint/HolidayTripVote.git
cd HolidayTripVote
```

### Step 2: Configure Environment
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your ThingSpeak credentials
# THINGSPEAK_WRITE_API_KEY=your_write_key
# THINGSPEAK_READ_API_KEY=your_read_key
# THINGSPEAK_CHANNEL_ID=your_channel_id
```

### Step 3: Install Python Dependencies
```bash
cd python
pip install -r requirements.txt
```

### Step 4: Upload Arduino Firmware
1. Open `arduino/voting_system/voting_system.ino` in Arduino IDE
2. Select correct board (Arduino Uno/Nano)
3. Select correct COM port
4. Click Upload

---

## ▶️ How to Run

### Step 1: Start Python Bridge
```bash
cd python
python bridge.py COM3    # Replace COM3 with your Arduino port
```

You should see:
```
==================================================
  HOLIDAY DESTINATION VOTING SYSTEM
  Python Bridge v1.0
==================================================
  COM Port:    COM3
  Baud Rate:   9600
  ThingSpeak:  Channel XXXXXXX
==================================================

[SYNCING] Fetching current votes from ThingSpeak...
[SYNCED] Loaded from ThingSpeak: {1: 5, 2: 3, 3: 2, 4: 1}
[CONNECTED] COM3 at 9600 baud
[READY] Waiting for votes... (Ctrl+C to exit)
```

### Step 2: Start Web Dashboard
```bash
# In project root folder
python -m http.server 8000
```

Open browser: `http://localhost:8000`

### Step 3: Vote!
Press buttons on Arduino to cast votes. Watch them appear in real-time!

---

## ☁️ ThingSpeak Configuration

### Channel Setup
1. Create account at [thingspeak.com](https://thingspeak.com)
2. Create new channel with 4 fields:
   - Field 1: Japan
   - Field 2: Germany
   - Field 3: Switzerland
   - Field 4: Norway

### API Keys
| Key Type | Purpose | Where Used |
|----------|---------|------------|
| Write API Key | Upload votes | Python bridge (.env) |
| Read API Key | Fetch results | JavaScript (script.js) |
| Channel ID | Identify channel | Both |

### Rate Limits (Free Tier)
- **Write:** 1 request per 15 seconds
- **Read:** No limit

---

## 🔐 Security Considerations

### What's Protected
| Item | Status | Method |
|------|--------|--------|
| Write API Key | ✅ Secure | Stored in `.env` (gitignored) |
| Read API Key | ⚠️ Public | In `script.js` (acceptable for read-only) |
| Vote Logs | ✅ Local | `votes.csv` is gitignored |
| Vote State | ✅ Local | `votes.json` is gitignored |

### Files NOT on GitHub
```
.env                 # Contains sensitive API keys
python/votes.csv     # Vote audit log
python/votes.json    # Current vote state
```

### Best Practices Used
1. ✅ Environment variables for secrets
2. ✅ `.gitignore` properly configured
3. ✅ `.env.example` provided for reference
4. ✅ Input validation in Python bridge
5. ✅ Error handling and logging

---

## 🔧 Troubleshooting

### Common Issues

#### ❌ Python: "Missing required environment variables"
**Solution:** Ensure `.env` file exists in project root with all required keys.

#### ❌ Python: "Could not connect to COM3"
**Solution:** 
1. Check Arduino is connected
2. Find correct port in Device Manager
3. Run: `python bridge.py COM4` (or your port)

#### ❌ Dashboard shows "No Data"
**Solution:**
1. Check ThingSpeak channel has data
2. Verify Read API key in `script.js`
3. Check browser console for errors

#### ❌ Votes not uploading
**Solution:**
1. Check internet connection
2. Verify Write API key in `.env`
3. Wait 15 seconds (ThingSpeak rate limit)

---

## 📁 Project File Structure

```
HolidayTripVote/
│
├── 📄 index.html          # Web dashboard UI
├── 📄 style.css           # Dashboard styling
├── 📄 script.js           # Dashboard logic (READ API)
├── 📄 README.md           # Quick start guide
├── 📄 DOCUMENTATION.md    # This file
├── 📄 .env.example        # Environment template
├── 📄 .gitignore          # Git ignore rules
│
├── 📁 arduino/
│   └── 📁 voting_system/
│       └── 📄 voting_system.ino   # Arduino firmware
│
├── 📁 python/
│   ├── 📄 bridge.py           # Python bridge script
│   ├── 📄 requirements.txt    # Python dependencies
│   ├── 📄 votes.json          # (gitignored) Vote state
│   └── 📄 votes.csv           # (gitignored) Audit log
│
└── 📄 .env                    # (gitignored) API keys
```

---

## 👥 Credits

**Project Type:** IoT Voting System  
**Stack:** Arduino + Python + ThingSpeak + HTML/CSS/JS  
**Course:** 525 Final Project  

---

*Last Updated: February 3, 2026*
