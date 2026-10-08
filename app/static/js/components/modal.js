/**
 * Modal Management: PDF Preview Viewer & Confirmation Dialogs
 */
export class ModalManager {
  static init() {
    this.pdfModal = document.getElementById('pdf-modal');
    this.pdfFrame = document.getElementById('pdf-modal-frame');
    this.pdfTitle = document.getElementById('pdf-modal-title');
    this.pdfDownloadLink = document.getElementById('pdf-modal-download');
    this.pdfCloseBtn = document.getElementById('pdf-modal-close');

    if (this.pdfCloseBtn) {
      this.pdfCloseBtn.addEventListener('click', () => this.closePdfModal());
    }

    if (this.pdfModal) {
      this.pdfModal.addEventListener('click', (e) => {
        if (e.target === this.pdfModal) {
          this.closePdfModal();
        }
      });
    }

    // Keyboard ESC listener
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        this.closePdfModal();
      }
    });
  }

  static openPdfPreview(pdfUrl, title = 'Certificate Preview', downloadUrl = null) {
    if (!this.pdfModal || !this.pdfFrame) return;

    if (this.pdfTitle) this.pdfTitle.textContent = title;
    if (this.pdfDownloadLink) {
      this.pdfDownloadLink.href = downloadUrl || pdfUrl;
    }

    this.pdfFrame.src = pdfUrl;
    this.pdfModal.classList.remove('hidden');
    this.pdfModal.classList.add('flex');
  }

  static closePdfModal() {
    if (!this.pdfModal || !this.pdfFrame) return;
    this.pdfModal.classList.add('hidden');
    this.pdfModal.classList.remove('flex');
    this.pdfFrame.src = 'about:blank';
  }

  static confirm(title, message, confirmText = 'Confirm', cancelText = 'Cancel') {
    return new Promise((resolve) => {
      const modal = document.createElement('div');
      modal.className = 'fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4';
      modal.innerHTML = `
        <div class="glass-panel-elevated max-w-md w-full rounded-2xl p-6 border border-slate-700 shadow-2xl transform transition-all scale-100">
          <h3 class="text-xl font-bold text-slate-100 font-display mb-2">${title}</h3>
          <p class="text-sm text-slate-300 mb-6">${message}</p>
          <div class="flex justify-end space-x-3">
            <button class="btn-cancel px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium text-sm transition-colors">
              ${cancelText}
            </button>
            <button class="btn-confirm px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-medium text-sm transition-colors shadow-lg shadow-rose-900/40">
              ${confirmText}
            </button>
          </div>
        </div>
      `;

      const cleanup = (result) => {
        modal.remove();
        resolve(result);
      };

      modal.querySelector('.btn-cancel').addEventListener('click', () => cleanup(false));
      modal.querySelector('.btn-confirm').addEventListener('click', () => cleanup(true));
      modal.addEventListener('click', (e) => {
        if (e.target === modal) cleanup(false);
      });

      document.body.appendChild(modal);
    });
  }
}
