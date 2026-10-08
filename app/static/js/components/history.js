/**
 * Bulk Certificate Generator - Job History Explorer Component
 */
import { ApiClient } from '../api.js';
import { bus, state } from '../state.js';
import { ModalManager } from './modal.js';
import { Toast } from './toast.js';

export class HistoryComponent {
  static init() {
    this.tableBody = document.getElementById('history-table-body');
    this.refreshBtn = document.getElementById('history-refresh-btn');
    this.filterSelect = document.getElementById('history-filter-status');
    this.searchInput = document.getElementById('history-search-input');

    // Pagination
    this.prevBtn = document.getElementById('history-prev-btn');
    this.nextBtn = document.getElementById('history-next-btn');
    this.pageInfo = document.getElementById('history-page-info');

    this.currentPage = 1;
    this.pageSize = 10;
    this.currentStatus = '';
    this.searchQuery = '';
    this.cachedJobs = [];

    this.bindEvents();

    bus.on('tab:changed', (tab) => {
      if (tab === 'history') {
        this.loadJobs();
      }
    });
  }

  static bindEvents() {
    this.refreshBtn?.addEventListener('click', () => {
      this.loadJobs();
      Toast.info('Refreshing job history...');
    });

    this.filterSelect?.addEventListener('change', (e) => {
      this.currentStatus = e.target.value;
      this.currentPage = 1;
      this.loadJobs();
    });

    this.searchInput?.addEventListener('input', (e) => {
      this.searchQuery = e.target.value.toLowerCase().trim();
      this.renderTable();
    });

    this.prevBtn?.addEventListener('click', () => {
      if (this.currentPage > 1) {
        this.currentPage--;
        this.loadJobs();
      }
    });

    this.nextBtn?.addEventListener('click', () => {
      this.currentPage++;
      this.loadJobs();
    });
  }

  static async loadJobs() {
    if (!this.tableBody) return;

    this.tableBody.innerHTML = `
      <tr>
        <td colspan="6" class="p-8 text-center text-slate-400">
          <div class="flex items-center justify-center space-x-3">
            <svg class="animate-spin h-5 w-5 text-amber-400" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
            <span>Loading batch history...</span>
          </div>
        </td>
      </tr>
    `;

    try {
      const params = {
        page: this.currentPage,
        page_size: this.pageSize,
      };
      if (this.currentStatus) {
        params.status = this.currentStatus;
      }

      const res = await ApiClient.listJobs(params);
      const jobs = Array.isArray(res) ? res : (res?.items || []);
      this.cachedJobs = jobs;
      this.totalJobs = res?.total ?? jobs.length;
      this.renderTable();
      this.updatePagination(jobs.length, this.totalJobs);
    } catch (err) {
      Toast.error(`Failed to load history: ${err.message}`);
      this.tableBody.innerHTML = `
        <tr>
          <td colspan="6" class="p-8 text-center text-rose-400">
            Failed to load job history: ${this._escapeHtml(err.message)}
          </td>
        </tr>
      `;
    }
  }

  static updatePagination(currentCount, totalCount = 0) {
    const totalPages = totalCount > 0 ? Math.ceil(totalCount / this.pageSize) : 1;
    if (this.pageInfo) {
      this.pageInfo.textContent = totalPages > 1 ? `Page ${this.currentPage} of ${totalPages}` : `Page ${this.currentPage}`;
    }
    if (this.prevBtn) {
      this.prevBtn.disabled = this.currentPage <= 1;
    }
    if (this.nextBtn) {
      this.nextBtn.disabled = totalCount > 0 ? this.currentPage >= totalPages : currentCount < this.pageSize;
    }
  }

  static renderTable() {
    if (!this.tableBody) return;
    this.tableBody.innerHTML = '';

    let items = this.cachedJobs;

    if (this.searchQuery) {
      items = items.filter(j =>
        j.title?.toLowerCase().includes(this.searchQuery) ||
        j.event_name?.toLowerCase().includes(this.searchQuery) ||
        j.organization?.toLowerCase().includes(this.searchQuery) ||
        j.id?.toLowerCase().includes(this.searchQuery)
      );
    }

    if (items.length === 0) {
      this.tableBody.innerHTML = `
        <tr>
          <td colspan="6" class="p-8 text-center text-slate-500">
            No batch jobs found in history.
          </td>
        </tr>
      `;
      return;
    }

    items.forEach(job => {
      const row = document.createElement('tr');
      row.className = 'border-b border-slate-800/80 hover:bg-slate-800/30 transition-colors text-sm';

      const dateStr = job.created_at ? new Date(job.created_at).toLocaleString() : '-';
      const pct = Math.round(job.progress_percentage || 0);

      row.innerHTML = `
        <td class="p-3.5">
          <div class="font-semibold text-slate-100">${this._escapeHtml(job.title)}</div>
          <div class="text-xs text-slate-400">${this._escapeHtml(job.event_name)} • ${this._escapeHtml(job.organization || 'Standard')}</div>
          <div class="text-[11px] font-mono text-slate-500 mt-0.5">${job.id}</div>
        </td>
        <td class="p-3.5">
          <span class="px-2.5 py-0.5 rounded-full text-xs font-medium border ${this._getStatusBadgeStyles(job.status)}">
            ${job.status}
          </span>
        </td>
        <td class="p-3.5">
          <div class="flex items-center space-x-2">
            <div class="w-16 bg-slate-800 rounded-full h-1.5 overflow-hidden">
              <div class="bg-amber-400 h-full rounded-full" style="width: ${pct}%"></div>
            </div>
            <span class="text-xs text-slate-400 font-mono">${pct}%</span>
          </div>
          <div class="text-xs text-slate-400 mt-1">
            <span class="text-emerald-400 font-medium">${job.success_count}</span> / ${job.total_count}
            ${job.failed_count > 0 ? `<span class="text-rose-400 ml-1 font-medium">(${job.failed_count} failed)</span>` : ''}
          </div>
        </td>
        <td class="p-3.5 text-xs text-slate-400">${dateStr}</td>
        <td class="p-3.5 text-right">
          <div class="flex items-center justify-end space-x-2">
            <button class="btn-inspect-job p-1.5 text-slate-400 hover:text-amber-300 hover:bg-slate-800 rounded-lg transition-colors" title="Monitor & View Certificates">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path></svg>
            </button>
            ${job.success_count > 0 ? `
              <a href="${ApiClient.getJobZipDownloadUrl(job.id)}" class="p-1.5 text-slate-400 hover:text-emerald-300 hover:bg-slate-800 rounded-lg transition-colors" title="Download ZIP Archive" download>
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
              </a>
            ` : ''}
            <button class="btn-delete-job p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors" title="Delete Job">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
            </button>
          </div>
        </td>
      `;

      // Event listeners
      row.querySelector('.btn-inspect-job')?.addEventListener('click', () => {
        state.setCurrentJob(job.id);
        state.setTab('monitor');
      });

      row.querySelector('.btn-delete-job')?.addEventListener('click', async () => {
        const confirmed = await ModalManager.confirm(
          'Delete Job Batch',
          `Are you sure you want to delete "${job.title}" and all its associated certificates? This action cannot be undone.`,
          'Delete Batch',
          'Cancel'
        );

        if (confirmed) {
          try {
            await ApiClient.deleteJob(job.id);
            Toast.success('Job batch deleted successfully.');
            if (state.currentJobId === job.id) {
              state.setCurrentJob(null);
            }
            this.loadJobs();
          } catch (err) {
            Toast.error(`Failed to delete job: ${err.message}`);
          }
        }
      });

      this.tableBody.appendChild(row);
    });
  }

  static _getStatusBadgeStyles(status) {
    switch (status) {
      case 'COMPLETED':
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
