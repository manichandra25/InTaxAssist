// Enhanced Interactive Tax Filing System JavaScript - Backend Integrated
class TaxFilingApp {
    constructor() {
        this.data = {
            mockTaxData: {
                salary: {
                    Basic: 600000,
                    HRA: 240000,
                    "Other Allowances": 120000,
                    "Special Allowance": 80000
                },
                deductions: {
                    "Section 80C": 150000,
                    "Section 80D": 25000,
                    "Section 24": 200000,
                    "Standard Deduction": 50000
                },
                tds: 45000
            },
            taxSlabs: {
                oldRegime: [
                    {min: 0, max: 250000, rate: 0},
                    {min: 250000, max: 500000, rate: 5},
                    {min: 500000, max: 1000000, rate: 20},
                    {min: 1000000, max: null, rate: 30}
                ],
                newRegime: [
                    {min: 0, max: 300000, rate: 0},
                    {min: 300000, max: 600000, rate: 5},
                    {min: 600000, max: 900000, rate: 10},
                    {min: 900000, max: 1200000, rate: 15},
                    {min: 1200000, max: 1500000, rate: 20},
                    {min: 1500000, max: null, rate: 30}
                ]
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
        this.initializeIcons();
        this.setupEventListeners();
        this.setupThemeToggle();
        this.setupTabs();
        this.setupSidebar();
        this.setupUpload();
        this.setupFinancialForm();
        this.setupCharts();
        this.setupChatbot();
        this.updateDashboardStats();
        
        // Check backend connection
        this.checkBackendConnection();
    }

    async checkBackendConnection() {
        try {
            const response = await fetch(`${this.backendUrl}/`);
            const data = await response.json();
            console.log('Backend connected:', data.message);
            this.showToast('Backend connected successfully', 'success');
        } catch (error) {
            console.warn('Backend not available, using mock data');
            this.showToast('Using offline mode - backend not available', 'warning');
        }
    }

    initializeIcons() {
        // Initialize Lucide icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('[data-tab]').forEach(tab => {
            tab.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchTab(tab.dataset.tab);
            });
        });

        // Calculate tax button
        const calculateBtn = document.getElementById('calculateTax');
        if (calculateBtn) {
            calculateBtn.addEventListener('click', async () => {
                await this.calculateTax();
            });
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
        if (defaultTab) {
            defaultTab.classList.add('active');
        }
    }

    switchTab(tabId) {
        // Remove active class from all tabs and nav items
        document.querySelectorAll('.tab-content').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelectorAll('.nav-item').forEach(nav => {
            nav.classList.remove('active');
        });

        // Add active class to selected tab and nav item
        const selectedTab = document.getElementById(tabId);
        const selectedNav = document.querySelector(`[data-tab="${tabId}"]`);
        
        if (selectedTab) {
            selectedTab.classList.add('active');
        }
        if (selectedNav) {
            selectedNav.classList.add('active');
        }

        this.activeTab = tabId;
    }

    setupSidebar() {
        // Expandable sections
        document.querySelectorAll('.expandable-header').forEach(header => {
            header.addEventListener('click', () => {
                const card = header.closest('.expandable-card');
                card.classList.toggle('expanded');
            });
        });
    }

    setupUpload() {
        const uploadZone = document.getElementById('uploadZone');
        const fileInput = document.getElementById('fileInput');
        const browseBtn = document.getElementById('browseBtn');

        if (!uploadZone || !fileInput || !browseBtn) return;

        // Click to browse
        browseBtn.addEventListener('click', () => {
            fileInput.click();
        });

        uploadZone.addEventListener('click', () => {
            fileInput.click();
        });

        // File input change
        fileInput.addEventListener('change', (e) => {
            const files = Array.from(e.target.files);
            this.handleFileUpload(files);
        });
    }

    async handleFileUpload(files) {
        for (const file of files) {
            if (this.validateFile(file)) {
                this.uploadedFiles.push(file);
                this.addFileToPreview(file);
                
                // Upload to backend and parse
                await this.uploadAndParseDocument(file);
                
                this.showToast(`${file.name} uploaded successfully`, 'success');
            }
        }
        
        this.updateDashboardStats();
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
            
            if (!response.ok) {
                throw new Error(`Upload failed: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                // Populate form with extracted data
                this.populateFormWithExtractedData(result.extracted_data);
                
                if (result.warnings && result.warnings.length > 0) {
                    result.warnings.forEach(warning => {
                        this.showToast(warning, 'warning');
                    });
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
        // Populate form fields with extracted data
        const fieldMap = {
            'basicSalary': 'basic_salary',
            'hra': 'hra',
            'specialAllowance': 'special_allowance',
            'otherAllowances': 'other_allowances',
            'section80c': 'section_80c',
            'section80d': 'section_80d',
            'section24': 'section_24',
            'tdsDeducted': 'tds_deducted'
        };
        
        Object.entries(fieldMap).forEach(([fieldId, dataKey]) => {
            const field = document.getElementById(fieldId);
            if (field && data[dataKey]) {
                field.value = data[dataKey];
                field.dispatchEvent(new Event('input'));
            }
        });
        
        // Update preview
        this.updateTaxPreview();
    }

    validateFile(file) {
        const allowedTypes = [
            'application/pdf',
            'image/jpeg',
            'image/png',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain'
        ];
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
        
        fileItem.innerHTML = `
            <div class="file-info">
                <span class="file-icon">${fileIcon}</span>
                <div class="file-details">
                    <span class="file-name">${file.name}</span>
                    <span class="file-size">${fileSize}</span>
                </div>
            </div>
            <button class="btn-remove" onclick="this.closest('.file-item').remove()">×</button>
        `;
        
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
        // Auto-calculation on input change
        const inputs = [
            'basicSalary', 'hra', 'specialAllowance', 'otherAllowances',
            'section80c', 'section80d', 'section24', 'tdsDeducted'
        ];
        
        inputs.forEach(inputId => {
            const input = document.getElementById(inputId);
            if (input) {
                input.addEventListener('input', () => {
                    clearTimeout(this.autoSaveTimeout);
                    this.autoSaveTimeout = setTimeout(() => {
                        this.updateTaxPreview();
                    }, 500);
                });
            }
        });
        
        // Load mock data
        this.loadMockData();
    }

    loadMockData() {
        // Load mock data into form
        const mockData = {
            basicSalary: 600000,
            hra: 240000,
            specialAllowance: 80000,
            otherAllowances: 120000,
            section80c: 150000,
            section80d: 25000,
            section24: 200000,
            tdsDeducted: 45000
        };

        Object.entries(mockData).forEach(([key, value]) => {
            const input = document.getElementById(key);
            if (input) {
                input.value = value;
            }
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
            // Fallback to mock calculation
            const mockOldTax = this.calculateMockTax(financialData, 'old');
            const mockNewTax = this.calculateMockTax(financialData, 'new');
            
            const oldRegimeTax = document.getElementById('oldRegimeTax');
            const newRegimeTax = document.getElementById('newRegimeTax');
            
            if (oldRegimeTax) oldRegimeTax.textContent = `₹${mockOldTax.toLocaleString()}`;
            if (newRegimeTax) newRegimeTax.textContent = `₹${mockNewTax.toLocaleString()}`;
        }
    }

    async calculateTax() {
        const financialData = this.getFormData();
        
        try {
            this.showLoadingOverlay('Calculating tax...');
            
            const result = await this.calculateTaxAPI(financialData);
            this.currentTaxCalculation = result;
            
            // Update results and switch to results tab
            this.updateResultsDisplay(result);
            this.switchTab('results');
            
            this.showToast('Tax calculation completed', 'success');
            
        } catch (error) {
            console.error('Tax calculation error:', error);
            this.showToast('Tax calculation failed. Using mock calculation.', 'error');
            
            // Fallback to mock calculation
            const mockResult = this.calculateMockTaxComplete(financialData);
            this.updateResultsDisplay(mockResult);
            this.switchTab('results');
            
        } finally {
            this.hideLoadingOverlay();
        }
    }

    async calculateTaxAPI(financialData) {
        const response = await fetch(`${this.backendUrl}/api/calculate-tax`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                financial_data: financialData,
                assessment_year: "2024-25"
            })
        });
        
        if (!response.ok) {
            throw new Error(`API request failed: ${response.statusText}`);
        }
        
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

    calculateMockTax(data, regime) {
        const grossIncome = data.basic_salary + data.hra + data.special_allowance + data.other_allowances;
        let deductions = data.standard_deduction;
        
        if (regime === 'old') {
            deductions += data.section_80c + data.section_80d + data.section_24;
        }
        
        const taxableIncome = Math.max(0, grossIncome - deductions);
        const slabs = this.data.taxSlabs[regime === 'old' ? 'oldRegime' : 'newRegime'];
        
        let tax = 0;
        let remaining = taxableIncome;
        
        for (const slab of slabs) {
            if (remaining <= 0) break;
            
            const slabAmount = slab.max ? Math.min(remaining, slab.max - slab.min) : remaining;
            tax += slabAmount * (slab.rate / 100);
            remaining -= slabAmount;
        }
        
        return Math.round(tax * 1.04); // Add 4% cess
    }

    calculateMockTaxComplete(data) {
        const oldTax = this.calculateMockTax(data, 'old');
        const newTax = this.calculateMockTax(data, 'new');
        
        return {
            old_regime: {
                total_tax: oldTax,
                effective_tax_rate: (oldTax / (data.basic_salary + data.hra + data.special_allowance + data.other_allowances) * 100).toFixed(2),
                refund_or_payable: oldTax - data.tds_deducted
            },
            new_regime: {
                total_tax: newTax,
                effective_tax_rate: (newTax / (data.basic_salary + data.hra + data.special_allowance + data.other_allowances) * 100).toFixed(2),
                refund_or_payable: newTax - data.tds_deducted
            },
            recommended_regime: oldTax <= newTax ? 'old' : 'new',
            savings_amount: Math.abs(oldTax - newTax)
        };
    }

    updateResultsDisplay(result) {
        const totalTaxLiability = document.getElementById('totalTaxLiability');
        const recommendedRegime = document.getElementById('recommendedRegime');
        const taxPaid = document.getElementById('taxPaid');
        const additionalPayment = document.getElementById('additionalPayment');
        
        const recommended = result.recommended_regime === 'old' ? result.old_regime : result.new_regime;
        
        if (totalTaxLiability) totalTaxLiability.textContent = `₹${recommended.total_tax.toLocaleString()}`;
        if (recommendedRegime) recommendedRegime.textContent = result.recommended_regime === 'old' ? 'Old Regime' : 'New Regime';
        if (taxPaid) taxPaid.textContent = `₹${this.getFormData().tds_deducted.toLocaleString()}`;
        if (additionalPayment) {
            const additional = recommended.refund_or_payable;
            additionalPayment.textContent = `₹${Math.abs(additional).toLocaleString()}`;
            additionalPayment.style.color = additional > 0 ? 'var(--color-error)' : 'var(--color-success)';
        }
    }

    setupChatbot() {
        const chatInput = document.getElementById('chatInput');
        const sendButton = document.getElementById('sendMessage');
        
        if (!chatInput || !sendButton) return;
        
        const sendMessage = async () => {
            const message = chatInput.value.trim();
            if (!message) return;
            
            // Add user message to chat
            this.addChatMessage('user', message);
            chatInput.value = '';
            
            try {
                const response = await this.sendChatbotQuery(message);
                this.addChatMessage('bot', response.response);
                
            } catch (error) {
                console.error('Chatbot error:', error);
                this.addChatMessage('bot', this.getFallbackResponse(message));
            }
        };
        
        sendButton.addEventListener('click', sendMessage);
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
        
        // Quick questions
        document.querySelectorAll('.quick-question-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const question = btn.textContent.trim();
                this.addChatMessage('user', question);
                
                try {
                    const response = await this.sendChatbotQuery(question);
                    this.addChatMessage('bot', response.response);
                } catch (error) {
                    this.addChatMessage('bot', this.getFallbackResponse(question));
                }
            });
        });
    }

    async sendChatbotQuery(message) {
        const response = await fetch(`${this.backendUrl}/api/chatbot`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                context: this.currentTaxCalculation ? { last_calculation: this.currentTaxCalculation } : null,
                user_id: 'demo_user'
            })
        });
        
        if (!response.ok) {
            throw new Error(`Chatbot API failed: ${response.statusText}`);
        }
        
        return await response.json();
    }

    getFallbackResponse(question) {
        const q = question.toLowerCase();
        
        if (q.includes('document')) {
            return "For tax filing, you need: Form 16, bank statements, investment proofs (80C, 80D), rent receipts for HRA, and home loan statements.";
        } else if (q.includes('hra')) {
            return "HRA exemption is minimum of: (1) Actual HRA received, (2) 50% of salary (metro) or 40% (non-metro), (3) Rent paid minus 10% of salary.";
        } else if (q.includes('regime')) {
            return "Old regime allows more deductions but has higher tax rates. New regime has lower rates but limited deductions. Choose based on your deductions.";
        } else if (q.includes('80c')) {
            return "Section 80C allows deduction up to ₹1,50,000 for investments in PPF, ELSS, NSC, life insurance, etc.";
        } else {
            return "I can help you with tax filing questions powered by Groq's Llama model. Try asking about documents needed, tax regimes, or deductions.";
        }
    }

    addChatMessage(sender, message) {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${sender}`;
        
        const avatar = sender === 'user' ? '👤' : '🤖';
        messageDiv.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">
                <p>${message}</p>
            </div>
        `;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    setupCharts() {
        // Initialize Chart.js charts
        this.initializeDashboardCharts();
    }

    initializeDashboardCharts() {
        const comparisonChart = document.getElementById('comparisonChart');
        if (comparisonChart && typeof Chart !== 'undefined') {
            const ctx = comparisonChart.getContext('2d');
            this.charts.comparison = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['2022-23', '2023-24', '2024-25 (Est.)'],
                    datasets: [{
                        label: 'Old Regime',
                        data: [175000, 185000, 190000],
                        backgroundColor: 'rgba(33, 128, 141, 0.8)',
                    }, {
                        label: 'New Regime',
                        data: [148000, 156000, 162000],
                        backgroundColor: 'rgba(50, 184, 198, 0.8)',
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { position: 'top' }
                    },
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            });
        }
    }

    updateDashboardStats() {
        // Update dashboard statistics
        const documentsCount = document.getElementById('documentsCount');
        if (documentsCount) {
            documentsCount.textContent = this.uploadedFiles.length;
        }
        
        if (this.currentTaxCalculation) {
            const recommended = this.currentTaxCalculation.recommended_regime === 'old' ? 
                this.currentTaxCalculation.old_regime : this.currentTaxCalculation.new_regime;
            
            const taxLiability = document.getElementById('taxLiability');
            const taxSavings = document.getElementById('taxSavings');
            
            if (taxLiability) taxLiability.textContent = `₹${recommended.total_tax.toLocaleString()}`;
            if (taxSavings) taxSavings.textContent = `₹${this.currentTaxCalculation.savings_amount.toLocaleString()}`;
        }
    }

    // Utility methods
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
        if (overlay) {
            overlay.classList.add('hidden');
        }
    }

    showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) return;
        
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        
        toastContainer.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 5000);
    }
}

// Initialize the application
const app = new TaxFilingApp();

// Export for global access
window.app = app;
