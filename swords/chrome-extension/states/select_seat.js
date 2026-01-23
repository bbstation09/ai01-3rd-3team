/**
 * SELECT_SEAT State - Select N seats based on preferences
 */

class SelectSeatState extends BaseState {
  async onEnter(data) {
    await super.onEnter(data);
    
    this.selectedSeats = [];
    this.targetCount = this.getContext().config.seatCount || 1;
    
    logger.info('SELECT_SEAT_ENTER', {targetCount: this.targetCount});
  }

  async execute() {
    const config = getSiteConfig();
    const prefs = config.seatPreferences;
    const maxAttempts = config.retry.maxAttempts.selectSeat;

    try {
      // Wait for seats to load
      await DOMUtils.waitForElement(config.selectors.seats[0], config.timing.pageLoadTimeout);

      // Get all available seats
      const availableSeats = this.getAvailableSeats();

      if (availableSeats.length === 0) {
        this.throwRecoverable('No available seats found');
      }

      logger.info('AVAILABLE_SEATS_FOUND', {count: availableSeats.length});

      // Filter out seats that are marked unavailable in context
      const context = this.getContext();
      const validSeats = availableSeats.filter(seat => 
        !context.unavailableSeats?.has(this.getSeatId(seat))
      );

      if (validSeats.length < this.targetCount) {
        this.throwRecoverable(`Insufficient valid seats: ${validSeats.length} < ${this.targetCount}`);
      }

      // Select seats based on preferences
      if (this.targetCount === 1) {
        await this.selectSingleSeat(validSeats);
      } else {
        await this.selectConsecutiveSeats(validSeats);
      }

      // Verify selection
      await sleep(300);
      
      if (this.selectedSeats.length === this.targetCount) {
        logger.info('SEATS_SELECTED_SUCCESS', {
          seats: this.selectedSeats.map(s => this.getSeatId(s))
        });

        this.updateContext({selectedSeats: this.selectedSeats});
        await this.transitionTo('CONFIRM', {}, 'Seats selected successfully');
      } else {
        this.throwRecoverable(`Selection mismatch: ${this.selectedSeats.length} !== ${this.targetCount}`);
      }

    } catch (error) {
      logger.error('SELECT_SEAT_ERROR', {error: error.message});
      throw error;
    }
  }

  getAvailableSeats() {
    const config = getSiteConfig();
    const seats = smartSelectAll(config.selectors.seats);
    
    // Filter to only visible and clickable
    return seats.filter(seat => DOMUtils.isElementReady(seat));
  }

  async selectSingleSeat(seats) {
    const config = getSiteConfig();
    const prefs = config.seatPreferences;

    // Sort by preference (center-most if preferCenter)
    if (prefs.preferCenter) {
      seats = this.sortByCenter(seats);
    }

    // Try seats in order until one succeeds
    for (let i = 0; i < seats.length && this.selectedSeats.length < 1; i++) {
      const seat = seats[i];
      
      try {
        await this.trySelectSeat(seat);
        this.selectedSeats.push(seat);
        break;
      } catch (error) {
        logger.warn('SEAT_SELECT_FAILED', {
          seat: this.getSeatId(seat),
          error: error.message
        });
        
        // Mark as unavailable
        const context = this.getContext();
        if (!context.unavailableSeats) {
          context.unavailableSeats = new Set();
        }
        context.unavailableSeats.add(this.getSeatId(seat));
      }
    }
  }

  async selectConsecutiveSeats(seats) {
    const config = getSiteConfig();
    const prefs = config.seatPreferences;

    // Group seats by row
    const rows = this.groupByRow(seats);

    // Try each row
    for (const [rowKey, rowSeats] of Object.entries(rows)) {
      if (rowSeats.length < this.targetCount) continue;

      // Sort by position
      rowSeats.sort((a, b) => this.getSeatPosition(a) - this.getSeatPosition(b));

      // Find consecutive group
      for (let i = 0; i <= rowSeats.length - this.targetCount; i++) {
        const group = rowSeats.slice(i, i + this.targetCount);
        
        // Check if consecutive
        if (this.isConsecutive(group, prefs.maxSeatsDistance)) {
          // Try to select all
          const success = await this.trySelectGroup(group);
          
          if (success) {
            this.selectedSeats = group;
            return;
          }
        }
      }
    }

    // Fallback: select any N seats
    logger.warn('CONSECUTIVE_NOT_FOUND', {message: 'Selecting non-consecutive seats'});
    await this.selectFallbackSeats(seats);
  }

  async selectFallbackSeats(seats) {
    for (let i = 0; i < seats.length && this.selectedSeats.length < this.targetCount; i++) {
      try {
        await this.trySelectSeat(seats[i]);
        this.selectedSeats.push(seats[i]);
      } catch (error) {
        logger.warn('FALLBACK_SEAT_FAILED', {seat: this.getSeatId(seats[i])});
      }
    }
  }

  async trySelectSeat(seat) {
    const config = getSiteConfig();
    
    await DOMUtils.scrollIntoView(seat);
    await this.safeClick(seat, config.timing.seatSelectDelay);
    
    // Verify click worked (seat should have 'selected' class or similar)
    await sleep(100);
    
    if (!this.isSeatSelected(seat)) {
      throw new Error('Seat click did not register');
    }
  }

  async trySelectGroup(seats) {
    const config = getSiteConfig();
    
    try {
      for (const seat of seats) {
        await this.trySelectSeat(seat);
      }
      return true;
    } catch (error) {
      // Deselect all
      for (const seat of seats) {
        if (this.isSeatSelected(seat)) {
          await this.safeClick(seat, 50);
        }
      }
      return false;
    }
  }

  sortByCenter(seats) {
    const containerWidth = document.querySelector('.seat-container')?.offsetWidth || window.innerWidth;
    const centerX = containerWidth / 2;

    return seats.sort((a, b) => {
      const aRect = a.getBoundingClientRect();
      const bRect = b.getBoundingClientRect();
      const aDist = Math.abs(aRect.left + aRect.width / 2 - centerX);
      const bDist = Math.abs(bRect.left + bRect.width / 2 - centerX);
      return aDist - bDist;
    });
  }

  groupByRow(seats) {
    const rows = {};
    
    seats.forEach(seat => {
      const row = this.getSeatRow(seat);
      if (!rows[row]) rows[row] = [];
      rows[row].push(seat);
    });

    return rows;
  }

  isConsecutive(seats, maxDistance) {
    for (let i = 0; i < seats.length - 1; i++) {
      const pos1 = this.getSeatPosition(seats[i]);
      const pos2 = this.getSeatPosition(seats[i + 1]);
      
      if (Math.abs(pos2 - pos1) > maxDistance) {
        return false;
      }
    }
    return true;
  }

  getSeatId(seat) {
    return seat.dataset.seatId || seat.id || seat.dataset.row + '-' + seat.dataset.col;
  }

  getSeatRow(seat) {
    return seat.dataset.row || seat.closest('[data-row]')?.dataset.row || '0';
  }

  getSeatPosition(seat) {
    return parseInt(seat.dataset.col || seat.dataset.position || '0');
  }

  isSeatSelected(seat) {
    return seat.classList.contains('selected') || 
           seat.dataset.seatStatus === 'selected' ||
           seat.getAttribute('aria-selected') === 'true';
  }

  canTransition(targetState) {
    return ['CONFIRM', 'ERROR'].includes(targetState);
  }
}

if (typeof window !== 'undefined') {
  window.SelectSeatState = SelectSeatState;
}
