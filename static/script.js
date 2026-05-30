// Modern JavaScript for CoderBuddy AI Website Generator
class CoderBuddy {
    constructor() {
        this.currentProject = null;
        this.isGenerating = false;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkHealth();
    }

    setupEventListeners() {
        // Auto-resize textarea
        const promptInput = document.getElementById('prompt');
        promptInput.addEventListener('input', () => {
            promptInput.style.height = 'auto';
            promptInput.style.height = promptInput.scrollHeight + 'px';
        });

        // Enter key to generate (Shift+Enter for new line)
        promptInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.generateWebsite();
            }
        });

        // Close modals on outside click
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                e.target.style.display = 'none';
            }
        });
    }

    async checkHealth() {
        try {
            const response = await fetch('/health');
            const health = await response.json();
            
            if (!health.generator_initialized || !health.api_key_configured) {
                this.showToast('Warning: Generator not properly configured', 'warning');
            }
        } catch (error) {
            console.error('Health check failed:', error);
        }
    }

    async generateWebsite() {
        if (this.isGenerating) return;

        const prompt = document.getElementById('prompt').value.trim();
        if (!prompt) {
            this.showToast('Please enter a website description', 'error');
            return;
        }

        const model = document.getElementById('modelSelect')?.value || 'llama-3.3-70b-versatile';
        
        this.setGeneratingState(true);
        this.hideSections();

        try {
            const response = await fetch('/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ prompt, model })
            });

            const result = await response.json();

            if (result.success) {
                this.currentProject = result;
                this.showResults(result);
                this.showToast('Website generated successfully!', 'success');
            } else {
                this.showError(result.error || 'Generation failed');
            }
        } catch (error) {
            console.error('Generation error:', error);
            this.showError('Network error. Please try again.');
        } finally {
            this.setGeneratingState(false);
        }
    }

    setGeneratingState(isGenerating) {
        this.isGenerating = isGenerating;
        const generateBtn = document.getElementById('generateBtn');
        const btnText = generateBtn.querySelector('span');
        const spinner = generateBtn.querySelector('.loading-spinner');

        if (isGenerating) {
            generateBtn.disabled = true;
            btnText.textContent = 'Generating...';
            spinner.style.display = 'block';
        } else {
            generateBtn.disabled = false;
            btnText.textContent = 'Generate Website';
            spinner.style.display = 'none';
        }
    }

    showResults(result) {
        const resultsSection = document.getElementById('results');
        resultsSection.style.display = 'block';

        // Populate files list
        this.populateFilesList(result.files);

        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth' });

        // Refresh preview after a short delay
        setTimeout(() => this.refreshPreview(), 1000);
    }

    populateFilesList(files) {
        const filesList = document.getElementById('filesList');
        filesList.innerHTML = '';

        files.forEach(file => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            
            const fileIcon = this.getFileIcon(file.path);
            const fileSize = this.formatFileSize(file.size);
            
            fileItem.innerHTML = `
                <div class="file-header">
                    <div class="file-name">
                        <i class="${fileIcon}"></i>
                        ${file.path}
                    </div>
                    <div class="file-size">${fileSize}</div>
                </div>
                <div class="file-content" id="content-${file.path.replace(/[^a-zA-Z0-9]/g, '-')}">
                    Loading...
                </div>
            `;

            fileItem.addEventListener('click', () => {
                this.loadFileContent(file.path);
            });

            filesList.appendChild(fileItem);
        });

        // Load first file content by default
        if (files.length > 0) {
            this.loadFileContent(files[0].path);
        }
    }

    async loadFileContent(filePath) {
        const contentId = `content-${filePath.replace(/[^a-zA-Z0-9]/g, '-')}`;
        const contentElement = document.getElementById(contentId);
        
        if (!contentElement) return;

        try {
            const response = await fetch(`/download/${filePath}`);
            if (response.ok) {
                const content = await response.text();
                contentElement.textContent = content;
                contentElement.scrollTop = 0;
            } else {
                contentElement.textContent = 'Failed to load file content';
            }
        } catch (error) {
            console.error('Error loading file content:', error);
            contentElement.textContent = 'Error loading file content';
        }
    }

    getFileIcon(filePath) {
        const extension = filePath.split('.').pop().toLowerCase();
        const iconMap = {
            'html': 'fas fa-code',
            'css': 'fas fa-palette',
            'js': 'fas fa-cube',
            'json': 'fas fa-file-code',
            'md': 'fas fa-file-alt',
            'txt': 'fas fa-file-text'
        };
        return iconMap[extension] || 'fas fa-file';
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    showError(message) {
        const errorSection = document.getElementById('error');
        const errorMessage = document.getElementById('errorMessage');
        
        errorMessage.textContent = message;
        errorSection.style.display = 'block';
        errorSection.scrollIntoView({ behavior: 'smooth' });
    }

    hideSections() {
        document.getElementById('results').style.display = 'none';
        document.getElementById('error').style.display = 'none';
    }

    async refreshPreview() {
        const iframe = document.getElementById('preview');
        if (iframe) {
            // Force reload by adding timestamp
            const timestamp = Date.now();
            iframe.src = `/generated/index.html?t=${timestamp}`;
        }
    }

    async downloadProject() {
        if (!this.currentProject) {
            this.showToast('No project to download', 'error');
            return;
        }

        try {
            // Create a simple ZIP download using individual file downloads
            // For now, download the main HTML file
            const htmlFile = this.currentProject.files.find(f => f.path === 'index.html');
            if (htmlFile) {
                const response = await fetch(`/download/${htmlFile.path}`);
                if (response.ok) {
                    const content = await response.text();
                    const blob = new Blob([content], { type: 'text/html' });
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `${this.currentProject.project_name || 'website'}.html`;
                    a.click();
                    window.URL.revokeObjectURL(url);
                    
                    this.showToast('Download started!', 'success');
                }
            }
        } catch (error) {
            console.error('Download error:', error);
            this.showToast('Download failed', 'error');
        }
    }

    async cleanProject() {
        try {
            const response = await fetch('/project/clean', { method: 'DELETE' });
            const result = await response.json();
            
            if (result.success) {
                this.currentProject = null;
                this.hideSections();
                this.showToast('Project cleaned successfully', 'success');
            } else {
                this.showToast('Failed to clean project', 'error');
            }
        } catch (error) {
            console.error('Clean error:', error);
            this.showToast('Clean operation failed', 'error');
        }
    }

    retryGeneration() {
        this.generateWebsite();
    }

    loadExample(type) {
        const examples = {
            portfolio: "Create a modern portfolio website for a web developer with a dark theme, smooth animations, skills section, project gallery, and contact form. Include a hero section with typing animation and navigation menu.",
            ecommerce: "Build a modern e-commerce website for selling tech products with product grid, shopping cart functionality, search bar, filter options, and a clean checkout process. Use a professional design with product images.",
            blog: "Design a beautiful blog website with article cards, categories sidebar, search functionality, comment sections, and a clean reading experience. Include a header with navigation and footer with social links."
        };

        const promptInput = document.getElementById('prompt');
        promptInput.value = examples[type];
        promptInput.style.height = 'auto';
        promptInput.style.height = promptInput.scrollHeight + 'px';
        
        // Add focus animation
        promptInput.focus();
        promptInput.classList.add('highlight');
        setTimeout(() => promptInput.classList.remove('highlight'), 1000);
    }

    showToast(message, type = 'success') {
        const toast = document.getElementById('toast');
        const toastMessage = document.getElementById('toastMessage');
        const toastContent = toast.querySelector('.toast-content');
        
        toastMessage.textContent = message;
        
        // Update toast color based on type
        const gradients = {
            success: 'linear-gradient(135deg, #00d2ff 0%, #3a7bd5 100%)',
            error: 'linear-gradient(135deg, #f44336 0%, #e91e63 100%)',
            warning: 'linear-gradient(135deg, #ff9800 0%, #ff5722 100%)'
        };
        
        toast.style.background = gradients[type] || gradients.success;
        
        // Update icon
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle'
        };
        
        const icon = toastContent.querySelector('i');
        icon.className = icons[type] || icons.success;
        
        toast.style.display = 'block';
        
        setTimeout(() => {
            toast.style.display = 'none';
        }, 3000);
    }

    showAbout() {
        document.getElementById('aboutModal').style.display = 'flex';
    }

    showSettings() {
        document.getElementById('settingsModal').style.display = 'flex';
    }
}

// Global functions for HTML onclick handlers
function generateWebsite() {
    window.coderBuddy.generateWebsite();
}

function refreshPreview() {
    window.coderBuddy.refreshPreview();
}

function downloadProject() {
    window.coderBuddy.downloadProject();
}

function cleanProject() {
    if (confirm('Are you sure you want to clean all generated files?')) {
        window.coderBuddy.cleanProject();
    }
}

function retryGeneration() {
    window.coderBuddy.retryGeneration();
}

function loadExample(type) {
    window.coderBuddy.loadExample(type);
}

function showAbout() {
    window.coderBuddy.showAbout();
}

function showSettings() {
    window.coderBuddy.showSettings();
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.coderBuddy = new CoderBuddy();
    
    // Add some nice entrance animations
    document.querySelectorAll('.hero-title, .hero-subtitle, .generator-card').forEach((el, index) => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        setTimeout(() => {
            el.style.transition = 'all 0.6s ease';
            el.style.opacity = '1';
            el.style.transform = 'translateY(0)';
        }, index * 200);
    });
});

// Add highlight animation class
const style = document.createElement('style');
style.textContent = `
    .highlight {
        animation: highlightPulse 1s ease;
    }
    
    @keyframes highlightPulse {
        0%, 100% { box-shadow: 0 0 0 0 rgba(102, 126, 234, 0.4); }
        50% { box-shadow: 0 0 0 10px rgba(102, 126, 234, 0); }
    }
`;
document.head.appendChild(style);
