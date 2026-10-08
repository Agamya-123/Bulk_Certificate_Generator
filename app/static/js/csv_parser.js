/**
 * RFC-4180 Compliant CSV Parser & Template Generator
 */
export class CsvParser {
  /**
   * Parse a raw CSV string into an array of objects
   */
  static parse(csvText) {
    if (!csvText || typeof csvText !== 'string') {
      return { recipients: [], errors: ['Empty CSV content'] };
    }

    const lines = this._splitRows(csvText);
    if (lines.length < 2) {
      return { recipients: [], errors: ['CSV must contain at least a header row and one data row'] };
    }

    const rawHeaders = this._parseRow(lines[0]);
    if (rawHeaders.length === 0) {
      return { recipients: [], errors: ['CSV header row is invalid or empty'] };
    }

    // Normalize headers
    const headerMap = this._mapHeaders(rawHeaders);
    if (!headerMap.name) {
      return {
        recipients: [],
        errors: ['Missing required column: "name" (or "recipient_name", "full_name", "student_name")']
      };
    }

    const recipients = [];
    const errors = [];

    for (let i = 1; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue; // Skip empty lines

      const values = this._parseRow(line);
      const rowNum = i + 1;

      const recipient = {
        name: '',
        email: null,
        identifier: null,
        custom_data: {}
      };

      rawHeaders.forEach((header, colIdx) => {
        const val = (values[colIdx] || '').trim();
        const normHeader = header.toLowerCase().replace(/[\s_-]+/g, '');

        if (colIdx === headerMap.nameIdx) {
          recipient.name = val;
        } else if (colIdx === headerMap.emailIdx) {
          recipient.email = val || null;
        } else if (colIdx === headerMap.identifierIdx) {
          recipient.identifier = val || null;
        } else if (val) {
          // Put extra columns into custom_data
          recipient.custom_data[header.trim()] = val;
        }
      });

      if (!recipient.name) {
        errors.push(`Row ${rowNum}: Recipient name is empty`);
        continue;
      }

      if (recipient.email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(recipient.email)) {
          errors.push(`Row ${rowNum}: Invalid email format "${recipient.email}"`);
        }
      }

      // If custom_data is empty, set to undefined/null
      if (Object.keys(recipient.custom_data).length === 0) {
        delete recipient.custom_data;
      }

      recipients.push(recipient);
    }

    return { recipients, errors };
  }

  /**
   * Auto-map header names to standard fields
   */
  static _mapHeaders(headers) {
    const map = {
      name: null,
      nameIdx: -1,
      email: null,
      emailIdx: -1,
      identifier: null,
      identifierIdx: -1,
    };

    const nameAliases = ['name', 'recipient_name', 'fullname', 'full_name', 'student_name', 'attendee', 'participant'];
    const emailAliases = ['email', 'recipient_email', 'mail', 'email_address', 'e-mail'];
    const idAliases = ['identifier', 'id', 'student_id', 'roll_no', 'roll_number', 'reg_no', 'registration_number', 'code'];

    headers.forEach((h, idx) => {
      const clean = h.toLowerCase().trim().replace(/[\s_-]+/g, '');
      if (map.nameIdx === -1 && (nameAliases.includes(clean) || nameAliases.includes(h.toLowerCase().trim()))) {
        map.name = h;
        map.nameIdx = idx;
      } else if (map.emailIdx === -1 && (emailAliases.includes(clean) || emailAliases.includes(h.toLowerCase().trim()))) {
        map.email = h;
        map.emailIdx = idx;
      } else if (map.identifierIdx === -1 && (idAliases.includes(clean) || idAliases.includes(h.toLowerCase().trim()))) {
        map.identifier = h;
        map.identifierIdx = idx;
      }
    });

    return map;
  }

  /**
   * Split string into rows considering quoted newlines
   */
  static _splitRows(text) {
    const rows = [];
    let currentRow = '';
    let inQuotes = false;

    for (let i = 0; i < text.length; i++) {
      const char = text[i];
      const nextChar = text[i + 1];

      if (char === '"') {
        if (inQuotes && nextChar === '"') {
          currentRow += '""';
          i++; // Skip escaped quote
        } else {
          inQuotes = !inQuotes;
          currentRow += char;
        }
      } else if ((char === '\r' || char === '\n') && !inQuotes) {
        if (char === '\r' && nextChar === '\n') {
          i++;
        }
        if (currentRow.trim().length > 0) {
          rows.push(currentRow);
        }
        currentRow = '';
      } else {
        currentRow += char;
      }
    }

    if (currentRow.trim().length > 0) {
      rows.push(currentRow);
    }

    return rows;
  }

  /**
   * Parse single CSV line handling quotes and commas
   */
  static _parseRow(rowText) {
    const fields = [];
    let currentField = '';
    let inQuotes = false;

    for (let i = 0; i < rowText.length; i++) {
      const char = rowText[i];
      const nextChar = rowText[i + 1];

      if (char === '"') {
        if (inQuotes && nextChar === '"') {
          currentField += '"';
          i++;
        } else {
          inQuotes = !inQuotes;
        }
      } else if (char === ',' && !inQuotes) {
        fields.push(currentField);
        currentField = '';
      } else {
        currentField += char;
      }
    }

    fields.push(currentField);
    return fields;
  }

  /**
   * Generate downloadable sample CSV template
   */
  static getSampleCsvContent() {
    return `name,email,identifier,grade,track
Alice Wonderland,alice@example.com,STU-001,Distinction,Frontend Engineering
Bob Builder,bob@example.com,STU-002,Merit,Backend Systems
Charlie Brown,charlie@example.com,STU-003,Pass,Cloud Infrastructure
Diana Prince,diana@example.com,STU-004,Distinction,Security Architecture
Edward Elric,edward@example.com,STU-005,Honors,Full-Stack Development`;
  }
}
