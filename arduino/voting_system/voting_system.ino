/*
 * Holiday Destination Voting System
 * Arduino Firmware
 * 
 * Hardware:
 * - 4 Push Buttons (Pin 2-5) → Candidates 1-4
 * - LED (Pin 13) → Vote accepted indicator
 * - Buzzer (Pin 11) → Confirmation beep
 * - 7-Segment Display (Pins 6-10, accent pin A0) → Shows candidate number
 * 
 * Serial Output Format: VOTE,X (where X = 1-4)
 */

// ========================================
// Pin Configuration
// ========================================
const int BUTTON_PINS[] = {2, 3, 4, 5};  // Buttons for candidates 1-4
const int NUM_CANDIDATES = 4;

const int LED_PIN = 13;      // Vote accepted LED
const int BUZZER_PIN = 11;   // Confirmation buzzer

// 7-Segment Display Pins (Common Cathode)
// Segments: a, b, c, d, e, f, g
const int SEGMENT_PINS[] = {6, 7, 8, 9, 10, A0, A1};

// 7-Segment digit patterns for 1-4 (Common Cathode: HIGH = ON)
//                              a  b  c  d  e  f  g
const bool DIGITS[5][7] = {
    {0, 0, 0, 0, 0, 0, 0},  // 0: blank (off)
    {0, 1, 1, 0, 0, 0, 0},  // 1
    {1, 1, 0, 1, 1, 0, 1},  // 2
    {1, 1, 1, 1, 0, 0, 1},  // 3
    {0, 1, 1, 0, 0, 1, 1}   // 4
};

// ========================================
// Timing Configuration
// ========================================
const unsigned long DEBOUNCE_DELAY = 200;    // Debounce time in ms
const unsigned long LED_DURATION = 500;      // LED on duration in ms
const unsigned long DISPLAY_DURATION = 2000; // 7-segment display duration in ms
const int BEEP_FREQUENCY = 1000;             // Buzzer frequency in Hz
const int BEEP_DURATION = 100;               // Buzzer duration in ms

// ========================================
// State Variables
// ========================================
unsigned long lastVoteTime = 0;
unsigned long ledOffTime = 0;
unsigned long displayOffTime = 0;
bool ledActive = false;
bool displayActive = false;

// ========================================
// Setup
// ========================================
void setup() {
    // Initialize Serial
    Serial.begin(9600);
    Serial.println("READY");
    
    // Configure button pins with internal pull-up
    for (int i = 0; i < NUM_CANDIDATES; i++) {
        pinMode(BUTTON_PINS[i], INPUT_PULLUP);
    }
    
    // Configure output pins
    pinMode(LED_PIN, OUTPUT);
    pinMode(BUZZER_PIN, OUTPUT);
    
    // Configure 7-segment pins
    for (int i = 0; i < 7; i++) {
        pinMode(SEGMENT_PINS[i], OUTPUT);
        digitalWrite(SEGMENT_PINS[i], LOW);
    }
    
    // Initial state
    digitalWrite(LED_PIN, LOW);
    digitalWrite(BUZZER_PIN, LOW);
    
    // Startup beep
    tone(BUZZER_PIN, BEEP_FREQUENCY, BEEP_DURATION);
}

// ========================================
// Main Loop
// ========================================
void loop() {
    unsigned long currentTime = millis();
    
    // Check each button
    for (int i = 0; i < NUM_CANDIDATES; i++) {
        if (digitalRead(BUTTON_PINS[i]) == LOW) {  // Button pressed (active low)
            // Debounce check
            if (currentTime - lastVoteTime >= DEBOUNCE_DELAY) {
                registerVote(i + 1);  // Candidate number is 1-indexed
                lastVoteTime = currentTime;
            }
        }
    }
    
    // Turn off LED after duration
    if (ledActive && currentTime >= ledOffTime) {
        digitalWrite(LED_PIN, LOW);
        ledActive = false;
    }
    
    // Clear display after duration
    if (displayActive && currentTime >= displayOffTime) {
        clearDisplay();
        displayActive = false;
    }
}

// ========================================
// Register Vote
// ========================================
void registerVote(int candidateNumber) {
    unsigned long currentTime = millis();
    
    // 1. Send vote via Serial
    Serial.print("VOTE,");
    Serial.println(candidateNumber);
    
    // 2. Light up LED
    digitalWrite(LED_PIN, HIGH);
    ledActive = true;
    ledOffTime = currentTime + LED_DURATION;
    
    // 3. Beep buzzer
    tone(BUZZER_PIN, BEEP_FREQUENCY, BEEP_DURATION);
    
    // 4. Display candidate number on 7-segment
    displayDigit(candidateNumber);
    displayActive = true;
    displayOffTime = currentTime + DISPLAY_DURATION;
}

// ========================================
// 7-Segment Display Functions
// ========================================
void displayDigit(int digit) {
    if (digit < 0 || digit > 4) digit = 0;  // Safety check
    
    for (int i = 0; i < 7; i++) {
        digitalWrite(SEGMENT_PINS[i], DIGITS[digit][i] ? HIGH : LOW);
    }
}

void clearDisplay() {
    for (int i = 0; i < 7; i++) {
        digitalWrite(SEGMENT_PINS[i], LOW);
    }
}
