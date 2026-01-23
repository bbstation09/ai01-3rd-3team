"""
🔐 CAPTCHA VLM Solver
Standalone application to detect and solve CAPTCHAs using VLM.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading

# Add current directory to path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.popup_watcher import PopupWatcher
from modules import vlm_handler
from modules.vlm_handler import encode_image_to_base64, call_vlm, capture_screen, click_and_restore
import time
import pyautogui

class CaptchaOnlyWatcher(PopupWatcher):
    """Subclass that ONLY handles CAPTCHA"""
    
    def _detect_and_handle_popup(self):
        """Override to focus only on CAPTCHA"""
        # Capture screen
        screenshot = capture_screen(self.mon_x, self.mon_y, self.mon_w, self.mon_h)
        width, height = screenshot.size
        base64_image = encode_image_to_base64(screenshot)
        
        # Specific Prompt for CAPTCHA ONLY
        prompt = f"""Screenshot size: {width}x{height} pixels.

Analyze for CAPTCHA popup.
1. Identify the distorted characters (e.g. VMCGHV).
2. Identify the input text box below the characters. It usually has the placeholder text "문자 입력".

Task:
- Extract the characters into "text".
- Calculate the CENTER coordinates (0.0 to 1.0) of the "문자 입력" input box.

Return JSON only:
{{"type":"CAPTCHA", "text":"CHARS", "x":0.xx, "y":0.xx}}

If no CAPTCHA popup is visible, return:
{{"type":"NONE"}}"""

        result = call_vlm(prompt, base64_image, max_tokens=150)
        
        if not result:
            return False
            
        p_type = result.get("type", "NONE").upper()
        p_text = result.get("text", "")
        raw_x = float(result.get("x", 0))
        raw_y = float(result.get("y", 0))
        
        # Only process CAPTCHA
        if p_type == "CAPTCHA":
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
        
        return False


class CaptchaSolverApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🔐 CAPTCHA Auto-Solver (VLM)")
        self.root.geometry("500x400")
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
        self.watcher = CaptchaOnlyWatcher(callback=self.log_message)
        
        self._setup_ui()
        
    def _setup_ui(self):
        # Header
        header = tk.Label(self.root, 
            text="🔐 CAPTCHA VLM Solver",
            font=('Segoe UI', 16, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['text'])
        header.pack(pady=15)
        
        # Controls Frame
        control_frame = tk.Frame(self.root, bg=self.colors['card'], padx=20, pady=20)
        control_frame.pack(fill='x', padx=20)
        
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
            height=10,
            bg='#000000',
            fg='#00ff00',
            font=('Consolas', 9))
        self.log_text.pack(fill='both', expand=True)
        
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
            # Update VLM config before starting
            vlm_handler.USE_PROVIDER = self.vlm_var.get()
            
            self.watcher.start()
            self.start_btn.config(text="⏹ STOP Monitoring", bg=self.colors['accent'])
            self.log_message("Monitoring STARTED...")
            self.log_message(f"Using Provider: {vlm_handler.USE_PROVIDER}")

def main():
    root = tk.Tk()
    app = CaptchaSolverApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
