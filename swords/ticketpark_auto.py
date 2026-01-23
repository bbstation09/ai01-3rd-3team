"""
🎫 TicketPark VLM Automation
Standalone application to detect and solve CAPTCHAs, enter performances, and select date/time using VLM.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
import pyautogui

# Add current directory to path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.popup_watcher import PopupWatcher
from modules import vlm_handler
from modules.vlm_handler import encode_image_to_base64, call_vlm, capture_screen, click_and_restore

class TicketParkWatcher(PopupWatcher):
    """
    Watcher that handles:
    1. CAPTCHA (Always active if detected)
    2. Auto Enter Performance (Optional)
    3. Auto Date/Time Selection (Optional)
    """
    def __init__(self, callback):
        super().__init__(callback)
        self.enable_auto_enter = False
        self.enable_date_time = False

    def _detect_and_handle_popup(self):
        """Override to handle multiple tasks"""
        # Capture screen
        screenshot = capture_screen(self.mon_x, self.mon_y, self.mon_w, self.mon_h)
        width, height = screenshot.size
        base64_image = encode_image_to_base64(screenshot)
        
        # Comprehensive Prompt
        prompt = f"""Screenshot size: {width}x{height} pixels.

Analyze the screen for the following elements. Priority: CAPTCHA > Date/Time Modal > Performance List.

1. **CAPTCHA**: 
   - Look for a distorted text image (usually 6 uppercase letters). READ EVERY CHARACTER CAREFULLY. Do not miss any.
   - Look for an INPUT BOX **BELOW** the distorted image. It contains the gray text "문자 | 입력" (or similar).
   - START coordinates for click must be the CENTER of that **INPUT BOX**, NOT the distorted image.

2. **Date/Time Modal**: A popup title like "날짜 선택", "시간 선택", and a "예매하기" (Reserve) button.
3. **Performance List**: A section title "HOT 공연" or "티켓 예매". Performance cards with images.

RETURN JSON ONLY. Choose ONE best action.

Type "CAPTCHA":
{{"type":"CAPTCHA", "text":"CHARS", "x":0.xxx, "y":0.xxx}} 
(text=The 6 identified letters. x,y=Center of the "문자 입력" input box, generally below the captcha text)

Type "DATE_TIME":
{{"type":"DATE_TIME", "date_x":0.xx, "date_y":0.xx, "time_x":0.xx, "time_y":0.xx, "reserve_x":0.xx, "reserve_y":0.xx}}

Type "AUTO_ENTER":
{{"type":"AUTO_ENTER", "x":0.xx, "y":0.xx}}

Type "NONE":
{{"type":"NONE"}}"""

        result = call_vlm(prompt, base64_image, max_tokens=300)
        
        if not result:
            return False
            
        p_type = result.get("type", "NONE").upper()
        
        # 1. CAPTCHA (Highest Priority)
        if p_type == "CAPTCHA":
             p_text = result.get("text", "")
             raw_x = float(result.get("x", 0))
             raw_y = float(result.get("y", 0))
             
             if raw_x > 1.0: raw_x /= width
             if raw_y > 1.0: raw_y /= height
             
             abs_x = self.mon_x + int(raw_x * width)
             abs_y = self.mon_y + int(raw_y * height)
             
             if p_text and raw_x > 0 and raw_y > 0:
                captcha_str = "".join(e for e in p_text if e.isalnum())
                self.update_status(f"🔐 CAPTCHA DETECTED: '{captcha_str}' (Click: {abs_x}, {abs_y})")
                
                click_and_restore(abs_x, abs_y)
                time.sleep(0.1)
                pyautogui.write(captcha_str)
                time.sleep(0.1)
                pyautogui.press('enter')
                return True

        # 2. Date/Time Selection (If Enabled)
        elif p_type == "DATE_TIME" and self.enable_date_time:
            # Simple logic: Click Date -> Wait -> Click Time -> Wait -> Click Reserve
            try:
                d_x = float(result.get("date_x", 0))
                d_y = float(result.get("date_y", 0))
                t_x = float(result.get("time_x", 0))
                t_y = float(result.get("time_y", 0))
                r_x = float(result.get("reserve_x", 0))
                r_y = float(result.get("reserve_y", 0))

                if d_x > 0 and t_x > 0 and r_x > 0:
                     self.update_status("📅 Auto Date/Time Selection detected")
                     
                     if d_x > 1.0: d_x /= width
                     if d_y > 1.0: d_y /= height
                     abs_d_x = self.mon_x + int(d_x * width)
                     abs_d_y = self.mon_y + int(d_y * height)

                     if t_x > 1.0: t_x /= width
                     if t_y > 1.0: t_y /= height
                     abs_t_x = self.mon_x + int(t_x * width)
                     abs_t_y = self.mon_y + int(t_y * height)

                     if r_x > 1.0: r_x /= width
                     if r_y > 1.0: r_y /= height
                     abs_r_x = self.mon_x + int(r_x * width)
                     abs_r_y = self.mon_y + int(r_y * height)

                     # Sequence
                     self.update_status(f"  -> Selecting Date ({abs_d_x},{abs_d_y})")
                     click_and_restore(abs_d_x, abs_d_y)
                     time.sleep(0.5)

                     self.update_status(f"  -> Selecting Time ({abs_t_x},{abs_t_y})")
                     click_and_restore(abs_t_x, abs_t_y)
                     time.sleep(0.5)

                     self.update_status(f"  -> Clicking Reserve ({abs_r_x},{abs_r_y})")
                     click_and_restore(abs_r_x, abs_r_y)
                     return True
            except:
                pass


        # 3. Auto Enter (If Enabled)
        elif p_type == "AUTO_ENTER" and self.enable_auto_enter:
             raw_x = float(result.get("x", 0))
             raw_y = float(result.get("y", 0))
             
             if raw_x > 1.0: raw_x /= width
             if raw_y > 1.0: raw_y /= height
             
             abs_x = self.mon_x + int(raw_x * width)
             abs_y = self.mon_y + int(raw_y * height)
             
             if raw_x > 0 and raw_y > 0:
                 self.update_status(f"🚪 Auto Enter: Clicking Performance ({abs_x}, {abs_y})")
                 click_and_restore(abs_x, abs_y)
                 # Wait a bit longer after entering to let page load
                 time.sleep(2.0) 
                 return True

        return False


class TicketParkAutoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎫 TicketPark VLM Automation")
        self.root.geometry("600x550")
        self.root.resizable(False, False)
        
        # Dark theme colors
        self.colors = {
            'bg': '#1a1a2e',
            'card': '#16213e',
            'text': '#ffffff',
            'accent': '#e94560',
            'success': '#00ff88'
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # Initialize Custom Watcher
        self.watcher = TicketParkWatcher(callback=self.log_message)
        
        self._setup_ui()
        
    def _setup_ui(self):
        # Header
        header = tk.Label(self.root, 
            text="🎫 TicketPark VLM Auto",
            font=('Segoe UI', 18, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['text'])
        header.pack(pady=15)
        
        # Controls Frame
        control_frame = tk.Frame(self.root, bg=self.colors['card'], padx=20, pady=20)
        control_frame.pack(fill='x', padx=20)
        
        # Options
        tk.Label(control_frame, text="Automation Options:", bg=self.colors['card'], fg=self.colors['text'], font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 10))

        self.var_auto_enter = tk.BooleanVar(value=False)
        self.cb_auto_enter = tk.Checkbutton(control_frame, 
            text="🚪 Auto Enter (Random Click on Main)",
            variable=self.var_auto_enter,
            bg=self.colors['card'], fg=self.colors['text'], selectcolor='#000000',
            font=('Segoe UI', 10), activebackground=self.colors['card'], activeforeground=self.colors['text'],
            command=self._update_options)
        self.cb_auto_enter.pack(anchor='w')

        self.var_date_time = tk.BooleanVar(value=False)
        self.cb_date_time = tk.Checkbutton(control_frame, 
            text="📅 Auto Date/Time/Reserve (Modal)",
            variable=self.var_date_time,
            bg=self.colors['card'], fg=self.colors['text'], selectcolor='#000000',
            font=('Segoe UI', 10), activebackground=self.colors['card'], activeforeground=self.colors['text'],
            command=self._update_options)
        self.cb_date_time.pack(anchor='w', pady=(5, 15))


        # VLM Selector
        vlm_frame = tk.Frame(control_frame, bg=self.colors['card'])
        vlm_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(vlm_frame, text="Model:", bg=self.colors['card'], fg=self.colors['text']).pack(side='left')
        
        self.vlm_var = tk.StringVar(value="LM_STUDIO")
        self.vlm_combo = ttk.Combobox(vlm_frame, 
            textvariable=self.vlm_var, 
            values=["LM_STUDIO", "GROQ"],
            state="readonly",
            width=15)
        self.vlm_combo.pack(side='left', padx=10)
        self.vlm_combo.bind("<<ComboboxSelected>>", self._on_vlm_change)
        
        # Buttons
        self.start_btn = tk.Button(control_frame,
            text="▶ START Monitoring",
            command=self.toggle_monitoring,
            font=('Segoe UI', 11, 'bold'),
            bg=self.colors['success'],
            fg='#000000',
            width=20,
            relief='flat',
            cursor='hand2')
        self.start_btn.pack()
        
        # Log Area
        log_frame = tk.Frame(self.root, bg=self.colors['bg'])
        log_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        tk.Label(log_frame, text="Activity Log:", bg=self.colors['bg'], fg='#aaaaaa').pack(anchor='w')
        
        self.log_text = scrolledtext.ScrolledText(log_frame,
            height=12,
            bg='#000000',
            fg='#00ff00',
            font=('Consolas', 9))
        self.log_text.pack(fill='both', expand=True)
        
    def _update_options(self):
        self.watcher.enable_auto_enter = self.var_auto_enter.get()
        self.watcher.enable_date_time = self.var_date_time.get()
        self.log_message(f"Options Updated: Enter={self.watcher.enable_auto_enter}, DateTime={self.watcher.enable_date_time}")

    def _on_vlm_change(self, event=None):
        vlm_handler.USE_PROVIDER = self.vlm_var.get()
        self.log_message(f"Provider switched to: {self.vlm_var.get()}")

    def log_message(self, message):
        def _update():
            self.log_text.insert('end', f"> {message}\n")
            self.log_text.see('end')
        self.root.after(0, _update)
        
    def toggle_monitoring(self):
        if self.watcher.is_running:
            self.watcher.stop()
            self.start_btn.config(text="▶ START Monitoring", bg=self.colors['success'])
            self.log_message("Monitoring STOPPED.")
        else:
            # Sync options before starting
            self._update_options()
            vlm_handler.USE_PROVIDER = self.vlm_var.get()
            
            self.watcher.start()
            self.start_btn.config(text="⏹ STOP Monitoring", bg=self.colors['accent'])
            self.log_message("Monitoring STARTED...")
            self.log_message(f"Using Provider: {vlm_handler.USE_PROVIDER}")

def main():
    root = tk.Tk()
    app = TicketParkAutoApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
