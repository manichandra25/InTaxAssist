// Enhanced Interactive Tax Filing System JavaScript - Backend Integrated
class TaxFilingApp {
    constructor() {
        this.data = {
            // Mock data for historical chart context
            mockTaxData: {
                previousYears: {
                    oldRegime: [175000, 185000],
                    newRegime: [148000, 156000]
                }
            }
        };

        // Backend configuration
        this.backendUrl = 'http://localhost:8000';

        this.charts = {};
        this.isDarkMode = false;
        this.activeTab = 'dashboard';
        this.uploadedFiles = [];
        this.autoSaveTimeout = null;
        this.currentTaxCalculation = null;
        this.init();
    }

    init() {
        // Run icon initialization first
        this.initializeIcons();
        
        // Setup all event listeners
        this.setupEventListeners();
        this.setupThemeToggle();
        this.setupTabs();
        this.setupAccordions(); // MODIFIED: Renamed from setupSidebar
        this.setupUpload();
        this.setupFinancialForm();
        this.setupCharts();
        this.setupChatbot();
        
        // NEW: Setup for dynamic content
        this.setupDynamicContent();

        // Update initial state
        this.updateDashboardStats();

        // Check backend connection
        this.checkBackendConnection();
    }

    async checkBackendConnection() {
        try {
            const response = await fetch(`${this.backendUrl}/`);
            if (response.ok) {
                 const data = await response.json();
                 console.log('Backend connected:', data.message);
                 this.showToast('Backend connected successfully', 'success');
            } else {
                 throw new Error('Backend not reachable');
            }
        } catch (error) {
            console.warn('Backend not available, using mock data');
            this.showToast('Using offline mode - backend not available', 'warning');
        }
    }

    initializeIcons() {
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }

    setupEventListeners() {
        document.querySelectorAll('[data-tab]').forEach(tab => {
            tab.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchTab(tab.dataset.tab);
            });
        });

        const calculateBtn = document.getElementById('calculateTax');
        if (calculateBtn) {
            calculateBtn.addEventListener('click', () => this.calculateTax());
        }

        // Setup export button
        const exportBtn = document.getElementById('exportBtn');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.showExportOptions());
        }
    }

    setupThemeToggle() {
        const themeToggle = document.getElementById('themeToggle');
        if (!themeToggle) return;
        const themeIcon = themeToggle.querySelector('.theme-icon');
        themeToggle.addEventListener('click', () => {
            this.isDarkMode = !this.isDarkMode;
            document.documentElement.setAttribute('data-color-scheme', this.isDarkMode ? 'dark' : 'light');
            if (themeIcon) themeIcon.textContent = this.isDarkMode ? '☀️' : '🌙';
        });
    }

    setupTabs() {
        const defaultTab = document.querySelector('[data-tab="dashboard"]');
        if (defaultTab) defaultTab.classList.add('active');
    }

    switchTab(tabId) {
        document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
        document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
        const selectedTab = document.getElementById(tabId);
        const selectedNav = document.querySelector(`[data-tab="${tabId}"]`);
        if (selectedTab) selectedTab.classList.add('active');
        if (selectedNav) selectedNav.classList.add('active');
        this.activeTab = tabId;
    }

    // MODIFIED: This now handles all accordion components
    setupAccordions() {
        document.querySelectorAll('.expandable-header').forEach(header => {
            // Make header keyboard-focusable for accessibility
            if (!header.hasAttribute('tabindex')) header.setAttribute('tabindex', '0');

            const toggle = (e) => {
                const card = header.closest('.expandable-card');
                if (!card) return; // guard against unexpected DOM structure
                card.classList.toggle('expanded');
            };

            header.addEventListener('click', toggle);
            // Support keyboard toggle via Enter or Space
            header.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    toggle(e);
                }
            });
        });
    }

    // NEW: Handles new dynamic elements
    setupDynamicContent() {
        this.startCountdownTimer();
        this.setupContinueButton();
        
        // Re-run lucide to render new icons added to accordions and buttons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }

    // NEW: Logic for the "Continue" button on the upload page
    setupContinueButton() {
        const continueBtn = document.getElementById('continueToFinancials');
        if (continueBtn) {
            continueBtn.addEventListener('click', () => {
                this.switchTab('financial');
            });
        }
    }

    // NEW: Logic for the countdown timer
    startCountdownTimer() {
        // Set your deadline here
        const deadline = new Date("July 31, 2026 23:59:59").getTime();
        const countdownTimerEl = document.getElementById('countdownTimer');
        
        if (!countdownTimerEl) return;

        const timerInterval = setInterval(() => {
            const now = new Date().getTime();
            const distance = deadline - now;

            const daysEl = document.getElementById('days');
            const hoursEl = document.getElementById('hours');
            const minutesEl = document.getElementById('minutes');
            const secondsEl = document.getElementById('seconds');

            if (distance < 0) {
                clearInterval(timerInterval);
                countdownTimerEl.innerHTML = "<h4 style='color: white;'>The deadline has passed!</h4>";
                return;
            }

            const days = Math.floor(distance / (1000 * 60 * 60 * 24));
            const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((distance % (1000 * 60)) / 1000);

            const format = (num) => num.toString().padStart(2, '0');

            if (daysEl) daysEl.textContent = format(days);
            if (hoursEl) hoursEl.textContent = format(hours);
            if (minutesEl) minutesEl.textContent = format(minutes);
            if (secondsEl) secondsEl.textContent = format(seconds);

        }, 1000);
    }

    setupUpload() {
        const uploadZone = document.getElementById('uploadZone');
        const fileInput = document.getElementById('fileInput');
        const browseBtn = document.getElementById('browseBtn');
        if (!uploadZone || !fileInput || !browseBtn) return;

        // Fix for the double-click event
        browseBtn.addEventListener('click', (event) => {
            event.stopPropagation(); // Stop click from bubbling to uploadZone
            fileInput.click();
        });
        
        uploadZone.addEventListener('click', () => {
            fileInput.click();
        });
        
        fileInput.addEventListener('change', (e) => {
            this.handleFileUpload(Array.from(e.target.files));
            e.target.value = null; // Clear input to allow re-uploading same file
        });
    }

    async handleFileUpload(files) {
        for (const file of files) {
            if (this.validateFile(file)) {
                this.uploadedFiles.push(file);
                this.addFileToPreview(file);
                await this.uploadAndParseDocument(file);
                this.showToast(`${file.name} uploaded successfully`, 'success');
            }
        }
        this.updateDashboardStats();
        // Do not auto-switch tab, wait for user to click "Continue"
        // this.switchTab('financial'); 
    }

    async uploadAndParseDocument(file) {
        try {
            this.showLoadingOverlay('Parsing document...');
            const formData = new FormData();
            formData.append('file', file);
            const response = await fetch(`${this.backendUrl}/api/upload`, {
                method: 'POST',
                body: formData
            });
            if (!response.ok) throw new Error(`Upload failed: ${response.statusText}`);
            const result = await response.json();
            if (result.success) {
                this.populateFormWithExtractedData(result.extracted_data);
                if (result.warnings && result.warnings.length > 0) {
                    result.warnings.forEach(warning => this.showToast(warning, 'warning'));
                }
            }
        } catch (error) {
            console.error('Document upload/parsing error:', error);
            this.showToast('Document parsing failed. Using manual entry.', 'error');
        } finally {
            this.hideLoadingOverlay();
        }
    }

    populateFormWithExtractedData(data) {
        // Validation: Check for unreasonably large values that might indicate extraction errors
        // These limits match the backend model validation
        const limits = {
            'basicSalary': { max: 50000000, label: 'Basic Salary', field: 'basic_salary' },
            'hra': { max: 10000000, label: 'HRA', field: 'hra' },
            'specialAllowance': { max: 10000000, label: 'Special Allowance', field: 'special_allowance' },
            'otherAllowances': { max: 10000000, label: 'Other Allowances', field: 'other_allowances' },
            'tdsDeducted': { max: 50000000, label: 'TDS', field: 'tds_deducted' },
            'section80c': { max: 150000, label: 'Section 80C', field: 'section_80c' },
            'section80d': { max: 100000, label: 'Section 80D', field: 'section_80d' },
            'section24': { max: 5000000, label: 'Section 24', field: 'section_24' }
        };
        
        const validationErrors = [];
        const fieldMap = {
            'basicSalary': 'basic_salary', 'hra': 'hra',
            'specialAllowance': 'special_allowance', 'otherAllowances': 'other_allowances',
            'section80c': 'section_80c', 'section80d': 'section_80d',
            'section24': 'section_24', 'tdsDeducted': 'tds_deducted'
        };
        // Helper: normalize numeric strings from backend/extraction (handles comma/dot separators)
        const normalizeNumericString = (v) => {
            if (v === null || v === undefined) return 0;
            let s = String(v).trim();
            // Remove any non-digit, non-dot, non-comma characters
            s = s.replace(/[^0-9.,]/g, '');
            if (!s) return 0;
            // If both comma and dot present, remove commas (assume comma thousands)
            if (s.indexOf(',') !== -1 && s.indexOf('.') !== -1) {
                s = s.replace(/,/g, '');
                return parseFloat(s) || 0;
            }
            // If only commas present, remove them
            if (s.indexOf(',') !== -1 && s.indexOf('.') === -1) {
                s = s.replace(/,/g, '');
                return parseFloat(s) || 0;
            }
            // If multiple dots, treat all but last as thousand separators
            const dotCount = (s.match(/\./g) || []).length;
            if (dotCount > 1) {
                const parts = s.split('.');
                const integerPart = parts.slice(0, -1).join('');
                const decimalPart = parts[parts.length - 1];
                s = integerPart + '.' + decimalPart;
            }
            return parseFloat(s) || 0;
        };
        
        Object.entries(fieldMap).forEach(([fieldId, dataKey]) => {
            const field = document.getElementById(fieldId);
            if (field && data[dataKey]) {
                const value = normalizeNumericString(data[dataKey]);
                const limit = limits[fieldId];
                
                // Validate extracted value
                if (isNaN(value)) {
                    console.warn(`Invalid extracted value for ${dataKey}: ${data[dataKey]}`);
                    validationErrors.push(`Invalid value for ${limit.label}`);
                    return;
                }
                
                if (value > limit.max) {
                    console.warn(`Extracted ${limit.label} (${value.toLocaleString()}) exceeds limit (${limit.max.toLocaleString()})`);
                    validationErrors.push(`${limit.label} (₹${value.toLocaleString()}) exceeds maximum of ₹${limit.max.toLocaleString()}, please verify`);
                    return; // Skip populating this field
                }
                
                if (value < 0) {
                    console.warn(`Negative value extracted for ${dataKey}: ${value}`);
                    validationErrors.push(`${limit.label} cannot be negative`);
                    return; // Skip populating this field
                }
                
                field.value = value || 0;
                field.dispatchEvent(new Event('input'));
            }
        });
        
        // Show validation errors if any
        if (validationErrors.length > 0) {
            validationErrors.forEach(error => {
                console.warn(`Validation: ${error}`);
                this.showToast(`⚠️ ${error}. Extracted value seems incorrect, please review manually.`, 'warning');
            });
        }
        
        this.updateTaxPreview();
    }

    validateFile(file) {
        const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
        const maxSize = 10 * 1024 * 1024; // 10MB
        if (!allowedTypes.includes(file.type)) {
            this.showToast(`Invalid file type: ${file.name}`, 'error');
            return false;
        }
        if (file.size > maxSize) {
            this.showToast(`File too large: ${file.name}`, 'error');
            return false;
        }
        return true;
    }

    addFileToPreview(file) {
        const fileList = document.getElementById('fileList');
        if (!fileList) return;
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        const fileIcon = this.getFileIcon(file.type);
        const fileSize = this.formatFileSize(file.size);
        fileItem.innerHTML = `<div class="file-info"><span class="file-icon">${fileIcon}</span><div class="file-details"><span class="file-name">${file.name}</span><span class="file-size">${fileSize}</span></div></div><button class="btn-remove" onclick="this.closest('.file-item').remove()">×</button>`;
        fileList.appendChild(fileItem);
    }

    getFileIcon(type) {
        if (type.includes('pdf')) return '📄';
        if (type.includes('image')) return '🖼️';
        if (type.includes('word')) return '📝';
        return '📋';
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    setupFinancialForm() {
        const inputs = ['basicSalary', 'hra', 'specialAllowance', 'otherAllowances', 'section80c', 'section80d', 'section24', 'tdsDeducted'];
        inputs.forEach(inputId => {
            const input = document.getElementById(inputId);
            if (input) {
                input.addEventListener('input', () => {
                    clearTimeout(this.autoSaveTimeout);
                    this.autoSaveTimeout = setTimeout(() => this.updateTaxPreview(), 500);
                });
            }
        });
        // Only load mock data if no data exists
        if (!this.hasExistingData()) {
            this.loadMockData();
        }
    }

    hasExistingData() {
        // Check if any input field has a value
        const inputs = ['basicSalary', 'hra', 'specialAllowance', 'otherAllowances', 
                       'section80c', 'section80d', 'section24', 'tdsDeducted'];
        return inputs.some(id => {
            const input = document.getElementById(id);
            return input && input.value && parseFloat(input.value) > 0;
        });
    }

    loadMockData() {
        const mockData = {
            basicSalary: 600000, hra: 240000, specialAllowance: 80000,
            otherAllowances: 120000, section80c: 150000, section80d: 25000,
            section24: 200000, tdsDeducted: 45000
        };
        Object.entries(mockData).forEach(([key, value]) => {
            const input = document.getElementById(key);
            if (input) input.value = value;
        });
        this.updateTaxPreview();
    }

    async updateTaxPreview() {
        const financialData = this.getFormData();
        try {
            const result = await this.calculateTaxAPI(financialData);
            const oldRegimeTax = document.getElementById('oldRegimeTax');
            const newRegimeTax = document.getElementById('newRegimeTax');
            if (oldRegimeTax) oldRegimeTax.textContent = `₹${result.old_regime.total_tax.toLocaleString()}`;
            if (newRegimeTax) newRegimeTax.textContent = `₹${result.new_regime.total_tax.toLocaleString()}`;
        } catch (error) {
            console.warn('Live preview failed, using mock calculation.');
        }
    }

    async calculateTax() {
        const financialData = this.getFormData();
        try {
            this.showLoadingOverlay('Calculating tax...');
            const result = await this.calculateTaxAPI(financialData);
            this.currentTaxCalculation = result;
            
            this.updateResultsDisplay(result);
            this.updateResultsCharts(result); 
            this.switchTab('results');
            
            this.showToast('Tax calculation completed', 'success');
        } catch (error) {
            console.error('Tax calculation error:', error);
            this.showToast('Tax calculation failed.', 'error');
        } finally {
            this.hideLoadingOverlay();
        }
    }

    async calculateTaxAPI(financialData) {
        console.log("DEBUG: Sending financial data to backend:", financialData);
        const response = await fetch(`${this.backendUrl}/api/calculate-tax`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ financial_data: financialData, assessment_year: "2025-26" })
        });
        if (!response.ok) throw new Error(`API request failed: ${response.statusText}`);
        const result = await response.json();
        console.log("DEBUG: Backend response:", result);
        console.log("DEBUG: Old regime - gross_income:", result.old_regime.gross_income, "taxable_income:", result.old_regime.taxable_income, "total_tax:", result.old_regime.total_tax);
        console.log("DEBUG: New regime - gross_income:", result.new_regime.gross_income, "taxable_income:", result.new_regime.taxable_income, "total_tax:", result.new_regime.total_tax);
        return result;
    }

    getFormData() {
        // Note: Form currently has these fields only
        // More fields (bonus, rental_income, etc.) can be added to the form later
        const maxReasonableValue = 50000000; // ₹5 crore max for validation
        
        const parseAndValidate = (value) => {
            const parsed = parseFloat(value) || 0;
            // Ensure value is within reasonable range
            if (parsed > maxReasonableValue) {
                console.warn(`Value exceeds max reasonable limit: ${parsed}, capping to 0`);
                return 0; // Cap unreasonably large values
            }
            if (parsed < 0) {
                console.warn(`Negative value provided: ${parsed}, converting to 0`);
                return 0; // Reject negative values
            }
            return parsed;
        };
        
        const formData = {
            basic_salary: parseAndValidate(document.getElementById('basicSalary')?.value),
            hra: parseAndValidate(document.getElementById('hra')?.value),
            special_allowance: parseAndValidate(document.getElementById('specialAllowance')?.value),
            other_allowances: parseAndValidate(document.getElementById('otherAllowances')?.value),
            section_80c: parseAndValidate(document.getElementById('section80c')?.value),
            section_80d: parseAndValidate(document.getElementById('section80d')?.value),
            section_24: parseAndValidate(document.getElementById('section24')?.value),
            tds_deducted: parseAndValidate(document.getElementById('tdsDeducted')?.value),
            // Additional fields not yet in form (default to 0)
            bonus: 0,
            rent_paid: 0,
            city: '',
            is_metro: false,
            interest_income: 0,
            rental_income: 0,
            capital_gains: 0,
            other_income: 0,
            section_80g: 0,
            section_80e: 0,
            section_80ccd1b: 0,
            section_80tta: 0,
            standard_deduction: 50000,
            professional_tax: 0,
            advance_tax: 0
        };
        console.log("DEBUG: getFormData() returning:", formData);
        return formData;
    }

    updateResultsDisplay(result) {
        const totalTaxLiability = document.getElementById('totalTaxLiability');
        const recommendedRegime = document.getElementById('recommendedRegime');
        const taxPaid = document.getElementById('taxPaid');
        const additionalPayment = document.getElementById('additionalPayment');
        const recommended = result.recommended_regime === 'old' ? result.old_regime : result.new_regime;
        
        // Update main tax results
        if (totalTaxLiability) totalTaxLiability.textContent = `₹${recommended.total_tax.toLocaleString()}`;
        if (recommendedRegime) recommendedRegime.textContent = result.recommended_regime.charAt(0).toUpperCase() + result.recommended_regime.slice(1) + ' Regime';
        if (taxPaid) taxPaid.textContent = `₹${this.getFormData().tds_deducted.toLocaleString()}`;
        if (additionalPayment) {
            const additional = recommended.refund_or_payable;
            additionalPayment.textContent = `₹${Math.abs(additional).toLocaleString()}`;
            additionalPayment.style.color = additional >= 0 ? 'var(--color-error)' : 'var(--color-success)';
        }

        // Update tax saving suggestions
        this.updateTaxSavingSuggestions(result);
    }

    async updateTaxSavingSuggestions(result) {
        try {
            // Get tax saving suggestions from the backend
            const response = await fetch(`${this.backendUrl}/api/tax-saving-suggestions`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    income: result.old_regime.gross_income,
                    current_deductions: {
                        section_80c: this.getFormData().section_80c,
                        section_80d: this.getFormData().section_80d,
                        section_80ccd1b: 0, // Add if you have NPS data
                        section_24: this.getFormData().section_24
                    },
                    regime: result.recommended_regime
                })
            });

            if (!response.ok) throw new Error('Failed to fetch suggestions');
            const suggestions = await response.json();

            // Ensure suggestions is treated as an array
            const suggestionsArray = Array.isArray(suggestions) ? suggestions : [];

            // Update the suggestions count
            const suggestionCount = document.querySelector('.tax-savings .count');
            if (suggestionCount) {
                suggestionCount.textContent = `${suggestionsArray.length} opportunities`;
            }

            // Clear existing suggestions
            const savingsList = document.querySelector('.savings-list');
            if (savingsList) {
                savingsList.innerHTML = '';

                // Add new suggestions
                suggestions.forEach(suggestion => {
                    const savingItem = document.createElement('div');
                    savingItem.className = 'expandable-card saving-item';
                    savingItem.innerHTML = `
                        <div class="expandable-header">
                            <div class="saving-header-content">
                                <span class="saving-icon" data-lucide="${this.getSuggestionIcon(suggestion.category)}"></span>
                                <h4>${suggestion.category}</h4>
                            </div>
                            <span class="expand-icon" data-lucide="chevron-down"></span>
                        </div>
                        <div class="expandable-content">
                            <p>${suggestion.description}</p>
                            <span class="saving-amount">Save up to ₹${suggestion.potential_savings.toLocaleString()}</span>
                            ${suggestion.details ? `<p class="saving-details">${suggestion.details}</p>` : ''}
                        </div>
                    `;
                    savingsList.appendChild(savingItem);
                });

                // Re-initialize Lucide icons and accordion behavior
                if (typeof lucide !== 'undefined') {
                    lucide.createIcons();
                }
                this.setupAccordions();
            }
        } catch (error) {
            console.error('Error updating tax suggestions:', error);
            this.showToast('Failed to update tax saving suggestions', 'error');
        }
    }

    getSuggestionIcon(category) {
        const iconMap = {
            'Section 80C Investment': 'trending-up',
            'Health Insurance (80D)': 'shield',
            'NPS Investment (80CCD1B)': 'landmark',
            'Home Loan Planning': 'home',
            'Regime Comparison': 'git-compare',
            'default': 'info'
        };
        return iconMap[category] || iconMap.default;
    }

    setupChatbot() {
        const chatInput = document.getElementById('chatInput');
        const sendButton = document.getElementById('sendMessage');
        if (!chatInput || !sendButton) return;
        const sendMessage = async () => {
            const message = chatInput.value.trim();
            if (!message) return;
            this.addChatMessage('user', message);
            chatInput.value = '';
            try {
                const response = await this.sendChatbotQuery(message);
                this.addChatMessage('bot', response.response);
            } catch (error) {
                console.error('Chatbot error:', error);
                this.addChatMessage('bot', "Sorry, I'm having trouble connecting. Please try again later.");
            }
        };
        sendButton.addEventListener('click', sendMessage);
        chatInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') sendMessage(); });
        document.querySelectorAll('.quick-question-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const question = btn.textContent.trim();
                this.addChatMessage('user', question);
                try {
                    const response = await this.sendChatbotQuery(question);
                    this.addChatMessage('bot', response.response);
                } catch (error) {
                    this.addChatMessage('bot', "Sorry, I'm having trouble connecting. Please try again later.");
                }
            });
        });
    }

    async sendChatbotQuery(message) {
        const response = await fetch(`${this.backendUrl}/api/chatbot`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                context: this.currentTaxCalculation ? { last_calculation: this.currentTaxCalculation } : null,
                user_id: 'demo_user'
            })
        });
        if (!response.ok) throw new Error(`Chatbot API failed: ${response.statusText}`);
        return await response.json();
    }

    addChatMessage(sender, message) {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return;
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${sender}`;
        const avatar = sender === 'user' ? '👤' : '🤖';

        // Convert the message from Markdown to HTML using the marked.js library
        const htmlMessage = marked.parse(message);

        // Insert the generated HTML directly into the message content div
        messageDiv.innerHTML = `<div class="message-avatar">${avatar}</div><div class="message-content">${htmlMessage}</div>`;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    setupCharts() {
        this.initializeDashboardCharts();
    }

    initializeDashboardCharts() {
        const comparisonChart = document.getElementById('comparisonChart');
        if (comparisonChart && typeof Chart !== 'undefined') {
            const ctx = comparisonChart.getContext('2d');
            this.charts.comparison = new Chart(ctx, {
                // MODIFIED: Changed to line chart
                type: 'line', 
                data: {
                    labels: ['2023-24', '2024-25', '2025-26 (Est.)'],
                    datasets: [{
                        label: 'Old Regime', 
                        data: [175000, 185000, 190000], 
                        backgroundColor: 'rgba(33, 128, 141, 0.2)',
                        borderColor: 'rgba(33, 128, 141, 1)',
                        tension: 0.3,
                        fill: true
                    }, {
                        label: 'New Regime', 
                        data: [148000, 156000, 162000], 
                        backgroundColor: 'rgba(50, 184, 198, 0.2)',
                        borderColor: 'rgba(50, 184, 198, 1)',
                        tension: 0.3,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { position: 'top' } },
                    scales: { y: { beginAtZero: true } }
                }
            });
        }
    }
    
    updateResultsCharts(result) {
        if (typeof Chart === 'undefined') return;

        // Old Regime Tax Breakdown Chart
        const oldBreakdownCtx = document.getElementById('oldRegimeBreakdownChart')?.getContext('2d');
        if (oldBreakdownCtx) {
            const oldRegimeData = {
                labels: ['Base Tax', 'Cess (4%)'],
                datasets: [{
                    data: [result.old_regime.tax_before_cess, result.old_regime.cess],
                    backgroundColor: ['rgba(33, 128, 141, 0.8)', 'rgba(230, 129, 97, 0.8)'],
                    borderWidth: 1
                }]
            };
            if (this.charts.oldRegimeBreakdown) {
                this.charts.oldRegimeBreakdown.destroy();
            }
            this.charts.oldRegimeBreakdown = new Chart(oldBreakdownCtx, {
                type: 'doughnut',
                data: oldRegimeData,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } }
                }
            });
        }

        // New Regime Tax Breakdown Chart
        const newBreakdownCtx = document.getElementById('newRegimeBreakdownChart')?.getContext('2d');
        if (newBreakdownCtx) {
            const newRegimeData = {
                labels: ['Base Tax', 'Cess (4%)'],
                datasets: [{
                    data: [result.new_regime.tax_before_cess, result.new_regime.cess],
                    backgroundColor: ['rgba(50, 184, 198, 0.8)', 'rgba(230, 129, 97, 0.8)'],
                    borderWidth: 1
                }]
            };
            if (this.charts.newRegimeBreakdown) {
                this.charts.newRegimeBreakdown.destroy();
            }
            this.charts.newRegimeBreakdown = new Chart(newBreakdownCtx, {
                type: 'doughnut',
                data: newRegimeData,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } }
                }
            });
        }

        // Year-over-Year Comparison Chart (Line)
        const yearCtx = document.getElementById('yearComparisonChart')?.getContext('2d');
        if (yearCtx) {
            const data = {
                labels: ['2023-24', '2024-25', '2025-26 (Current)'],
                datasets: [{
                    label: 'Old Regime Tax',
                    data: [...this.data.mockTaxData.previousYears.oldRegime, result.old_regime.total_tax],
                    backgroundColor: 'rgba(33, 128, 141, 0.2)',
                    borderColor: 'rgba(33, 128, 141, 1)',
                    tension: 0.3,
                    fill: true
                }, {
                    label: 'New Regime Tax',
                    data: [...this.data.mockTaxData.previousYears.newRegime, result.new_regime.total_tax],
                    backgroundColor: 'rgba(50, 184, 198, 0.2)',
                    borderColor: 'rgba(50, 184, 198, 1)',
                    tension: 0.3,
                    fill: true
                }]
            };
            if (this.charts.yearComparison) {
                this.charts.yearComparison.destroy();
            }
            this.charts.yearComparison = new Chart(yearCtx, {
                // MODIFIED: Changed to line chart
                type: 'line', 
                data: data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { position: 'top' } },
                    scales: { y: { beginAtZero: true } }
                }
            });
        }
    }

    updateDashboardStats() {
        const documentsCount = document.getElementById('documentsCount');
        if (documentsCount) documentsCount.textContent = this.uploadedFiles.length;
        if (this.currentTaxCalculation) {
            const recommended = this.currentTaxCalculation.recommended_regime === 'old' ?
                this.currentTaxCalculation.old_regime : this.currentTaxCalculation.new_regime;
            const taxLiability = document.getElementById('taxLiability');
            const taxSavings = document.getElementById('taxSavings');
            if (taxLiability) taxLiability.textContent = `₹${recommended.total_tax.toLocaleString()}`;
            if (taxSavings) taxSavings.textContent = `₹${this.currentTaxCalculation.savings_amount.toLocaleString()}`;
        }
    }

    showLoadingOverlay(message = 'Processing...') {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            const messageElement = overlay.querySelector('p');
            if (messageElement) messageElement.textContent = message;
            overlay.classList.remove('hidden');
        }
    }

    hideLoadingOverlay() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) overlay.classList.add('hidden');
    }

    showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) return;
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        toastContainer.appendChild(toast);
        setTimeout(() => toast.remove(), 5000);
    }

    showExportOptions() {
        // Check if tax calculation has been performed
        if (!this.currentTaxCalculation) {
            this.showToast('Please calculate tax first before exporting', 'warning');
            return;
        }

        // Create modal for export format selection
        const modal = document.createElement('div');
        modal.className = 'export-modal-overlay';
        modal.id = 'exportModal';
        modal.innerHTML = `
            <div class="export-modal">
                <div class="export-modal-header">
                    <h3>Export Tax Summary</h3>
                    <button class="export-modal-close" onclick="this.closest('.export-modal-overlay').remove()">×</button>
                </div>
                <div class="export-modal-body">
                    <p class="export-description">Choose a format to download your ITR-compatible tax summary:</p>
                    <div class="export-options">
                        <button class="export-option-btn pdf-btn" onclick="app.exportTaxSummary('pdf')">
                            <span class="export-icon">📄</span>
                            <div class="export-option-content">
                                <h4>PDF Document</h4>
                                <p>Professional format ready for filing</p>
                            </div>
                        </button>
                        <button class="export-option-btn csv-btn" onclick="app.exportTaxSummary('csv')">
                            <span class="export-icon">📊</span>
                            <div class="export-option-content">
                                <h4>CSV Spreadsheet</h4>
                                <p>Editable format for portal import</p>
                            </div>
                        </button>
                        <button class="export-option-btn excel-btn" onclick="app.exportTaxSummary('excel')">
                            <span class="export-icon">📗</span>
                            <div class="export-option-content">
                                <h4>Excel File</h4>
                                <p>Formatted spreadsheet with styles</p>
                            </div>
                        </button>
                        <button class="export-option-btn json-btn" onclick="app.exportTaxSummary('json')">
                            <span class="export-icon">📋</span>
                            <div class="export-option-content">
                                <h4>JSON Data</h4>
                                <p>Structured format for integration</p>
                            </div>
                        </button>
                    </div>
                    <div class="export-info-box">
                        <p><strong>ℹ️ Note:</strong> This summary is in ITR (Income Tax Return) filing format compatible with the Income Tax Department's e-filing portal.</p>
                        <p>Please review all details with your Chartered Accountant before official filing.</p>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        
        // Close modal when clicking overlay
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }

    async exportTaxSummary(format) {
        try {
            this.showLoadingOverlay(`Generating ${format.toUpperCase()} export...`);
            
            // Prepare data for export
            const exportData = {
                format: format,
                financial_data: this.getFormData(),
                tax_calculation: this.currentTaxCalculation,
                user_info: this.getUserInfo(),
                assessment_year: this.getAssessmentYear()
            };

            // Call backend API
            const response = await fetch(`${this.backendUrl}/api/export-tax-summary`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(exportData)
            });

            if (!response.ok) {
                throw new Error(`Export failed: ${response.statusText}`);
            }

            // Handle different response types
            if (format === 'json') {
                const jsonData = await response.json();
                this.downloadJSON(jsonData);
                this.showToast('Tax summary exported as JSON successfully', 'success');
            } else if (format === 'pdf') {
                const blob = await response.blob();
                this.downloadFile(blob, `ITR_Summary_${this.getAssessmentYear()}.pdf`, 'application/pdf');
                this.showToast('Tax summary exported as PDF successfully', 'success');
            } else if (format === 'csv') {
                const blob = await response.blob();
                this.downloadFile(blob, `ITR_Summary_${this.getAssessmentYear()}.csv`, 'text/csv');
                this.showToast('Tax summary exported as CSV successfully', 'success');
            } else if (format === 'excel') {
                const blob = await response.blob();
                this.downloadFile(blob, `ITR_Summary_${this.getAssessmentYear()}.xlsx`, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
                this.showToast('Tax summary exported as Excel successfully', 'success');
            }

            // Close modal
            const modal = document.getElementById('exportModal');
            if (modal) modal.remove();

        } catch (error) {
            console.error('Export error:', error);
            this.showToast(`Export failed: ${error.message}`, 'error');
        } finally {
            this.hideLoadingOverlay();
        }
    }

    downloadFile(blob, filename, mimeType) {
        const url = window.URL.createObjectURL(new Blob([blob], { type: mimeType }));
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
    }

    downloadJSON(data) {
        const jsonString = JSON.stringify(data, null, 2);
        const blob = new Blob([jsonString], { type: 'application/json' });
        this.downloadFile(blob, `ITR_Summary_${this.getAssessmentYear()}.json`, 'application/json');
    }

    getUserInfo() {
        // Get user information - can be extended to get from profile section
        return {
            name: localStorage.getItem('userName') || '[Taxpayer Name]',
            pan: localStorage.getItem('userPAN') || '[PAN]',
            aadhar: localStorage.getItem('userAadhar') || '[Aadhar No.]',
            dob: localStorage.getItem('userDOB') || '[DOB]',
            address: localStorage.getItem('userAddress') || '[Address]',
            email: localStorage.getItem('userEmail') || '[Email]',
            mobile: localStorage.getItem('userMobile') || '[Mobile]',
            residential_status: 'Resident'
        };
    }

    getAssessmentYear() {
        // Return current assessment year (AY 2024-25 for FY 2023-24)
        const currentYear = new Date().getFullYear();
        return `2024-25`;
    }
}

// Initialize the application
const app = new TaxFilingApp();

// Export for global access
window.app = app;   