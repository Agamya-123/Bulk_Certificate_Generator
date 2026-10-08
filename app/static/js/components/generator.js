/**
 * Bulk Certificate Generator - Batch Creation Component
 */
import { ApiClient } from '../api.js';
import { CsvParser } from '../csv_parser.js';
import { state } from '../state.js';
import { Toast } from './toast.js';

export class GeneratorComponent {
  static init() {
    this.form = document.getElementById('job-form');
    this.recipients = [];
    this.currentMode = 'csv'; // 'csv' | 'table' | 'json'

    // Form elements
    this.titleInput = document.getElementById('field-title');
    this.eventNameInput = document.getElementById('field-event-name');
    this.issueDateInput = document.getElementById('field-issue-date');
    this.issuerNameInput = document.getElementById('field-issuer-name');
    this.issuerTitleInput = document.getElementById('field-issuer-title');
    this.orgInput = document.getElementById('field-org');
    this.descInput = document.getElementById('field-desc');

    // Ingestion tabs
    this.modeCsvBtn = document.getElementById('mode-csv-btn');
    this.modeTableBtn = document.getElementById('mode-table-btn');
    this.modeJsonBtn = document.getElementById('mode-json-btn');

    this.modeCsvSection = document.getElementById('mode-csv-section');
    this.modeTableSection = document.getElementById('mode-table-section');
    this.modeJsonSection = document.getElementById('mode-json-section');

    // Table elements
    this.tableBody = document.getElementById('recipients-table-body');
    this.addTableRowBtn = document.getElementById('add-table-row-btn');

    // CSV elements
    this.dropzone = document.getElementById('csv-dropzone');
    this.fileInput = document.getElementById('csv-file-input');
    this.sampleCsvBtn = document.getElementById('download-sample-csv-btn');
    this.csvPreviewContainer = document.getElementById('csv-preview-container');
    this.csvSummaryText = document.getElementById('csv-summary-text');

    // JSON elements
    this.jsonEditor = document.getElementById('json-editor');
    this.loadDemoBtn = document.getElementById('load-demo-batch-btn');

    // Submit button
    this.submitBtn = document.getElementById('submit-job-btn');

    this.bindEvents();
    this.loadDefaultValues();
  }

  static loadDefaultValues() {
    // Populate today's date formatted nicely
    const today = new Date();
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    if (this.issueDateInput && !this.issueDateInput.value) {
      this.issueDateInput.value = today.toLocaleDateString('en-US', options);
    }
  }

  static bindEvents() {
    // Mode Switching
    this.modeCsvBtn?.addEventListener('click', () => this.switchMode('csv'));
    this.modeTableBtn?.addEventListener('click', () => this.switchMode('table'));
    this.modeJsonBtn?.addEventListener('click', () => this.switchMode('json'));

    // Manual Table Operations
    this.addTableRowBtn?.addEventListener('click', () => this.addTableRow());

    // CSV Dropzone Operations
    if (this.dropzone && this.fileInput) {
      this.dropzone.addEventListener('click', () => this.fileInput.click());

      this.fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) this.handleCsvFile(file);
      });

      ['dragenter', 'dragover'].forEach(eventName => {
        this.dropzone.addEventListener(eventName, (e) => {
          e.preventDefault();
          e.stopPropagation();
          this.dropzone.classList.add('dropzone-active');
        });
      });

      ['dragleave', 'drop'].forEach(eventName => {
        this.dropzone.addEventListener(eventName, (e) => {
          e.preventDefault();
          e.stopPropagation();
          this.dropzone.classList.remove('dropzone-active');
        });
      });

      this.dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const file = dt.files[0];
        if (file) this.handleCsvFile(file);
      });
    }

    // Sample CSV Download
    this.sampleCsvBtn?.addEventListener('click', () => {
      const csvContent = CsvParser.getSampleCsvContent();
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.setAttribute('href', url);
      link.setAttribute('download', 'recipients_sample.csv');
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      Toast.info('Sample CSV template downloaded');
    });

    // Demo batch loader
    this.loadDemoBtn?.addEventListener('click', () => this.loadDemoBatch());

    // Form Submission
    this.form?.addEventListener('submit', (e) => this.handleSubmit(e));
  }

  static switchMode(mode) {
    this.currentMode = mode;

    // Reset buttons
    const activeClass = 'bg-amber-600/20 text-amber-300 border-amber-500/50 shadow-sm';
    const inactiveClass = 'bg-slate-800/60 text-slate-400 border-slate-700/50 hover:text-slate-200';

    [
      { btn: this.modeCsvBtn, sec: this.modeCsvSection, name: 'csv' },
      { btn: this.modeTableBtn, sec: this.modeTableSection, name: 'table' },
      { btn: this.modeJsonBtn, sec: this.modeJsonSection, name: 'json' },
    ].forEach(item => {
      if (item.name === mode) {
        item.btn?.classList.remove(...inactiveClass.split(' '));
        item.btn?.classList.add(...activeClass.split(' '));
        item.sec?.classList.remove('hidden');
      } else {
        item.btn?.classList.remove(...activeClass.split(' '));
        item.btn?.classList.add(...inactiveClass.split(' '));
        item.sec?.classList.add('hidden');
      }
    });

    if (mode === 'table' && (!this.tableBody || this.tableBody.children.length === 0)) {
      this.addTableRow('Alice Wonderland', 'alice@example.com', 'STU-001');
      this.addTableRow('Bob Builder', 'bob@example.com', 'STU-002');
    }
  }

  static addTableRow(name = '', email = '', identifier = '') {
    if (!this.tableBody) return;
    const row = document.createElement('tr');
    row.className = 'border-b border-slate-800 hover:bg-slate-800/30 transition-colors';
    row.innerHTML = `
      <td class="p-3">
        <input type="text" value="${this._escapeHtml(name)}" placeholder="Full Name" class="row-name w-full px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-700 text-slate-100 text-sm focus:border-amber-500 focus:outline-none" required />
      </td>
      <td class="p-3">
        <input type="email" value="${this._escapeHtml(email)}" placeholder="email@example.com" class="row-email w-full px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-700 text-slate-100 text-sm focus:border-amber-500 focus:outline-none" />
      </td>
      <td class="p-3">
        <input type="text" value="${this._escapeHtml(identifier)}" placeholder="Optional ID (e.g. STU-101)" class="row-id w-full px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-700 text-slate-100 text-sm focus:border-amber-500 focus:outline-none" />
      </td>
      <td class="p-3 text-center">
        <button type="button" class="btn-remove-row text-slate-500 hover:text-rose-400 p-1.5 transition-colors rounded-lg hover:bg-rose-500/10">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
        </button>
      </td>
    `;

    row.querySelector('.btn-remove-row').addEventListener('click', () => {
      row.remove();
    });

    this.tableBody.appendChild(row);
  }

  static handleCsvFile(file) {
    if (!file.name.endsWith('.csv') && file.type !== 'text/csv') {
      Toast.error('Please upload a valid .csv file');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target.result;
      const { recipients, errors } = CsvParser.parse(content);

      if (errors.length > 0 && recipients.length === 0) {
        Toast.error(`CSV Parsing Failed: ${errors[0]}`);
        return;
      }

      this.recipients = recipients;
      if (this.csvPreviewContainer && this.csvSummaryText) {
        this.csvPreviewContainer.classList.remove('hidden');
        this.csvSummaryText.textContent = `Successfully parsed ${recipients.length} valid recipient(s). Ready to submit.`;
      }

      if (errors.length > 0) {
        Toast.warning(`Loaded ${recipients.length} recipients with ${errors.length} warning(s).`);
      } else {
        Toast.success(`Loaded ${recipients.length} recipients from CSV!`);
      }
    };
    reader.readAsText(file);
  }

  static loadDemoBatch() {
    this.titleInput.value = 'Advanced Cloud Computing & Microservices Bootcamp';
    this.eventNameInput.value = 'Cloud Architecture Masterclass 2026';
    this.issuerNameInput.value = 'Dr. Sarah Connor';
    this.issuerTitleInput.value = 'Chief Technology Officer';
    this.orgInput.value = 'Tech Excellence Institute';
    this.descInput.value = 'In recognition of successfully completing 80 hours of rigorous hands-on training in distributed systems and cloud native architectures.';

    const demoRecipients = [
      { name: 'Alex Johnson', email: 'alex.johnson@example.com', identifier: 'ENG-2026-001', custom_data: { grade: 'Distinction' } },
      { name: 'Maria Garcia', email: 'maria.garcia@example.com', identifier: 'ENG-2026-002', custom_data: { grade: 'Merit' } },
      { name: 'Liam Davies', email: 'liam.davies@example.com', identifier: 'ENG-2026-003' },
      { name: 'Aisha Patel', email: 'aisha.patel@example.com', identifier: 'ENG-2026-004', custom_data: { grade: 'Distinction' } },
      { name: 'Hiroshi Tanaka', email: 'hiroshi.tanaka@example.com', identifier: 'ENG-2026-005' },
    ];

    if (this.jsonEditor) {
      this.jsonEditor.value = JSON.stringify(demoRecipients, null, 2);
    }

    this.recipients = demoRecipients;
    this.switchMode('json');
    Toast.success('Demo batch details loaded successfully!');
  }

  static getRecipientsForSubmission() {
    if (this.currentMode === 'csv') {
      return this.recipients;
    }

    if (this.currentMode === 'table') {
      const rows = this.tableBody ? Array.from(this.tableBody.querySelectorAll('tr')) : [];
      const list = [];
      for (const row of rows) {
        const name = row.querySelector('.row-name')?.value.trim();
        const email = row.querySelector('.row-email')?.value.trim() || null;
        const id = row.querySelector('.row-id')?.value.trim() || null;
        if (name) {
          list.push({
            name,
            email,
            identifier: id,
          });
        }
      }
      return list;
    }

    if (this.currentMode === 'json') {
      if (!this.jsonEditor || !this.jsonEditor.value.trim()) {
        throw new Error('JSON editor is empty');
      }
      try {
        const parsed = JSON.parse(this.jsonEditor.value.trim());
        if (!Array.isArray(parsed)) {
          throw new Error('JSON content must be an array of recipient objects');
        }
        return parsed;
      } catch (err) {
        throw new Error(`Invalid JSON syntax: ${err.message}`);
      }
    }

    return [];
  }

  static async handleSubmit(e) {
    e.preventDefault();

    let recipientsList;
    try {
      recipientsList = this.getRecipientsForSubmission();
    } catch (err) {
      Toast.error(err.message);
      return;
    }

    if (!recipientsList || recipientsList.length === 0) {
      Toast.error('Please provide at least 1 recipient before submitting.');
      return;
    }

    const payload = {
      title: this.titleInput.value.trim(),
      event_name: this.eventNameInput.value.trim(),
      issue_date: this.issueDateInput.value.trim(),
      issuer_name: this.issuerNameInput.value.trim(),
      issuer_title: this.issuerTitleInput.value.trim(),
      organization: this.orgInput.value.trim() || undefined,
      description: this.descInput.value.trim() || undefined,
      recipients: recipientsList,
    };

    // UI Loading state
    if (this.submitBtn) {
      this.submitBtn.disabled = true;
      this.submitBtn.innerHTML = `
        <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
        Submitting Job...
      `;
    }

    try {
      const response = await ApiClient.createJob(payload);
      Toast.success(`Job created! Generating ${response.total_recipients} certificates.`);

      // Switch to monitor and start polling
      state.setCurrentJob(response.job_id);
      state.setTab('monitor');
    } catch (err) {
      Toast.error(`Failed to create job: ${err.message}`);
    } finally {
      if (this.submitBtn) {
        this.submitBtn.disabled = false;
        this.submitBtn.innerHTML = `
          <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
          Generate Certificates
        `;
      }
    }
  }

  static _escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }
}
