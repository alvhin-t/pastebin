/**
 * Paste View Page JavaScript
 * Handles copying content, raw view, and time formatting
 */

(function() {
    'use strict';

    // DOM Elements
    const copyContentBtn = document.getElementById('copyContentBtn');
    const rawBtn = document.getElementById('rawBtn');
    const pasteContent = document.getElementById('pasteContent');
    const expiryTime = document.getElementById('expiryTime');
    const copyToast = document.getElementById('copyToast');

    /**
     * Initialize view page
     */
    function init() {
        setupEventListeners();
        formatExpiryTime();
        enableKeyboardShortcuts();
    }

    /**
     * Set up event listeners
     */
    function setupEventListeners() {
        if (copyContentBtn) {
            copyContentBtn.addEventListener('click', handleCopyContent);
        }

        if (rawBtn) {
            rawBtn.addEventListener('click', handleRawView);
        }
    }

    /**
     * Handle copying paste content to clipboard
     */
    async function handleCopyContent() {
        const content = pasteContent.textContent;

        try {
            // Use modern Clipboard API
            if (navigator.clipboard && navigator.clipboard.writeText) {
                await navigator.clipboard.writeText(content);
                showToast('Copied to clipboard!');
            } else {
                // Fallback for older browsers
                copyToClipboardFallback(content);
                showToast('Copied to clipboard!');
            }
        } catch (error) {
            console.error('Error copying to clipboard:', error);
            showToast('Failed to copy. Please select and copy manually.', true);
        }
    }

    /**
     * Fallback method for copying to clipboard
     */
    function copyToClipboardFallback(text) {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.left = '-9999px';
        document.body.appendChild(textarea);
        textarea.select();
        
        try {
            document.execCommand('copy');
        } finally {
            document.body.removeChild(textarea);
        }
    }

    /**
     * Handle raw view button
     */
    function handleRawView() {
        const content = pasteContent.textContent;
        
        // Create a blob with the content
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        
        // Open in new tab
        window.open(url, '_blank');
        
        // Clean up the URL after a short delay
        setTimeout(() => URL.revokeObjectURL(url), 100);
    }

    /**
     * Format the expiry time to be more readable
     */
    function formatExpiryTime() {
        if (!expiryTime) return;

        const expiryText = expiryTime.textContent.trim();
        
        try {
            const expiryDate = new Date(expiryText);
            
            // Format as relative time if recent, otherwise absolute
            const now = new Date();
            const diffMs = expiryDate - now;
            const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
            const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
            const diffMinutes = Math.floor(diffMs / (1000 * 60));

            let formattedTime;

            if (diffMs < 0) {
                formattedTime = 'Expired';
            } else if (diffMinutes < 60) {
                formattedTime = `${diffMinutes} minute${diffMinutes !== 1 ? 's' : ''}`;
            } else if (diffHours < 24) {
                formattedTime = `${diffHours} hour${diffHours !== 1 ? 's' : ''}`;
            } else if (diffDays < 7) {
                formattedTime = `${diffDays} day${diffDays !== 1 ? 's' : ''}`;
            } else if (diffDays < 30) {
                const weeks = Math.floor(diffDays / 7);
                formattedTime = `${weeks} week${weeks !== 1 ? 's' : ''}`;
            } else if (diffDays < 365) {
                const months = Math.floor(diffDays / 30);
                formattedTime = `${months} month${months !== 1 ? 's' : ''}`;
            } else {
                const years = Math.floor(diffDays / 365);
                formattedTime = `${years} year${years !== 1 ? 's' : ''}`;
            }

            // Set the formatted time with tooltip showing exact date
            expiryTime.textContent = formattedTime;
            expiryTime.title = expiryDate.toLocaleString();
            
            // Add datetime attribute for semantic HTML
            expiryTime.setAttribute('datetime', expiryDate.toISOString());

        } catch (error) {
            console.error('Error formatting expiry time:', error);
        }
    }

    /**
     * Show toast notification
     */
    function showToast(message, isError = false) {
        if (!copyToast) return;

        const toastText = copyToast.querySelector('span');
        if (toastText) {
            toastText.textContent = message;
        }

        // Change color for errors
        if (isError) {
            copyToast.style.background = 'var(--error)';
        } else {
            copyToast.style.background = 'var(--text-primary)';
        }

        // Show toast
        copyToast.style.display = 'flex';

        // Hide after 3 seconds
        setTimeout(() => {
            copyToast.style.display = 'none';
        }, 3000);
    }

    /**
     * Enable keyboard shortcuts
     */
    function enableKeyboardShortcuts() {
        document.addEventListener('keydown', function(e) {
            // Ctrl/Cmd + C: Copy content
            if ((e.ctrlKey || e.metaKey) && e.key === 'c' && !window.getSelection().toString()) {
                e.preventDefault();
                handleCopyContent();
            }

            // Ctrl/Cmd + R: Raw view
            if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
                e.preventDefault();
                handleRawView();
            }
        });
    }

    /**
     * Add syntax highlighting hint based on content
     * (Future enhancement - could integrate highlight.js or similar)
     */
    function detectContentType() {
        if (!pasteContent) return;

        const content = pasteContent.textContent;
        
        // Simple detection patterns
        const patterns = {
            python: /^(import |from |def |class |if __name__)/m,
            javascript: /^(const |let |var |function |import |export )/m,
            json: /^\s*[\{\[]/,
            html: /^<!DOCTYPE html|^<html/i,
            css: /^[\w\-]+\s*\{/m,
            sql: /^(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP)/im
        };

        for (const [lang, pattern] of Object.entries(patterns)) {
            if (pattern.test(content)) {
                pasteContent.dataset.language = lang;
                break;
            }
        }
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
