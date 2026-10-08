/**
 * Stacked Floating Toast Notifications
 */
export class Toast {
  static container = null;

  static init() {
    this.container = document.getElementById('toast-container');
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.id = 'toast-container';
      this.container.className = 'fixed bottom-5 right-5 z-50 flex flex-col space-y-3 max-w-md w-full px-4';
      document.body.appendChild(this.container);
    }
  }

  static show(message, type = 'info', duration = 4000) {
    this.init();

    const toast = document.createElement('div');
    toast.className = `flex items-center justify-between p-4 rounded-xl border shadow-xl backdrop-blur-md transform transition-all duration-300 translate-y-4 opacity-0 ${this._getTypeStyles(type)}`;

    const iconSvg = this._getIcon(type);

    toast.innerHTML = `
      <div class="flex items-start space-x-3">
        <div class="flex-shrink-0 mt-0.5">${iconSvg}</div>
        <div class="text-sm font-medium text-slate-100">${this._escapeHtml(message)}</div>
      </div>
      <button class="ml-4 text-slate-400 hover:text-slate-200 transition-colors p-1" aria-label="Close">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
      </button>
    `;

    const closeBtn = toast.querySelector('button');
    const dismiss = () => {
      toast.classList.add('opacity-0', 'translate-y-4');
      setTimeout(() => {
        if (toast.parentElement) {
          toast.remove();
        }
      }, 300);
    };

    closeBtn.addEventListener('click', dismiss);

    this.container.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => {
      toast.classList.remove('opacity-0', 'translate-y-4');
      toast.classList.add('opacity-100', 'translate-y-0');
    });

    if (duration > 0) {
      setTimeout(dismiss, duration);
    }
  }

  static success(msg, duration) {
    this.show(msg, 'success', duration);
  }

  static error(msg, duration = 6000) {
    this.show(msg, 'error', duration);
  }

  static warning(msg, duration) {
    this.show(msg, 'warning', duration);
  }

  static info(msg, duration) {
    this.show(msg, 'info', duration);
  }

  static _getTypeStyles(type) {
    switch (type) {
      case 'success':
        return 'bg-emerald-950/90 border-emerald-500/30 text-emerald-200';
      case 'error':
        return 'bg-rose-950/90 border-rose-500/30 text-rose-200';
      case 'warning':
        return 'bg-amber-950/90 border-amber-500/30 text-amber-200';
      default:
        return 'bg-slate-900/90 border-slate-700 text-slate-200';
    }
  }

  static _getIcon(type) {
    switch (type) {
      case 'success':
        return '<svg class="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>';
      case 'error':
        return '<svg class="w-5 h-5 text-rose-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>';
      case 'warning':
        return '<svg class="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>';
      default:
        return '<svg class="w-5 h-5 text-sky-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>';
    }
  }

  static _escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }
}
