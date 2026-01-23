/**
 * IDLE State - Waiting for user to start
 */

class IdleState extends BaseState {
  async onEnter(data) {
    await super.onEnter(data);
    
    // Initialize context
    this.updateContext({
      retryCount: 0,
      errors: [],
      seats: [],
      selectedSeats: [],
      unavailableSeats: new Set(),
    });

    logger.info('IDLE_STATE', {message: 'Waiting for user to start'});
    
    // Listen for start command via postMessage (from content.js)
    this.startListener = (event) => {
      console.log('[IdleState] Received message:', event.data);
      if (event.data && event.data.type === 'START_AUTOMATION') {
        console.log('[IdleState] Handling START_AUTOMATION');
        this.handleStart(event.data.payload);
      }
    };

    window.addEventListener('message', this.startListener);
    console.log('[IdleState] Listener registered');
  }

  async handleStart(config) {
    console.log('[IdleState] handleStart called with:', config);
    logger.info('START_REQUESTED', config);
    
    // Store config in context
    this.updateContext({
      config,
      startTime: Date.now()
    });

    // Transition based on whether we have a target time
    if (config.targetTime && config.targetTime > Date.now()) {
      console.log('[IdleState] Transitioning to WAIT_OPEN');
      await this.transitionTo('WAIT_OPEN', {
        targetTime: config.targetTime
      }, 'User started with wait time');
    } else {
      console.log('[IdleState] Transitioning to CLICK_START');
      await this.transitionTo('CLICK_START', {}, 'User started immediately');
    }
  }

  async onExit() {
    window.removeEventListener('message', this.startListener);
    await super.onExit();
  }

  canTransition(targetState) {
    // Can only go to WAIT_OPEN or CLICK_START from IDLE
    return ['WAIT_OPEN', 'CLICK_START', 'ERROR'].includes(targetState);
  }
}

if (typeof window !== 'undefined') {
  window.IdleState = IdleState;
}
