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

        // Populate entities
        this.displayEntities(data.entities);

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
