/**
 * Bulk Certificate Generator - Live Job Monitor Component
 */
import { ApiClient } from '../api.js';
import { bus, state } from '../state.js';
import { ModalManager } from './modal.js';
import { Toast } from './toast.js';

export class MonitorComponent {
  static init() {
    this.pollInterval = 1000; // 1s polling during active processing
    this.pollTimer = null;
    this.currentFilter = 'ALL';
    this.searchQuery = '';
    this.cachedCertificates = [];

    // Header & Meta Elements
    this.emptyState = document.getElementById('monitor-empty-state');
    this.activeState = document.getElementById('monitor-active-state');
    this.jobTitle = document.getElementById('monitor-job-title');
    this.jobEvent = document.getElementById('monitor-job-event');
    this.jobOrg = document.getElementById('monitor-job-org');
    this.jobStatusBadge = document.getElementById('monitor-status-badge');
    this.jobIdDisplay = document.getElementById('monitor-job-id');

    // Metrics & Progress
    this.progressBar = document.getElementById('monitor-progress-bar');
    this.progressText = document.getElementById('monitor-progress-percentage');
    this.statTotal = document.getElementById('monitor-stat-total');
    this.statProcessed = document.getElementById('monitor-stat-processed');
    this.statSuccess = document.getElementById('monitor-stat-success');
    this.statFailed = document.getElementById('monitor-stat-failed');

    // Action Buttons
    this.downloadZipBtn = document.getElementById('monitor-download-zip-btn');
    this.newBatchBtn = document.getElementById('monitor-new-batch-btn');

    // Table & Filters
    this.certTableBody = document.getElementById('monitor-cert-table-body');
    this.filterAllBtn = document.getElementById('filter-cert-all');
    this.filterSuccessBtn = document.getElementById('filter-cert-success');
    this.filterFailedBtn = document.getElementById('filter-cert-failed');
    this.searchInput = document.getElementById('cert-search-input');

    this.bindEvents();

    // Listen for global job selection
    bus.on('job:selected', ({ jobId }) => {
      if (jobId) {
        this.loadJob(jobId);
      }
    });

    bus.on('tab:changed', (tab) => {
      if (tab === 'monitor' && state.currentJobId) {
        this.loadJob(state.currentJobId);
      }
    });
  }

  static bindEvents() {
    this.newBatchBtn?.addEventListener('click', () => {
      state.setTab('generator');
    });

    this.downloadZipBtn?.addEventListener('click', () => {
      if (!state.currentJobId) return;
      window.location.href = ApiClient.getJobZipDownloadUrl(state.currentJobId);
      Toast.info('Downloading bulk certificates archive...');
    });

    // Filter tabs
    this.filterAllBtn?.addEventListener('click', () => this.setFilter('ALL'));
    this.filterSuccessBtn?.addEventListener('click', () => this.setFilter('SUCCESS'));
    this.filterFailedBtn?.addEventListener('click', () => this.setFilter('FAILED'));

    // Search
    this.searchInput?.addEventListener('input', (e) => {
      this.searchQuery = e.target.value.toLowerCase().trim();
      this.renderCertificatesTable();
    });
  }

  static setFilter(filter) {
    this.currentFilter = filter;

    const activeClass = 'bg-slate-700 text-white shadow-sm';
    const inactiveClass = 'text-slate-400 hover:text-slate-200';

    [
      { btn: this.filterAllBtn, name: 'ALL' },
      { btn: this.filterSuccessBtn, name: 'SUCCESS' },
      { btn: this.filterFailedBtn, name: 'FAILED' },
    ].forEach(item => {
      if (item.name === filter) {
        item.btn?.classList.add(...activeClass.split(' '));
        item.btn?.classList.remove(...inactiveClass.split(' '));
      } else {
        item.btn?.classList.remove(...activeClass.split(' '));
        item.btn?.classList.add(...inactiveClass.split(' '));
      }
    });

    this.renderCertificatesTable();
  }

  static async loadJob(jobId) {
    this.stopPolling();

    if (this.emptyState) this.emptyState.classList.add('hidden');
    if (this.activeState) this.activeState.classList.remove('hidden');

    try {
      const jobData = await ApiClient.getJobStatus(jobId);
      this.updateView(jobData);

      // Start polling if not completed or failed
      if (jobData.status === 'PENDING' || jobData.status === 'PROCESSING') {
        this.startPolling(jobId);
      }
    } catch (err) {
      Toast.error(`Failed to load job status: ${err.message}`);
    }
  }

  static startPolling(jobId) {
    this.stopPolling();
    this.pollTimer = setInterval(async () => {
      try {
        const jobData = await ApiClient.getJobStatus(jobId);
        this.updateView(jobData);

        if (jobData.status === 'COMPLETED' || jobData.status === 'PARTIALLY_COMPLETED' || jobData.status === 'FAILED') {
          this.stopPolling();
          if (jobData.status === 'COMPLETED') {
            Toast.success(`Batch completed! All ${jobData.success_count} certificates generated.`);
          } else if (jobData.status === 'PARTIALLY_COMPLETED') {
            Toast.warning(`Batch completed with errors: ${jobData.success_count} succeeded, ${jobData.failed_count} failed.`);
          } else {
            Toast.error('Batch generation failed.');
          }
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, this.pollInterval);
  }

  static stopPolling() {
    if (this.pollTimer) {
      clearInterval(this.pollTimer);
      this.pollTimer = null;
    }
  }

  static updateView(job) {
    if (!job) return;

    if (this.jobTitle) this.jobTitle.textContent = job.title;
    if (this.jobEvent) this.jobEvent.textContent = job.event_name;
    if (this.jobOrg) this.jobOrg.textContent = job.organization || 'Standard Organization';
    if (this.jobIdDisplay) this.jobIdDisplay.textContent = `ID: ${job.id}`;

    // Status Badge
    if (this.jobStatusBadge) {
      this.jobStatusBadge.className = `px-3 py-1 rounded-full text-xs font-semibold border ${this._getStatusBadgeStyles(job.status)}`;
      this.jobStatusBadge.textContent = job.status;
    }

    // Stats
    if (this.statTotal) this.statTotal.textContent = job.total_count;
    if (this.statProcessed) this.statProcessed.textContent = job.processed_count;
    if (this.statSuccess) this.statSuccess.textContent = job.success_count;
    if (this.statFailed) this.statFailed.textContent = job.failed_count;

    // Progress Bar
    const pct = Math.round(job.progress_percentage || 0);
    if (this.progressBar) {
      this.progressBar.style.width = `${pct}%`;
      if (pct === 100) {
        this.progressBar.classList.remove('progress-shimmer');
      } else {
        this.progressBar.classList.add('progress-shimmer');
      }
    }
    if (this.progressText) this.progressText.textContent = `${pct}%`;

    // Download ZIP Button
    if (this.downloadZipBtn) {
      if (job.success_count > 0) {
        this.downloadZipBtn.disabled = false;
        this.downloadZipBtn.classList.remove('opacity-50', 'cursor-not-allowed');
      } else {
        this.downloadZipBtn.disabled = true;
        this.downloadZipBtn.classList.add('opacity-50', 'cursor-not-allowed');
      }
    }

    // Cache and render certificates
    this.cachedCertificates = job.certificates || [];
    this.renderCertificatesTable();
  }

  static renderCertificatesTable() {
    if (!this.certTableBody) return;
    this.certTableBody.innerHTML = '';

    let items = this.cachedCertificates;

    // Filter
    if (this.currentFilter !== 'ALL') {
      items = items.filter(c => c.status === this.currentFilter);
    }

    // Search
    if (this.searchQuery) {
      items = items.filter(c =>
        c.recipient_name?.toLowerCase().includes(this.searchQuery) ||
        c.recipient_email?.toLowerCase().includes(this.searchQuery) ||
        c.recipient_identifier?.toLowerCase().includes(this.searchQuery) ||
        c.certificate_code?.toLowerCase().includes(this.searchQuery)
      );
    }

    if (items.length === 0) {
      this.certTableBody.innerHTML = `
        <tr>
          <td colspan="5" class="p-8 text-center text-slate-500 text-sm">
            No certificates found matching the criteria.
          </td>
        </tr>
      `;
      return;
    }

    items.forEach(cert => {
      const row = document.createElement('tr');
      row.className = 'border-b border-slate-800/80 hover:bg-slate-800/30 transition-colors text-sm';

      const isSuccess = cert.status === 'SUCCESS';
      const isFailed = cert.status === 'FAILED';

      const sizeStr = cert.file_size_bytes ? `${Math.round(cert.file_size_bytes / 1024)} KB` : '-';

      row.innerHTML = `
        <td class="p-3.5">
          <div class="font-medium text-slate-100">${this._escapeHtml(cert.recipient_name)}</div>
          <div class="text-xs text-slate-400">${this._escapeHtml(cert.recipient_email || 'No email')}</div>
        </td>
        <td class="p-3.5 font-mono text-xs text-slate-300">
          ${cert.certificate_code ? `<span class="px-2 py-0.5 rounded bg-slate-800 text-amber-300/90 border border-slate-700">${cert.certificate_code}</span>` : '-'}
          ${cert.recipient_identifier ? `<span class="ml-2 text-slate-500 text-xs">(${cert.recipient_identifier})</span>` : ''}
        </td>
        <td class="p-3.5">
          <span class="px-2.5 py-0.5 rounded-full text-xs font-medium border ${this._getStatusBadgeStyles(cert.status)}">
            ${cert.status}
          </span>
          ${isFailed && cert.error_message ? `<div class="text-xs text-rose-400 mt-1">${this._escapeHtml(cert.error_message)}</div>` : ''}
        </td>
        <td class="p-3.5 text-xs text-slate-400">${sizeStr}</td>
        <td class="p-3.5 text-right">
          <div class="flex items-center justify-end space-x-2">
            ${isSuccess ? `
              <button class="btn-preview-pdf p-1.5 text-slate-400 hover:text-amber-300 hover:bg-slate-800 rounded-lg transition-colors" title="Preview PDF">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path></svg>
              </button>
              <a href="${ApiClient.getCertificateDownloadUrl(cert.id)}" class="p-1.5 text-slate-400 hover:text-emerald-300 hover:bg-slate-800 rounded-lg transition-colors" title="Download PDF" download>
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
              </a>
              <button class="btn-verify-cert p-1.5 text-slate-400 hover:text-sky-300 hover:bg-slate-800 rounded-lg transition-colors" title="Verify Certificate">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path></svg>
              </button>
            ` : '-'}
          </div>
        </td>
      `;

      if (isSuccess) {
        row.querySelector('.btn-preview-pdf')?.addEventListener('click', () => {
          ModalManager.openPdfPreview(
            ApiClient.getCertificateDownloadUrl(cert.id),
            `Certificate - ${cert.recipient_name}`,
            ApiClient.getCertificateDownloadUrl(cert.id)
          );
        });

        row.querySelector('.btn-verify-cert')?.addEventListener('click', () => {
          bus.emit('verify:lookup', cert.certificate_code);
          state.setTab('verify');
        });
      }

      this.certTableBody.appendChild(row);
    });
  }

  static _getStatusBadgeStyles(status) {
    switch (status) {
      case 'COMPLETED':
      case 'SUCCESS':
        return 'bg-emerald-950/60 text-emerald-300 border-emerald-500/30';
      case 'PROCESSING':
      case 'PENDING':
        return 'bg-amber-950/60 text-amber-300 border-amber-500/30 animate-pulse';
      case 'PARTIALLY_COMPLETED':
        return 'bg-yellow-950/60 text-yellow-300 border-yellow-500/30';
      case 'FAILED':
        return 'bg-rose-950/60 text-rose-300 border-rose-500/30';
      default:
        return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  }

  static _escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }
}
