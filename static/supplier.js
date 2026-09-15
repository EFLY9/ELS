let currentData = null;
let amendingSubmissionId = null;
let currentProductType = 'tv';

function onProductTypeChange() {
    currentProductType = document.getElementById('productTypeSelect').value;
    const title = document.getElementById('uploadTitle');
    if (title) {
        title.textContent = currentProductType === 'refrigerator' ? 'Upload Refrigerator Test Report' : 'Upload TV Test Report';
    }
}

function getActiveFormFields() {
    return currentProductType === 'refrigerator' ? FRIDGE_FORM_FIELDS : FORM_FIELDS;
}

// --- Views ---
function hideAll() {
    ['dashboardView', 'uploadView', 'loadingView', 'resultsView'].forEach(id => {
        document.getElementById(id).style.display = 'none';
    });
}

function showDashboard() {
    hideAll();
    document.getElementById('dashboardView').style.display = '';
    amendingSubmissionId = null;
    currentData = null;
    loadDashboard();
}

function showNewUpload() {
    hideAll();
    document.getElementById('uploadView').style.display = '';
    amendingSubmissionId = null;
    currentData = null;
}

function showLoading() {
    hideAll();
    document.getElementById('loadingView').style.display = '';
}

function showResults() {
    hideAll();
    document.getElementById('resultsView').style.display = '';
}

// --- Dashboard ---
async function loadDashboard() {
    const container = document.getElementById('submissionsList');
    try {
        const resp = await fetch('/api/submissions');
        const data = await resp.json();
        const subs = data.submissions;

        if (subs.length === 0) {
            container.innerHTML = '<div class="panel" style="padding:40px;text-align:center;">'
                + '<p style="color:var(--text-secondary);font-size:15px;">No submissions yet.</p>'
                + '<p style="color:var(--text-secondary);font-size:13px;margin-top:8px;">Click "+ New Application" to upload a TV test report and start your first registration.</p>'
                + '</div>';
            return;
        }

        let html = '<table style="width:100%;border-collapse:collapse;">';
        html += '<thead><tr style="border-bottom:2px solid var(--border);text-align:left;">'
            + '<th style="padding:10px 12px;font-size:12px;color:var(--text-secondary);font-weight:600;">ID</th>'
            + '<th style="padding:10px 12px;font-size:12px;color:var(--text-secondary);font-weight:600;">Product</th>'
            + '<th style="padding:10px 12px;font-size:12px;color:var(--text-secondary);font-weight:600;">Brand / Model</th>'
            + '<th style="padding:10px 12px;font-size:12px;color:var(--text-secondary);font-weight:600;">Report Ref</th>'
            + '<th style="padding:10px 12px;font-size:12px;color:var(--text-secondary);font-weight:600;">Submitted</th>'
            + '<th style="padding:10px 12px;font-size:12px;color:var(--text-secondary);font-weight:600;">Status</th>'
            + '<th style="padding:10px 12px;"></th>'
            + '</tr></thead><tbody>';

        for (const sub of subs) {
            const dt = new Date(sub.submitted_at);
            const dateStr = dt.toLocaleDateString() + ' ' + dt.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});

            let statusBadge, actionBtn;
            if (sub.status === 'Approved') {
                statusBadge = '<span class="badge badge-approved">Approved</span>';
                actionBtn = '<span style="color:var(--text-secondary);font-size:13px;">-</span>';
            } else if (sub.status === 'Rejected') {
                statusBadge = '<span class="badge badge-rejected">Rejected</span>';
                actionBtn = '<span style="color:var(--text-secondary);font-size:13px;">-</span>';
            } else if (sub.status === 'Returned') {
                statusBadge = '<span class="badge badge-returned">Returned</span>';
                actionBtn = '<button class="btn btn-sm btn-primary" onclick="event.stopPropagation();amendSubmission(\'' + sub.id + '\')">Amend</button>';
            } else if (sub.status === 'De-registered') {
                statusBadge = '<span class="badge badge-rejected">De-registered</span>';
                actionBtn = '<span style="color:var(--text-secondary);font-size:13px;">-</span>';
            } else {
                statusBadge = '<span class="badge badge-pending">Pending Review</span>';
                actionBtn = '<span style="color:var(--text-secondary);font-size:13px;">Under review</span>';
            }

            let commentRow = '';
            if (sub.status === 'Returned' && sub.return_comments) {
                commentRow = '<tr><td colspan="6" style="padding:4px 12px 12px 12px;font-size:12px;color:var(--warning);font-style:italic;border-bottom:1px solid var(--border);">'
                    + 'Officer comments: "' + escapeHtml(sub.return_comments) + '"</td></tr>';
            } else if (sub.status === 'Rejected' && sub.rejection_reason) {
                commentRow = '<tr><td colspan="6" style="padding:4px 12px 12px 12px;font-size:12px;color:var(--error);font-style:italic;border-bottom:1px solid var(--border);">'
                    + 'Rejection reason: "' + escapeHtml(sub.rejection_reason) + '"</td></tr>';
            } else if (sub.status === 'De-registered' && sub.deregister_reason) {
                commentRow = '<tr><td colspan="6" style="padding:4px 12px 12px 12px;font-size:12px;color:var(--error);font-style:italic;border-bottom:1px solid var(--border);">'
                    + 'De-registration reason: "' + escapeHtml(sub.deregister_reason) + '"</td></tr>';
            }

            html += '<tr style="border-bottom:' + (commentRow ? 'none' : '1px solid var(--border)') + ';">'
                + '<td style="padding:12px;font-size:13px;font-family:monospace;">' + escapeHtml(sub.id) + '</td>'
                + '<td style="padding:12px;font-size:13px;">' + (sub.product_type === 'refrigerator' ? 'Fridge' : 'TV') + '</td>'
                + '<td style="padding:12px;font-size:13px;"><strong>' + escapeHtml(sub.brand || '') + '</strong> ' + escapeHtml(sub.model || '') + '</td>'
                + '<td style="padding:12px;font-size:13px;">' + escapeHtml(sub.report_ref || '') + '</td>'
                + '<td style="padding:12px;font-size:13px;color:var(--text-secondary);">' + dateStr + '</td>'
                + '<td style="padding:12px;">' + statusBadge + '</td>'
                + '<td style="padding:12px;text-align:right;">' + actionBtn + '</td>'
                + '</tr>';
            html += commentRow;
        }

        html += '</tbody></table>';
        container.innerHTML = '<div class="panel" style="overflow-x:auto;">' + html + '</div>';
    } catch (e) {
        container.innerHTML = '<div class="panel" style="padding:24px;color:var(--error);">Error loading submissions: ' + escapeHtml(e.message) + '</div>';
    }
}

// --- Amend a returned submission ---
async function amendSubmission(id) {
    try {
        const resp = await fetch('/api/submissions/' + id);
        if (!resp.ok) { alert('Submission not found'); return; }
        const sub = await resp.json();

        amendingSubmissionId = id;
        currentProductType = sub.product_type || 'tv';

        const regFields = sub.registration_fields || sub.extracted.registration_fields || {};
        const prevSources = sub.field_sources || {};

        currentData = {
            extracted: sub.extracted,
            validation: sub.validation,
            can_submit: false,
        };

        renderIssues(sub.validation, false);

        // Show officer return comments + re-upload option
        const commentsBar = document.getElementById('returnCommentsBar');
        commentsBar.style.display = '';
        let barHtml = '<div class="returned-notice" style="margin-bottom:16px;">';
        barHtml += '<h3 style="font-size:14px;color:var(--warning);">Officer returned this submission for clarification</h3>';
        if (sub.return_comments) {
            barHtml += '<p style="font-size:13px;color:var(--text);margin-top:6px;">Comments: <em>"' + escapeHtml(sub.return_comments) + '"</em></p>';
        }
        barHtml += '<div style="margin-top:12px;display:flex;gap:10px;align-items:center;">';
        barHtml += '<span style="font-size:13px;color:var(--text-secondary);">You can re-upload a corrected test report or edit the fields below:</span>';
        barHtml += '</div>';
        barHtml += '<div style="margin-top:10px;display:flex;gap:10px;align-items:center;">';
        barHtml += '<button class="btn btn-primary btn-sm" onclick="document.getElementById(\'amendFileInput\').click()">Upload New PDF</button>';
        barHtml += '<input type="file" id="amendFileInput" accept=".pdf" style="display:none;" onchange="reuploadForAmend(this)">';
        barHtml += '<span style="font-size:12px;color:var(--text-secondary);">or edit the fields directly on the right</span>';
        barHtml += '</div>';
        barHtml += '</div>';
        commentsBar.innerHTML = barHtml;

        renderForm(regFields, prevSources);
        showResults();
    } catch (e) {
        alert('Error: ' + e.message);
    }
}

// --- Re-upload for amend ---
async function reuploadForAmend(input) {
    const file = input.files[0];
    if (!file) return;
    input.value = '';

    showLoading();
    const formData = new FormData();
    formData.append('file', file);
    try {
        const resp = await fetch('/api/upload?product_type=' + currentProductType, { method: 'POST', body: formData });
        if (!resp.ok) {
            const err = await resp.json();
            alert(err.detail || 'Upload failed');
            amendSubmission(amendingSubmissionId);
            return;
        }
        const newData = await resp.json();
        currentData = newData;
        renderIssues(newData.validation, newData.can_submit);
        renderForm(newData.extracted.registration_fields || {});
        showResults();
    } catch (e) {
        alert('Error: ' + e.message);
        amendSubmission(amendingSubmissionId);
    }
}

// --- Upload Handlers ---
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');

dropZone.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('drag-over'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file && file.type === 'application/pdf') uploadFile(file);
});
fileInput.addEventListener('change', (e) => { if (e.target.files[0]) uploadFile(e.target.files[0]); });

async function uploadFile(file) {
    showLoading();
    const formData = new FormData();
    formData.append('file', file);
    try {
        const resp = await fetch('/api/upload?product_type=' + currentProductType, { method: 'POST', body: formData });
        if (!resp.ok) {
            const err = await resp.json();
            alert(err.detail || 'Upload failed');
            showDashboard();
            return;
        }
        currentData = await resp.json();
        document.getElementById('returnCommentsBar').style.display = 'none';
        renderResults(currentData);
        showResults();
    } catch (e) {
        alert('Error: ' + e.message);
        showDashboard();
    }
}

async function runDemo() {
    showLoading();
    try {
        const resp = await fetch('/api/demo?product_type=' + currentProductType);
        currentData = await resp.json();
        document.getElementById('returnCommentsBar').style.display = 'none';
        renderResults(currentData);
        showResults();
    } catch (e) {
        alert('Error: ' + e.message);
        showDashboard();
    }
}

// --- Render Results ---
function renderResults(data) {
    renderIssues(data.validation, data.can_submit);
    renderForm(data.extracted.registration_fields || {});
}

function renderIssues(validation, canSubmit) {
    const panel = document.getElementById('issuesPanel');
    const statusBadge = document.getElementById('overallStatus');
    const failCount = validation.summary.failed;
    const warnCount = validation.summary.warnings;

    if (failCount === 0) {
        statusBadge.textContent = 'Ready';
        statusBadge.style.background = 'var(--success-bg)';
        statusBadge.style.color = 'var(--success)';
    } else {
        statusBadge.textContent = failCount + ' Issue' + (failCount !== 1 ? 's' : '');
        statusBadge.style.background = 'var(--error-bg)';
        statusBadge.style.color = 'var(--error)';
    }

    let html = '';

    if (failCount === 0) {
        html += '<div class="message summary-good">';
        html += '<strong>Your test report passed all compliance checks!</strong><br>';
        html += 'Review the registration fields on the right and click <strong>Submit</strong> when ready.';
        html += '</div>';
    } else {
        html += '<div class="message summary-issues">';
        html += 'We found <strong>' + failCount + ' issue' + (failCount !== 1 ? 's' : '') + '</strong>';
        if (warnCount > 0) html += ' and <strong>' + warnCount + ' warning' + (warnCount !== 1 ? 's' : '') + '</strong>';
        html += ' in your test report.';
        html += '</div>';

        html += '<div class="message assistant">';
        html += 'You can <strong>manually fill in missing fields</strong> on the right. Once all required fields are filled, you can submit.';
        html += '</div>';

        for (const section of validation.sections) {
            const issues = section.checks.filter(c => c.passed === false || c.passed === null);
            if (issues.length === 0) continue;

            html += '<div class="val-section">';
            html += '<div class="val-section-header open" onclick="toggleSection(this)">';
            html += '<span class="toggle">&#9654;</span>';
            html += (section.name || section.title);
            html += '<span class="section-stats" style="color:var(--error)">' + issues.length + ' issue' + (issues.length !== 1 ? 's' : '') + '</span>';
            html += '</div>';
            html += '<div class="val-checks">';

            for (const check of issues) {
                const isFail = check.passed === false;
                const status = isFail ? 'fail' : 'warn';
                const icon = isFail ? '&#10007;' : '?';
                const friendly = buildFriendlyMessage(check);

                html += '<div class="val-check ' + status + '">';
                html += '<div class="status-icon">' + icon + '</div>';
                html += '<div class="check-content">';
                html += '<div class="check-name">' + escapeHtml(check.name) + '</div>';
                html += '<div class="check-detail">' + friendly + '</div>';
                html += '</div></div>';
            }

            html += '</div></div>';
        }
    }

    panel.innerHTML = html;
}

function buildFriendlyMessage(check) {
    const val = check.extracted_value;
    const hasValue = val !== null && val !== undefined && val !== '' && val !== false;

    if (!hasValue && check.passed === false) {
        return 'Your test report is <strong>missing</strong> this information. Expected: <span class="check-value">' + escapeHtml(check.expected || '') + '</span>';
    }
    if (check.passed === false && hasValue) {
        return 'Found <span class="check-value">' + escapeHtml(String(val)) + '</span> — ' + escapeHtml(check.reason);
    }
    if (check.passed === null) {
        return 'Unable to verify. ' + escapeHtml(check.reason);
    }
    return escapeHtml(check.reason);
}

function toggleSection(header) {
    header.classList.toggle('open');
    const checks = header.nextElementSibling;
    checks.style.display = checks.style.display === 'none' ? 'block' : 'none';
}

// --- Registration Form (Editable) ---
const FORM_FIELDS = [
    {
        section: 'Television Details',
        fields: [
            { key: 'type_of_television', label: 'Type of Television', required: true },
            { key: 'brand', label: 'Brand', required: true },
            { key: 'model_numbers', label: 'Model No./Family of Model', isArray: true, required: true },
            { key: 'definition', label: 'Definition (Resolution)' },
            { key: 'diagonal_screen_size', label: 'Diagonal Screen Size (inches)', required: true },
            { key: 'screen_aspect_ratio', label: 'Screen Aspect Ratio', required: true },
            { key: 'colour', label: 'Colour' },
            { key: 'year_of_manufacture', label: 'Year of Manufacture', required: true },
            { key: 'country_of_origin', label: 'Country/Region of Origin', required: true },
        ]
    },
    {
        section: 'Test Report Details',
        fields: [
            { key: 'test_report_reference_no', label: 'Reference No.', required: true },
            { key: 'date_of_issue', label: 'Date of Issue', required: true },
            { key: 'test_standard', label: 'Test Standard', required: true },
            { key: 'screen_area_dm2', label: 'Screen Area (dm2)', required: true },
            { key: 'power_input_on_mode_w', label: 'Power Input ON-Mode (W)', required: true },
            { key: 'passive_standby_power_w', label: 'Passive Standby Power (W)', required: true },
            { key: 'active_high_standby_w', label: 'Active High Standby (W)' },
            { key: 'active_low_standby_w', label: 'Active Low Standby (W)' },
        ]
    },
    {
        section: 'Testing Laboratory Details',
        fields: [
            { key: 'lab_type', label: 'Type of Laboratory' },
            { key: 'lab_name', label: 'Name', required: true },
            { key: 'lab_address', label: 'Address' },
            { key: 'lab_country', label: 'Country/Region', required: true },
        ]
    }
];

const FRIDGE_FORM_FIELDS = [
    {
        section: 'Refrigerator Details',
        fields: [
            { key: 'type', label: 'Type', required: true },
            { key: 'brand', label: 'Brand', required: true },
            { key: 'model_numbers', label: 'Model No./Family of Model', isArray: true, required: true },
            { key: 'colour', label: 'Colour' },
            { key: 'features', label: 'Features' },
            { key: 'country_of_origin', label: 'Country of Origin', required: true },
            { key: 'refrigerant_type', label: 'Type of Refrigerant', required: true },
            { key: 'refrigerant_charge_g', label: 'Total Refrigerant Charge (g)', required: true },
        ]
    },
    {
        section: 'Test Report Details',
        fields: [
            { key: 'test_report_reference_no', label: 'Reference No.', required: true },
            { key: 'date_of_issue', label: 'Date of Issue', required: true },
            { key: 'test_standard', label: 'Test Standard', required: true },
            { key: 'total_volume_measured_l', label: 'Total Volume - Measured (litres)', required: true },
            { key: 'total_adjusted_volume_rated_l', label: 'Total Adjusted Volume - Rated (litres)', required: true },
            { key: 'annual_energy_consumption_kwh', label: 'Annual Energy Consumption (kWh)', required: true },
        ]
    },
    {
        section: 'Testing Laboratory Details',
        fields: [
            { key: 'lab_type', label: 'Type of Laboratory' },
            { key: 'lab_name', label: 'Name', required: true },
            { key: 'lab_address', label: 'Address' },
            { key: 'lab_country', label: 'Country/Region', required: true },
        ]
    }
];

let fieldSources = {};

function renderForm(regFields, existingSources) {
    const panel = document.getElementById('formPanel');
    fieldSources = {};
    let html = '';

    html += '<div class="message assistant">';
    html += '<strong style="color:var(--success)">Green</strong> = extracted from PDF. ';
    html += '<strong style="color:var(--error)">Red</strong> = missing — please fill in. ';
    html += '<strong style="color:var(--warning)">Yellow</strong> = manually entered.';
    html += '</div>';

    for (const section of getActiveFormFields()) {
        html += '<div class="reg-form-section"><h3>' + section.section + '</h3>';
        for (const field of section.fields) {
            let value = regFields[field.key];
            if (field.isArray && Array.isArray(value)) value = value.join(', ');

            const hasValue = value !== null && value !== undefined && value !== '';
            let source;
            if (existingSources && existingSources[field.key]) {
                source = existingSources[field.key];
            } else {
                source = hasValue ? 'extracted' : 'missing';
            }
            fieldSources[field.key] = source;

            const inputClass = 'field-input source-' + source;
            const reqMark = field.required ? '<span class="field-required">*</span>' : '';

            html += '<div class="reg-field">';
            html += '<div class="field-label">' + field.label + reqMark + '</div>';
            html += '<input class="' + inputClass + '" type="text" '
                + 'id="field-' + field.key + '" '
                + 'data-key="' + field.key + '" '
                + 'data-required="' + (field.required ? '1' : '0') + '" '
                + 'value="' + escapeAttr(hasValue ? String(value) : '') + '" '
                + (hasValue ? '' : 'placeholder="Enter ' + escapeAttr(field.label) + '"')
                + ' oninput="onFieldEdit(this)">';
            html += '</div>';
        }
        html += '</div>';
    }

    panel.innerHTML = html;
    updateSubmitButton();
}

function onFieldEdit(input) {
    const key = input.dataset.key;
    const value = input.value.trim();

    if (value && fieldSources[key] === 'missing') {
        fieldSources[key] = 'manual';
        input.className = 'field-input source-manual';
    } else if (!value) {
        fieldSources[key] = 'missing';
        input.className = 'field-input source-missing';
    }

    updateSubmitButton();
}

function updateSubmitButton() {
    const submitBar = document.getElementById('submitBar');
    let missingRequired = 0;

    for (const section of getActiveFormFields()) {
        for (const field of section.fields) {
            if (!field.required) continue;
            const input = document.getElementById('field-' + field.key);
            if (!input || !input.value.trim()) missingRequired++;
        }
    }

    const isAmend = !!amendingSubmissionId;
    const submitLabel = isAmend ? 'Re-submit' : 'Submit Registration';
    const disabledLabel = 'Fill ' + missingRequired + ' required field' + (missingRequired !== 1 ? 's' : '') + ' to submit';

    if (missingRequired === 0) {
        submitBar.innerHTML = '<button class="btn btn-success" style="flex:1;" onclick="submitRegistration()">' + submitLabel + '</button>';
    } else {
        submitBar.innerHTML = '<button class="btn" style="flex:1;background:#94a3b8;color:white;cursor:not-allowed;" '
            + 'onclick="alert(\'Please fill in the ' + missingRequired + ' required field' + (missingRequired !== 1 ? 's' : '') + ' marked with * before submitting.\')">'
            + disabledLabel + '</button>';
    }
}

function getEditedFields() {
    const fields = {};
    for (const section of getActiveFormFields()) {
        for (const field of section.fields) {
            const input = document.getElementById('field-' + field.key);
            fields[field.key] = input ? input.value.trim() : '';
        }
    }
    return fields;
}

function getFieldSources() {
    const sources = {};
    for (const section of getActiveFormFields()) {
        for (const field of section.fields) {
            sources[field.key] = fieldSources[field.key] || 'missing';
        }
    }
    return sources;
}

async function submitRegistration() {
    const edited = getEditedFields();
    const sources = getFieldSources();

    try {
        let resp;
        if (amendingSubmissionId) {
            resp = await fetch('/api/submissions/' + amendingSubmissionId + '/resubmit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ edited_fields: edited, field_sources: sources }),
            });
        } else {
            resp = await fetch('/api/submit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    extracted: currentData.extracted,
                    validation: currentData.validation,
                    edited_fields: edited,
                    field_sources: sources,
                    product_type: currentProductType,
                }),
            });
        }

        if (!resp.ok) {
            const err = await resp.json();
            alert(err.detail || 'Submission failed');
            return;
        }

        const result = await resp.json();
        const modalTitle = document.getElementById('modalTitle');
        const modalDesc = document.getElementById('modalDesc');
        const modalIcon = document.getElementById('modalIcon');

        if (result.auto_approved) {
            modalIcon.textContent = '\u2705';
            modalTitle.textContent = 'Registration Auto-Approved';
            modalDesc.innerHTML = 'All validation checks passed and all fields were extracted from your document.<br>'
                + 'Submission ID: <strong>' + result.submission_id + '</strong><br><br>'
                + 'Your TV product registration has been <strong>automatically approved</strong>.';
        } else if (amendingSubmissionId) {
            modalIcon.textContent = '\u2705';
            modalTitle.textContent = 'Submission Re-submitted';
            modalDesc.innerHTML = 'Submission ID: <strong>' + result.submission_id + '</strong><br><br>'
                + 'Your amended submission has been re-submitted for officer review.';
        } else {
            modalIcon.textContent = '\u2705';
            modalTitle.textContent = 'Registration Submitted';
            modalDesc.innerHTML = 'Submission ID: <strong>' + result.submission_id + '</strong><br><br>'
                + 'Your submission will be reviewed by an NEA officer.';
        }

        document.getElementById('successModal').style.display = 'flex';
    } catch (e) {
        alert('Error submitting: ' + e.message);
    }
}

function closeModalAndRefresh() {
    document.getElementById('successModal').style.display = 'none';
    showDashboard();
}

// --- Copy Functions ---
function copyField(btn, value) {
    navigator.clipboard.writeText(value).then(() => {
        btn.textContent = 'Copied!';
        setTimeout(() => { btn.textContent = 'Copy'; }, 1500);
    });
}

function copyAllFields() {
    const fields = getEditedFields();
    const lines = [];
    for (const section of getActiveFormFields()) {
        lines.push('--- ' + section.section + ' ---');
        for (const field of section.fields) {
            lines.push(field.label + ': ' + (fields[field.key] || 'N/A'));
        }
        lines.push('');
    }
    navigator.clipboard.writeText(lines.join('\n')).then(() => showToast('All fields copied to clipboard'));
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

// Load dashboard on page load
loadDashboard();
