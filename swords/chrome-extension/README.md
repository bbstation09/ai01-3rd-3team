# SWORD Ticketing Automation Extension

**SWORD** is a Chrome Extension designed to automate the ticketing process, specifically tailored for high-demand ticket sales. It utilizes a Finite State Machine (FSM) to manage the booking flow, from seat selection to final payment.

## ⚠️ Important Note
**Currently, this extension is configured and tested ONLY for the local test environment.**
- It relies on `main.py` (Flask server) running on `localhost`.
- Site-specific selectors in `config/sites.js` are tuned for this local mock site.
- While the architecture supports real sites (Interpark, Yes24), it requires configuration updates to work on them.

## Features
- **Auto-Resume**: Automatically detects the current step (Seat, Discount, Delivery, Payment) and resumes automation after page reloads.
- **Smart Seat Selection**: Automatically selects seats based on configured preferences (Zone, Position).
- **CAPTCHA Detection**: Detects CAPTCHA challenges and pauses for manual input (or auto-resume).
- **Payment Automation**: Handles discount selection (General), delivery method (Pickup/Mobile), and final payment submission (Bank Transfer).
- **Robustness**: Includes retry logic and error recovery for network glitches or UI delays.

## Installation
1.  Open Chrome and go to `chrome://extensions`.
2.  Enable **Developer mode** (top right).
3.  Click **Load unpacked**.
4.  Select this `chrome-extension` directory.

## Usage
1.  Start the local test server (`main.py`).
2.  Navigate to the ticketing URL (e.g., `http://localhost:5000/...`).
3.  The extension will automatically initialize.
4.  Use the `Alt+S` shortcut (or configured key) to start/stop if manual control is needed. (Currently, it auto-starts on recognized pages).
5.  Open the Chrome DevTools Console (F12) to view detailed logs (`[SWORD] ...`).

## Configuration
- **`config/sites.js`**: Contains all selectors, timing sequences, and retry limits. Modify this file to adapt to different websites.
