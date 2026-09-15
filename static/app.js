let currentData = null;

// --- Views ---
function showUpload() {
    document.getElementById('uploadView').style.display = '';
    document.getElementById('loadingView').style.display = 'none';
    document.getElementById('resultsView').style.display = 'none';
}

function showLoading() {
    document.getElementById('uploadView').style.display = 'none';
    document.getElementById('loadingView').style.display = '';
    document.getElementById('resultsView').style.display = 'none';
}

function showResults() {
    document.getElementById('uploadView').style.display = 'none';
    document.getElementById('loadingView').style.display = 'none';
    document.getElementById('resultsView').style.display = '';
}

// --- Upload Handlers ---
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');

dropZone.addEventListener('click', () => fileInput.click());

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-over');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file && file.type === 'application/pdf') {
        uploadFile(file);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files[0]) {
        uploadFile(e.target.files[0]);
    }
});

async function uploadFile(file) {
    showLoading();
    const formData = new FormData();
    formData.append('file', file);

    try {
        const resp = await fetch('/api/upload', { method: 'POST', body: formData });
        if (!resp.ok) {
            const err = await resp.json();
            alert(err.detail || 'Upload failed');
            showUpload();
            return;
        }
        currentData = await resp.json();
        renderResults(currentData);
        showResults();
    } catch (e) {
        alert('Error: ' + e.message);
        showUpload();
    }
}

async function runDemo() {
    showLoading();
    try {
        const resp = await fetch('/api/demo');
        currentData = await resp.json();
        renderResults(currentData);
        showResults();
    } catch (e) {
        alert('Error: ' + e.message);
        showUpload();
    }
}

// --- Render Results ---
function renderResults(data) {
    renderValidation(data.validation);
    renderForm(data.extracted.registration_fields || {});
}

function renderValidation(validation) {
    const panel = document.getElementById('validationPanel');
    const summary = validation.summary;

    const failCount = summary.failed;
    const warnCount = summary.warnings;
    const passedAll = failCount === 0 && warnCount === 0;

    const statusBadge = document.getElementById('overallStatus');
    if (passedAll) {
        statusBadge.textContent = 'All Passed';
        statusBadge.style.background = 'var(--success-bg)';
        statusBadge.style.color = 'var(--success)';
    } else {
        statusBadge.textContent = `${failCount} Issues`;
        statusBadge.style.background = 'var(--error-bg)';
        statusBadge.style.color = 'var(--error)';
    }

    let html = '';

    // Summary bar
    html += `<div class="summary-bar">
        <div class="summary-stat"><div class="number">${summary.total}</div><div class="label">Total Checks</div></div>
        <div class="summary-stat pass"><div class="number">${summary.passed}</div><div class="label">Passed</div></div>
        <div class="summary-stat fail"><div class="number">${summary.failed}</div><div class="label">Failed</div></div>
        <div class="summary-stat warn"><div class="number">${summary.warnings}</div><div class="label">Warnings</div></div>
    </div>`;

    // Conversational summary
    if (passedAll) {
        html += `<div class="message summary-good">
            <strong>All compliance checks passed.</strong> The test report contains all required information and meets the validation criteria. The extracted data is ready for ELS registration.
        </div>`;
    } else {
        const issues = [];
        if (failCount > 0) issues.push(`<strong>${failCount} check${failCount > 1 ? 's' : ''} failed</strong>`);
        if (warnCount > 0) issues.push(`<strong>${warnCount} item${warnCount > 1 ? 's' : ''} need attention</strong>`);
        html += `<div class="message summary-issues">
            ${issues.join(' and ')}. Please review the details below. Failed checks indicate non-compliance with ELS requirements. Warnings indicate missing or unverifiable information.
        </div>`;
    }

    // Sections
    for (const section of validation.sections) {
        const sectionChecks = section.checks;
        const sectionPassed = sectionChecks.filter(c => c.passed === true).length;
        const sectionFailed = sectionChecks.filter(c => c.passed === false).length;
        const sectionWarn = sectionChecks.filter(c => c.passed === null).length;

        const hasIssues = sectionFailed > 0 || sectionWarn > 0;
        const openByDefault = hasIssues;

        html += `<div class="val-section">
            <div class="val-section-header ${openByDefault ? 'open' : ''}" onclick="toggleSection(this)">
                <span class="toggle">&#9654;</span>
                ${section.name || section.title}
                <span class="section-stats">
                    ${sectionPassed}/${sectionChecks.length} passed
                    ${sectionFailed > 0 ? ` &middot; <span style="color:var(--error)">${sectionFailed} failed</span>` : ''}
                    ${sectionWarn > 0 ? ` &middot; <span style="color:var(--warning)">${sectionWarn} warnings</span>` : ''}
                </span>
            </div>
            <div class="val-checks" style="display: ${openByDefault ? 'block' : 'none'}">`;

        for (const check of sectionChecks) {
            const status = check.passed === true ? 'pass' : check.passed === false ? 'fail' : 'warn';
            const icon = check.passed === true ? '&#10003;' : check.passed === false ? '&#10007;' : '?';

            let detail = check.reason;
            if (check.extracted_value !== null && check.extracted_value !== undefined && check.extracted_value !== '') {
                detail += ` <span class="check-value">${escapeHtml(String(check.extracted_value))}</span>`;
            }

            html += `<div class="val-check ${status}">
                <div class="status-icon">${icon}</div>
                <div class="check-content">
                    <div class="check-name">${escapeHtml(check.name)}</div>
                    <div class="check-detail">${detail}</div>
                </div>
            </div>`;
        }

        html += `</div></div>`;
    }

    panel.innerHTML = html;
}

function toggleSection(header) {
    header.classList.toggle('open');
    const checks = header.nextElementSibling;
    checks.style.display = checks.style.display === 'none' ? 'block' : 'none';
}

// --- Registration Form ---
const FORM_FIELDS = [
    {
        section: 'Television Details',
        fields: [
            { key: 'type_of_television', label: 'Type of Television' },
            { key: 'brand', label: 'Brand' },
            { key: 'model_numbers', label: 'Model No./Family of Model', isArray: true },
            { key: 'definition', label: 'Definition (Resolution)' },
            { key: 'diagonal_screen_size', label: 'Diagonal Screen Size (inches)' },
            { key: 'screen_aspect_ratio', label: 'Screen Aspect Ratio' },
            { key: 'colour', label: 'Colour' },
            { key: 'year_of_manufacture', label: 'Year of Manufacture' },
            { key: 'country_of_origin', label: 'Country/Region of Origin' },
        ]
    },
    {
        section: 'Test Report Details',
        fields: [
            { key: 'test_report_reference_no', label: 'Reference No.' },
            { key: 'date_of_issue', label: 'Date of Issue' },
            { key: 'test_standard', label: 'Test Standard' },
            { key: 'screen_area_dm2', label: 'Screen Area (dm2)' },
            { key: 'power_input_on_mode_w', label: 'Power Input ON-Mode (W)' },
            { key: 'passive_standby_power_w', label: 'Passive Standby Power (W)' },
            { key: 'active_high_standby_w', label: 'Active High Standby (W)' },
            { key: 'active_low_standby_w', label: 'Active Low Standby (W)' },
        ]
    },
    {
        section: 'Testing Laboratory Details',
        fields: [
            { key: 'lab_type', label: 'Type of Laboratory' },
            { key: 'lab_name', label: 'Name' },
            { key: 'lab_address', label: 'Address' },
            { key: 'lab_country', label: 'Country/Region' },
            { key: 'lab_postal_code', label: 'Postal Code' },
        ]
    }
];

function renderForm(regFields) {
    const panel = document.getElementById('formPanel');
    let html = '';

    html += `<div class="message assistant">
        Below are the extracted fields ready for the ELS registration form.
        <strong style="color:var(--success)">Green</strong> fields were extracted successfully.
        <strong style="color:var(--warning)">Yellow</strong> fields need review.
        <strong style="color:var(--error)">Red</strong> fields are missing from the report.
    </div>`;

    for (const section of FORM_FIELDS) {
        html += `<div class="reg-form-section"><h3>${section.section}</h3>`;

        for (const field of section.fields) {
            let value = regFields[field.key];
            let displayValue, statusClass;

            if (field.isArray && Array.isArray(value)) {
                value = value.join(', ');
            }

            if (value === null || value === undefined || value === '') {
                displayValue = 'Not found in report';
                statusClass = 'missing';
            } else if (field.key === 'colour' && !value) {
                displayValue = 'Not explicitly stated';
                statusClass = 'review';
            } else {
                displayValue = String(value);
                statusClass = 'extracted';
            }

            html += `<div class="reg-field">
                <div class="field-label">${field.label}</div>
                <div class="field-value ${statusClass}" data-value="${escapeAttr(displayValue)}">${escapeHtml(displayValue)}</div>
                ${statusClass === 'extracted' ? `<button class="copy-btn" onclick="copyField(this, '${escapeAttr(displayValue)}')">Copy</button>` : ''}
            </div>`;
        }

        html += `</div>`;
    }

    panel.innerHTML = html;
}

// --- Copy Functions ---
function copyField(btn, value) {
    navigator.clipboard.writeText(value).then(() => {
        btn.textContent = 'Copied!';
        setTimeout(() => { btn.textContent = 'Copy'; }, 1500);
    });
}

function copyAllFields() {
    if (!currentData) return;
    const regFields = currentData.extracted.registration_fields || {};
    const lines = [];

    for (const section of FORM_FIELDS) {
        lines.push(`--- ${section.section} ---`);
        for (const field of section.fields) {
            let value = regFields[field.key];
            if (field.isArray && Array.isArray(value)) value = value.join(', ');
            lines.push(`${field.label}: ${value || 'N/A'}`);
        }
        lines.push('');
    }

    navigator.clipboard.writeText(lines.join('\n')).then(() => {
        showToast('All fields copied to clipboard');
    });
}

function showToast(msg) {
    const toast = document.getElementById('toast');
    toast.textContent = msg;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 2000);
}

// --- Helpers ---
function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function escapeAttr(str) {
    return str.replace(/'/g, "\\'").replace(/"/g, '&quot;');
}
