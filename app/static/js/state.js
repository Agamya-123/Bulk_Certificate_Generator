/**
 * Bulk Certificate Generator - Global State Management & Event Bus
 */

class EventEmitter {
  constructor() {
    this.events = {};
  }

  on(event, listener) {
    if (!this.events[event]) {
      this.events[event] = [];
    }
    this.events[event].push(listener);
    return () => this.off(event, listener);
  }

  off(event, listener) {
    if (!this.events[event]) return;
    this.events[event] = this.events[event].filter(l => l !== listener);
  }

  emit(event, data) {
    if (!this.events[event]) return;
    this.events[event].forEach(listener => {
      try {
        listener(data);
      } catch (err) {
        console.error(`Error in event listener for ${event}:`, err);
      }
    });
  }
}

export const bus = new EventEmitter();

export const state = {
  activeTab: 'generator', // 'generator' | 'monitor' | 'history' | 'verify'
  currentJobId: null,
  currentJobData: null,
  isPolling: false,
  pollTimer: null,
  apiHealthy: null,

  setTab(tab) {
    this.activeTab = tab;
    bus.emit('tab:changed', tab);
  },

  setCurrentJob(jobId, jobData = null) {
    this.currentJobId = jobId;
    this.currentJobData = jobData;
    bus.emit('job:selected', { jobId, jobData });
  },

  setApiHealth(isHealthy) {
    this.apiHealthy = isHealthy;
    bus.emit('health:changed', isHealthy);
  }
};
