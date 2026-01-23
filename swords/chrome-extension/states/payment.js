/**
 * PAYMENT State - Terminal success state
 */

class PaymentState extends BaseState {
  async onEnter(data) {
    await super.onEnter(data);
    
    const context = this.getContext();
    const elapsed = Date.now() - context.startTime;

    logger.info('PAYMENT_SUCCESS', {
      totalTime: elapsed,
      seats: context.selectedSeats?.map(s => this.getSeatId(s))
    });

    // Notify user (only if chrome API available)
    if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.sendMessage) {
      try {
        chrome.runtime.sendMessage({
          type: 'AUTOMATION_SUCCESS',
          payload: {
            message: '🎉 Successfully reached payment page!',
            elapsed,
            seats: context.selectedSeats?.length || 0
          }
        });
      } catch (e) {
        // Ignore if background not available
      }
    }

    // Play success sound (if permission granted)
    this.playSuccessSound();

    // Show visual notification
    this.showSuccessOverlay();
  }

  injectAutoAccept() {
    // Override native dialogs to auto-accept
    const script = document.createElement('script');
    script.textContent = `
      window.confirm = () => true;
      window.alert = () => true;
      window.onbeforeunload = null;
    `;
    (document.head || document.documentElement).appendChild(script);
    script.remove();
  }

  getSeatId(seat) {
    if (!seat) return 'unknown';
    return seat.dataset?.seatId || seat.id || 'seat';
  }

  playSuccessSound() {
    try {
      const audio = new Audio('data:audio/wav;base64,UklGRhYAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=');
      audio.play().catch(() => {});
    } catch (e) {}
  }

  showSuccessOverlay() {
    const overlay = document.createElement('div');
    overlay.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 20px 30px;
      border-radius: 10px;
      box-shadow: 0 10px 40px rgba(0,0,0,0.3);
      z-index: 999999;
      font-family: Arial, sans-serif;
      font-size: 16px;
      animation: slideIn 0.5s ease-out;
    `;

    overlay.innerHTML = `
      <div style="display: flex; align-items: center; gap: 15px;">
        <div style="font-size: 32px;">🎉</div>
        <div>
          <div style="font-weight: bold; font-size: 18px;">Automation Complete!</div>
          <div style="font-size: 14px; opacity: 0.9;">Payment page reached successfully</div>
        </div>
      </div>
    `;

    document.body.appendChild(overlay);

    // Remove after 5 seconds
    setTimeout(() => {
      overlay.style.animation = 'slideOut 0.5s ease-in';
      setTimeout(() => overlay.remove(), 500);
    }, 5000);

    // Add animations
    if (!document.querySelector('#sword-overlay-animations')) {
      const style = document.createElement('style');
      style.id = 'sword-overlay-animations';
      style.textContent = `
        @keyframes slideIn {
          from {
            transform: translateX(400px);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
        @keyframes slideOut {
          from {
            transform: translateX(0);
            opacity: 1;
          }
          to {
            transform: translateX(400px);
            opacity: 0;
          }
        }
      `;
      document.head.appendChild(style);
    }
  }

  async execute() {
    const config = getSiteConfig();
    const maxAttempts = 5;

    try {
      logger.info('PAYMENT_EXECUTE');

      // 1. Handle Discount Selection (Step 2)
      if (DOMUtils.findByText('할인 권종 선택') || location.href.includes('step2')) {
          // Check for "General" or default discount option
          const generalDiscount = DOMUtils.findClickableByText('일반') || 
                                DOMUtils.findClickableByText('General');
          
          if (generalDiscount && DOMUtils.isElementReady(generalDiscount)) {
            logger.info('SELECTING_GENERAL_DISCOUNT');
            await this.safeClick(generalDiscount, 200);
          }
      }

      // 2. Handle Delivery Method (Step 3)
      if (DOMUtils.findByText('수령 방법') || location.href.includes('step3')) {
          logger.info('HANDLING_DELIVERY_METHOD');
          
          // Prefer "Mobile Ticket" or "On-site Pickup"
          const deliveryMethods = [
              '현장수령', '모바일티켓', 'Mobile Ticket', 'On-site Pickup', 'Ticket Pickup'
          ];
          
          let selectedMethod = null;
          for (const method of deliveryMethods) {
              const el = DOMUtils.findClickableByText(method);
              if (el && DOMUtils.isElementReady(el)) {
                  selectedMethod = el;
                  logger.info('SELECTING_DELIVERY_METHOD', {method});
                  break;
              }
          }

          if (selectedMethod) {
              await this.safeClick(selectedMethod, 200);
          } else {
             // Fallback: Click the first available option
             const firstOption = document.querySelector('.delivery-option, .radio-label');
             if (firstOption) {
                 logger.info('SELECTING_FALLBACK_DELIVERY');
                 await this.safeClick(firstOption, 200);
             }
          }
      }

      // 3. Handle Payment Method & Final Submit (Step 4)
      if (DOMUtils.findByText('결제 수단 선택') || location.href.includes('step4')) {
          logger.info('HANDLING_PAYMENT_METHOD');

          // 1. Select Payment Method (User requested Bank Transfer)
          // Try "Bank Transfer" (계좌이체) first, then others
          const paymentMethods = ['계좌이체', 'Bank Transfer', '무통장입금'];
          let paymentSelected = false;

          for (const method of paymentMethods) {
              const el = DOMUtils.findClickableByText(method);
              if (el && DOMUtils.isElementReady(el)) {
                  logger.info('SELECTING_PAYMENT_METHOD', {method});
                  await this.safeClick(el, 200);
                  paymentSelected = true;
                  break;
              }
          }

          if (!paymentSelected) {
              logger.warn('PREFERRED_PAYMENT_NOT_FOUND', {preferred: paymentMethods});
              // Fallback: Default selection might already be active
          }
          
          // 2. Click Final Payment Button
          // Button text might be "220,000원 결제하기"
          const payBtns = [
              '결제하기', 
              'Pay Now', 
              '원 결제하기' // Partial match for price + text
          ];
          
          let payBtn = null;
          for (const text of payBtns) {
              payBtn = DOMUtils.findClickableByText(text);
              if (payBtn) break;
          }

          if (payBtn && DOMUtils.isElementReady(payBtn)) {
             logger.info('CLICKING_FINAL_PAYMENT_BUTTON');
             
             // Auto-accept native confirms just in case
             this.injectAutoAccept();

             await DOMUtils.scrollIntoView(payBtn);
             await this.safeClick(payBtn, config.timing.clickDelay);
             
             // Wait for potential DOM confirmation dialog
             await sleep(1000);
             
             // Handle DOM popup confirmation if it appears
             // Look for "OK", "Confirm", "확인" in a popup/modal
             const confirmTexts = ['확인', 'Confirm', 'Yes', 'OK'];
             for (const text of confirmTexts) {
                 const confirmBtn = DOMUtils.findClickableByText(text);
                 // Only click if it's inside a popup/modal or generally visible on top
                 if (confirmBtn && DOMUtils.isElementReady(confirmBtn)) {
                     // Check if it looks like a popup button (z-index check or parent check could be added)
                     logger.info('CLICKING_CONFIRMATION_DIALOG', {text});
                     await this.safeClick(confirmBtn, 200);
                     break;
                 }
             }

          } else {
             logger.warn('FINAL_PAYMENT_BUTTON_NOT_FOUND');
          }
          
          return; // Step 4 is the end
      }

      // 4. General "Next Step" Click (for Steps 1-3)
      const nextBtnText = ['다음 단계', 'Next Step', 'Payment', '결제하기'];
      let nextBtn = null;

      for (const text of nextBtnText) {
         nextBtn = DOMUtils.findClickableByText(text);
         if (nextBtn) break;
      }
      
      // Fallback selector
      if (!nextBtn) {
        nextBtn = document.querySelector('#btnNextStep') || 
                  document.querySelector('.btn-next-step');
      }

      if (nextBtn && DOMUtils.isElementReady(nextBtn)) {
        logger.info('CLICKING_PAYMENT_NEXT_BUTTON');
        await DOMUtils.scrollIntoView(nextBtn);
        await this.safeClick(nextBtn, config.timing.clickDelay);
        
        // Wait for final confirmation or success
        await sleep(2000);
        
        // Assuming this leads to final success or another step
        // For now, we treat this as success of the automation flow
      } else {
         logger.warn('PAYMENT_NEXT_BUTTON_NOT_FOUND');
      }

    } catch (e) {
      logger.error('PAYMENT_EXECUTION_ERROR', {error: e.message});
      // Don't throw, let the user take over if automation fails here
    }
  }

  canTransition(targetState) {
    // Can only transition to IDLE (reset) or ERROR
    return ['IDLE', 'ERROR'].includes(targetState);
  }
}

if (typeof window !== 'undefined') {
  window.PaymentState = PaymentState;
}
