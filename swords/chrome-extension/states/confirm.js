/**
 * CONFIRM State - Click confirmation button
 */

class ConfirmState extends BaseState {
  async onEnter(data) {
    await super.onEnter(data);
    logger.info('CONFIRM_ENTER');
  }

  async execute() {
    const config = getSiteConfig();
    const maxAttempts = config.retry.maxAttempts.confirm;

    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      try {
        logger.info('CONFIRM_ATTEMPT', {attempt: attempt + 1});

        // 1. Wait for ANY confirm button selector
        await DOMUtils.waitForAnyElement(
          config.selectors.confirmButton,
          config.timing.elementTimeout
        ).catch(() => logger.warn('WAIT_TIMEOUT', {attempt}));

        // 2. Try to find element using selectors
        let confirmBtn = smartSelect(config.selectors.confirmButton);

        // 3. Fallback: Find by text content (partial match)
        if (!confirmBtn) {
           const searchTexts = ['좌석 선택 완료', '좌석선택완료', 'Selection Complete', 'Next'];
           logger.debug('TRYING_TEXT_SEARCH', {texts: searchTexts});
           
           for (const text of searchTexts) {
             confirmBtn = DOMUtils.findClickableByText(text);
             if (confirmBtn) break;
           }
        }

        if (!confirmBtn) {
          logger.warn('CONFIRM_BUTTON_NOT_FOUND', {attempt});
          await sleep(config.timing.retryDelay);
          continue;
        }

        // Check if button is enabled
        if (!DOMUtils.isElementReady(confirmBtn)) {
          logger.warn('CONFIRM_BUTTON_DISABLED', {attempt});
          await sleep(config.timing.retryDelay);
          continue;
        }

        // Scroll and click
        await DOMUtils.scrollIntoView(confirmBtn);
        await this.safeClick(confirmBtn, config.timing.clickDelay);

        logger.info('CONFIRM_CLICKED');

        // Wait for navigation
        await sleep(1000);

        // Check if we're on payment page
        if (this.isPaymentPage()) {
          await this.transitionTo('PAYMENT', {}, 'Navigated to payment');
          return;
        } else {
          logger.warn('NOT_ON_PAYMENT_PAGE', {url: location.href});
          
          if (attempt < maxAttempts - 1) {
            await sleep(config.timing.retryDelay);
            continue;
          } else {
            this.throwRecoverable('Failed to reach payment page');
          }
        }

      } catch (error) {
        logger.error('CONFIRM_ERROR', {
          attempt,
          error: error.message
        });

        if (attempt >= maxAttempts - 1) {
          throw error;
        }

        await sleep(config.timing.retryDelay * Math.pow(1.5, attempt));
      }
    }
  }

  isPaymentPage() {
    return location.href.includes('/payment') ||
           location.href.includes('/checkout') ||
           location.href.includes('/order') ||
           document.querySelector('.payment-form') !== null ||
           document.querySelector('#payment') !== null;
  }

  canTransition(targetState) {
    return ['PAYMENT', 'ERROR'].includes(targetState);
  }
}

if (typeof window !== 'undefined') {
  window.ConfirmState = ConfirmState;
}
