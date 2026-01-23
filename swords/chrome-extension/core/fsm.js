/**
 * Finite State Machine Core Engine
 * Manages state transitions, history, and context
 */

class FSM {
  constructor(initialState = 'IDLE') {
    this.states = new Map();
    this.currentState = initialState;
    this.previousState = null;
    this.history = [];
    this.context = {
      retryCount: 0,
      errors: [],
      startTime: null,
      config: {}
    };
    this.listeners = new Map();
    this.maxHistorySize = 50;
  }

  /**
   * Register a state handler
   */
  registerState(name, stateInstance) {
    stateInstance.fsm = this;
    stateInstance.name = name;
    this.states.set(name, stateInstance);
    return this;
  }

  /**
   * Transition to a new state
   */
  async transition(nextState, data = {}, reason = '') {
    if (!this.states.has(nextState)) {
      throw new Error(`Unknown state: ${nextState}`);
    }

    const currentHandler = this.states.get(this.currentState);
    const nextHandler = this.states.get(nextState);

    // Validation
    if (currentHandler && !currentHandler.canTransition(nextState)) {
      logger.warn('TRANSITION_BLOCKED', {
        from: this.currentState,
        to: nextState,
        reason: 'Validation failed'
      });
      return false;
    }

    logger.info('STATE_TRANSITION', {
      from: this.currentState,
      to: nextState,
      reason,
      data
    });

    try {
      // Exit current state
      if (currentHandler) {
        await currentHandler.onExit();
      }

      // Record history
      this.history.push({
        from: this.currentState,
        to: nextState,
        timestamp: Date.now(),
        reason,
        data: {...data}
      });

      // Trim history if too large
      if (this.history.length > this.maxHistorySize) {
        this.history = this.history.slice(-this.maxHistorySize);
      }

      // Update state
      this.previousState = this.currentState;
      this.currentState = nextState;

      // Emit transition event
      this.emit('transition', {
        from: this.previousState,
        to: nextState,
        data
      });

      // Enter new state
      await nextHandler.onEnter(data);

      // Auto-execute if state supports it
      if (typeof nextHandler.execute === 'function') {
        await nextHandler.execute();
      }

      return true;

    } catch (error) {
      logger.error('TRANSITION_ERROR', {
        from: this.currentState,
        to: nextState,
        error: error.message,
        stack: error.stack
      });

      // Transition to ERROR state
      if (nextState !== 'ERROR') {
        await this.handleError(error);
      }

      return false;
    }
  }

  /**
   * Handle errors by transitioning to ERROR state
   */
  async handleError(error) {
    this.context.errors.push({
      error: error.message,
      state: this.currentState,
      timestamp: Date.now(),
      stack: error.stack
    });

    await this.transition('ERROR', {
      error,
      recoverable: error.recoverable !== false
    }, 'Error occurred');
  }

  /**
   * Reset the FSM to initial state
   */
  async reset() {
    logger.info('FSM_RESET', {currentState: this.currentState});
    
    // Clear context but preserve config
    const savedConfig = this.context.config;
    this.context = {
      retryCount: 0,
      errors: [],
      startTime: null,
      config: savedConfig
    };

    await this.transition('IDLE', {}, 'Reset');
  }

  /**
   * Event emitter pattern
   */
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  emit(event, data) {
    if (this.listeners.has(event)) {
      for (const callback of this.listeners.get(event)) {
        try {
          callback(data);
        } catch (error) {
          logger.error('EVENT_LISTENER_ERROR', {event, error: error.message});
        }
      }
    }
  }

  /**
   * Get current state info
   */
  getState() {
    return {
      current: this.currentState,
      previous: this.previousState,
      context: {...this.context},
      history: this.history.slice(-10) // Last 10 transitions
    };
  }

  /**
   * Check if can transition to target state
   */
  canTransitionTo(targetState) {
    const currentHandler = this.states.get(this.currentState);
    return currentHandler ? currentHandler.canTransition(targetState) : false;
  }

  /**
   * Pause/Resume (useful for debugging)
   */
  pause() {
    this.paused = true;
    logger.info('FSM_PAUSED');
  }

  resume() {
    this.paused = false;
    logger.info('FSM_RESUMED');
  }

  /**
   * Execute current state (manual trigger)
   */
  async executeCurrent() {
    if (this.paused) {
      logger.warn('FSM_PAUSED', {action: 'execute blocked'});
      return;
    }

    const handler = this.states.get(this.currentState);
    if (handler && typeof handler.execute === 'function') {
      await handler.execute();
    }
  }
}

// Export for use in content script
if (typeof window !== 'undefined') {
  window.FSM = FSM;
}
