/**
 * DOM Utility Functions
 */

const DOMUtils = {
  /**
   * Wait for element with progressive backoff
   */
  async waitForElement(selector, maxTime = 10000) {
    const element = document.querySelector(selector);
    if (element) return element;

    const intervals = [100, 300, 500, 1000, 2000];
    let elapsed = 0;

    for (const interval of intervals) {
      try {
        const el = await this._waitWithTimeout(selector, interval);
        return el;
      } catch {
        elapsed += interval;
        if (elapsed >= maxTime) {
          throw new Error(`Timeout waiting for ${selector} after ${elapsed}ms`);
        }
      }
    }

    // Final attempt with remaining time
    const remaining = maxTime - elapsed;
    if (remaining > 0) {
      return await this._waitWithTimeout(selector, remaining);
    }

    throw new Error(`Timeout waiting for ${selector}`);
  },

  /**
   * Wait for ANY element in a list of selectors
   */
  async waitForAnyElement(selectors, timeout = 10000) {
    if (!Array.isArray(selectors)) selectors = [selectors];
    
    // Check if any exist immediately
    for (const selector of selectors) {
      if (document.querySelector(selector)) return document.querySelector(selector);
    }

    const startTime = Date.now();
    
    return new Promise((resolve, reject) => {
       const check = () => {
          for (const selector of selectors) {
             const el = document.querySelector(selector);
             if (el) {
                resolve(el);
                return;
             }
          }

          if (Date.now() - startTime >= timeout) {
             reject(new Error(`Timeout waiting for any of: ${selectors.join(', ')}`));
             return;
          }

          requestAnimationFrame(check);
       };
       check();
    });
  },

  _waitWithTimeout(selector, timeout) {
    return new Promise((resolve, reject) => {
      const element = document.querySelector(selector);
      if (element) return resolve(element);

      const observer = new MutationObserver(() => {
        const el = document.querySelector(selector);
        if (el) {
          observer.disconnect();
          resolve(el);
        }
      });

      observer.observe(document.body, {
        childList: true,
        subtree: true
      });

      setTimeout(() => {
        observer.disconnect();
        reject(new Error('Timeout'));
      }, timeout);
    });
  },

  /**
   * Check if element is ready for interaction
   */
  isElementReady(element) {
    if (!element) return false;
    if (element.disabled) return false;
    if (element.style.display === 'none') return false;
    if (element.style.visibility === 'hidden') return false;
    
    // Removed strict offsetParent check which fails for fixed/absolute elements
    // if (!element.offsetParent && element.tagName !== 'BODY') return false;

    const rect = element.getBoundingClientRect();
    if (rect.width <= 0 || rect.height <= 0) return false;

    // Check if element is within viewport (optional, but good for interactive elements)
    // const style = window.getComputedStyle(element);
    // if (style.opacity === '0') return false;

    return true;
  },

  /**
   * Safe click with validation
   */
  async safeClick(element, options = {}) {
    const { delay = 0, validate = true } = options;

    if (validate && !this.isElementReady(element)) {
      throw new Error('Element not ready for click');
    }

    if (delay > 0) await sleep(delay);

    // Try native click first
    try {
      element.click();
    } catch (e) {
      // Fallback to event dispatch
      element.dispatchEvent(new MouseEvent('click', {
        bubbles: true,
        cancelable: true,
        view: window
      }));
    }
  },

  /**
   * Extract data from window object (common pattern in ticketing sites)
   */
  extractPageData(key) {
    try {
      // Common patterns
      if (window[key]) return window[key];
      if (window.__INITIAL_STATE__?.[key]) return window.__INITIAL_STATE__[key];
      if (window.__APP_DATA__?.[key]) return window.__APP_DATA__[key];

      // Check embedded JSON scripts
      const scripts = document.querySelectorAll('script[type="application/json"]');
      for (const script of scripts) {
        try {
          const data = JSON.parse(script.textContent);
          if (data[key]) return data[key];
        } catch {}
      }

      return null;
    } catch (error) {
      logger.warn('EXTRACT_DATA_ERROR', {key, error: error.message});
      return null;
    }
  },

  /**
   * Scroll element into view smoothly
   */
  async scrollIntoView(element, options = {}) {
    const { behavior = 'smooth', block = 'center' } = options;
    
    element.scrollIntoView({ behavior, block });
    
    // Wait for scroll to complete
    await sleep(300);
  },

  /**
   * Get all elements matching selector that are actually visible
   */
  getVisibleElements(selector) {
    const elements = document.querySelectorAll(selector);
    return Array.from(elements).filter(el => this.isElementReady(el));
  },

  /**
   * Find first visible element from a list of selectors
   */
  findVisibleElement(selectorArray) {
    if (!Array.isArray(selectorArray)) selectorArray = [selectorArray];
    
    for (const selector of selectorArray) {
      const elements = document.querySelectorAll(selector);
      for (const el of elements) {
        if (this.isElementReady(el)) {
          return el;
        }
      }
    }
    return null;
  },

  /**
   * Wait for page to be fully loaded
   */
  async waitForPageLoad(timeout = 10000) {
    if (document.readyState === 'complete') return true;

    return new Promise((resolve, reject) => {
      const handler = () => {
        if (document.readyState === 'complete') {
          resolve(true);
        }
      };

      document.addEventListener('readystatechange', handler);

      setTimeout(() => {
        document.removeEventListener('readystatechange', handler);
        reject(new Error('Page load timeout'));
      }, timeout);
    });
  },

  /**
   * Create a fingerprint of an element (for popup detection)
   */
  getElementFingerprint(element) {
    const rect = element.getBoundingClientRect();
    return `${element.tagName}_${element.className}_${rect.width}x${rect.height}`;
  },

  /**
   * Remove element safely
   */
  removeElement(selector) {
    const elements = document.querySelectorAll(selector);
    elements.forEach(el => el.remove());
  },

  /**
   * Find element by text content (like jQuery :contains)
   * @param {string} text - Text to search for
   * @param {string} tagFilter - Optional tag filter (e.g., 'button', 'a')
   * @returns {Element|null}
   */
  findByText(text, tagFilter = null) {
    const selector = tagFilter || '*';
    const elements = document.querySelectorAll(selector);
    
    for (const el of elements) {
      // Check direct text content
      if (el.textContent.trim().includes(text)) {
        // Prefer the deepest matching element
        const children = el.querySelectorAll('*');
        for (const child of children) {
          if (child.textContent.trim() === text && this.isElementReady(child)) {
            return child;
          }
        }
        // Return parent if children don't match exactly
        if (this.isElementReady(el)) {
          return el;
        }
      }
    }
    return null;
  },

  /**
   * Find clickable element by text (button, a, or element with onclick)
   * @param {string} text - Text to search for
   * @returns {Element|null}
   */
  findClickableByText(text) {
    // Try common clickable elements first
    const clickableTags = ['button', 'a', '[onclick]', '[role="button"]', '.btn', '.button'];
    
    for (const selector of clickableTags) {
      const elements = document.querySelectorAll(selector);
      for (const el of elements) {
        if (el.textContent.trim().includes(text) && this.isElementReady(el)) {
          return el;
        }
      }
    }
    
    // Fallback to any element with the text
    return this.findByText(text);
  }
};

/**
 * Sleep utility
 */
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Smart selector helper - tries single selector or array of selectors
 */
function smartSelect(selectors) {
  if (!selectors) return null;
  if (typeof selectors === 'string') return document.querySelector(selectors);
  if (Array.isArray(selectors)) {
    for (const selector of selectors) {
      const el = document.querySelector(selector);
      if (el) return el;
    }
  }
  return null;
}

/**
 * Smart selector all - returns array of elements from single selector or array
 */
function smartSelectAll(selectors) {
  if (!selectors) return [];
  const results = new Set();
  
  const selectorList = Array.isArray(selectors) ? selectors : [selectors];
  
  for (const selector of selectorList) {
    const elements = document.querySelectorAll(selector);
    elements.forEach(el => results.add(el));
  }
  
  return Array.from(results);
}

// Export
if (typeof window !== 'undefined') {
  window.DOMUtils = DOMUtils;
  window.sleep = sleep;
  window.smartSelect = smartSelect;
  window.smartSelectAll = smartSelectAll;
}
