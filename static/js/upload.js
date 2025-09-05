// Legal Document Analyzer - Upload and Processing JavaScript
class DocumentAnalyzer {
    constructor() {
        this.currentFile = null;
        this.isProcessing = false;
        
        this.initializeEventListeners();
        this.initializeDragAndDrop();
    }

    initializeEventListeners() {
        // File input change
        document.getElementById('fileInput').addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFileSelect(e.target.files[0]);
            }
        });

        // Choose file button
        document.getElementById('chooseFileBtn').addEventListener('click', () => {
            document.getElementById('fileInput').click();
        });

        // Analyze button
        document.getElementById('analyzeBtn').addEventListener('click', () => {
            this.analyzeDocument();
        });

        // New analysis button
        document.getElementById('newAnalysisBtn').addEventListener('click', () => {
            this.resetInterface();
        });

        // Download report button
        document.getElementById('downloadReportBtn').addEventListener('click', () => {
            this.downloadReport();
        });
    }

    initializeDragAndDrop() {
        const uploadArea = document.getElementById('uploadArea');

        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, this.preventDefaults, false);
            document.body.addEventListener(eventName, this.preventDefaults, false);
        });

        // Highlight drop area
        ['dragenter', 'dragover'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => {
                uploadArea.classList.add('dragover');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => {
                uploadArea.classList.remove('dragover');
            }, false);
        });

        // Handle dropped files
        uploadArea.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileSelect(files[0]);
            }
        }, false);
    }

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    handleFileSelect(file) {
        // Validate file type
        const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf', 'image/tiff', 'image/bmp'];
        if (!allowedTypes.includes(file.type)) {
            this.showError('Invalid file type. Please upload: JPG, PNG, PDF, TIFF, or BMP files.');
            return;
        }

        // Validate file size (16MB limit)
        const maxSize = 16 * 1024 * 1024; // 16MB in bytes
        if (file.size > maxSize) {
            this.showError('File is too large. Maximum file size is 16MB.');
            return;
        }

        this.currentFile = file;
        this.updateUploadArea(file);
        this.enableAnalyzeButton();
    }

    updateUploadArea(file) {
        const uploadArea = document.getElementById('uploadArea');
        const uploadContent = document.getElementById('uploadContent');

        uploadArea.classList.add('has-file');

        // Create file info display
        const fileInfo = document.createElement('div');
        fileInfo.className = 'file-info';
        fileInfo.innerHTML = `
            <div class="file-name">
                <i class="fas fa-file-alt me-2 text-primary"></i>
                ${file.name}
            </div>
            <div class="file-size text-muted">
                ${this.formatFileSize(file.size)} • ${file.type.split('/')[1].toUpperCase()}
            </div>
            <button type="button" class="btn btn-sm btn-outline-secondary mt-2" id="changeFileBtn">
                <i class="fas fa-edit me-1"></i>
                Change File
            </button>
        `;

        // Replace upload content with file info
        uploadContent.style.display = 'none';
        uploadArea.appendChild(fileInfo);

        // Add change file functionality
        document.getElementById('changeFileBtn').addEventListener('click', () => {
            document.getElementById('fileInput').click();
        });
    }

    enableAnalyzeButton() {
        const analyzeBtn = document.getElementById('analyzeBtn');
        analyzeBtn.disabled = false;
        analyzeBtn.classList.add('pulse-animation');
    }

    async analyzeDocument() {
        if (!this.currentFile || this.isProcessing) {
            return;
        }

        this.isProcessing = true;
        this.showLoadingState();

        const formData = new FormData();
        formData.append('file', this.currentFile);

        try {
            // Update loading step
            this.updateLoadingStep('Uploading file');

            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Upload failed');
            }

            this.updateLoadingStep('Extracting text');
            
            // Add artificial delay for better UX
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            this.updateLoadingStep('Analyzing entities');
            await new Promise(resolve => setTimeout(resolve, 1500));
            
            this.updateLoadingStep('Generating summary');
            await new Promise(resolve => setTimeout(resolve, 1000));

            const result = await response.json();

            if (result.success) {
                this.displayResults(result.data);
            } else {
                throw new Error(result.error || 'Analysis failed');
            }

        } catch (error) {
            console.error('Analysis error:', error);
            this.showError(error.message || 'An unexpected error occurred while analyzing the document.');
        } finally {
            this.isProcessing = false;
            this.hideLoadingState();
        }
    }

    showLoadingState() {
        document.getElementById('uploadContent').style.display = 'none';
        document.getElementById('uploadLoading').classList.remove('d-none');
        document.getElementById('analyzeBtn').disabled = true;
    }

    hideLoadingState() {
        document.getElementById('uploadLoading').classList.add('d-none');
        document.getElementById('uploadContent').style.display = 'block';
    }

    updateLoadingStep(step) {
        document.getElementById('loadingStep').textContent = step;
    }

    displayResults(data) {
        // Populate original text
        document.getElementById('originalText').textContent = data.original_text;

        // Populate summary
        document.getElementById('summaryText').textContent = data.summary;

        // Display risk assessment
        this.displayRiskAssessment(data.risk_assessment || {});

        // Display clause analysis
        this.displayClauseAnalysis(data.clause_analysis || []);

        // Populate entities
        this.displayEntities(data.entities);

        // Store PDF report path for download
        if (data.pdf_report) {
            this.pdfReportPath = data.pdf_report;
            document.getElementById('downloadReportBtn').style.display = 'inline-block';
        }

        // Show results section
        document.getElementById('resultsSection').classList.remove('d-none');
        
        // Scroll to results
        document.getElementById('resultsSection').scrollIntoView({ 
            behavior: 'smooth',
            block: 'start'
        });

        // Hide upload section
        document.querySelector('.upload-section').style.display = 'none';
    }

    displayEntities(entities) {
        const entitiesGrid = document.getElementById('entitiesGrid');
        entitiesGrid.innerHTML = '';

        if (!entities || Object.keys(entities).length === 0) {
            entitiesGrid.innerHTML = '<p class="text-muted">No entities were identified in this document.</p>';
            return;
        }

        const entityTypeMapping = {
            'PERSON': { name: 'People', class: 'person', icon: 'fas fa-user' },
            'ORGANIZATION': { name: 'Organizations', class: 'organization', icon: 'fas fa-building' },
            'DATE': { name: 'Dates', class: 'date', icon: 'fas fa-calendar' },
            'MONEY': { name: 'Financial Terms', class: 'money', icon: 'fas fa-dollar-sign' },
            'CONTRACT_TERM': { name: 'Contract Terms', class: 'contract-term', icon: 'fas fa-file-contract' },
            'LEGAL_REF': { name: 'Legal References', class: 'legal-ref', icon: 'fas fa-gavel' },
            'LOCATION': { name: 'Locations', class: 'location', icon: 'fas fa-map-marker-alt' }
        };

        Object.entries(entities).forEach(([entityType, entityList]) => {
            if (entityList && entityList.length > 0) {
                const mapping = entityTypeMapping[entityType] || { 
                    name: entityType.replace('_', ' '), 
                    class: 'default',
                    icon: 'fas fa-tag'
                };

                const entityGroup = document.createElement('div');
                entityGroup.className = `entity-group ${mapping.class}`;
                
                entityGroup.innerHTML = `
                    <h6>
                        <i class="${mapping.icon} me-2"></i>
                        ${mapping.name}
                    </h6>
                    <ul class="entity-list">
                        ${entityList.slice(0, 5).map(entity => `
                            <li class="entity-item">
                                ${this.escapeHtml(entity.text)}
                                <span class="entity-confidence">
                                    ${Math.round(entity.confidence * 100)}%
                                </span>
                            </li>
                        `).join('')}
                        ${entityList.length > 5 ? `<li class="entity-item text-muted">+${entityList.length - 5} more</li>` : ''}
                    </ul>
                `;

                entitiesGrid.appendChild(entityGroup);
            }
        });
    }

    showError(message) {
        document.getElementById('errorMessage').textContent = message;
        const errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
        errorModal.show();
    }

    resetInterface() {
        // Reset file selection
        this.currentFile = null;
        this.pdfReportPath = null;
        document.getElementById('fileInput').value = '';

        // Reset upload area
        const uploadArea = document.getElementById('uploadArea');
        uploadArea.classList.remove('has-file', 'error');
        
        // Remove file info if exists
        const fileInfo = uploadArea.querySelector('.file-info');
        if (fileInfo) {
            fileInfo.remove();
        }

        // Show upload content
        document.getElementById('uploadContent').style.display = 'block';

        // Disable analyze button
        const analyzeBtn = document.getElementById('analyzeBtn');
        analyzeBtn.disabled = true;
        analyzeBtn.classList.remove('pulse-animation');

        // Hide download button
        document.getElementById('downloadReportBtn').style.display = 'none';

        // Hide results and show upload section
        document.getElementById('resultsSection').classList.add('d-none');
        document.querySelector('.upload-section').style.display = 'block';

        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        
        return text.replace(/[&<>"']/g, (m) => map[m]);
    }

    displayRiskAssessment(riskData) {
        const riskElement = document.getElementById('riskAssessment');
        
        if (!riskData || !riskData.level) {
            riskElement.innerHTML = '<p class="text-muted">Risk assessment not available.</p>';
            return;
        }

        const level = riskData.level.toUpperCase();
        const description = riskData.description || 'No description available';

        let badgeClass = 'bg-secondary';
        let iconClass = 'fas fa-question-circle';
        
        if (level === 'HIGH') {
            badgeClass = 'bg-danger';
            iconClass = 'fas fa-exclamation-triangle';
        } else if (level === 'MEDIUM') {
            badgeClass = 'bg-warning';
            iconClass = 'fas fa-exclamation-circle';
        } else if (level === 'LOW') {
            badgeClass = 'bg-success';
            iconClass = 'fas fa-check-circle';
        }

        riskElement.innerHTML = `
            <div class="d-flex align-items-center mb-3">
                <span class="badge ${badgeClass} me-3 p-2">
                    <i class="${iconClass} me-1"></i>
                    ${level} RISK
                </span>
            </div>
            <p class="mb-0">${this.escapeHtml(description)}</p>
        `;
    }

    displayClauseAnalysis(clauses) {
        const clauseElement = document.getElementById('clauseAnalysis');
        
        if (!clauses || clauses.length === 0) {
            clauseElement.innerHTML = '<p class="text-muted">No clause analysis available.</p>';
            return;
        }

        const clauseCounts = { harmful: 0, warning: 0, good: 0, neutral: 0 };
        clauses.forEach(clause => {
            const type = clause.classification || 'neutral';
            clauseCounts[type] = (clauseCounts[type] || 0) + 1;
        });

        let analysisHtml = `
            <div class="row mb-4">
                <div class="col-md-3 col-6 mb-2">
                    <div class="text-center p-3 border rounded" style="background-color: #ffebee;">
                        <div class="h4 text-danger mb-1">🔴 ${clauseCounts.harmful}</div>
                        <small class="text-muted">Harmful</small>
                    </div>
                </div>
                <div class="col-md-3 col-6 mb-2">
                    <div class="text-center p-3 border rounded" style="background-color: #fff3e0;">
                        <div class="h4 text-warning mb-1">🟡 ${clauseCounts.warning}</div>
                        <small class="text-muted">Warning</small>
                    </div>
                </div>
                <div class="col-md-3 col-6 mb-2">
                    <div class="text-center p-3 border rounded" style="background-color: #e8f5e8;">
                        <div class="h4 text-success mb-1">🟢 ${clauseCounts.good}</div>
                        <small class="text-muted">Good</small>
                    </div>
                </div>
                <div class="col-md-3 col-6 mb-2">
                    <div class="text-center p-3 border rounded" style="background-color: #f5f5f5;">
                        <div class="h4 text-secondary mb-1">⚪ ${clauseCounts.neutral}</div>
                        <small class="text-muted">Neutral</small>
                    </div>
                </div>
            </div>
        `;

        // Add individual clauses (show first 5)
        analysisHtml += '<h6 class="mb-3">Clause Details:</h6>';
        
        const displayClauses = clauses.slice(0, 5);
        displayClauses.forEach((clause, index) => {
            const classification = clause.classification || 'neutral';
            const confidence = Math.round((clause.confidence || 0) * 100);
            const text = clause.text || 'No text available';
            const reasoning = clause.reasoning || 'No analysis available';
            
            const colorMap = {
                harmful: { bg: '#ffebee', text: '#d32f2f', emoji: '🔴' },
                warning: { bg: '#fff3e0', text: '#f57c00', emoji: '🟡' },
                good: { bg: '#e8f5e8', text: '#388e3c', emoji: '🟢' },
                neutral: { bg: '#f5f5f5', text: '#424242', emoji: '⚪' }
            };
            
            const colors = colorMap[classification] || colorMap.neutral;
            
            analysisHtml += `
                <div class="mb-3 p-3 border rounded" style="background-color: ${colors.bg}; border-left: 4px solid ${colors.text} !important;">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <span class="badge" style="background-color: ${colors.text}; color: white;">
                            ${colors.emoji} ${classification.toUpperCase()} (${confidence}%)
                        </span>
                    </div>
                    <div class="mb-2">
                        <strong>Text:</strong> ${this.escapeHtml(text.substring(0, 200))}${text.length > 200 ? '...' : ''}
                    </div>
                    <div>
                        <strong>Analysis:</strong> ${this.escapeHtml(reasoning)}
                    </div>
                </div>
            `;
        });

        if (clauses.length > 5) {
            analysisHtml += `<p class="text-muted">... and ${clauses.length - 5} more clauses analyzed.</p>`;
        }

        clauseElement.innerHTML = analysisHtml;
    }

    downloadReport() {
        if (!this.pdfReportPath) {
            this.showError('No report available for download.');
            return;
        }

        // Extract filename from path
        const filename = this.pdfReportPath.split('/').pop();
        const downloadUrl = `/download-report/${filename}`;
        
        // Create temporary link to trigger download
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

// Add CSS animation for pulse effect
const style = document.createElement('style');
style.textContent = `
    .pulse-animation {
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% {
            transform: scale(1);
        }
        50% {
            transform: scale(1.05);
        }
        100% {
            transform: scale(1);
        }
    }
`;
document.head.appendChild(style);

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new DocumentAnalyzer();
});
