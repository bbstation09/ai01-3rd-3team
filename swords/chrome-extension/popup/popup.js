/**
 * Popup UI Controller
 */

document.addEventListener('DOMContentLoaded', () => {
  const ui = {
    status: document.getElementById('status'),
    countdown: document.getElementById('countdown'),
    hour: document.getElementById('hour'),
    minute: document.getElementById('minute'),
    second: document.getElementById('second'),
    seatCount: document.getElementById('seatCount'),
    autoRefresh: document.getElementById('autoRefresh'),
    debugMode: document.getElementById('debugMode'),
    btnStartNow: document.getElementById('btnStartNow'),
    btnStart: document.getElementById('btnStart'),
    btnStop: document.getElementById('btnStop'),
    btnReset: document.getElementById('btnReset'),
    logs: document.getElementById('logs'),
    btnClearLogs: document.getElementById('btnClearLogs')
  };

  let isRunning = false;

  // Load saved settings
  chrome.storage.local.get(['seatCount', 'autoRefresh', 'debugMode'], (result) => {
    ui.seatCount.value = result.seatCount || 1;
    ui.autoRefresh.checked = result.autoRefresh !== false;
    ui.debugMode.checked = result.debugMode || false;
  });

  // **NEW: Immediate Start Button**
  ui.btnStartNow.addEventListener('click', async () => {
    const config = {
      targetTime: Date.now() - 1000, // 1초 전 = 즉시 실행
      seatCount: parseInt(ui.seatCount.value),
      autoRefresh: false // 즉시 실행은 refresh 안함
    };

    await startAutomation(config);
  });

  // Start button
  ui.btnStart.addEventListener('click', async () => {
    const config = {
      targetTime: getTargetTime(),
      seatCount: parseInt(ui.seatCount.value),
      autoRefresh: ui.autoRefresh.checked
    };

    await startAutomation(config);
  });

  // **Shared start function**
  async function startAutomation(config) {
    // Save settings
    chrome.storage.local.set({
      seatCount: config.seatCount,
      autoRefresh: config.autoRefresh
    });

    // Get active tab
    const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
    
    if (!tab) {
      showError('활성화된 탭이 없습니다.');
      return;
    }

    // Check if scripts already loaded
    const isLoaded = await checkScriptsLoaded(tab.id);
    
    // Inject content scripts dynamically if NOT already loaded
    if (!isLoaded && !tab.url.includes('file://')) {
      try {
        await injectScripts(tab.id);
        addLog('📦 스크립트 주입 완료', 'info');
        await sleep(500); // Wait for scripts to load
      } catch (error) {
        showError('스크립트 주입 실패: ' + error.message);
        addLog('❌ Injection failed: ' + error.message, 'error');
        return;
      }
    } else if (isLoaded) {
      addLog('✅ 스크립트 이미 로드됨', 'info');
    }

    // Small delay for file:// URLs
    if (tab.url.includes('file://')) {
      await sleep(200);
    }

    // Execute start automation with retry logic
    try {
      let success = false;
      let lastError = '';
      const maxRetries = 5;
      
      for (let attempt = 1; attempt <= maxRetries && !success; attempt++) {
        console.log(`[Popup] Attempt ${attempt}/${maxRetries}...`);
        
        const result = await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          world: 'MAIN',  // ← CRITICAL: Must match content_scripts world
          func: (cfg) => {
            console.log('[Popup] Checking SwordAutomation...', typeof window.SwordAutomation);
            if (typeof window.SwordAutomation !== 'undefined') {
              console.log('[Popup] Starting automation with config:', cfg);
              window.SwordAutomation.startAutomation(cfg);
              return { success: true };
            }
            console.error('[Popup] SwordAutomation not found!');
            return { success: false, error: 'SwordAutomation not found' };
          },
          args: [config]
        });

        console.log('[Popup] executeScript result:', result);

        if (result && result[0] && result[0].result && result[0].result.success) {
          success = true;
          isRunning = true;
          updateUI();
          addLog('✅ 자동화 시작!', 'success');
        } else {
          lastError = result && result[0] && result[0].result ? result[0].result.error : 'Unknown error';
          if (attempt < maxRetries) {
            addLog(`⏳ SwordAutomation 대기 중... (${attempt}/${maxRetries})`, 'info');
            await sleep(300); // Wait before retry
          }
        }
      }
      
      if (!success) {
        showError('SwordAutomation이 초기화되지 않았습니다. 페이지를 새로고침하세요.');
        addLog('❌ Start failed: ' + lastError, 'error');
      }
    } catch (error) {
      showError('실행 실패: ' + error.message);
      addLog('❌ Execution error: ' + error.message, 'error');
    }
  }

  // Check if scripts already loaded
  async function checkScriptsLoaded(tabId) {
    try {
      const result = await chrome.scripting.executeScript({
        target: { tabId },
        world: 'MAIN',
        func: () => {
          return typeof window.SwordAutomation !== 'undefined';
        }
      });
      return result && result[0] && result[0].result;
    } catch {
      return false;
    }
  }

  // Dynamic script injection
  async function injectScripts(tabId) {
    const scripts = [
      'config/sites.js',
      'utils/logger.js',
      'utils/dom.js',
      'core/recovery.js',
      'core/fsm.js',
      'states/base.js',
      'states/idle.js',
      'states/wait_open.js',
      'states/click_start.js',
      'states/handle_popup.js',
      'states/select_zone.js',
      'states/select_seat.js',
      'states/confirm.js',
      'states/payment.js',
      'states/error.js',
      'content.js'
    ];

    for (const file of scripts) {
      await chrome.scripting.executeScript({
        target: { tabId },
        files: [file]
      });
    }
  }

  function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // Stop button
  ui.btnStop.addEventListener('click', async () => {
    const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
    
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      world: 'MAIN',
      func: () => {
        if (window.SwordAutomation) {
          window.SwordAutomation.stopAutomation();
        }
      }
    });

    isRunning = false;
    updateUI();
    addLog('Stopped', 'warn');
  });

  // Reset button
  ui.btnReset.addEventListener('click', async () => {
    const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
    
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      world: 'MAIN',
      func: () => {
        if (window.SwordAutomation && window.SwordAutomation.fsm) {
          window.SwordAutomation.fsm.reset();
        }
      }
    });

    ui.status.textContent = 'IDLE';
    ui.countdown.textContent = '';
    addLog('Reset', 'info');
  });

  // Debug mode toggle
  ui.debugMode.addEventListener('change', async () => {
    chrome.storage.local.set({debugMode: ui.debugMode.checked});
    
    const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      world: 'MAIN',
      func: () => {
        if (window.SwordAutomation) {
          window.SwordAutomation.toggleDebugOverlay();
        }
      }
    });
  });

  // Clear logs
  ui.btnClearLogs.addEventListener('click', () => {
    ui.logs.innerHTML = '';
    chrome.runtime.sendMessage({type: 'CLEAR_LOGS'});
  });

  // Listen for background messages
  chrome.runtime.onMessage.addListener((message) => {
    switch (message.type) {
      case 'STATE_CHANGED':
        ui.status.textContent = message.payload.to;
        addLog(`State: ${message.payload.to}`, 'info');
        break;

      case 'COUNTDOWN_UPDATE':
        ui.countdown.textContent = message.payload.formatted;
        break;

      case 'AUTOMATION_COMPLETE':
        isRunning = false;
        updateUI();
        ui.status.textContent = 'SUCCESS';
        ui.status.style.color = '#00ff88';
        addLog('✅ Automation complete!', 'success');
        break;

      case 'AUTOMATION_FAILED':
        isRunning = false;
        updateUI();
        ui.status.textContent = 'FAILED';
        ui.status.style.color = '#ff4444';
        addLog(`❌ Failed: ${message.payload.reason}`, 'error');
        break;
    }
  });

  // Helper functions
  function getTargetTime() {
    const now = new Date();
    const target = new Date(
      now.getFullYear(),
      now.getMonth(),
      now.getDate(),
      parseInt(ui.hour.value),
      parseInt(ui.minute.value),
      parseInt(ui.second.value)
    );

    // If time is in the past, add 1 day
    if (target < now) {
      target.setDate(target.getDate() + 1);
    }

    return target.getTime();
  }

  function updateUI() {
    ui.btnStart.disabled = isRunning;
    ui.btnStop.disabled = !isRunning;
  }

  function addLog(message, level = 'info') {
    const entry = document.createElement('div');
    entry.className = `log-entry log-${level}`;
    entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    
    ui.logs.prepend(entry);

    // Keep last 50 entries
    while (ui.logs.children.length > 50) {
      ui.logs.lastChild.remove();
    }
  }

  function showError(message) {
    const error = document.createElement('div');
    error.className = 'error-message';
    error.textContent = message;
    document.body.appendChild(error);

    setTimeout(() => error.remove(), 3000);
  }

  // Initial state update
  updateUI();
  addLog('Extension ready', 'info');
});
