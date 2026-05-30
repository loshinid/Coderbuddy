class CoderBuddyApp {
    constructor() {
        console.log('🚀 CoderBuddyApp constructor called');
        this.currentProject = null;
        this.isGenerating = false;
        this.init();
    }

    init() {
        console.log('🔧 Initializing CoderBuddyApp...');
        this.setupEventListeners();
        this.loadExamples();
        console.log('✅ CoderBuddyApp initialized successfully');
    }

    setupEventListeners() {
        console.log('🎯 Setting up event listeners...');
        
        const generateBtn = document.getElementById('generateBtn');
        const promptInput = document.getElementById('prompt');
        const exampleBtns = document.querySelectorAll('.example-btn');

        console.log('📋 Elements found:', {
            generateBtn: !!generateBtn,
            promptInput: !!promptInput,
            exampleBtns: exampleBtns.length
        });

        if (generateBtn) {
            console.log('✅ Adding click listener to generate button');
            generateBtn.addEventListener('click', (e) => {
                console.log('🖱️ Generate button clicked!');
                e.preventDefault();
                this.generateWebsite();
            });
        } else {
            console.error('❌ Generate button not found!');
        }

        if (promptInput) {
            console.log('✅ Adding keydown listener to prompt input');
            promptInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && e.ctrlKey) {
                    console.log('⌨️ Ctrl+Enter pressed');
                    this.generateWebsite();
                }
            });
        } else {
            console.error('❌ Prompt input not found!');
        }

        exampleBtns.forEach((btn, index) => {
            console.log(`✅ Adding click listener to example button ${index}`);
            btn.addEventListener('click', () => {
                const example = btn.dataset.example;
                if (promptInput) {
                    promptInput.value = example;
                    promptInput.focus();
                    console.log('📝 Example selected:', example);
                }
            });
        });

        console.log('✅ Event listeners setup complete');
    }

    loadExamples() {
        const examples = [
            "Create a modern landing page for a tech startup",
            "Build a portfolio website for a photographer",
            "Design an e-commerce product page",
            "Make a restaurant website with menu",
            "Create a personal blog layout"
        ];

        const exampleBtns = document.querySelectorAll('.example-btn');
        exampleBtns.forEach((btn, index) => {
            if (examples[index]) {
                btn.dataset.example = examples[index];
            }
        });
    }

    async generateWebsite() {
        console.log('🚀 generateWebsite() method called');
        
        if (this.isGenerating) {
            console.log('⏳ Generation already in progress, ignoring');
            return;
        }

        const promptInput = document.getElementById('prompt');
        if (!promptInput) {
            console.error('❌ Prompt input element not found');
            this.showToast('Error: Prompt input not found', 'error');
            return;
        }
        const prompt = promptInput.value.trim();

        console.log('📝 Prompt validation:', {
            promptInput: !!promptInput,
            promptLength: prompt.length,
            prompt: prompt.substring(0, 50) + (prompt.length > 50 ? '...' : '')
        });

        if (!prompt) {
            console.log('❌ Empty prompt validation failed');
            this.showToast('Please enter a prompt', 'error');
            return;
        }

        console.log('🔄 Starting generation process...');
        this.setGeneratingState(true);
        this.hideSections();

        try {
            console.log('📡 Sending API request to /generate...');
            
            const requestBody = {
                prompt: prompt,
                model: 'llama-3.1-8b-instant'
            };
            
            console.log('📦 Request body:', requestBody);

            const response = await fetch('/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody)
            });

            console.log('📨 API response received:', {
                status: response.status,
                statusText: response.statusText,
                ok: response.ok
            });

            if (!response.ok) {
                console.error('❌ API request failed:', response.status);
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            console.log('📋 Parsed response:', result);

            if (result.success) {
                console.log('✅ Generation successful!');
                this.currentProject = result;
                this.showResults(result);
                this.showToast('Website generated successfully!', 'success');
                
                // Auto-refresh preview after successful generation
                setTimeout(() => {
                    this.refreshPreview();
                }, 1000);
            } else {
                console.error('❌ Generation failed:', result.error);
                
                // Handle specific error types with user-friendly messages
                let errorMessage = result.error || 'Generation failed';
                if (result.error_type === 'RateLimitError') {
                    errorMessage = 'API rate limit reached. Please wait a moment and try again.';
                    console.log('⏱️ Rate limit detected - showing user-friendly message');
                } else if (result.error_type === 'TimeoutError') {
                    errorMessage = 'Request timed out. Please try again.';
                    console.log('⏰ Timeout detected - showing user-friendly message');
                } else if (result.error_type === 'ValueError' && result.error.includes('Failed to parse delimited response')) {
                    errorMessage = 'AI response format issue. The system generated a fallback website instead.';
                    console.log('🔧 Delimiter parsing failed - fallback content used');
                } else if (result.error_type === 'ValueError' && result.error.includes('No sections parsed')) {
                    errorMessage = 'AI response was incomplete. Generated a basic website template.';
                    console.log('📝 No sections parsed - using fallback template');
                }
                
                this.showError(errorMessage);
            }
        } catch (error) {
            console.error('💥 Generation error:', error);
            this.showError(`Failed to generate website: ${error.message}`);
        } finally {
            console.log('🏁 Generation process completed');
            this.setGeneratingState(false);
        }
    }

    setGeneratingState(isGenerating) {
        console.log('⚙️ Setting generation state:', isGenerating);
        this.isGenerating = isGenerating;
        const generateBtn = document.getElementById('generateBtn');
        const promptInput = document.getElementById('prompt');

        if (generateBtn) {
            if (isGenerating) {
                console.log('🔄 Enabling loading state');
                generateBtn.disabled = true;
                generateBtn.innerHTML = '<div class="loading-spinner"></div> Generating...';
                generateBtn.style.cursor = 'not-allowed';
            } else {
                console.log('✅ Disabling loading state');
                generateBtn.disabled = false;
                generateBtn.innerHTML = '<i class="fas fa-rocket"></i> <span>Generate Website</span>';
                generateBtn.style.cursor = 'pointer';
            }
        } else {
            console.error('❌ Generate button not found for state update');
        }

        if (promptInput) {
            promptInput.disabled = isGenerating;
            if (isGenerating) {
                promptInput.style.cursor = 'not-allowed';
            } else {
                promptInput.style.cursor = 'text';
            }
        }
    }

    showResults(project) {
        const resultsSection = document.getElementById('results');
        const projectName = document.getElementById('projectName');
        const generationTime = document.getElementById('generationTime');
        const totalFiles = document.getElementById('totalFiles');

        // Check if results section exists
        if (!resultsSection) {
            console.error('❌ Results section element not found');
            this.showToast('Error: Results section not found', 'error');
            return;
        }

        // Update project info if elements exist
        if (projectName) {
            projectName.textContent = project.project_name || 'Untitled Project';
        } else {
            console.warn('⚠️ Project name element not found');
        }

        if (generationTime) {
            generationTime.textContent = `${(project.generation_time || 0).toFixed(2)}s`;
        } else {
            console.warn('⚠️ Generation time element not found');
        }

        if (totalFiles) {
            totalFiles.textContent = project.total_files || 0;
        } else {
            console.warn('⚠️ Total files element not found');
        }

        this.populateFilesList(project.files || []);
        this.refreshPreview();

        resultsSection.style.display = 'block';
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    populateFilesList(files) {
        const filesList = document.getElementById('filesList');
        if (!filesList) {
            console.error('❌ Files list element not found');
            this.showToast('Error: Files list not found', 'error');
            return;
        }
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
        
        if (!contentElement) {
            console.warn(`⚠️ Content element not found: ${contentId}`);
            return;
        }

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
        
        if (!errorSection) {
            console.error('❌ Error section element not found');
            this.showToast(message, 'error');
            return;
        }
        
        if (!errorMessage) {
            console.warn('⚠️ Error message element not found');
            this.showToast(message, 'error');
            return;
        }
        
        errorMessage.textContent = message;
        errorSection.style.display = 'block';
        errorSection.scrollIntoView({ behavior: 'smooth' });
    }

    hideSections() {
        const resultsSection = document.getElementById('results');
        const errorSection = document.getElementById('error');
        
        if (resultsSection) {
            resultsSection.style.display = 'none';
        } else {
            console.warn('⚠️ Results section not found for hiding');
        }
        
        if (errorSection) {
            errorSection.style.display = 'none';
        } else {
            console.warn('⚠️ Error section not found for hiding');
        }
    }

    async refreshPreview() {
        console.log('🔄 Refreshing preview...');
        const iframe = document.getElementById('preview');
        
        if (iframe) {
            // Force reload by adding timestamp
            const timestamp = Date.now();
            const previewUrl = `/generated/index.html?t=${timestamp}`;
            console.log('🖼️ Loading preview URL:', previewUrl);
            
            iframe.src = previewUrl;
            
            // Add load event listener to detect when preview loads
            iframe.onload = () => {
                console.log('✅ Preview loaded successfully');
            };
            
            iframe.onerror = (error) => {
                console.error('❌ Preview load error:', error);
            };
        } else {
            console.error('❌ Preview iframe not found');
        }
    }

    async downloadProject() {
        if (!this.currentProject) {
            this.showToast('No project to download', 'error');
            return;
        }

        try {
            // Download complete project as ZIP
            const response = await fetch('/download-zip');
            
            if (response.ok) {
                // Get filename from Content-Disposition header
                const contentDisposition = response.headers.get('content-disposition');
                let filename = 'website.zip';
                if (contentDisposition) {
                    const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
                    if (filenameMatch) {
                        filename = filenameMatch[1];
                    }
                }
                
                // Create blob and download
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                a.style.display = 'none';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                this.showToast(`Downloaded ${filename} successfully!`, 'success');
            } else {
                const errorData = await response.json().catch(() => ({}));
                const errorMessage = errorData.detail || 'Failed to download project';
                this.showToast(errorMessage, 'error');
            }
        } catch (error) {
            console.error('Download error:', error);
            this.showToast('Failed to download project', 'error');
        }
    }

    async cleanProject() {
        if (!this.currentProject) {
            this.showToast('No project to clean', 'error');
            return;
        }

        if (!confirm('Are you sure you want to clean current project? This will delete all generated files.')) {
            return;
        }

        try {
            const response = await fetch('/project/clean', {
                method: 'DELETE'
            });
            
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
            this.showToast('Failed to clean project', 'error');
        }
    }

    showToast(message, type = 'info') {
        const toast = document.getElementById('toast');
        const toastMessage = document.getElementById('toastMessage');
        
        if (!toast) {
            console.warn('⚠️ Toast element not found, using alert fallback');
            alert(message);
            return;
        }
        
        if (!toastMessage) {
            console.warn('⚠️ Toast message element not found, using alert fallback');
            alert(message);
            return;
        }
        
        toastMessage.textContent = message;
        toast.className = `toast ${type}`;
        toast.style.display = 'block';
        
        setTimeout(() => {
            if (toast) {
                toast.style.display = 'none';
            }
        }, 3000);
    }

    showAbout() {
        alert('CoderBuddy AI Website Generator\n\nGenerate modern websites from text prompts using AI.\n\nBuilt with FastAPI, LangChain, and Groq.');
    }

    showSettings() {
        alert('Settings coming soon!\n\nCurrent features:\n- AI-powered website generation\n- Live preview\n- File downloads\n- Project management');
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.coderBuddyApp = new CoderBuddyApp();
});

// Global functions for onclick handlers
function generateWebsite() {
    console.log('🌐 Global generateWebsite() called');
    if (window.coderBuddyApp) {
        console.log('✅ Calling app.generateWebsite()');
        window.coderBuddyApp.generateWebsite();
    } else {
        console.error('❌ CoderBuddyApp not found in window object');
        alert('Application not loaded properly. Please refresh the page.');
    }
}

function downloadProject() {
    console.log('🌐 Global downloadProject() called');
    if (window.coderBuddyApp) {
        window.coderBuddyApp.downloadProject();
    } else {
        console.error('❌ CoderBuddyApp not found in window object');
    }
}

function cleanProject() {
    console.log('🌐 Global cleanProject() called');
    if (window.coderBuddyApp) {
        window.coderBuddyApp.cleanProject();
    } else {
        console.error('❌ CoderBuddyApp not found in window object');
    }
}

function refreshPreview() {
    console.log('🌐 Global refreshPreview() called');
    if (window.coderBuddyApp) {
        window.coderBuddyApp.refreshPreview();
    } else {
        console.error('❌ CoderBuddyApp not found in window object');
    }
}

function showAbout() {
    console.log('🌐 Global showAbout() called');
    if (window.coderBuddyApp) {
        window.coderBuddyApp.showAbout();
    } else {
        console.error('❌ CoderBuddyApp not found in window object');
    }
}

function showSettings() {
    console.log('🌐 Global showSettings() called');
    if (window.coderBuddyApp) {
        window.coderBuddyApp.showSettings();
    } else {
        console.error('❌ CoderBuddyApp not found in window object');
    }
}
