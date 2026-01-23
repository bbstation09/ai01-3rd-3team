/**
 * HANDLE_CAPTCHA State - Detect and handle CAPTCHA
 */

class HandleCaptchaState extends BaseState {
  async onEnter(data) {
    await super.onEnter(data);
    logger.info('CAPTCHA_DETECTED');

    // Ensure persistence is set so we resume after reload
    try {
      sessionStorage.setItem('SWORD_RUNNING', 'true');
    } catch(e) {}

    // Show alert overlay
    this.showCaptchaAlert();

    // Play alert sound
    this.playAlertSound();

    // Focus input if found
    const config = getSiteConfig();
    if (config?.captcha?.input) {
      const input = smartSelect(config.captcha.input);
      if (input) {
        input.focus();
        input.style.border = '3px solid #f5576c';
        input.style.boxShadow = '0 0 10px #f5576c';
      }
    }

    // Start polling for CAPTCHA resolution
    this.startPolling();
  }

  showCaptchaAlert() {
    this.overlay = document.createElement('div');
    this.overlay.id = 'sword-captcha-alert';
    this.overlay.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100vh;
      background: rgba(255, 0, 0, 0.2);
      pointer-events: none;
      z-index: 999990;
      display: flex;
      justify-content: center;
      align-items: center;
    `;

    const box = document.createElement('div');
    box.style.cssText = `
      background: white;
      padding: 30px;
      border-radius: 15px;
      box-shadow: 0 10px 40px rgba(0,0,0,0.5);
      text-align: center;
      border: 4px solid #f5576c;
      pointer-events: auto;
      animation: pulse 1s infinite alternate;
    `;

    box.innerHTML = `
      <div style="font-size: 48px; margin-bottom: 20px;">🚨</div>
      <h2 style="margin: 0 0 10px; color: #f5576c;">CAPTCHA Detected!</h2>
      <p style="font-size: 18px; margin: 0 0 20px;">Please solve the CAPTCHA manually.</p>
      <div style="font-size: 14px; color: #666;">Automation paused. Resuming automatically when resolved.</div>
    `;

    const style = document.createElement('style');
    style.textContent = `
      @keyframes pulse {
        from { transform: scale(1); }
        to { transform: scale(1.05); }
      }
    `;

    this.overlay.appendChild(style);
    this.overlay.appendChild(box);
    document.body.appendChild(this.overlay);
  }

  playAlertSound() {
    // Simple beep pattern
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    
    const playBeep = (freq, duration, time) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.frequency.value = freq;
      osc.type = 'square';
      osc.start(time);
      osc.stop(time + duration);
    };

    const now = ctx.currentTime;
    playBeep(800, 0.1, now);
    playBeep(800, 0.1, now + 0.2);
    playBeep(800, 0.1, now + 0.4);
  }

  startPolling() {
    const config = getSiteConfig();
    let attempts = 0;

    this.pollInterval = setInterval(() => {
      attempts++;
      
      // Check if CAPTCHA elements are gone
      const captchaContainer = smartSelect(config.captcha.selectors);
      
      if (!captchaContainer) {
        // CAPTCHA gone!
        logger.info('CAPTCHA_RESOLVED');
        this.transitionTo('CLICK_START', {}, 'Captcha resolved');
        return;
      }

      // Or check if we navigated away (URL change)
      // This is handled automatically by page reload, but for SPA:
      if (!location.href.includes('captcha') && !document.querySelector('#captcha')) {
         logger.info('CAPTCHA_PAGE_EXITED');
         this.transitionTo('CLICK_START', {}, 'Navigated away from captcha');
         return;
      }

    }, 500);
  }

  async onExit() {
    if (this.pollInterval) clearInterval(this.pollInterval);
    if (this.overlay) this.overlay.remove();
    await super.onExit();
  }

  canTransition(targetState) {
    return ['CLICK_START', 'SELECT_ZONE', 'ERROR'].includes(targetState);
  }
}

if (typeof window !== 'undefined') {
  window.HandleCaptchaState = HandleCaptchaState;
}
