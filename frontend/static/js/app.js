/**
 * Pastebin Frontend Application
 * Handles paste creation, form validation, and user interactions
 * No frameworks - vanilla JavaScript with modern APIs
 */

(function() {
    'use strict';

    // DOM Elements
    const pasteForm = document.getElementById('pasteForm');
    const contentTextarea = document.getElementById('content');
    const expirySelect = document.getElementById('expiry');
    const submitBtn = document.getElementById('submitBtn');
    const charCount = document.getElementById('charCount');
    
    const errorAlert = document.getElementById('errorAlert');
    const errorMessage = document.getElementById('errorMessage');
    const successAlert = document.getElementById('successAlert');
    const pasteUrlInput = document.getElementById('pasteUrl');
    const copyBtn = document.getElementById('copyBtn');
    const newPasteBtn = document.getElementById('newPasteBtn');

    // Constants
    const MAX_PASTE_SIZE = 1048576; // 1MB in bytes
    const API_ENDPOINT = '/api/paste';

    /**
     * Initialize the application
     */
    function init() {
        setupEventListeners();
        updateCharCount();
        
        // Focus on textarea on load
        if (contentTextarea) {
            contentTextarea.focus();
        }
    }

    /**
     * Set up all event listeners
     */
    function setupEventListeners() {
        // Form submission
        if (pasteForm) {
            pasteForm.addEventListener('submit', handleSubmit);
        }

        // Character count update
        if (contentTextarea) {
            contentTextarea.addEventListener('input', updateCharCount);
            
            // Also validate size on paste
            contentTextarea.addEventListener('paste', function(e) {
                setTimeout(validateContentSize, 0);
            });
        }

        // Copy button
        if (copyBtn) {
            copyBtn.addEventListener('click', handleCopyUrl);
        }

        // New paste button
        if (newPasteBtn) {
            newPasteBtn.addEventListener('click', resetForm);
        }

        // Keyboard shortcut: Ctrl/Cmd + Enter to submit
        if (contentTextarea) {
            contentTextarea.addEventListener('keydown', function(e) {
                if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                    e.preventDefault();
                    pasteForm.dispatchEvent(new Event('submit'));
                }
            });
        }
    }

    /**
     * Update character count display
     */
    function updateCharCount() {
        if (!contentTextarea || !charCount) return;

        const length = contentTextarea.value.length;
        const byteSize = new Blob([contentTextarea.value]).size;
        
        charCount.textContent = `${length.toLocaleString()} characters (${formatBytes(byteSize)})`;
        
        // Visual feedback for size limits
        if (byteSize > MAX_PASTE_SIZE * 0.9) {
            charCount.style.color = 'var(--error)';
        } else if (byteSize > MAX_PASTE_SIZE * 0.7) {
            charCount.style.color = 'var(--text-secondary)';
        } else {
            charCount.style.color = 'var(--text-muted)';
        }
    }

    /**
     * Validate content size
     */
    function validateContentSize() {
        const byteSize = new Blob([contentTextarea.value]).size;
        
        if (byteSize > MAX_PASTE_SIZE) {
            showError(`Content too large. Maximum size is ${formatBytes(MAX_PASTE_SIZE)}.`);
            return false;
        }
        
        return true;
    }

    /**
     * Handle form submission
     */
    async function handleSubmit(e) {
        e.preventDefault();

        // Hide previous messages
        hideError();
        hideSuccess();

        // Validate content
        const content = contentTextarea.value.trim();
        
        if (!content) {
            showError('Please enter some content to share.');
            contentTextarea.focus();
            return;
        }

        if (!validateContentSize()) {
            return;
        }

        // Get expiry value
        const expiry = expirySelect.value;

        // Show loading state
        setLoading(true);

        try {
            // Make API request
            const response = await fetch(API_ENDPOINT, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    content: content,
                    expiry: expiry
                })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                // Success - show the paste URL
                const fullUrl = window.location.origin + data.url;
                handleSuccess(fullUrl);
            } else {
                // Error from server
                showError(data.error || 'Failed to create paste. Please try again.');
            }

        } catch (error) {
            console.error('Error creating paste:', error);
            showError('Network error. Please check your connection and try again.');
        } finally {
            setLoading(false);
        }
    }

    /**
     * Handle successful paste creation
     */
    function handleSuccess(url) {
        // Set URL in input
        pasteUrlInput.value = url;
        
        // Show success alert
        showSuccess();
        
        // Scroll to success message
        successAlert.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    /**
     * Handle copying URL to clipboard
     */
    async function handleCopyUrl() {
        const url = pasteUrlInput.value;
        
        try {
            // Modern Clipboard API
            if (navigator.clipboard && navigator.clipboard.writeText) {
                await navigator.clipboard.writeText(url);
                showCopyFeedback();
            } else {
                // Fallback for older browsers
                pasteUrlInput.select();
                document.execCommand('copy');
                showCopyFeedback();
            }
        } catch (error) {
            console.error('Error copying to clipboard:', error);
            // Fallback: select the text for manual copying
            pasteUrlInput.select();
            showError('Could not copy automatically. Please copy manually.');
        }
    }

    /**
     * Show visual feedback for successful copy
     */
    function showCopyFeedback() {
        const originalText = copyBtn.innerHTML;
        
        copyBtn.innerHTML = `
            <svg class="btn-icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <path d="M8 0a8 8 0 1 0 0 16A8 8 0 0 0 8 0zm3.5 7.5l-4 4a.5.5 0 0 1-.7 0l-2-2a.5.5 0 1 1 .7-.7L7 10.3l3.6-3.6a.5.5 0 1 1 .7.7z"/>
            </svg>
            Copied!
        `;
        
        copyBtn.style.background = 'var(--success)';
        
        setTimeout(() => {
            copyBtn.innerHTML = originalText;
            copyBtn.style.background = '';
        }, 2000);
    }

    /**
     * Reset form for new paste
     */
    function resetForm() {
        pasteForm.reset();
        hideError();
        hideSuccess();
        updateCharCount();
        contentTextarea.focus();
        
        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    /**
     * Set loading state
     */
    function setLoading(isLoading) {
        const btnText = submitBtn.querySelector('.btn-text');
        const btnLoader = submitBtn.querySelector('.btn-loader');
        
        if (isLoading) {
            btnText.style.display = 'none';
            btnLoader.style.display = 'flex';
            submitBtn.disabled = true;
            contentTextarea.disabled = true;
            expirySelect.disabled = true;
        } else {
            btnText.style.display = 'inline';
            btnLoader.style.display = 'none';
            submitBtn.disabled = false;
            contentTextarea.disabled = false;
            expirySelect.disabled = false;
        }
    }

    /**
     * Show error message
     */
    function showError(message) {
        errorMessage.textContent = message;
        errorAlert.style.display = 'flex';
    }

    /**
     * Hide error message
     */
    function hideError() {
        errorAlert.style.display = 'none';
    }

    /**
     * Show success message
     */
    function showSuccess() {
        successAlert.style.display = 'flex';
    }

    /**
     * Hide success message
     */
    function hideSuccess() {
        successAlert.style.display = 'none';
    }

    /**
     * Format bytes to human-readable string
     */
    function formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
