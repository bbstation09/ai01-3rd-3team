/**
 * Error Recovery Manager
 */

class RecoveryManager {
  constructor() {
    this.strategies = new Map();
    this.initializeStrategies();
  }

  initializeStrategies() {
    // Network timeout
    this.registerStrategy('NETWORK_TIMEOUT', {
      maxRetries: 3,
      async recover(context, error) {
        logger.warn('RECOVERY_NETWORK_TIMEOUT', {attempt: context.retryCount});
        await sleep(1000 * Math.pow(1.5, context.retryCount));
        location.reload();
      },
      fallback: 'FAILED'
    });

    // Element not found
    this.registerStrategy('ELEMENT_NOT_FOUND', {
      maxRetries: 5,
      async recover(context, error) {
        logger.warn('RECOVERY_ELEMENT_NOT_FOUND', {
          selector: error.selector,
          attempt: context.retryCount
        });
        
        // Progressive wait
        await sleep(500 * Math.pow(1.2, context.retryCount));
        
        // Try scroll to trigger lazy loading
        window.scrollTo(0, document.body.scrollHeight / 2);
        await sleep(500);
      },
      fallback: 'ERROR'
    });

    // Seat conflict (someone else took it)
    this.registerStrategy('SEAT_CONFLICT', {
      maxRetries: 10,
      async recover(context, error) {
        logger.warn('RECOVERY_SEAT_CONFLICT', {
          seat: error.seat,
          attempt: context.retryCount
        });
        
        // Just wait briefly and try next seat
        await sleep(100);
        
        // Mark this seat as unavailable in context
        if (!context.unavailableSeats) {
          context.unavailableSeats = new Set();
        }
        if (error.seat) {
          context.unavailableSeats.add(error.seat);
        }
      },
      fallback: 'ERROR'
    });

    // Popup loop (same popup appears repeatedly)
    this.registerStrategy('POPUP_LOOP', {
      maxRetries: 3,
      async recover(context, error) {
        logger.warn('RECOVERY_POPUP_LOOP', {attempt: context.retryCount});
        
        // Force close and continue
        const popup = error.popup;
        if (popup) {
          popup.remove();
        }
        
        await sleep(500);
      },
      fallback: 'SKIP_POPUP'
    });

    // Page reload detected
    this.registerStrategy('PAGE_RELOAD', {
      maxRetries: 2,
      async recover(context, error) {
        logger.warn('RECOVERY_PAGE_RELOAD', {attempt: context.retryCount});
        
        // Wait for page to fully load
        await DOMUtils.waitForPageLoad();
        
        // Reset to appropriate state based on URL
        const url = location.href;
        if (url.includes('/seat')) {
          return 'SELECT_ZONE';
        } else if (url.includes('/book')) {
          return 'CLICK_START';
        }
        
        return 'WAIT_OPEN';
      },
      fallback: 'FAILED'
    });

    // CAPTCHA failure
    this.registerStrategy('CAPTCHA_FAILED', {
      maxRetries: 1,
      async recover(context, error) {
        logger.error('RECOVERY_CAPTCHA_FAILED', {error: error.message});
        
        // Try auto-solver once, then require manual
        if (context.retryCount === 0) {
          await sleep(1000);
          return 'CAPTCHA_SOLVE';
        }
        
        // Show notification to user
        this.notifyManualCaptcha();
      },
      fallback: 'MANUAL_REQUIRED'
    });

    // Button disabled
    this.registerStrategy('BUTTON_DISABLED', {
      maxRetries: 5,
      async recover(context, error) {
        logger.warn('RECOVERY_BUTTON_DISABLED', {
          button: error.button,
          attempt: context.retryCount
        });
        
        // Wait for button to become enabled
        const delay = 500 * Math.pow(1.3, context.retryCount);
        await sleep(delay);
      },
      fallback: 'ERROR'
    });
  }

  registerStrategy(errorType, strategy) {
    this.strategies.set(errorType, strategy);
  }

  async handle(error, context) {
    const errorType = error.type || 'UNKNOWN';
    const strategy = this.strategies.get(errorType);

    if (!strategy) {
      logger.error('UNKNOWN_ERROR_TYPE', {type: errorType, message: error.message});
      return 'FAILED';
    }

    // Check retry limit
    if (context.retryCount >= strategy.maxRetries) {
      logger.error('MAX_RETRIES_EXCEEDED', {
        type: errorType,
        maxRetries: strategy.maxRetries
      });
      return strategy.fallback || 'FAILED';
    }

    // Execute recovery strategy
    try {
      const result = await strategy.recover(context, error);
      
      // If recovery returns a state, transition to it
      if (typeof result === 'string') {
        return result;
      }
      
      // Otherwise, retry current state
      return 'RETRY';
      
    } catch (recoveryError) {
      logger.error('RECOVERY_FAILED', {
        type: errorType,
        error: recoveryError.message
      });
      return strategy.fallback || 'FAILED';
    }
  }

  notifyManualCaptcha() {
    // Send message to popup UI
    chrome.runtime.sendMessage({
      type: 'MANUAL_ACTION_REQUIRED',
      payload: {
        action: 'SOLVE_CAPTCHA',
        message: 'Please solve the CAPTCHA manually'
      }
    });
  }

  /**
   * Create error with metadata
   */
  static createError(type, message, metadata = {}) {
    const error = new Error(message);
    error.type = type;
    error.recoverable = metadata.recoverable !== false;
    Object.assign(error, metadata);
    return error;
  }
}

// Export
if (typeof window !== 'undefined') {
  window.RecoveryManager = RecoveryManager;
}
