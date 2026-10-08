/**
 * Bulk Certificate Generator - Public Certificate Verification Component
 */
import { ApiClient } from '../api.js';
import { bus } from '../state.js';
import { Toast } from './toast.js';

export class VerifyComponent {
  static init() {
    this.form = document.getElementById('verify-form');
    this.codeInput = document.getElementById('verify-code-input');
    this.submitBtn = document.getElementById('verify-submit-btn');

    this.resultContainer = document.getElementById('verify-result-container');
    this.idleContainer = document.getElementById('verify-idle-container');
    this.errorContainer = document.getElementById('verify-error-container');
    this.errorMessage = document.getElementById('verify-error-message');

    // Result card fields
    this.certCodeBadge = document.getElementById('res-cert-code');
    this.recipientName = document.getElementById('res-recipient-name');
    this.recipientEmail = document.getElementById('res-recipient-email');
    this.recipientId = document.getElementById('res-recipient-id');
    this.eventName = document.getElementById('res-event-name');
    this.certTitle = document.getElementById('res-cert-title');
    this.orgName = document.getElementById('res-org-name');
    this.issueDate = document.getElementById('res-issue-date');
    this.issuerName = document.getElementById('res-issuer-name');
    this.issuerTitle = document.getElementById('res-issuer-title');
    this.desc = document.getElementById('res-desc');
    this.verifyHash = document.getElementById('res-verify-hash');
    this.downloadBtn = document.getElementById('res-download-pdf-btn');
    this.copyHashBtn = document.getElementById('res-copy-hash-btn');

    this.bindEvents();
    this.checkUrlParams();

    bus.on('verify:lookup', (code) => {
      if (this.codeInput) {
        this.codeInput.value = code;
        this.lookup(code);
      }
    });
  }

  static bindEvents() {
    this.form?.addEventListener('submit', (e) => {
      e.preventDefault();
      const code = this.codeInput?.value.trim();
      if (code) {
        this.lookup(code);
      }
    });

    this.copyHashBtn?.addEventListener('click', () => {
      const hash = this.verifyHash?.textContent;
      if (hash) {
        navigator.clipboard.writeText(hash).then(() => {
          Toast.success('SHA-256 verification hash copied to clipboard');
        }).catch(() => {
          Toast.info('Hash: ' + hash);
        });
      }
    });
  }

  static checkUrlParams() {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    if (code && this.codeInput) {
      this.codeInput.value = code;
      this.lookup(code);
    }
  }

  static async lookup(code) {
    if (!code) return;

    if (this.idleContainer) this.idleContainer.classList.add('hidden');
    if (this.errorContainer) this.errorContainer.classList.add('hidden');
    if (this.resultContainer) this.resultContainer.classList.add('hidden');

    if (this.submitBtn) {
      this.submitBtn.disabled = true;
      this.submitBtn.innerHTML = `
        <svg class="animate-spin h-5 w-5 text-slate-900 mx-auto" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
      `;
    }

    try {
      const data = await ApiClient.verifyCertificate(code);
      this.renderVerifiedData(data);
      Toast.success('Certificate verified successfully!');
    } catch (err) {
      if (this.errorContainer && this.errorMessage) {
        this.errorMessage.textContent = err.message || 'No valid certificate found matching this verification code.';
        this.errorContainer.classList.remove('hidden');
      }
      Toast.error('Verification failed: Certificate not found or invalid.');
    } finally {
      if (this.submitBtn) {
        this.submitBtn.disabled = false;
        this.submitBtn.innerHTML = `
          <svg class="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
          Verify
        `;
      }
    }
  }

  static renderVerifiedData(data) {
    if (!this.resultContainer) return;

    if (this.certCodeBadge) this.certCodeBadge.textContent = data.certificate_code;
    if (this.recipientName) this.recipientName.textContent = data.recipient_name;
    if (this.recipientEmail) this.recipientEmail.textContent = data.recipient_email || 'Not Specified';
    if (this.recipientId) this.recipientId.textContent = data.recipient_identifier || 'N/A';
    if (this.eventName) this.eventName.textContent = data.event_name;
    if (this.certTitle) this.certTitle.textContent = data.title;
    if (this.orgName) this.orgName.textContent = data.organization || 'Standard Organization';
    if (this.issueDate) this.issueDate.textContent = data.issue_date;
    if (this.issuerName) this.issuerName.textContent = data.issuer_name;
    if (this.issuerTitle) this.issuerTitle.textContent = data.issuer_title;
    if (this.desc) this.desc.textContent = data.description || '';
    if (this.verifyHash) this.verifyHash.textContent = data.verification_hash || 'SHA256-VERIFIED';

    if (this.downloadBtn) {
      this.downloadBtn.href = ApiClient.getCertificateDownloadUrl(data.certificate_id);
    }

    this.resultContainer.classList.remove('hidden');
  }
}
