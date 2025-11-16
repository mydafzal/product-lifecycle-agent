// ===== Global State =====
let uploadedFiles = {
    sales: false,
    inventory: false,
    price_optimizer: false,
    marketing_planner: false,
    labor_simulator: false
};

let workflowRunning = false;
let eventSource = null;
let uploadValidated = false; // current-session flag

// ===== DOM Elements =====
const uploadForm = document.getElementById('uploadForm');
const uploadBtn = document.getElementById('uploadBtn');
const uploadAlert = document.getElementById('uploadAlert');
const runWorkflowBtn = document.getElementById('runWorkflowBtn');
const workflowAlert = document.getElementById('workflowAlert');
const logsContent = document.getElementById('logsContent');
const filesContent = document.getElementById('filesContent');
const clearLogsBtn = document.getElementById('clearLogsBtn');
const refreshFilesBtn = document.getElementById('refreshFilesBtn');
const loadingOverlay = document.getElementById('loadingOverlay');
const previewModal = document.getElementById('previewModal');
const closePreviewBtn = document.getElementById('closePreviewBtn');
const previewTitle = document.getElementById('previewTitle');
const previewContent = document.getElementById('previewContent');

// ===== File Input Handlers =====
const fileInputs = {
    sales: document.getElementById('sales-file'),
    inventory: document.getElementById('inventory-file'),
    price_optimizer: document.getElementById('price-file'),
    marketing_planner: document.getElementById('marketing-file'),
    labor_simulator: document.getElementById('labor-file')
};

// Add change event listeners to all file inputs
Object.keys(fileInputs).forEach(key => {
    fileInputs[key].addEventListener('change', function(e) {
        const file = e.target.files[0];
        const statusElement = document.getElementById(`${key}-status`);
        
        if (file) {
            uploadedFiles[key] = true;
            statusElement.className = 'file-status selected';
            statusElement.innerHTML = '<i class="fas fa-check-circle"></i> ' + file.name;
        } else {
            uploadedFiles[key] = false;
            statusElement.className = 'file-status waiting';
            statusElement.innerHTML = '<i class="fas fa-clock"></i> Waiting...';
        }
        
        checkAllFilesSelected();
    });
});

// ===== Check if all files are selected =====
function checkAllFilesSelected() {
    const allSelected = Object.values(uploadedFiles).every(selected => selected === true);
    // Enable upload button if all files are selected
    uploadBtn.disabled = !allSelected;
}

// ===== Upload Form Handler =====
uploadForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    showLoading();
    hideAlert(uploadAlert);
    
    const formData = new FormData();
    
    // Add all files to FormData
    Object.keys(fileInputs).forEach(key => {
        const file = fileInputs[key].files[0];
        if (file) {
            formData.append(key, file);
        }
    });
    
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        hideLoading();
        
        if (data.success) {
            showAlert(uploadAlert, 'success', '<i class="fas fa-check-circle"></i> ' + data.message);
            
            // Update file status to success
            Object.keys(uploadedFiles).forEach(key => {
                const statusElement = document.getElementById(`${key}-status`);
                statusElement.className = 'file-status success';
                const validation = data.validation[key];
                statusElement.innerHTML = `<i class="fas fa-check-circle"></i> ${validation.rows} rows validated`;
            });
            
            // Enable workflow button
            runWorkflowBtn.disabled = false;

            // Mark current-session as validated and notify others
            uploadValidated = true;
            sessionStorage.setItem('uploadValidated', 'true');
            window.dispatchEvent(new Event('ims:uploadValidated'));
            
            // Scroll to workflow section
            document.getElementById('workflow').scrollIntoView({ behavior: 'smooth' });
        } else {
            showAlert(uploadAlert, 'error', '<i class="fas fa-exclamation-circle"></i> ' + data.error);
            
            // Update file status to error if validation failed
            if (data.validation) {
                Object.keys(data.validation).forEach(key => {
                    const validation = data.validation[key];
                    if (!validation.valid) {
                        const statusElement = document.getElementById(`${key}-status`);
                        statusElement.className = 'file-status error';
                        statusElement.innerHTML = '<i class="fas fa-times-circle"></i> ' + validation.error;
                    }
                });
            }
        }
    } catch (error) {
        hideLoading();
        showAlert(uploadAlert, 'error', '<i class="fas fa-exclamation-circle"></i> Upload failed: ' + error.message);
    }
});

// ===== Run Workflow Handler =====
runWorkflowBtn.addEventListener('click', async function() {
    if (workflowRunning) {
        showAlert(workflowAlert, 'warning', '<i class="fas fa-exclamation-triangle"></i> Workflow is already running');
        return;
    }
    
    hideAlert(workflowAlert);
    
    // Get threshold values
    const underperfThreshold = document.getElementById('underperf-threshold').value;
    const maxPriceChange = document.getElementById('max-price-change').value;
    
    const payload = {};
    if (underperfThreshold) payload.underperf_threshold = parseFloat(underperfThreshold);
    if (maxPriceChange) payload.max_price_change = parseFloat(maxPriceChange);
    
    try {
        const response = await fetch('/run-workflow', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert(workflowAlert, 'success', '<i class="fas fa-check-circle"></i> ' + data.message);
            workflowRunning = true;
            runWorkflowBtn.disabled = true;
            runWorkflowBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Running...';
            
            // Clear logs and start streaming
            clearLogs();
            startLogStreaming();
            
            // Scroll to logs section
            document.getElementById('logs').scrollIntoView({ behavior: 'smooth' });
        } else {
            showAlert(workflowAlert, 'error', '<i class="fas fa-exclamation-circle"></i> ' + data.error);
        }
    } catch (error) {
        showAlert(workflowAlert, 'error', '<i class="fas fa-exclamation-circle"></i> Failed to start workflow: ' + error.message);
    }
});

// ===== Log Streaming =====
function startLogStreaming() {
    if (eventSource) {
        eventSource.close();
    }
    
    eventSource = new EventSource('/stream-logs');
    
    eventSource.onmessage = function(event) {
        const data = JSON.parse(event.data);
        const logLine = data.log;
        
        // Check if workflow is complete
        if (logLine === '__WORKFLOW_COMPLETE__') {
            workflowRunning = false;
            runWorkflowBtn.disabled = false;
            runWorkflowBtn.innerHTML = '<i class="fas fa-play"></i> Run Workflow';
            eventSource.close();
            
            // Load output files
            loadOutputFiles();
            
            // Check for governance decisions that need human review
            checkGovernanceDecisions();
            
            // Scroll to results
            setTimeout(() => {
                document.getElementById('results').scrollIntoView({ behavior: 'smooth' });
            }, 1000);
            
            return;
        }
        
        addLogLine(logLine);
    };
    
    eventSource.onerror = function(error) {
        console.error('EventSource error:', error);
        eventSource.close();
    };
}

function addLogLine(logText) {
    // Remove empty state if present
    const emptyState = logsContent.querySelector('.logs-empty');
    if (emptyState) {
        emptyState.remove();
    }
    
    const logLine = document.createElement('div');
    logLine.className = 'log-line';
    
    // Add color coding based on content
    if (logText.includes('✅') || logText.includes('success')) {
        logLine.classList.add('log-success');
    } else if (logText.includes('❌') || logText.includes('error') || logText.includes('failed')) {
        logLine.classList.add('log-error');
    } else if (logText.includes('⚠️') || logText.includes('warning')) {
        logLine.classList.add('log-warning');
    } else if (logText.includes('INFO')) {
        logLine.classList.add('log-info');
    }
    
    logLine.textContent = logText;
    logsContent.appendChild(logLine);
    
    // Auto-scroll to bottom
    logsContent.parentElement.scrollTop = logsContent.parentElement.scrollHeight;
}

function clearLogs() {
    logsContent.innerHTML = '<div class="logs-empty"><i class="fas fa-info-circle"></i><p>Waiting for logs...</p></div>';
}

clearLogsBtn.addEventListener('click', clearLogs);

// ===== Load Output Files =====
async function loadOutputFiles() {
    try {
        const response = await fetch('/output-files');
        const data = await response.json();
        
        if (data.success && data.files.length > 0) {
            filesContent.innerHTML = '';
            
            data.files.forEach(file => {
                const fileCard = createFileCard(file);
                filesContent.appendChild(fileCard);
            });
        } else {
            filesContent.innerHTML = `
                <div class="files-empty">
                    <i class="fas fa-folder-open"></i>
                    <p>No output files available yet.</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Failed to load output files:', error);
        filesContent.innerHTML = `
            <div class="files-empty">
                <i class="fas fa-exclamation-circle"></i>
                <p>Failed to load output files: ${error.message}</p>
            </div>
        `;
    }
}

function createFileCard(file) {
    const card = document.createElement('div');
    card.className = 'file-card';
    
    const icon = file.name.endsWith('.csv') ? 'fa-file-csv' : 'fa-file-code';
    const sizeKB = (file.size / 1024).toFixed(2);
    
    card.innerHTML = `
        <div class="file-card-header">
            <i class="fas ${icon}"></i>
            <div class="file-card-title">${file.name}</div>
        </div>
        <div class="file-card-meta">
            <div><i class="fas fa-weight"></i> ${sizeKB} KB</div>
            <div><i class="fas fa-clock"></i> ${file.modified}</div>
        </div>
        <div class="file-card-actions">
            <button class="btn btn-primary btn-small" onclick="previewFile('${file.name}')">
                <i class="fas fa-eye"></i> Preview
            </button>
            <button class="btn btn-success btn-small" onclick="downloadFile('${file.name}')">
                <i class="fas fa-download"></i> Download
            </button>
        </div>
    `;
    
    return card;
}

refreshFilesBtn.addEventListener('click', loadOutputFiles);

// ===== File Preview =====
async function previewFile(filename) {
    showLoading();
    
    try {
        const response = await fetch(`/preview/${filename}`);
        const data = await response.json();
        
        hideLoading();
        
        if (data.success) {
            previewTitle.textContent = filename;
            
            if (filename.endsWith('.csv')) {
                // Display CSV as table
                const table = createPreviewTable(data.data);
                previewContent.innerHTML = table;
            } else if (filename.endsWith('.json')) {
                // Display JSON
                previewContent.innerHTML = `<pre>${JSON.stringify(data.data, null, 2)}</pre>`;
            }
            
            previewModal.style.display = 'flex';
        } else {
            alert('Failed to preview file: ' + data.error);
        }
    } catch (error) {
        hideLoading();
        alert('Failed to preview file: ' + error.message);
    }
}

function createPreviewTable(data) {
    const columns = data.columns;
    const rows = data.rows;
    const totalRows = data.total_rows;
    
    let html = '<table class="preview-table">';
    
    // Header
    html += '<thead><tr>';
    columns.forEach(col => {
        html += `<th>${col}</th>`;
    });
    html += '</tr></thead>';
    
    // Body
    html += '<tbody>';
    rows.forEach(row => {
        html += '<tr>';
        columns.forEach(col => {
            html += `<td>${row[col] !== null && row[col] !== undefined ? row[col] : ''}</td>`;
        });
        html += '</tr>';
    });
    html += '</tbody>';
    
    html += '</table>';
    
    if (totalRows > rows.length) {
        html += `<p class="text-center mt-2" style="color: var(--text-secondary);">Showing ${rows.length} of ${totalRows} rows</p>`;
    }
    
    return html;
}

// ===== File Download =====
function downloadFile(filename) {
    window.location.href = `/download/${filename}`;
}

// ===== Modal Close =====
closePreviewBtn.addEventListener('click', function() {
    previewModal.style.display = 'none';
});

previewModal.addEventListener('click', function(e) {
    if (e.target === previewModal) {
        previewModal.style.display = 'none';
    }
});

// ===== Utility Functions =====
function showLoading() {
    loadingOverlay.style.display = 'flex';
}

function hideLoading() {
    loadingOverlay.style.display = 'none';
}

function showAlert(element, type, message) {
    element.className = `alert alert-${type}`;
    element.innerHTML = message;
    element.style.display = 'flex';
}

function hideAlert(element) {
    element.style.display = 'none';
}

// ===== Smooth Scroll for Navigation =====
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        
        // Remove active class from all links
        document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
        
        // Add active class to clicked link
        this.classList.add('active');
        
        // Scroll to section
        const target = this.getAttribute('href');
        document.querySelector(target).scrollIntoView({ behavior: 'smooth' });
    });
});

// ===== Initialize =====
document.addEventListener('DOMContentLoaded', function() {
    console.log('Intelligent Management System initialized');
    
    // On every reload, clear validation so UI starts in a clean state
    sessionStorage.removeItem('uploadValidated');
    uploadValidated = false;

    // If not validated this session, keep workflow button disabled and ensure sections are in empty state
    if (!uploadValidated) {
        runWorkflowBtn.disabled = true;
        // Clear any logs/files UI on fresh load without validation
        clearLogs();
        filesContent.innerHTML = `
            <div class="files-empty">
                <i class="fas fa-folder-open"></i>
                <p>No output files available yet.</p>
            </div>
        `;
    }

    // Check if workflow is running on page load (only start streaming if validated in this session)
    checkWorkflowStatus();
});

async function checkWorkflowStatus() {
    try {
        const response = await fetch('/workflow-status');
        const data = await response.json();
        
        if (data.running && uploadValidated) {
            workflowRunning = true;
            runWorkflowBtn.disabled = true;
            runWorkflowBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Running...';
            startLogStreaming();
        }
        
        if (data.output_dir && uploadValidated) {
            loadOutputFiles();
        }
    } catch (error) {
        console.error('Failed to check workflow status:', error);
    }
}

// ===== Governance Approval Functions =====
async function checkGovernanceDecisions() {
    try {
        const response = await fetch('/governance-decisions');
        const data = await response.json();
        
        if (data.success && data.decisions) {
            const decisions = data.decisions;
            
            // If there are items needing manual review, show popup
            if (decisions.manual_review && decisions.manual_review.length > 0) {
                showGovernanceApprovalModal(decisions);
            } else {
                // No manual review needed, show transparency report directly
                showTransparencyReport();
            }
        }
    } catch (error) {
        console.error('Failed to check governance decisions:', error);
    }
}

function showGovernanceApprovalModal(decisions) {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.id = 'governanceModal';
    modal.style.display = 'flex';
    
    const autoApproved = decisions.auto_approved || [];
    const manualReview = decisions.manual_review || [];
    const rejected = decisions.rejected || [];
    
    modal.innerHTML = `
        <div class="modal-content" style="max-width: 900px; max-height: 90vh; overflow-y: auto;">
            <div class="modal-header">
                <h3><i class="fas fa-gavel"></i> Governance Review Required</h3>
                <button class="modal-close" onclick="closeGovernanceModal()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="modal-body">
                <div class="governance-summary">
                    <div class="summary-card success">
                        <i class="fas fa-check-circle"></i>
                        <div>
                            <h4>${autoApproved.length}</h4>
                            <p>Auto-Approved</p>
                        </div>
                    </div>
                    <div class="summary-card warning">
                        <i class="fas fa-exclamation-triangle"></i>
                        <div>
                            <h4>${manualReview.length}</h4>
                            <p>Need Review</p>
                        </div>
                    </div>
                    <div class="summary-card error">
                        <i class="fas fa-times-circle"></i>
                        <div>
                            <h4>${rejected.length}</h4>
                            <p>Rejected</p>
                        </div>
                    </div>
                </div>
                
                ${autoApproved.length > 0 ? `
                <div class="governance-section">
                    <h4 class="section-title success"><i class="fas fa-check-circle"></i> Auto-Approved SKUs</h4>
                    <div class="governance-table-container">
                        ${createGovernanceTable(autoApproved, 'approved', false)}
                    </div>
                </div>
                ` : ''}
                
                ${manualReview.length > 0 ? `
                <div class="governance-section">
                    <h4 class="section-title warning"><i class="fas fa-exclamation-triangle"></i> SKUs Requiring Your Review</h4>
                    <p class="section-description">Please review and approve or reject each SKU below:</p>
                    <div class="governance-table-container">
                        ${createGovernanceTable(manualReview, 'review', true)}
                    </div>
                </div>
                ` : ''}
                
                ${rejected.length > 0 ? `
                <div class="governance-section">
                    <h4 class="section-title error"><i class="fas fa-times-circle"></i> Rejected SKUs</h4>
                    <div class="governance-table-container">
                        ${createGovernanceTable(rejected, 'rejected', false)}
                    </div>
                </div>
                ` : ''}
                
                ${manualReview.length > 0 ? `
                <div class="modal-actions">
                    <button class="btn btn-secondary" onclick="closeGovernanceModal()">
                        <i class="fas fa-times"></i> Cancel
                    </button>
                    <button class="btn btn-success" onclick="submitGovernanceApprovals()">
                        <i class="fas fa-check"></i> Submit Approvals
                    </button>
                </div>
                ` : `
                <div class="modal-actions">
                    <button class="btn btn-primary" onclick="closeGovernanceModalAndShowReport()">
                        <i class="fas fa-file-alt"></i> View Transparency Report
                    </button>
                </div>
                `}
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}

function createGovernanceTable(items, type, editable) {
    let html = '<table class="governance-table">';
    html += '<thead><tr>';
    html += '<th>SKU ID</th>';
    html += '<th>Rank</th>';
    html += '<th>ROI</th>';
    html += '<th>Reason</th>';
    if (editable) {
        html += '<th>Decision</th>';
        html += '<th>Notes</th>';
    }
    html += '</tr></thead><tbody>';
    
    items.forEach(item => {
        html += '<tr>';
        html += `<td><strong>${item.sku_id}</strong></td>`;
        html += `<td>${item.rank}</td>`;
        html += `<td class="${item.roi >= 0 ? 'text-success' : 'text-error'}">$${item.roi.toFixed(2)}</td>`;
        html += `<td class="reason-cell">${item.reason}</td>`;
        
        if (editable) {
            html += `<td>
                <select class="governance-decision" data-sku="${item.sku_id}">
                    <option value="approved">✓ Approve</option>
                    <option value="rejected">✗ Reject</option>
                </select>
            </td>`;
            html += `<td>
                <input type="text" class="governance-notes" data-sku="${item.sku_id}" placeholder="Optional notes...">
            </td>`;
        }
        
        html += '</tr>';
    });
    
    html += '</tbody></table>';
    return html;
}

function closeGovernanceModal() {
    const modal = document.getElementById('governanceModal');
    if (modal) {
        modal.remove();
    }
}

function closeGovernanceModalAndShowReport() {
    closeGovernanceModal();
    showTransparencyReport();
}

async function submitGovernanceApprovals() {
    console.log('Submit Approvals button clicked!');
    
    // Disable the submit button to prevent multiple clicks
    const submitBtn = document.querySelector('button[onclick="submitGovernanceApprovals()"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    }
    
    const decisions = document.querySelectorAll('.governance-decision');
    const approvals = [];
    
    decisions.forEach(select => {
        const sku_id = select.getAttribute('data-sku');
        const decision = select.value;
        const notesInput = document.querySelector(`.governance-notes[data-sku="${sku_id}"]`);
        const notes = notesInput ? notesInput.value : '';
        
        approvals.push({ sku_id, decision, notes });
    });
    
    console.log('Approvals collected:', approvals);
    
    // Function to re-enable button
    const enableSubmitButton = () => {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-check"></i> Submit Approvals';
        }
    };
    
    if (approvals.length === 0) {
        alert('No approvals to submit');
        enableSubmitButton();
        return;
    }
    
    // Show loading with custom message
    try {
        const loadingDiv = document.getElementById('loading');
        const loadingText = loadingDiv ? loadingDiv.querySelector('p') : null;
        if (loadingText) {
            loadingText.textContent = 'Generating transparency report with your decisions...';
        }
    } catch (e) {
        console.log('Could not update loading text:', e);
    }
    showLoading();
    
    try {
        const response = await fetch('/approve-governance', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ approvals })
        });
        
        const data = await response.json();
        
        // Reset loading text
        try {
            const loadingDiv = document.getElementById('loading');
            const loadingText = loadingDiv ? loadingDiv.querySelector('p') : null;
            if (loadingText) {
                loadingText.textContent = 'Processing...';
            }
        } catch (e) {
            console.log('Could not reset loading text:', e);
        }
        hideLoading();
        
        if (data.success) {
            closeGovernanceModal();
            alert(`✓ Successfully processed ${approvals.length} approvals. ${data.total_approved} SKUs approved in total.`);
            
            // Navigate to results section and refresh files
            document.getElementById('results').scrollIntoView({ behavior: 'smooth' });
            
            // Update nav active state
            document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));
            document.querySelector('a[href="#results"]').classList.add('active');
            
            // Refresh files with a slight delay to ensure report is fully written
            setTimeout(() => {
                loadOutputFiles();
                // Also trigger the refresh button to ensure files are loaded
                const refreshBtn = document.querySelector('#results .btn-secondary');
                if (refreshBtn) {
                    refreshBtn.click();
                }
            }, 1000);
            
            // Also show transparency report
            setTimeout(() => {
                showTransparencyReport();
            }, 1500);
        } else {
            enableSubmitButton();
            alert('Failed to submit approvals: ' + data.error);
        }
    } catch (error) {
        // Reset loading text
        try {
            const loadingDiv = document.getElementById('loading');
            const loadingText = loadingDiv ? loadingDiv.querySelector('p') : null;
            if (loadingText) {
                loadingText.textContent = 'Processing...';
            }
        } catch (e) {
            console.log('Could not reset loading text:', e);
        }
        hideLoading();
        enableSubmitButton();
        alert('Failed to submit approvals: ' + error.message);
    }
}

// ===== Transparency Report Functions =====
async function showTransparencyReport() {
    showLoading();
    
    try {
        const response = await fetch('/transparency-report');
        const data = await response.json();
        
        hideLoading();
        
        if (data.success) {
            displayTransparencyReport(data.report, data.summary, data.markdown);
        } else {
            alert('Failed to load transparency report: ' + data.error);
        }
    } catch (error) {
        hideLoading();
        alert('Failed to load transparency report: ' + error.message);
    }
}

function displayTransparencyReport(report, summary, markdown) {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.id = 'transparencyModal';
    modal.style.display = 'flex';
    
    // Convert markdown to HTML if available
    let reportContent = '';
    if (markdown) {
        // Use marked.js to convert markdown to HTML (we'll need to include this library)
        reportContent = `<div class="markdown-content">${convertMarkdownToHTML(markdown)}</div>`;
    } else {
        // Fallback to table view
        reportContent = `
            <div class="report-summary">
                <h4>Summary</h4>
                <div class="summary-grid">
                    <div class="summary-item">
                        <strong>Total SKUs Flagged:</strong> ${summary.total_skus_flagged || 0}
                    </div>
                    <div class="summary-item">
                        <strong>Total ROI:</strong> <span class="${(summary.total_roi || 0) >= 0 ? 'text-success' : 'text-error'}">$${(summary.total_roi || 0).toFixed(2)}</span>
                    </div>
                    <div class="summary-item">
                        <strong>Marketing Spend:</strong> $${(summary.total_marketing_spend || 0).toFixed(2)}
                    </div>
                    <div class="summary-item">
                        <strong>Labor Cost:</strong> $${(summary.total_labor_cost || 0).toFixed(2)}
                    </div>
                </div>
            </div>
            
            <div class="report-table-container">
                <h4>Complete SKU Journey</h4>
                <p class="section-description">This report shows what happened to each SKU from trigger to final decision:</p>
                ${createTransparencyTable(report)}
            </div>
        `;
    }
    
    modal.innerHTML = `
        <div class="modal-content" style="max-width: 95%; max-height: 95vh; overflow-y: auto;">
            <div class="modal-header">
                <h3><i class="fas fa-file-alt"></i> SKU Journey Transparency Report</h3>
                <button class="modal-close" onclick="closeTransparencyModal()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="modal-body">
                ${reportContent}
                
                <div class="modal-actions">
                    <button class="btn btn-success" onclick="downloadTransparencyReport()">
                        <i class="fas fa-download"></i> Download CSV
                    </button>
                    ${markdown ? `<button class="btn btn-primary" onclick="downloadMarkdownReport()">
                        <i class="fas fa-download"></i> Download Markdown
                    </button>` : ''}
                    <button class="btn btn-secondary" onclick="closeTransparencyModal()">
                        <i class="fas fa-times"></i> Close
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}

function convertMarkdownToHTML(markdown) {
    // Simple markdown to HTML converter
    // For production, use a library like marked.js
    let html = markdown;
    
    // Headers
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');
    
    // Bold
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Italic
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Lists
    html = html.replace(/^\- (.*$)/gim, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    
    // Line breaks
    html = html.replace(/\n\n/g, '</p><p>');
    html = '<p>' + html + '</p>';
    
    // Horizontal rules
    html = html.replace(/^---$/gim, '<hr>');
    
    return html;
}

function createTransparencyTable(report) {
    const columns = report.columns;
    const rows = report.rows;
    
    let html = '<div style="overflow-x: auto;"><table class="transparency-table">';
    html += '<thead><tr>';
    
    // Create headers
    columns.forEach(col => {
        html += `<th>${formatColumnName(col)}</th>`;
    });
    html += '</tr></thead><tbody>';
    
    // Create rows
    rows.forEach(row => {
        html += '<tr>';
        columns.forEach(col => {
            let value = row[col];
            let cellClass = '';
            
            // Format specific columns
            if (col === 'final_decision') {
                if (value === 'auto-approved') cellClass = 'text-success';
                else if (value === 'rejected') cellClass = 'text-error';
                else if (value === 'manual-review') cellClass = 'text-warning';
            } else if (col === 'human_decision') {
                if (value === 'approved') cellClass = 'text-success';
                else if (value === 'rejected') cellClass = 'text-error';
            } else if (col === 'roi' || col === 'incremental_revenue') {
                if (value !== null && value !== undefined && value !== '') {
                    cellClass = parseFloat(value) >= 0 ? 'text-success' : 'text-error';
                    value = '$' + parseFloat(value).toFixed(2);
                }
            } else if (col.includes('_pct') || col === 'gap_pct' || col === 'price_change_pct') {
                if (value !== null && value !== undefined && value !== '') {
                    value = (parseFloat(value) * 100).toFixed(1) + '%';
                }
            }
            
            html += `<td class="${cellClass}">${value !== null && value !== undefined && value !== '' ? value : '-'}</td>`;
        });
        html += '</tr>';
    });
    
    html += '</tbody></table></div>';
    return html;
}

function formatColumnName(col) {
    return col.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function closeTransparencyModal() {
    const modal = document.getElementById('transparencyModal');
    if (modal) {
        modal.remove();
    }
}

function downloadTransparencyReport() {
    window.location.href = '/download/transparency_report.csv';
}

function downloadMarkdownReport() {
    window.location.href = '/download/transparency_report.md';
}
