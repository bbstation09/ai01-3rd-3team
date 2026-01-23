/**
 * SELECT_ZONE State - Choose seat section/zone
 */

class SelectZoneState extends BaseState {
  async onEnter(data) {
    await super.onEnter(data);
    logger.info('SELECT_ZONE_ENTER');
  }

  async execute() {
    const config = getSiteConfig();
    const prefs = config.seatPreferences;

    try {
      // Wait for any configured zone selector to appear
      await DOMUtils.waitForAnyElement(config.selectors.zones, config.timing.pageLoadTimeout);

      // Get all zones
      const zones = smartSelectAll(config.selectors.zones);

      if (zones.length === 0) {
        // No zones - might be direct seat selection
        logger.info('NO_ZONES_FOUND', {message: 'Proceeding directly to seat selection'});
        await this.transitionTo('SELECT_SEAT', {}, 'No zones to select');
        return;
      }

      logger.info('ZONES_FOUND', {count: zones.length});

      // Select zone based on preferences
      const selectedZone = this.selectPreferredZone(zones, prefs.zones);

      if (!selectedZone) {
        this.throwRecoverable('No valid zone found');
      }

      logger.info('ZONE_SELECTED', {
        zone: this.getZoneName(selectedZone)
      });

      // Click zone
      await DOMUtils.scrollIntoView(selectedZone);
      await this.safeClick(selectedZone, config.timing.clickDelay);

      // Wait a bit for UI update
      await sleep(300);

      // Check if there is a "Next" button (e.g. "좌석 선택하기")
      if (config.selectors.nextButton) {
        const nextBtn = DOMUtils.findVisibleElement(config.selectors.nextButton);
        if (nextBtn && DOMUtils.isElementReady(nextBtn)) {
          logger.info('CLICK_NEXT_BUTTON');
          await this.safeClick(nextBtn, 100);
        }
      }

      // Wait for seats to load
      await sleep(500);

      // Check if seats loaded
      const seatsLoaded = await this.waitForSeatsLoad();

      if (seatsLoaded) {
        await this.transitionTo('SELECT_SEAT', {
          zone: this.getZoneName(selectedZone)
        }, 'Zone selected, seats loaded');
      } else {
        this.throwRecoverable('Seats did not load after zone selection');
      }

    } catch (error) {
      logger.error('SELECT_ZONE_ERROR', {error: error.message});
      throw error;
    }
  }

  selectPreferredZone(zones, preferredNames) {
    // Try to match preferred zone names
    for (const prefName of preferredNames) {
      const zone = zones.find(z => {
        const name = this.getZoneName(z);
        return name.includes(prefName) || prefName.includes(name);
      });
      
      if (zone && DOMUtils.isElementReady(zone)) {
        return zone;
      }
    }

    // Fallback to first available zone
    return zones.find(z => DOMUtils.isElementReady(z));
  }

  getZoneName(zone) {
    return zone.textContent?.trim() || 
           zone.dataset.zoneName || 
           zone.dataset.zoneId || 
           zone.getAttribute('aria-label') || 
           'Unknown';
  }

  async waitForSeatsLoad(timeout = 5000) {
    const config = getSiteConfig();
    
    try {
      await DOMUtils.waitForElement(config.selectors.seats[0], timeout);
      return true;
    } catch {
      return false;
    }
  }

  canTransition(targetState) {
    return ['SELECT_SEAT', 'ERROR'].includes(targetState);
  }
}

if (typeof window !== 'undefined') {
  window.SelectZoneState = SelectZoneState;
}
