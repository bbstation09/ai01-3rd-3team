/**
 * CLICK_START State - Find and click reservation button
 */

class ClickStartState extends BaseState {
  async onEnter(data) {
    await super.onEnter(data);
    logger.info('CLICK_START_ENTER');
  }

  async execute() {
    const config = getSiteConfig();
    const maxAttempts = config.retry.maxAttempts.clickStart;

      for (let attempt = 0; attempt < maxAttempts; attempt++) {
      try {
        logger.info('CLICK_START_ATTEMPT', {attempt: attempt + 1, max: maxAttempts});

        // 0. Check if we are already in Zone Selection phase (e.g. after CAPTCHA/Reload)
        if (config.selectors.zones) {
           const zones = DOMUtils.findVisibleElement(config.selectors.zones);
           if (zones) {
              logger.info('ZONES_DETECTED_SKIPPING_CLICK');
              await this.transitionTo('SELECT_ZONE', {}, 'Zones already visible');
              return;
           }
        }

        // 0.5 Check if we are already in Seat Selection phase
        if (config.selectors.seats) {
           const seats = DOMUtils.findVisibleElement(config.selectors.seats);
           if (seats) {
              logger.info('SEATS_DETECTED_SKIPPING_CLICK');
              await this.transitionTo('SELECT_SEAT', {}, 'Seats already visible');
              return;
           }
        }

        // 0.6 Check if we are in Payment/Discount phase (Step 2, 3, 4)
        if (location.href.includes('/step2') || 
            location.href.includes('/step3') || 
            location.href.includes('/step4') || 
            DOMUtils.findByText('할인 권종 선택') || 
            DOMUtils.findByText('수령 방법') ||
            DOMUtils.findByText('Discount')) {
            logger.info('PAYMENT_PAGE_DETECTED_SKIPPING_CLICK');
            await this.transitionTo('PAYMENT', {}, 'Payment page detected');
            return;
        }

        // Try to find VISIBLE button using smart selector first
        let button = DOMUtils.findVisibleElement(config.selectors.reserveButton);

        // Fallback: Find by text content if selector fails
        if (!button) {
          logger.debug('TRYING_TEXT_SEARCH', {texts: ['예매하기', '예매', 'Reserve', 'Book']});
          button = DOMUtils.findClickableByText('예매하기') 
                || DOMUtils.findClickableByText('예매') 
                || DOMUtils.findClickableByText('Reserve')
                || DOMUtils.findClickableByText('Book');
        }

        if (!button) {
          // Check if we are blocked by CAPTCHA
          let captchaDetected = false;
          
          // 1. Check configured selectors
          if (config.captcha && config.captcha.selectors) {
             const captcha = smartSelect(config.captcha.selectors);
             if (captcha) captchaDetected = true;
          }
          
          // 2. Fallback: Check for text "보안문자"
          if (!captchaDetected) {
             if (DOMUtils.findByText('보안문자') || DOMUtils.findByText('CAPTCHA')) {
                captchaDetected = true;
             }
          }

          if (captchaDetected) {
             await this.transitionTo('HANDLE_CAPTCHA', {}, 'Captcha detected instead of button');
             return;
          }

          // Wait and retry
          await sleep(config.timing.retryDelay * Math.pow(config.retry.backoffMultiplier, attempt));
          continue;
        }



        // Scroll into view
        await DOMUtils.scrollIntoView(button);

        // Click!
        await this.safeClick(button, config.timing.clickDelay);

        logger.info('RESERVE_BUTTON_CLICKED');

        // Wait a bit for page to react
        await sleep(500);

        // Check for popup or go to next state
        const hasPopup = smartSelect(config.selectors.popup);
        if (hasPopup) {
          await this.transitionTo('HANDLE_POPUP', {}, 'Popup detected');
        } else {
          await this.transitionTo('SELECT_ZONE', {}, 'No popup, proceeding to zone selection');
        }

        return;

      } catch (error) {
        logger.error('CLICK_START_ERROR', {
          attempt,
          error: error.message
        });

        if (attempt >= maxAttempts - 1) {
          this.throwRecoverable('Failed to click reserve button after ' + maxAttempts + ' attempts');
        }

        await sleep(config.timing.retryDelay * Math.pow(config.retry.backoffMultiplier, attempt));
      }
    }
  }

  canTransition(targetState) {
    return ['HANDLE_POPUP', 'SELECT_ZONE', 'SELECT_SEAT', 'HANDLE_CAPTCHA', 'PAYMENT', 'ERROR'].includes(targetState);
  }
}

if (typeof window !== 'undefined') {
  window.ClickStartState = ClickStartState;
}
