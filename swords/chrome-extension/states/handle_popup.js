/**
 * HANDLE_POPUP State - Close/accept popup dialogs
 */

class HandlePopupState extends BaseState {
  constructor() {
    super();
    this.popupTracker = new Set(); // Track seen popups
    this.maxPopups = 5; // Max popups to handle before giving up
    this.handledCount = 0;
  }

  async onEnter(data) {
    await super.onEnter(data);
    logger.info('HANDLE_POPUP_ENTER');
  }

  async execute() {
    const config = getSiteConfig();

    try {
      // Find popup
      const popup = smartSelect(config.selectors.popup);

      if (!popup) {
        // No popup found, proceed
        logger.info('NO_POPUP_FOUND');
        await this.transitionTo('SELECT_ZONE', {}, 'No popup to handle');
        return;
      }

      // Check if we've seen this popup before
      const fingerprint = DOMUtils.getElementFingerprint(popup);
      if (this.popupTracker.has(fingerprint)) {
        logger.warn('POPUP_LOOP_DETECTED', {fingerprint});
        
        if (this.handledCount >= this.maxPopups) {
          // Force close and continue
          popup.remove();
          await this.transitionTo('SELECT_ZONE', {}, 'Popup loop - forced continue');
          return;
        }
      }

      this.popupTracker.add(fingerprint);
      this.handledCount++;

      logger.info('POPUP_DETECTED', {
        fingerprint,
        count: this.handledCount
      });

      // Try to find close button
      const closeButton = smartSelect(config.selectors.popupClose, popup);

      if (closeButton) {
        await this.safeClick(closeButton, 100);
        logger.info('POPUP_CLOSED_VIA_BUTTON');
      } else {
        // Try clicking overlay to close
        popup.click();
        logger.info('POPUP_CLOSED_VIA_OVERLAY');
      }

      // Wait for popup to disappear
      await sleep(300);

      // Check if popup is gone
      const stillThere = smartSelect(config.selectors.popup);
      if (stillThere) {
        // Popup still exists, try again
        logger.warn('POPUP_STILL_EXISTS');
        await this.execute();
      } else {
        // Popup closed, check for more
        await sleep(200);
        const anotherPopup = smartSelect(config.selectors.popup);
        
        if (anotherPopup && this.handledCount < this.maxPopups) {
          // Handle next popup
          logger.info('ANOTHER_POPUP_DETECTED');
          await this.execute();
        } else {
          // All popups handled
          logger.info('ALL_POPUPS_HANDLED', {count: this.handledCount});
          await this.transitionTo('SELECT_ZONE', {}, 'Popups handled');
        }
      }

    } catch (error) {
      logger.error('HANDLE_POPUP_ERROR', {error: error.message});
      
      // Try to force continue
      const popups = smartSelectAll(config.selectors.popup);
      popups.forEach(p => p.remove());
      
      await this.transitionTo('SELECT_ZONE', {}, 'Error handling popup - forced continue');
    }
  }

  async onExit() {
    this.popupTracker.clear();
    this.handledCount = 0;
    await super.onExit();
  }

  canTransition(targetState) {
    return ['SELECT_ZONE', 'CAPTCHA_SOLVE', 'ERROR'].includes(targetState);
  }
}

if (typeof window !== 'undefined') {
  window.HandlePopupState = HandlePopupState;
}
