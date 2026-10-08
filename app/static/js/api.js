/**
 * Bulk Certificate Generator - REST API Client
 */
export class ApiClient {
  static BASE_URL = '/api/v1';

  /**
   * Universal fetch helper with error normalization
   */
  static async request(endpoint, options = {}) {
    const url = `${this.BASE_URL}${endpoint}`;
    const defaultHeaders = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };

    const config = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);

      // Handle non-JSON responses (like binary downloads or error pages)
      const contentType = response.headers.get('content-type');
      let data;
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        data = await response.text();
      }

      if (!response.ok) {
        let errorMessage = 'An unexpected API error occurred';
        if (data && typeof data === 'object') {
          if (Array.isArray(data.detail)) {
            // Pydantic validation error array
            errorMessage = data.detail.map(e => `${e.loc?.join('.') || 'field'}: ${e.msg}`).join(', ');
          } else if (data.detail) {
            errorMessage = data.detail;
          } else if (data.message) {
            errorMessage = data.message;
          }
        } else if (typeof data === 'string' && data.length > 0) {
          errorMessage = data;
        }
        const error = new Error(errorMessage);
        error.status = response.status;
        error.data = data;
        throw error;
      }

      return data;
    } catch (err) {
      if (!err.status) {
        err.message = `Network Connection Error: ${err.message}`;
      }
      throw err;
    }
  }

  // System Health
  static async getHealth() {
    return this.request('/health');
  }

  static async checkHealth() {
    return this.getHealth();
  }

  // Jobs API
  static async createJob(jobData) {
    return this.request('/jobs', {
      method: 'POST',
      body: JSON.stringify(jobData),
    });
  }

  static async getJobStatus(jobId) {
    return this.request(`/jobs/${jobId}`);
  }

  static async listJobs(params = {}) {
    const query = new URLSearchParams();
    if (params.status) query.append('status', params.status);
    if (params.search) query.append('search', params.search);
    if (params.page) query.append('page', params.page);
    if (params.page_size) query.append('page_size', params.page_size);

    const queryString = query.toString() ? `?${query.toString()}` : '';
    return this.request(`/jobs${queryString}`);
  }

  static async listJobCertificates(jobId, params = {}) {
    const query = new URLSearchParams();
    if (params.status) query.append('status', params.status);
    if (params.page) query.append('page', params.page);
    if (params.page_size) query.append('page_size', params.page_size);

    const queryString = query.toString() ? `?${query.toString()}` : '';
    return this.request(`/jobs/${jobId}/certificates${queryString}`);
  }

  static async deleteJob(jobId) {
    return this.request(`/jobs/${jobId}`, {
      method: 'DELETE',
    });
  }

  // Certificate API
  static async getCertificate(certificateId) {
    return this.request(`/certificates/${certificateId}`);
  }

  static async verifyCertificate(code) {
    return this.request(`/certificates/verify/${encodeURIComponent(code)}`);
  }

  // URLs for direct downloads/preview
  static getCertificateDownloadUrl(certificateId) {
    return `${this.BASE_URL}/certificates/${certificateId}/download`;
  }

  static getJobZipDownloadUrl(jobId) {
    return `${this.BASE_URL}/jobs/${jobId}/download-zip`;
  }
}
