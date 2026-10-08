/**
 * Bulk Certificate Generator - Main SPA Controller
 */
import { ApiClient } from './api.js';
import { bus, state } from './state.js';
import { Toast } from './components/toast.js';
import { ModalManager } from './components/modal.js';
import { GeneratorComponent } from './components/generator.js';
import { MonitorComponent } from './components/monitor.js';
import { HistoryComponent } from './components/history.js';
import { VerifyComponent } from './components/verify.js';

class App {
  static init() {
    // 1. Initialize Sub-components
    Toast.init();
    ModalManager.init();
    GeneratorComponent.init();
    MonitorComponent.init();
    HistoryComponent.init();
    VerifyComponent.init();

    // 2. Navigation Tab Buttons
    this.navBtns = {
      generator: document.getElementById('nav-tab-generator'),
      monitor: document.getElementById('nav-tab-monitor'),
      history: document.getElementById('nav-tab-history'),
      verify: document.getElementById('nav-tab-verify'),
    };

    // Tab Views
    this.tabViews = {
      generator: document.getElementById('tab-generator'),
      monitor: document.getElementById('tab-monitor'),
      history: document.getElementById('tab-history'),
      verify: document.getElementById('tab-verify'),
    };

    // Live Server Health Indicator
    this.healthBadge = document.getElementById('server-health-badge');
    this.healthDot = document.getElementById('server-health-dot');
    this.healthText = document.getElementById('server-health-text');

    this.bindNavigation();
    this.checkInitialRoute();
    this.startHealthCheck();
  }

  static bindNavigation() {
    Object.keys(this.navBtns).forEach((tabKey) => {
      const btn = this.navBtns[tabKey];
      btn?.addEventListener('click', () => {
        state.setTab(tabKey);
      });
    });

    // Listen for tab changes from anywhere in the app
    bus.on('tab:changed', (newTab) => {
      this.switchTabUI(newTab);
    });
  }

  static switchTabUI(activeTab) {
    const activeClass = 'bg-amber-500/10 text-amber-300 border-amber-500/30';
    const inactiveClass = 'text-slate-400 hover:text-slate-200 border-transparent hover:bg-slate-800/40';

    Object.keys(this.navBtns).forEach((tabKey) => {
      const btn = this.navBtns[tabKey];
      const view = this.tabViews[tabKey];

      if (tabKey === activeTab) {
        btn?.classList.remove(...inactiveClass.split(' '));
        btn?.classList.add(...activeClass.split(' '));
        view?.classList.remove('hidden');
      } else {
        btn?.classList.remove(...activeClass.split(' '));
        btn?.classList.add(...inactiveClass.split(' '));
        view?.classList.add('hidden');
      }
    });

    // Update URL hash without scrolling
    if (window.location.hash !== `#${activeTab}`) {
      history.replaceState(null, '', `#${activeTab}${window.location.search}`);
    }
  }

  static checkInitialRoute() {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('code')) {
      state.setTab('verify');
      return;
    }

    const hash = window.location.hash.replace('#', '');
    if (hash && ['generator', 'monitor', 'history', 'verify'].includes(hash)) {
      state.setTab(hash);
    } else {
      state.setTab('generator');
    }
  }

  static async startHealthCheck() {
    const updateHealth = async () => {
      try {
        const res = await ApiClient.checkHealth();
        if (res.status === 'healthy') {
          if (this.healthDot) {
            this.healthDot.className = 'w-2 h-2 rounded-full bg-emerald-400 animate-pulse';
          }
          if (this.healthText) {
            this.healthText.textContent = `API Online (v${res.version})`;
            this.healthText.className = 'text-xs text-emerald-400 font-medium';
          }
        }
      } catch (err) {
        if (this.healthDot) {
          this.healthDot.className = 'w-2 h-2 rounded-full bg-rose-500';
        }
        if (this.healthText) {
          this.healthText.textContent = 'API Offline';
          this.healthText.className = 'text-xs text-rose-400 font-medium';
        }
      }
    };

    updateHealth();
    setInterval(updateHealth, 30000); // Check every 30s
  }
}

// Bootstrap once DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  App.init();
});
