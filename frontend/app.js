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
            header.addEventListener('click', () => {
                const card = header.closest('.expandable-card');
                card.classList.toggle('expanded');
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
        const fieldMap = {
            'basicSalary': 'basic_salary', 'hra': 'hra',
            'specialAllowance': 'special_allowance', 'otherAllowances': 'other_allowances',
            'section80c': 'section_80c', 'section80d': 'section_80d',
            'section24': 'section_24', 'tdsDeducted': 'tds_deducted'
        };
        Object.entries(fieldMap).forEach(([fieldId, dataKey]) => {
            const field = document.getElementById(fieldId);
            if (field && data[dataKey]) {
                field.value = data[dataKey];
                field.dispatchEvent(new Event('input'));
            }
        });
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
        this.loadMockData();
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
        const response = await fetch(`${this.backendUrl}/api/calculate-tax`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ financial_data: financialData, assessment_year: "2025-26" })
        });
        if (!response.ok) throw new Error(`API request failed: ${response.statusText}`);
        return await response.json();
    }

    getFormData() {
        return {
            basic_salary: parseFloat(document.getElementById('basicSalary')?.value) || 0,
            hra: parseFloat(document.getElementById('hra')?.value) || 0,
            special_allowance: parseFloat(document.getElementById('specialAllowance')?.value) || 0,
            other_allowances: parseFloat(document.getElementById('otherAllowances')?.value) || 0,
            section_80c: parseFloat(document.getElementById('section80c')?.value) || 0,
            section_80d: parseFloat(document.getElementById('section80d')?.value) || 0,
            section_24: parseFloat(document.getElementById('section24')?.value) || 0,
            tds_deducted: parseFloat(document.getElementById('tdsDeducted')?.value) || 0,
            standard_deduction: 50000
        };
    }

    updateResultsDisplay(result) {
        const totalTaxLiability = document.getElementById('totalTaxLiability');
        const recommendedRegime = document.getElementById('recommendedRegime');
        const taxPaid = document.getElementById('taxPaid');
        const additionalPayment = document.getElementById('additionalPayment');
        const recommended = result.recommended_regime === 'old' ? result.old_regime : result.new_regime;
        if (totalTaxLiability) totalTaxLiability.textContent = `₹${recommended.total_tax.toLocaleString()}`;
        if (recommendedRegime) recommendedRegime.textContent = result.recommended_regime.charAt(0).toUpperCase() + result.recommended_regime.slice(1) + ' Regime';
        if (taxPaid) taxPaid.textContent = `₹${this.getFormData().tds_deducted.toLocaleString()}`;
        if (additionalPayment) {
            const additional = recommended.refund_or_payable;
            additionalPayment.textContent = `₹${Math.abs(additional).toLocaleString()}`;
            additionalPayment.style.color = additional >= 0 ? 'var(--color-error)' : 'var(--color-success)';
        }
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
}

// Initialize the application
const app = new TaxFilingApp();

// Export for global access
window.app = app;   