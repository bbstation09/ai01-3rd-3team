/**
 * WAIT_OPEN State - Countdown to open time
 */

class WaitOpenState extends BaseState {
  async onEnter(data) {
    await super.onEnter(data);
    
    this.targetTime = data.targetTime;
    this.cancelled = false;
    
    logger.info('WAIT_OPEN_START', {
      targetTime: new Date(this.targetTime).toISOString(),
      remaining: this.targetTime - Date.now()
    });

    // Listen for cancel (only if chrome API available)
    this.cancelListener = (message) => {
      if (message.type === 'CANCEL') {
        this.handleCancel();
      }
    };
    if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.onMessage) {
      chrome.runtime.onMessage.addListener(this.cancelListener);
    }

    // Start countdown
    this.checkInterval = setInterval(() => this.checkTime(), 100);
  }

  async checkTime() {
    if (this.cancelled) return;

    const now = Date.now();
    const remaining = this.targetTime - now;

    // Update UI every second
    if (Math.floor(remaining / 1000) !== Math.floor(this.lastRemaining / 1000)) {
      this.sendProgress(remaining);
    }
    this.lastRemaining = remaining;

    // Time reached!
    if (remaining <= 0) {
      logger.info('OPEN_TIME_REACHED');
      
      // Refresh page if configured
      const config = this.getContext().config;
      if (config.autoRefresh) {
        location.reload();
        await sleep(1000); // Wait for reload
      }

      await this.transitionTo('CLICK_START', {}, 'Open time reached');
    }
  }

  sendProgress(remaining) {
    const seconds = Math.floor(remaining / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    // Only send if chrome API available
    if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.sendMessage) {
      try {
        chrome.runtime.sendMessage({
          type: 'COUNTDOWN_UPDATE',
          payload: {
            remaining,
            formatted: `${hours}:${(minutes % 60).toString().padStart(2, '0')}:${(seconds % 60).toString().padStart(2, '0')}`
          }
        });
      } catch (e) {}
    }
  }

  handleCancel() {
    this.cancelled = true;
    logger.info('WAIT_CANCELLED');
    this.transitionTo('IDLE', {}, 'User cancelled');
  }

  async onExit() {
    clearInterval(this.checkInterval);
    if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.onMessage) {
      try { chrome.runtime.onMessage.removeListener(this.cancelListener); } catch(e) {}
    }
    await super.onExit();
  }

  canTransition(targetState) {
    return ['CLICK_START', 'IDLE', 'ERROR'].includes(targetState);
  }
}

if (typeof window !== 'undefined') {
  window.WaitOpenState = WaitOpenState;
}
