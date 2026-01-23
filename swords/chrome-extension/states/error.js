/**
 * ERROR State - Handle errors and recovery
 */

class ErrorState extends BaseState {
  async onEnter(data) {
    await super.onEnter(data);
    
    this.error = data.error;
    this.recoverable = data.recoverable !== false;

    logger.error('ERROR_STATE_ENTER', {
      error: this.error?.message,
      type: this.error?.type,
      recoverable: this.recoverable,
      retryCount: this.getContext().retryCount
    });
  }

  async execute() {
    const context = this.getContext();
    const recoveryManager = new RecoveryManager();

    if (!this.recoverable) {
      // Fatal error - cannot recover
      logger.error('FATAL_ERROR', {error: this.error?.message});
      await this.transitionTo('FAILED', {
        reason: 'Fatal error',
        error: this.error
      });
      return;
    }

    // Increment retry counter
    context.retryCount++;

    // Try recovery
    try {
      const nextState = await recoveryManager.handle(this.error, context);

      logger.info('RECOVERY_DECISION', {
        nextState,
        retryCount: context.retryCount
      });

      if (nextState === 'RETRY') {
        // Retry the previous state
        const previousState = this.fsm.previousState;
        
        if (previousState && previousState !== 'ERROR') {
          await this.transitionTo(previousState, {}, 'Retrying after error');
        } else {
          // Can't retry, go to IDLE
          await this.transitionTo('IDLE', {}, 'Cannot retry, resetting');
        }
      } else if (nextState === 'FAILED') {
        // Recovery failed
        await this.transitionTo('FAILED', {
          reason: 'Recovery failed',
          error: this.error
        });
      } else {
        // Transition to suggested state
        await this.transitionTo(nextState, {}, 'Recovery suggested state');
      }

    } catch (recoveryError) {
      logger.error('RECOVERY_ERROR', {error: recoveryError.message});
      
      await this.transitionTo('FAILED', {
        reason: 'Recovery threw error',
        error: recoveryError
      });
    }
  }

  canTransition(targetState) {
    // Can transition anywhere from ERROR
    return true;
  }
}

/**
 * FAILED State - Terminal failure state
 */
class FailedState extends BaseState {
  async onEnter(data) {
    await super.onEnter(data);
    
    const context = this.getContext();

    logger.error('AUTOMATION_FAILED', {
      reason: data.reason,
      error: data.error?.message,
      totalTime: Date.now() - context.startTime,
      retryCount: context.retryCount,
      errors: context.errors
    });

    // Notify user (only if chrome API available)
    if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.sendMessage) {
      try {
        chrome.runtime.sendMessage({
          type: 'AUTOMATION_FAILED',
          payload: {
            message: '❌ Automation failed',
            reason: data.reason,
            error: data.error?.message,
            logs: logger.getLogs({level: 'ERROR'})
          }
        });
      } catch (e) {}
    }

    // Show failure notification
    this.showFailureNotification(data);
  }

  showFailureNotification(data) {
    const overlay = document.createElement('div');
    overlay.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
      color: white;
      padding: 20px 30px;
      border-radius: 10px;
      box-shadow: 0 10px 40px rgba(0,0,0,0.3);
      z-index: 999999;
      font-family: Arial, sans-serif;
      max-width: 400px;
    `;

    overlay.innerHTML = `
      <div style="font-weight: bold; font-size: 18px; margin-bottom: 10px;">❌ Automation Failed</div>
      <div style="font-size: 14px; opacity: 0.9; margin-bottom: 10px;">
        ${data.reason || 'Unknown error'}
      </div>
      <button style="
        background: white;
        color: #f5576c;
        border: none;
        padding: 8px 16px;
        border-radius: 5px;
        cursor: pointer;
        font-weight: bold;
      ">View Logs</button>
    `;

    const button = overlay.querySelector('button');
    button.addEventListener('click', () => {
      console.log('=== Automation Error Logs ===');
      console.log(logger.exportLogs());
    });

    document.body.appendChild(overlay);

    setTimeout(() => overlay.remove(), 10000);
  }

  async execute() {
    // Terminal state - no automatic transition
  }

  canTransition(targetState) {
    // Can only reset to IDLE
    return targetState === 'IDLE';
  }
}

if (typeof window !== 'undefined') {
  window.ErrorState = ErrorState;
  window.FailedState = FailedState;
}
