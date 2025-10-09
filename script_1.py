# Copy the original frontend files to the frontend directory

import shutil

# Read the original frontend files from file search results
frontend_files = {
    "index.html": file_39.snippet,
    "style.css": file_39.snippet,
    "app.js": file_2.snippet
}

# I need to properly read the files
with open("tax-filing-system/frontend/index.html", "w", encoding="utf-8") as f:
    # Let me create the complete HTML file based on the structure from the search
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interactive Tax Filing System</title>
    <link rel="stylesheet" href="style.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://unpkg.com/lucide@latest/dist/umd/lucide.js"></script>
</head>
<body>
    <!-- Theme Toggle -->
    <button id="themeToggle" class="theme-toggle" aria-label="Toggle theme">
        <span class="theme-icon">🌙</span>
    </button>

    <!-- Loading Overlay -->
    <div id="loadingOverlay" class="loading-overlay hidden">
        <div class="loading-spinner">
            <div class="spinner"></div>
            <p>Processing your tax data...</p>
        </div>
    </div>

    <!-- Toast Notifications -->
    <div id="toastContainer" class="toast-container"></div>

    <!-- Main Layout -->
    <div class="app-layout">
        <!-- Sidebar -->
        <aside id="sidebar" class="sidebar">
            <div class="sidebar-header">
                <div class="logo">
                    <span class="icon" data-lucide="calculator"></span>
                    <h3>TaxPro</h3>
                </div>
                <button id="sidebarToggle" class="sidebar-toggle">
                    <span class="icon" data-lucide="menu"></span>
                </button>
            </div>
            
            <nav class="sidebar-nav">
                <a href="#" class="nav-item active" data-tab="dashboard">
                    <span class="icon" data-lucide="layout-dashboard"></span>
                    <span class="text">Dashboard</span>
                </a>
                <a href="#" class="nav-item" data-tab="upload">
                    <span class="icon" data-lucide="upload"></span>
                    <span class="text">Upload Documents</span>
                </a>
                <a href="#" class="nav-item" data-tab="financial">
                    <span class="icon" data-lucide="calculator"></span>
                    <span class="text">Financial Summary</span>
                </a>
                <a href="#" class="nav-item" data-tab="results">
                    <span class="icon" data-lucide="bar-chart-3"></span>
                    <span class="text">Tax Results</span>
                </a>
                <a href="#" class="nav-item" data-tab="help">
                    <span class="icon" data-lucide="help-circle"></span>
                    <span class="text">Help & Chat</span>
                </a>
            </nav>
        </aside>

        <!-- Main Content -->
        <main class="main-content">
            <!-- Navbar -->
            <nav class="navbar">
                <div class="navbar-content">
                    <div class="navbar-brand">
                        <h2>TaxPro Interactive</h2>
                    </div>
                    <div class="navbar-actions">
                        <button class="btn btn--outline btn--sm" id="exportBtn">
                            <span class="icon" data-lucide="download"></span>
                            Export
                        </button>
                        <div class="profile-dropdown">
                            <button class="btn btn--secondary btn--sm" id="profileBtn">
                                <span class="icon" data-lucide="user"></span>
                            </button>
                            <div class="dropdown-menu" id="profileDropdown">
                                <a href="#" class="dropdown-item">Profile Settings</a>
                                <a href="#" class="dropdown-item">Tax History</a>
                                <hr class="dropdown-divider">
                                <a href="#" class="dropdown-item">Logout</a>
                            </div>
                        </div>
                    </div>
                </div>
            </nav>

            <!-- Dashboard Tab -->
            <div id="dashboard" class="tab-content active">
                <div class="dashboard-header">
                    <h1>Tax Filing Dashboard</h1>
                    <p>Complete your tax filing with our interactive system</p>
                </div>

                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-icon" data-lucide="file-text"></div>
                        <div class="stat-content">
                            <h3 id="documentsCount">0</h3>
                            <p>Documents Uploaded</p>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon" data-lucide="calculator"></div>
                        <div class="stat-content">
                            <h3 id="taxLiability">₹0</h3>
                            <p>Tax Liability</p>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon" data-lucide="trending-down"></div>
                        <div class="stat-content">
                            <h3 id="taxSavings">₹0</h3>
                            <p>Potential Savings</p>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon" data-lucide="percent"></div>
                        <div class="stat-content">
                            <h3 id="completionRate">0%</h3>
                            <p>Completion Rate</p>
                        </div>
                    </div>
                </div>

                <div class="dashboard-cards">
                    <div class="card">
                        <div class="card__header">
                            <h3>Recent Activity</h3>
                        </div>
                        <div class="card__body">
                            <div class="activity-list" id="activityList">
                                <div class="activity-item">
                                    <span class="activity-icon" data-lucide="upload"></span>
                                    <div class="activity-content">
                                        <p>Welcome to TaxPro Interactive</p>
                                        <small>Start by uploading your documents</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="card">
                        <div class="card__header">
                            <h3>Tax Comparison</h3>
                        </div>
                        <div class="card__body">
                            <canvas id="comparisonChart" width="400" height="300"></canvas>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Upload Tab -->
            <div id="upload" class="tab-content">
                <div class="upload-header">
                    <h1>Upload Tax Documents</h1>
                    <p>Drag and drop your tax documents or click to browse</p>
                </div>

                <div class="upload-container">
                    <div id="uploadZone" class="upload-zone">
                        <div class="upload-content">
                            <span class="upload-icon" data-lucide="upload-cloud"></span>
                            <h3>Drop your files here</h3>
                            <p>or click to browse files</p>
                            <button id="browseBtn" class="btn btn--primary">Browse Files</button>
                        </div>
                        <div id="uploadOverlay" class="upload-overlay hidden">
                            <span class="overlay-icon" data-lucide="upload"></span>
                            <p>Release to upload</p>
                        </div>
                    </div>
                    <input type="file" id="fileInput" multiple accept=".pdf,.jpg,.jpeg,.png,.doc,.docx" hidden>
                </div>

                <div class="uploaded-files">
                    <h3>Uploaded Documents</h3>
                    <div id="fileList" class="file-list">
                        <!-- Uploaded files will appear here -->
                    </div>
                </div>

                <div class="document-checklist">
                    <h3>Required Documents</h3>
                    <div class="checklist" id="documentChecklist">
                        <div class="checklist-item" data-document="form16">
                            <span class="checklist-icon" data-lucide="square"></span>
                            <span>Form 16 (Salary Certificate)</span>
                        </div>
                        <div class="checklist-item" data-document="bank-statements">
                            <span class="checklist-icon" data-lucide="square"></span>
                            <span>Bank Statements</span>
                        </div>
                        <div class="checklist-item" data-document="investment-proofs">
                            <span class="checklist-icon" data-lucide="square"></span>
                            <span>Investment Proofs (80C, 80D)</span>
                        </div>
                        <div class="checklist-item" data-document="rent-receipts">
                            <span class="checklist-icon" data-lucide="square"></span>
                            <span>Rent Receipts (HRA)</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Financial Tab -->
            <div id="financial" class="tab-content">
                <div class="financial-header">
                    <h1>Financial Summary</h1>
                    <p>Review and edit your financial information</p>
                </div>

                <div class="financial-form">
                    <div class="expandable-card expanded">
                        <div class="expandable-header">
                            <h3>Income Details</h3>
                            <span class="expand-icon" data-lucide="chevron-down"></span>
                        </div>
                        <div class="expandable-content">
                            <div class="form-grid">
                                <div class="form-group">
                                    <label class="form-label">Basic Salary</label>
                                    <input type="number" class="form-control" id="basicSalary" placeholder="600000">
                                </div>
                                <div class="form-group">
                                    <label class="form-label">HRA</label>
                                    <input type="number" class="form-control" id="hra" placeholder="240000">
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Special Allowance</label>
                                    <input type="number" class="form-control" id="specialAllowance" placeholder="80000">
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Other Allowances</label>
                                    <input type="number" class="form-control" id="otherAllowances" placeholder="120000">
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="expandable-card expanded">
                        <div class="expandable-header">
                            <h3>Deductions</h3>
                            <span class="expand-icon" data-lucide="chevron-down"></span>
                        </div>
                        <div class="expandable-content">
                            <div class="form-grid">
                                <div class="form-group">
                                    <label class="form-label">Section 80C</label>
                                    <input type="number" class="form-control" id="section80c" placeholder="150000">
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Section 80D</label>
                                    <input type="number" class="form-control" id="section80d" placeholder="25000">
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Section 24 (Home Loan)</label>
                                    <input type="number" class="form-control" id="section24" placeholder="200000">
                                </div>
                                <div class="form-group">
                                    <label class="form-label">TDS Deducted</label>
                                    <input type="number" class="form-control" id="tdsDeducted" placeholder="45000">
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="tax-preview">
                        <h3>Tax Preview <span class="live-indicator">LIVE</span></h3>
                        <div class="preview-grid">
                            <div class="preview-card">
                                <h4>Old Regime</h4>
                                <div class="tax-amount" id="oldRegimeTax">₹0</div>
                            </div>
                            <div class="preview-card">
                                <h4>New Regime</h4>
                                <div class="tax-amount" id="newRegimeTax">₹0</div>
                            </div>
                        </div>
                    </div>

                    <div class="form-actions">
                        <button class="btn btn--primary btn--lg" id="calculateTax">Calculate Tax</button>
                    </div>
                </div>
            </div>

            <!-- Results Tab -->
            <div id="results" class="tab-content">
                <div class="results-header">
                    <h1>Tax Calculation Results</h1>
                    <p>Detailed breakdown of your tax calculations</p>
                </div>

                <div class="results-summary">
                    <div class="summary-card primary">
                        <h3>Total Tax Liability</h3>
                        <div class="amount" id="totalTaxLiability">₹0</div>
                        <div class="regime-badge" id="recommendedRegime">Old Regime</div>
                    </div>
                    <div class="summary-card">
                        <h3>Tax Paid (TDS)</h3>
                        <div class="amount" id="taxPaid">₹0</div>
                    </div>
                    <div class="summary-card">
                        <h3>Additional Payment</h3>
                        <div class="amount" id="additionalPayment">₹0</div>
                    </div>
                </div>

                <div class="results-content">
                    <div class="card">
                        <div class="card__header">
                            <h3>Tax Breakdown</h3>
                            <div class="chart-controls">
                                <button class="toggle-btn active" data-chart="breakdown">Breakdown</button>
                                <button class="toggle-btn" data-chart="comparison">Comparison</button>
                            </div>
                        </div>
                        <div class="card__body">
                            <canvas id="taxBreakdownChart" width="400" height="300"></canvas>
                        </div>
                    </div>

                    <div class="card">
                        <div class="card__header">
                            <h3>Year-over-Year Comparison</h3>
                        </div>
                        <div class="card__body">
                            <canvas id="yearComparisonChart" width="400" height="300"></canvas>
                        </div>
                    </div>
                </div>

                <div class="tax-savings">
                    <h3>Tax Saving Suggestions <span class="count">3 opportunities</span></h3>
                    <div class="savings-list">
                        <div class="saving-item">
                            <div class="saving-icon" data-lucide="trending-up"></div>
                            <div class="saving-content">
                                <h4>Increase 80C Investment</h4>
                                <p>You can save additional ₹0 by maximizing your 80C deductions</p>
                                <span class="saving-amount">Already maximized ✓</span>
                            </div>
                        </div>
                        <div class="saving-item">
                            <div class="saving-icon" data-lucide="shield"></div>
                            <div class="saving-content">
                                <h4>Health Insurance Premium</h4>
                                <p>Consider increasing health insurance coverage for higher 80D deductions</p>
                                <span class="saving-amount">Save up to ₹7,500</span>
                            </div>
                        </div>
                        <div class="saving-item">
                            <div class="saving-icon" data-lucide="home"></div>
                            <div class="saving-content">
                                <h4>Home Loan Planning</h4>
                                <p>Your home loan interest deduction is well optimized</p>
                                <span class="saving-amount">Optimized ✓</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Help Tab -->
            <div id="help" class="tab-content">
                <div class="help-header">
                    <h1>Help Center & Chat</h1>
                    <p>Get instant help with your tax filing questions</p>
                </div>

                <div class="help-content">
                    <div class="chatbot-container">
                        <div class="chat-messages" id="chatMessages">
                            <div class="chat-message bot">
                                <div class="message-avatar">🤖</div>
                                <div class="message-content">
                                    <p>Hi! I'm your tax assistant. I can help you with tax filing questions, deduction calculations, and regime comparisons. What would you like to know?</p>
                                </div>
                            </div>
                        </div>
                        <div class="chat-input">
                            <input type="text" id="chatInput" placeholder="Ask me anything about taxes..." class="form-control">
                            <button id="sendMessage" class="btn btn--primary">
                                <span class="icon" data-lucide="send"></span>
                            </button>
                        </div>
                    </div>

                    <div class="quick-questions">
                        <h3>Quick Questions</h3>
                        <div class="question-grid">
                            <button class="quick-question-btn" data-question="What documents do I need for tax filing?">
                                What documents do I need for tax filing?
                            </button>
                            <button class="quick-question-btn" data-question="How is HRA calculated?">
                                How is HRA calculated?
                            </button>
                            <button class="quick-question-btn" data-question="What are the differences between old and new tax regime?">
                                What are the differences between old and new tax regime?
                            </button>
                            <button class="quick-question-btn" data-question="What deductions can I claim?">
                                What deductions can I claim?
                            </button>
                            <button class="quick-question-btn" data-question="How to save more tax legally?">
                                How to save more tax legally?
                            </button>
                        </div>
                    </div>

                    <div class="faq-section">
                        <h3>Frequently Asked Questions</h3>
                        
                        <div class="faq-item">
                            <h4>What is the deadline for filing ITR?</h4>
                            <p>The deadline for filing Income Tax Return (ITR) for AY 2024-25 is July 31, 2024, for individuals and HUFs not required to get their accounts audited.</p>
                        </div>

                        <div class="faq-item">
                            <h4>Can I switch between old and new tax regime?</h4>
                            <p>Yes, salaried individuals can switch between old and new tax regime every year. However, business income earners need to stick to their choice for that year.</p>
                        </div>

                        <div class="faq-item">
                            <h4>What happens if I file ITR after the due date?</h4>
                            <p>Late filing attracts penalties and you cannot carry forward certain losses. It's always recommended to file within the due date.</p>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <!-- Modals -->
    <div id="exportModal" class="modal hidden">
        <div class="modal-content">
            <div class="modal-header">
                <h3>Export Tax Data</h3>
                <button class="modal-close">&times;</button>
            </div>
            <div class="modal-body">
                <p>Choose export format:</p>
                <div class="export-options">
                    <button class="btn btn--outline">PDF Report</button>
                    <button class="btn btn--outline">Excel Sheet</button>
                    <button class="btn btn--outline">JSON Data</button>
                </div>
            </div>
        </div>
    </div>

    <script src="app.js"></script>
</body>
</html>'''
    f.write(html_content)

print("Created tax-filing-system/frontend/index.html - Complete HTML file")