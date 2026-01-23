/**
 * Background Service Worker (Manifest V3)
 * Handles persistent state and communication
 */

// State storage
let automationState = {
  running: false,
  currentState: 'IDLE',
  logs: [],
  tabs: new Map()
};

// Listen for extension installation
chrome.runtime.onInstalled.addListener((details) => {
  console.log('Sword Automation installed:', details.reason);
  
  if (details.reason === 'install') {
    // First install - set defaults
    chrome.storage.local.set({
      debugMode: false,
      seatCount: 1,
      autoRefresh: true
    });
  }
});

// Listen for messages from content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  handleMessage(message, sender, sendResponse);
  return true; // Keep async channel open
});

async function handleMessage(message, sender, sendResponse) {
  const tabId = sender.tab?.id;

  switch (message.type) {
    case 'CONTENT_READY':
      console.log('Content script ready', sender.tab?.url);
      automationState.tabs.set(tabId, {ready: true, url: sender.tab.url});
      sendResponse({success: true});
      break;

    case 'STATE_UPDATE':
      console.log('State update:', message.payload);
      automationState.currentState = message.payload.to;
      broadcastToPopup({
        type: 'STATE_CHANGED',
        payload: message.payload
      });
      sendResponse({success: true});
      break;

    case 'LOG':
      // Store log
      automationState.logs.push(message.payload);
      
      // Keep last 1000 logs
      if (automationState.logs.length > 1000) {
        automationState.logs = automationState.logs.slice(-1000);
      }
      break;

    case 'AUTOMATION_SUCCESS':
      console.log('✅ Automation succeeded!');
      automationState.running = false;
      
      // Show browser notification
      showNotification('Success!', message.payload.message);
      
      broadcastToPopup({
        type: 'AUTOMATION_COMPLETE',
        payload: message.payload
      });
      break;

    case 'AUTOMATION_FAILED':
      console.error('❌ Automation failed:', message.payload);
      automationState.running = false;
      
      showNotification('Failed', message.payload.message, 'error');
      
      broadcastToPopup({
        type: 'AUTOMATION_FAILED',
        payload: message.payload
      });
      break;

    case 'COUNTDOWN_UPDATE':
      // Forward to popup
      broadcastToPopup(message);
      break;

    case 'MANUAL_ACTION_REQUIRED':
      // Show notification that manual action is needed
      showNotification('Action Required', message.payload.message, 'warning');
      broadcastToPopup(message);
      break;

    case 'GET_LOGS':
      sendResponse({logs: automationState.logs});
      break;

    case 'CLEAR_LOGS':
      automationState.logs = [];
      sendResponse({success: true});
      break;

    default:
      console.warn('Unknown message type:', message.type);
  }
}

// Broadcast message to all extension popups
function broadcastToPopup(message) {
  chrome.runtime.sendMessage(message).catch(() => {
    // Popup might not be open
  });
}

// Show browser notification
function showNotification(title, message, type = 'info') {
  const iconMap = {
    info: 'icons/icon48.png',
    error: 'icons/icon48.png',
    warning: 'icons/icon48.png'
  };

  chrome.notifications.create({
    type: 'basic',
    iconUrl: iconMap[type],
    title: `Sword: ${title}`,
    message: message,
    priority: 2
  });
}

// Tab management
chrome.tabs.onRemoved.addListener((tabId) => {
  automationState.tabs.delete(tabId);
});

// Keep service worker alive (Manifest V3 workaround)
chrome.alarms.create('keepAlive', {periodInMinutes: 1});
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'keepAlive') {
    // Just ping to keep alive
  }
});

console.log('🗡️ Sword Background Service Worker ready');
