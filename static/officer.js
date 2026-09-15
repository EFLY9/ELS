let currentData = null;

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
        ]
    }
];

const FRIDGE_FORM_FIELDS = [
    {
        section: 'Refrigerator Details',
        fields: [
            { key: 'type', label: 'Type' },
            { key: 'brand', label: 'Brand' },
            { key: 'model_numbers', label: 'Model No./Family of Model', isArray: true },
            { key: 'colour', label: 'Colour' },
            { key: 'features', label: 'Features' },
            { key: 'country_of_origin', label: 'Country of Origin' },
            { key: 'refrigerant_type', label: 'Type of Refrigerant' },
            { key: 'refrigerant_charge_g', label: 'Total Refrigerant Charge (g)' },
        ]
    },
    {
        section: 'Test Report Details',
        fields: [
            { key: 'test_report_reference_no', label: 'Reference No.' },
            { key: 'date_of_issue', label: 'Date of Issue' },
            { key: 'test_standard', label: 'Test Standard' },
            { key: 'total_volume_measured_l', label: 'Total Volume - Measured (litres)' },
            { key: 'total_adjusted_volume_rated_l', label: 'Total Adjusted Volume - Rated (litres)' },
            { key: 'annual_energy_consumption_kwh', label: 'Annual Energy Consumption (kWh)' },
        ]
    },
    {
        section: 'Testing Laboratory Details',
        fields: [
            { key: 'lab_type', label: 'Type of Laboratory' },
            { key: 'lab_name', label: 'Name' },
            { key: 'lab_address', label: 'Address' },
            { key: 'lab_country', label: 'Country/Region' },
        ]
    }
];

function getFormFieldsForProduct(productType) {
    return productType === 'refrigerator' ? FRIDGE_FORM_FIELDS : FORM_FIELDS;
}

// --- Views ---
function showList() {
    document.getElementById('listView').style.display = '';
    document.getElementById('detailView').style.display = 'none';
    loadSubmissions();
}

function showDetail() {
    document.getElementById('listView').style.display = 'none';
    document.getElementById('detailView').style.display = '';
}

// --- Load Submissions ---
async function loadSubmissions() {
    const container = document.getElementById('submissionsList');
    try {
        const resp = await fetch('/api/submissions');
        const data = await resp.json();
        const subs = data.submissions;

        if (subs.length === 0) {
            container.innerHTML = '<div class="panel" style="padding:40px;text-align:center;">'
                + '<p style="color:var(--text-secondary);font-size:15px;">No submissions yet.</p>'
                + '<p style="color:var(--text-secondary);font-size:13px;margin-top:8px;">Submissions from suppliers will appear here once they upload and submit their TV test reports.</p>'
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
            + '<th style="padding:10px 12px;font-size:12px;color:var(--text-secondary);font-weight:600;">Validation</th>'
            + '<th style="padding:10px 12px;font-size:12px;color:var(--text-secondary);font-weight:600;">Status</th>'
            + '<th style="padding:10px 12px;"></th>'
            + '</tr></thead><tbody>';

        for (const sub of subs) {
            const dt = new Date(sub.submitted_at);
            const dateStr = dt.toLocaleDateString() + ' ' + dt.toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'});
            const allPassed = sub.passed === sub.total;

            let actions = '<div style="display:flex;gap:6px;justify-content:flex-end;">';
            actions += '<button class="btn btn-sm btn-outline" style="color:var(--success);border-color:var(--success);" onclick="event.stopPropagation();viewSubmission(\'' + sub.id + '\')">View</button>';
            if (sub.status === 'Approved') {
                actions += '<button class="btn btn-sm btn-outline" style="color:var(--warning);border-color:var(--warning);" onclick="event.stopPropagation();listAction(\'' + sub.id + '\',\'deregister\')">De-register</button>';
            }
            actions += '<button class="btn btn-sm btn-outline" style="color:var(--error);border-color:var(--error);" onclick="event.stopPropagation();listAction(\'' + sub.id + '\',\'delete\')">Delete</button>';
            actions += '</div>';

            html += '<tr style="border-bottom:1px solid var(--border);cursor:pointer;" onclick="viewSubmission(\'' + sub.id + '\')">'
                + '<td style="padding:12px;font-size:13px;font-family:monospace;">' + escapeHtml(sub.id) + '</td>'
                + '<td style="padding:12px;font-size:13px;">' + (sub.product_type === 'refrigerator' ? 'Fridge' : 'TV') + '</td>'
                + '<td style="padding:12px;font-size:13px;"><strong>' + escapeHtml(sub.brand) + '</strong> ' + escapeHtml(sub.model) + '</td>'
                + '<td style="padding:12px;font-size:13px;">' + escapeHtml(sub.report_ref) + '</td>'
                + '<td style="padding:12px;font-size:13px;color:var(--text-secondary);">' + dateStr + '</td>'
                + '<td style="padding:12px;font-size:13px;">'
                + '<span style="color:' + (allPassed ? 'var(--success)' : 'var(--error)') + ';font-weight:600;">'
                + sub.passed + '/' + sub.total + '</span></td>'
                + '<td style="padding:12px;"><span class="badge badge-' + getStatusClass(sub.status) + '">' + escapeHtml(sub.status) + '</span></td>'
                + '<td style="padding:12px;white-space:nowrap;">' + actions + '</td>'
                + '</tr>';
        }

        html += '</tbody></table>';
        container.innerHTML = '<div class="panel" style="overflow-x:auto;">' + html + '</div>';
    } catch (e) {
        container.innerHTML = '<div class="panel" style="padding:24px;color:var(--error);">Error loading submissions: ' + escapeHtml(e.message) + '</div>';
    }
}

async function listAction(id, action) {
    if (action === 'delete') {
        if (!confirm('Are you sure you want to delete submission ' + id + '? This cannot be undone.')) return;
        try {
            const resp = await fetch('/api/submissions/' + id + '/action', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action: 'delete', comments: ''})
            });
            if (!resp.ok) { const err = await resp.json(); alert(err.detail || 'Failed'); return; }
            showToast('Submission deleted');
            loadSubmissions();
        } catch (e) { alert('Error: ' + e.message); }
    } else if (action === 'deregister') {
        const reason = prompt('Enter reason for de-registration:');
        if (reason === null) return;
        if (!reason.trim()) { alert('Reason is required'); return; }
        try {
            const resp = await fetch('/api/submissions/' + id + '/action', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action: 'deregister', comments: reason.trim()})
            });
            if (!resp.ok) { const err = await resp.json(); alert(err.detail || 'Failed'); return; }
            showToast('Submission de-registered');
            loadSubmissions();
        } catch (e) { alert('Error: ' + e.message); }
    }
}

async function viewSubmission(id) {
    try {
        const resp = await fetch('/api/submissions/' + id);
        if (!resp.ok) { alert('Submission not found'); return; }
        const sub = await resp.json();
        currentData = sub;

        const meta = document.getElementById('submissionMeta');
        const dt = new Date(sub.submitted_at);
        const statusColor = sub.status === 'Approved' ? 'var(--success)' : sub.status === 'Rejected' ? 'var(--error)' : 'var(--warning)';
        const statusBg = sub.status === 'Approved' ? 'var(--success-bg)' : sub.status === 'Rejected' ? 'var(--error-bg)' : 'var(--warning-bg)';
        meta.innerHTML = '<div class="panel" style="padding:16px 20px;display:flex;gap:24px;flex-wrap:wrap;align-items:center;">'
            + '<div><span style="font-size:12px;color:var(--text-secondary);">Submission ID</span><br><strong style="font-family:monospace;">' + escapeHtml(sub.id) + '</strong></div>'
            + '<div><span style="font-size:12px;color:var(--text-secondary);">Brand / Model</span><br><strong>' + escapeHtml(sub.brand) + ' ' + escapeHtml(sub.model) + '</strong></div>'
            + '<div><span style="font-size:12px;color:var(--text-secondary);">Report Ref</span><br><strong>' + escapeHtml(sub.report_ref) + '</strong></div>'
            + '<div><span style="font-size:12px;color:var(--text-secondary);">Submitted</span><br><strong>' + dt.toLocaleDateString() + ' ' + dt.toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}) + '</strong></div>'
            + '<div><span style="font-size:12px;color:var(--text-secondary);">Status</span><br><span class="badge" style="background:' + statusBg + ';color:' + statusColor + ';">' + escapeHtml(sub.status) + '</span>'
            + (sub.auto_approved ? '<br><span style="font-size:11px;color:var(--text-secondary);">Auto-approved by system</span>' : '')
            + '</div>'
            + '</div>';

        renderValidation(sub.validation);
        const regFields = sub.registration_fields || sub.extracted.registration_fields || {};
        renderForm(regFields, sub.field_sources || null, sub.product_type || 'tv');
        renderActions(sub);
        showDetail();
    } catch (e) {
        alert('Error: ' + e.message);
    }
}

// --- Render Validation (full) ---
function renderValidation(validation) {
    const panel = document.getElementById('validationPanel');
    const summary = validation.summary;
    const failCount = summary.failed;
    const warnCount = summary.warnings;
    const allPassed = failCount === 0 && warnCount === 0;

    const badge = document.getElementById('overallStatus');
    if (allPassed) {
        badge.textContent = 'All Passed';
        badge.style.background = 'var(--success-bg)';
        badge.style.color = 'var(--success)';
    } else {
        badge.textContent = failCount + ' Issue' + (failCount !== 1 ? 's' : '');
        badge.style.background = 'var(--error-bg)';
        badge.style.color = 'var(--error)';
    }

    let html = '<div class="summary-bar">'
        + '<div class="summary-stat"><div class="number">' + summary.total + '</div><div class="label">Total Checks</div></div>'
        + '<div class="summary-stat pass"><div class="number">' + summary.passed + '</div><div class="label">Passed</div></div>'
        + '<div class="summary-stat fail"><div class="number">' + summary.failed + '</div><div class="label">Failed</div></div>'
        + '<div class="summary-stat warn"><div class="number">' + summary.warnings + '</div><div class="label">Warnings</div></div>'
        + '</div>';

    if (allPassed) {
        html += '<div class="message summary-good"><strong>All compliance checks passed.</strong> This submission meets all ELS validation criteria.</div>';
    } else {
        const parts = [];
        if (failCount > 0) parts.push('<strong>' + failCount + ' check' + (failCount > 1 ? 's' : '') + ' failed</strong>');
        if (warnCount > 0) parts.push('<strong>' + warnCount + ' item' + (warnCount > 1 ? 's' : '') + ' need attention</strong>');
        html += '<div class="message summary-issues">' + parts.join(' and ') + '. Review the details below.</div>';
    }

    for (const section of validation.sections) {
        const checks = section.checks;
        const sp = checks.filter(c => c.passed === true).length;
        const sf = checks.filter(c => c.passed === false).length;
        const sw = checks.filter(c => c.passed === null).length;
        const hasIssues = sf > 0 || sw > 0;

        html += '<div class="val-section">'
            + '<div class="val-section-header' + (hasIssues ? ' open' : '') + '" onclick="toggleSection(this)">'
            + '<span class="toggle">&#9654;</span> '
            + escapeHtml(section.name || section.title)
            + '<span class="section-stats">' + sp + '/' + checks.length + ' passed'
            + (sf > 0 ? ' &middot; <span style="color:var(--error)">' + sf + ' failed</span>' : '')
            + (sw > 0 ? ' &middot; <span style="color:var(--warning)">' + sw + ' warnings</span>' : '')
            + '</span></div>'
            + '<div class="val-checks" style="display:' + (hasIssues ? 'block' : 'none') + '">';

        for (const check of checks) {
            const status = check.passed === true ? 'pass' : check.passed === false ? 'fail' : 'warn';
            const icon = check.passed === true ? '&#10003;' : check.passed === false ? '&#10007;' : '?';
            let detail = escapeHtml(check.reason);
            if (check.extracted_value !== null && check.extracted_value !== undefined && check.extracted_value !== '') {
                detail += ' <span class="check-value">' + escapeHtml(String(check.extracted_value)) + '</span>';
            }
            html += '<div class="val-check ' + status + '">'
                + '<div class="status-icon">' + icon + '</div>'
                + '<div class="check-content">'
                + '<div class="check-name">' + escapeHtml(check.name) + '</div>'
                + '<div class="check-detail">' + detail + '</div>'
                + '</div></div>';
        }

        html += '</div></div>';
    }

    panel.innerHTML = html;
}

function toggleSection(header) {
    header.classList.toggle('open');
    const checks = header.nextElementSibling;
    checks.style.display = checks.style.display === 'none' ? 'block' : 'none';
}

// --- Registration Form ---
function renderForm(regFields, fieldSources, productType) {
    const activeFields = getFormFieldsForProduct(productType);
    const panel = document.getElementById('formPanel');
    const hasSources = fieldSources && Object.keys(fieldSources).length > 0;
    const manualCount = hasSources ? Object.values(fieldSources).filter(s => s === 'manual').length : 0;

    let html = '<div class="message assistant">';
    if (hasSources && manualCount > 0) {
        html += '<strong style="color:var(--warning)">' + manualCount + ' field' + (manualCount !== 1 ? 's were' : ' was') + ' manually entered</strong> by the supplier (not extracted from the test report). ';
        html += 'Fields marked <span class="source-badge manual">Manual</span> should be verified against the original document.';
    } else {
        html += 'Registration fields. '
            + '<strong style="color:var(--success)">Green</strong> = extracted from PDF, '
            + '<strong style="color:var(--error)">Red</strong> = missing.';
    }
    html += '</div>';

    for (const section of activeFields) {
        html += '<div class="reg-form-section"><h3>' + section.section + '</h3>';
        for (const field of section.fields) {
            let value = regFields[field.key];
            if (field.isArray && Array.isArray(value)) value = value.join(', ');

            const source = hasSources ? (fieldSources[field.key] || 'extracted') : null;
            let displayValue, statusClass;
            if (value === null || value === undefined || value === '') {
                displayValue = 'Not provided';
                statusClass = 'missing';
            } else {
                displayValue = String(value);
                statusClass = source === 'manual' ? 'review' : 'extracted';
            }

            html += '<div class="reg-field">'
                + '<div class="field-label">' + field.label + '</div>'
                + '<div class="field-value ' + statusClass + '">' + escapeHtml(displayValue) + '</div>';

            if (hasSources && value && source) {
                html += '<span class="source-badge ' + (source === 'manual' ? 'manual' : 'extracted') + '">'
                    + (source === 'manual' ? 'Manual' : 'Extracted') + '</span>';
            }

            if (statusClass !== 'missing') {
                html += '<button class="copy-btn" onclick="copyField(this,\'' + escapeAttr(displayValue) + '\')">Copy</button>';
            }

            html += '</div>';
        }
        html += '</div>';
    }

    panel.innerHTML = html;
}

// --- Copy ---
function copyField(btn, value) {
    navigator.clipboard.writeText(value).then(() => {
        btn.textContent = 'Copied!';
        setTimeout(() => { btn.textContent = 'Copy'; }, 1500);
    });
}

function copyAllFields() {
    if (!currentData) return;
    const regFields = currentData.registration_fields || currentData.extracted.registration_fields || {};
    const fields = getFormFieldsForProduct(currentData.product_type || 'tv');
    const lines = [];
    for (const section of fields) {
        lines.push('--- ' + section.section + ' ---');
        for (const field of section.fields) {
            let value = regFields[field.key];
            if (field.isArray && Array.isArray(value)) value = value.join(', ');
            lines.push(field.label + ': ' + (value || 'N/A'));
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

// --- Status Helpers ---
function getStatusClass(status) {
    if (status === 'Approved') return 'approved';
    if (status === 'Rejected') return 'rejected';
    if (status === 'Returned') return 'returned';
    if (status === 'De-registered') return 'rejected';
    return 'pending';
}

function getActionIcon(action) {
    if (action === 'approve') return '&#9989;';
    if (action === 'reject') return '&#10060;';
    if (action === 'deregister') return '&#128683;';
    if (action === 'return') return '&#8617;&#65039;';
    if (action === 'submit') return '&#128196;';
    return '&#8226;';
}

function getActionLabel(action) {
    if (action === 'approve') return 'Approved by officer';
    if (action === 'reject') return 'Rejected by officer';
    if (action === 'return') return 'Returned for clarification';
    if (action === 'submit') return 'Submitted by supplier';
    return action;
}

// --- Officer Actions ---
function renderActions(sub) {
    const bar = document.getElementById('actionBar');

    if (sub.status === 'Pending Review') {
        bar.innerHTML = '<div class="action-bar">'
            + '<span class="action-label">Officer Action:</span>'
            + '<button class="btn-approve" onclick="showActionModal(\'approve\')">Approve</button>'
            + '<button class="btn-return" onclick="showActionModal(\'return\')">Return for Clarification</button>'
            + '<button class="btn-reject" onclick="showActionModal(\'reject\')">Reject</button>'
            + '</div>';
    } else {
        let html = '<div class="action-bar" style="flex-direction:column;align-items:stretch;">';
        html += '<span class="action-label" style="margin-bottom:8px;">Action History</span>';

        const history = sub.history || [];
        if (history.length === 0) {
            if (sub.auto_approved) {
                html += '<div class="history-entry approve">'
                    + '<div class="history-icon">&#9989;</div>'
                    + '<div class="history-content">'
                    + '<div class="history-action">Auto-approved by system</div>'
                    + '<div class="history-time">' + formatDateTime(sub.approved_at || sub.submitted_at) + '</div>'
                    + '</div></div>';
            }
        } else {
            // Show submission as first entry
            html += '<div class="history-entry submit">'
                + '<div class="history-icon">&#128196;</div>'
                + '<div class="history-content">'
                + '<div class="history-action">Submitted by supplier</div>'
                + '<div class="history-time">' + formatDateTime(sub.submitted_at) + '</div>'
                + '</div></div>';

            for (const entry of history) {
                html += '<div class="history-entry ' + entry.action + '">'
                    + '<div class="history-icon">' + getActionIcon(entry.action) + '</div>'
                    + '<div class="history-content">'
                    + '<div class="history-action">' + escapeHtml(getActionLabel(entry.action)) + '</div>'
                    + '<div class="history-time">' + formatDateTime(entry.at) + '</div>'
                    + (entry.comments ? '<div class="history-comments">"' + escapeHtml(entry.comments) + '"</div>' : '')
                    + '</div></div>';
            }
        }

        html += '</div>';
        bar.innerHTML = html;
    }
}

function formatDateTime(isoStr) {
    if (!isoStr) return '';
    const dt = new Date(isoStr);
    return dt.toLocaleDateString() + ' ' + dt.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});
}

function showActionModal(action) {
    if (action === 'approve') {
        if (confirm('Are you sure you want to approve this submission?')) {
            performAction('approve', '');
        }
        return;
    }

    const title = action === 'reject' ? 'Reject Submission' : 'Return for Clarification';
    const desc = action === 'reject'
        ? 'Please provide the reason for rejecting this submission. This will be visible to the supplier.'
        : 'Please provide comments explaining what the supplier needs to clarify or correct. They will see these comments.';
    const btnClass = action === 'reject' ? 'btn-reject' : 'btn-return';
    const btnLabel = action === 'reject' ? 'Reject' : 'Return';

    const container = document.getElementById('actionModalContainer');
    container.innerHTML = '<div class="action-modal" onclick="if(event.target===this)closeActionModal()">'
        + '<div class="action-modal-content">'
        + '<h3>' + title + '</h3>'
        + '<p>' + desc + '</p>'
        + '<textarea id="actionComments" placeholder="Enter your comments here..." autofocus></textarea>'
        + '<div class="action-modal-buttons">'
        + '<button class="btn btn-outline" onclick="closeActionModal()">Cancel</button>'
        + '<button class="' + btnClass + '" onclick="submitActionFromModal(\'' + action + '\')">' + btnLabel + '</button>'
        + '</div></div></div>';
}

function closeActionModal() {
    document.getElementById('actionModalContainer').innerHTML = '';
}

function submitActionFromModal(action) {
    const comments = document.getElementById('actionComments').value.trim();
    if (!comments) {
        alert('Please enter your comments before proceeding.');
        return;
    }
    performAction(action, comments);
}

async function performAction(action, comments) {
    try {
        const resp = await fetch('/api/submissions/' + currentData.id + '/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: action, comments: comments }),
        });
        if (!resp.ok) {
            const err = await resp.json();
            alert(err.detail || 'Action failed');
            return;
        }
        const result = await resp.json();
        closeActionModal();
        const actionLabels = { approve: 'approved', reject: 'rejected', return: 'returned for clarification' };
        showToast('Submission ' + (actionLabels[action] || action));
        viewSubmission(currentData.id);
    } catch (e) {
        alert('Error: ' + e.message);
    }
}

// Load submissions on page load
loadSubmissions();
