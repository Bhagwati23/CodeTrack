/**
 * CodeTrack Pro - Main JavaScript File
 * Handles UI interactions, animations, and common functionality
 */

// =============================================================================
// GLOBAL VARIABLES AND UTILITIES
// =============================================================================

const CodeTrack = {
    // Configuration
    config: {
        apiBaseUrl: '/api',
        animationDuration: 300,
        debounceDelay: 300,
        notificationCheckInterval: 30000
    },
    
    // State management
    state: {
        currentTheme: localStorage.getItem('theme') || 'dark',
        notifications: [],
        activeSessions: new Map(),
        isOnline: navigator.onLine
    },
    
    // Utility functions
    utils: {
        // Debounce function
        debounce(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },
        
        // Throttle function
        throttle(func, limit) {
            let inThrottle;
            return function() {
                const args = arguments;
                const context = this;
                if (!inThrottle) {
                    func.apply(context, args);
                    inThrottle = true;
                    setTimeout(() => inThrottle = false, limit);
                }
            };
        },
        
        // Format date
        formatDate(date) {
            return new Date(date).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        },
        
        // Format time ago
        timeAgo(date) {
            const now = new Date();
            const diff = now - new Date(date);
            const seconds = Math.floor(diff / 1000);
            const minutes = Math.floor(seconds / 60);
            const hours = Math.floor(minutes / 60);
            const days = Math.floor(hours / 24);
            
            if (days > 0) return `${days}d ago`;
            if (hours > 0) return `${hours}h ago`;
            if (minutes > 0) return `${minutes}m ago`;
            return 'Just now';
        },
        
        // Copy to clipboard
        async copyToClipboard(text) {
            try {
                await navigator.clipboard.writeText(text);
                return true;
            } catch (err) {
                console.error('Failed to copy text: ', err);
                return false;
            }
        },
        
        // Show toast notification
        showToast(message, type = 'info', duration = 3000) {
            const toast = document.createElement('div');
            toast.className = `toast toast-${type}`;
            toast.innerHTML = `
                <div class="toast-content">
                    <i class="fas fa-${this.getToastIcon(type)}"></i>
                    <span>${message}</span>
                </div>
                <button class="toast-close" onclick="this.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            `;
            
            document.body.appendChild(toast);
            
            // Show toast
            setTimeout(() => toast.classList.add('show'), 100);
            
            // Auto remove
            setTimeout(() => {
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 300);
            }, duration);
        },
        
        // Get toast icon based on type
        getToastIcon(type) {
            const icons = {
                success: 'check-circle',
                error: 'exclamation-circle',
                warning: 'exclamation-triangle',
                info: 'info-circle'
            };
            return icons[type] || 'info-circle';
        },
        
        // Generate random ID
        generateId() {
            return Math.random().toString(36).substr(2, 9);
        },
        
        // Validate email
        isValidEmail(email) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return emailRegex.test(email);
        },
        
        // Validate username
        isValidUsername(username) {
            const usernameRegex = /^[a-zA-Z0-9_]{3,20}$/;
            return usernameRegex.test(username);
        }
    }
};

// =============================================================================
// THEME MANAGEMENT
// =============================================================================

const ThemeManager = {
    init() {
        this.applyTheme(CodeTrack.state.currentTheme);
        this.setupThemeToggle();
    },
    
    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        CodeTrack.state.currentTheme = theme;
        localStorage.setItem('theme', theme);
        
        // Update theme icon
        const themeIcon = document.getElementById('theme-icon');
        if (themeIcon) {
            themeIcon.className = theme === 'dark' ? 'fas fa-moon' : 'fas fa-sun';
        }
    },
    
    toggleTheme() {
        const newTheme = CodeTrack.state.currentTheme === 'dark' ? 'light' : 'dark';
        this.applyTheme(newTheme);
        
        // Animate theme transition
        document.body.style.transition = 'background-color 0.3s ease';
        setTimeout(() => {
            document.body.style.transition = '';
        }, 300);
    },
    
    setupThemeToggle() {
        const themeButton = document.querySelector('[onclick*="toggleTheme"]');
        if (themeButton) {
            themeButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleTheme();
            });
        }
    }
};

// =============================================================================
// NOTIFICATION SYSTEM
// =============================================================================

const NotificationManager = {
    init() {
        this.setupNotificationDropdown();
        this.startPeriodicCheck();
    },
    
    setupNotificationDropdown() {
        const notificationButton = document.querySelector('[onclick*="notificationDropdown"]');
        const dropdown = document.getElementById('notificationDropdown');
        
        if (notificationButton && dropdown) {
            notificationButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleDropdown(dropdown);
            });
        }
    },
    
    toggleDropdown(dropdown) {
        const isVisible = dropdown.classList.contains('show');
        
        // Close all dropdowns
        document.querySelectorAll('.dropdown-menu').forEach(menu => {
            menu.classList.remove('show');
        });
        
        // Toggle current dropdown
        if (!isVisible) {
            dropdown.classList.add('show');
            this.loadNotifications();
        }
    },
    
    async loadNotifications() {
        try {
            const response = await fetch('/dashboard/notifications?limit=5');
            const data = await response.json();
            
            if (data.notifications) {
                this.renderNotifications(data.notifications);
            }
        } catch (error) {
            console.error('Error loading notifications:', error);
        }
    },
    
    renderNotifications(notifications) {
        const container = document.getElementById('notification-list');
        if (!container) return;
        
        if (notifications.length === 0) {
            container.innerHTML = `
                <div class="text-center p-3">
                    <p class="text-secondary mb-0">No notifications</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = notifications.map(notification => `
            <div class="notification-item ${notification.is_read ? '' : 'unread'}" 
                 onclick="NotificationManager.markAsRead(${notification.id})">
                <div class="notification-content">
                    <h6 class="notification-title">${notification.title}</h6>
                    <p class="notification-message">${notification.message}</p>
                    <small class="notification-time">${CodeTrack.utils.timeAgo(notification.created_at)}</small>
                </div>
                ${!notification.is_read ? '<div class="notification-dot"></div>' : ''}
            </div>
        `).join('');
    },
    
    async markAsRead(notificationId) {
        try {
            await fetch('/dashboard/mark_notification_read', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ notification_id: notificationId })
            });
            
            // Update UI
            const notificationItem = document.querySelector(`[onclick*="${notificationId}"]`);
            if (notificationItem) {
                notificationItem.classList.add('read');
                notificationItem.querySelector('.notification-dot')?.remove();
            }
            
            // Update unread count
            this.updateUnreadCount();
        } catch (error) {
            console.error('Error marking notification as read:', error);
        }
    },
    
    updateUnreadCount() {
        const badge = document.querySelector('.navbar .badge');
        const unreadCount = document.querySelectorAll('.notification-item.unread').length;
        
        if (badge) {
            if (unreadCount > 0) {
                badge.textContent = unreadCount;
                badge.style.display = 'flex';
            } else {
                badge.style.display = 'none';
            }
        }
    },
    
    startPeriodicCheck() {
        setInterval(() => {
            this.loadNotifications();
        }, CodeTrack.config.notificationCheckInterval);
    }
};

// =============================================================================
// CODE EDITOR FUNCTIONALITY
// =============================================================================

const CodeEditor = {
    init() {
        this.setupSyntaxHighlighting();
        this.setupAutoComplete();
        this.setupCodeExecution();
    },
    
    setupSyntaxHighlighting() {
        // Simple syntax highlighting for code blocks
        document.querySelectorAll('pre code').forEach(block => {
            this.highlightCode(block);
        });
    },
    
    highlightCode(block) {
        // Basic syntax highlighting implementation
        const code = block.textContent;
        const highlighted = code
            .replace(/\b(function|const|let|var|if|else|for|while|return|class|import|export)\b/g, 
                    '<span class="keyword">$1</span>')
            .replace(/\b(\d+)\b/g, '<span class="number">$1</span>')
            .replace(/(".*?"|'.*?')/g, '<span class="string">$1</span>')
            .replace(/(\/\/.*$)/gm, '<span class="comment">$1</span>');
        
        block.innerHTML = highlighted;
    },
    
    setupAutoComplete() {
        // Auto-complete functionality for code editors
        const codeTextareas = document.querySelectorAll('.code-textarea');
        codeTextareas.forEach(textarea => {
            this.setupAutoCompleteForElement(textarea);
        });
    },
    
    setupAutoCompleteForElement(textarea) {
        // Basic auto-complete implementation
        textarea.addEventListener('input', CodeTrack.utils.debounce((e) => {
            const cursorPos = e.target.selectionStart;
            const text = e.target.value;
            const lineStart = text.lastIndexOf('\n', cursorPos - 1) + 1;
            const currentLine = text.substring(lineStart, cursorPos);
            
            // Simple bracket completion
            if (currentLine.endsWith('{')) {
                this.insertAtCursor(textarea, '}');
            } else if (currentLine.endsWith('[')) {
                this.insertAtCursor(textarea, ']');
            } else if (currentLine.endsWith('(')) {
                this.insertAtCursor(textarea, ')');
            }
        }, 100));
    },
    
    insertAtCursor(textarea, text) {
        const cursorPos = textarea.selectionStart;
        const textBefore = textarea.value.substring(0, cursorPos);
        const textAfter = textarea.value.substring(cursorPos);
        
        textarea.value = textBefore + text + textAfter;
        textarea.selectionStart = textarea.selectionEnd = cursorPos + text.length;
    },
    
    setupCodeExecution() {
        // Code execution functionality
        const executeButtons = document.querySelectorAll('[data-execute-code]');
        executeButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                this.executeCode(e.target);
            });
        });
    },
    
    async executeCode(button) {
        const container = button.closest('.code-editor');
        const codeTextarea = container.querySelector('.code-textarea');
        const outputDiv = container.querySelector('.code-output');
        const language = container.dataset.language || 'python';
        
        if (!codeTextarea || !outputDiv) return;
        
        // Show loading state
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Executing...';
        outputDiv.innerHTML = '<div class="loading"></div>';
        
        try {
            const response = await fetch('/contest/submit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    code: codeTextarea.value,
                    language: language,
                    problem_id: container.dataset.problemId
                })
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                outputDiv.innerHTML = `
                    <div class="execution-result success">
                        <h6><i class="fas fa-check-circle"></i> Execution Successful</h6>
                        <pre>${result.output || 'No output'}</pre>
                    </div>
                `;
            } else {
                outputDiv.innerHTML = `
                    <div class="execution-result error">
                        <h6><i class="fas fa-exclamation-circle"></i> Execution Failed</h6>
                        <pre>${result.error || 'Unknown error'}</pre>
                    </div>
                `;
            }
        } catch (error) {
            outputDiv.innerHTML = `
                <div class="execution-result error">
                    <h6><i class="fas fa-exclamation-circle"></i> Network Error</h6>
                    <pre>Failed to execute code: ${error.message}</pre>
                </div>
            `;
        } finally {
            // Reset button
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-play"></i> Execute';
        }
    }
};

// =============================================================================
// CHART FUNCTIONALITY
// =============================================================================

const ChartManager = {
    charts: new Map(),
    
    init() {
        this.setupResponsiveCharts();
        this.setupChartThemes();
    },
    
    setupResponsiveCharts() {
        // Make charts responsive
        window.addEventListener('resize', CodeTrack.utils.debounce(() => {
            this.charts.forEach(chart => {
                chart.resize();
            });
        }, 250));
    },
    
    setupChartThemes() {
        // Set up chart theme based on current theme
        Chart.defaults.color = CodeTrack.state.currentTheme === 'dark' ? '#ffffff' : '#1a202c';
        Chart.defaults.borderColor = CodeTrack.state.currentTheme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
    },
    
    createProgressChart(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;
        
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels || [],
                datasets: data.datasets || []
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: CodeTrack.state.currentTheme === 'dark' ? '#ffffff' : '#1a202c',
                            usePointStyle: true
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            color: CodeTrack.state.currentTheme === 'dark' ? '#b3b3b3' : '#4a5568'
                        },
                        grid: {
                            color: CodeTrack.state.currentTheme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)'
                        }
                    },
                    y: {
                        ticks: {
                            color: CodeTrack.state.currentTheme === 'dark' ? '#b3b3b3' : '#4a5568'
                        },
                        grid: {
                            color: CodeTrack.state.currentTheme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)'
                        }
                    }
                }
            }
        });
        
        this.charts.set(canvasId, chart);
        return chart;
    }
};

// =============================================================================
// FORM VALIDATION
// =============================================================================

const FormValidator = {
    init() {
        this.setupRealTimeValidation();
        this.setupFormSubmission();
    },
    
    setupRealTimeValidation() {
        // Real-time validation for forms
        document.querySelectorAll('form').forEach(form => {
            const inputs = form.querySelectorAll('input, textarea, select');
            inputs.forEach(input => {
                input.addEventListener('blur', () => {
                    this.validateField(input);
                });
                
                input.addEventListener('input', CodeTrack.utils.debounce(() => {
                    this.validateField(input);
                }, 300));
            });
        });
    },
    
    validateField(field) {
        const value = field.value.trim();
        const fieldName = field.name || field.id;
        const fieldType = field.type;
        
        // Remove existing validation classes
        field.classList.remove('is-valid', 'is-invalid');
        
        // Remove existing feedback
        const existingFeedback = field.parentNode.querySelector('.invalid-feedback, .valid-feedback');
        if (existingFeedback) {
            existingFeedback.remove();
        }
        
        let isValid = true;
        let errorMessage = '';
        
        // Required field validation
        if (field.hasAttribute('required') && !value) {
            isValid = false;
            errorMessage = `${this.getFieldLabel(field)} is required.`;
        }
        
        // Email validation
        if (fieldType === 'email' && value && !CodeTrack.utils.isValidEmail(value)) {
            isValid = false;
            errorMessage = 'Please enter a valid email address.';
        }
        
        // Username validation
        if (fieldName === 'username' && value && !CodeTrack.utils.isValidUsername(value)) {
            isValid = false;
            errorMessage = 'Username must be 3-20 characters, letters, numbers, and underscores only.';
        }
        
        // Password validation
        if (fieldName === 'password' && value && value.length < 8) {
            isValid = false;
            errorMessage = 'Password must be at least 8 characters long.';
        }
        
        // Password confirmation validation
        if (fieldName === 'confirm_password' && value) {
            const passwordField = document.querySelector('[name="password"]');
            if (passwordField && value !== passwordField.value) {
                isValid = false;
                errorMessage = 'Passwords do not match.';
            }
        }
        
        // Apply validation result
        if (isValid && value) {
            field.classList.add('is-valid');
        } else if (!isValid) {
            field.classList.add('is-invalid');
            this.showFieldError(field, errorMessage);
        }
        
        return isValid;
    },
    
    getFieldLabel(field) {
        const label = field.parentNode.querySelector('label');
        return label ? label.textContent.replace('*', '').trim() : field.name || field.id;
    },
    
    showFieldError(field, message) {
        const feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        feedback.textContent = message;
        field.parentNode.appendChild(feedback);
    },
    
    setupFormSubmission() {
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', (e) => {
                if (!this.validateForm(form)) {
                    e.preventDefault();
                }
            });
        });
    },
    
    validateForm(form) {
        const inputs = form.querySelectorAll('input, textarea, select');
        let isValid = true;
        
        inputs.forEach(input => {
            if (!this.validateField(input)) {
                isValid = false;
            }
        });
        
        return isValid;
    }
};

// =============================================================================
// ANIMATION UTILITIES
// =============================================================================

const AnimationManager = {
    init() {
        this.setupScrollAnimations();
        this.setupHoverEffects();
    },
    
    setupScrollAnimations() {
        // Intersection Observer for scroll animations
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-fadeIn');
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });
        
        // Observe elements with animation classes
        document.querySelectorAll('.animate-on-scroll').forEach(el => {
            observer.observe(el);
        });
    },
    
    setupHoverEffects() {
        // Enhanced hover effects for interactive elements
        document.querySelectorAll('.hover-lift').forEach(element => {
            element.addEventListener('mouseenter', () => {
                element.style.transform = 'translateY(-4px)';
            });
            
            element.addEventListener('mouseleave', () => {
                element.style.transform = 'translateY(0)';
            });
        });
    }
};

// =============================================================================
// INITIALIZATION
// =============================================================================

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all managers
    ThemeManager.init();
    NotificationManager.init();
    CodeEditor.init();
    ChartManager.init();
    FormValidator.init();
    AnimationManager.init();
    
    // Setup global event listeners
    setupGlobalEventListeners();
    
    // Initialize any page-specific functionality
    initializePageSpecific();
    
    console.log('CodeTrack Pro initialized successfully!');
});

function setupGlobalEventListeners() {
    // Close dropdowns when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.dropdown')) {
            document.querySelectorAll('.dropdown-menu').forEach(menu => {
                menu.classList.remove('show');
            });
        }
    });
    
    // Handle online/offline status
    window.addEventListener('online', () => {
        CodeTrack.state.isOnline = true;
        CodeTrack.utils.showToast('Connection restored', 'success');
    });
    
    window.addEventListener('offline', () => {
        CodeTrack.state.isOnline = false;
        CodeTrack.utils.showToast('Connection lost', 'warning');
    });
    
    // Handle window scroll for navbar
    window.addEventListener('scroll', CodeTrack.utils.throttle(() => {
        const navbar = document.getElementById('navbar');
        if (navbar) {
            if (window.scrollY > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        }
    }, 100));
}

function initializePageSpecific() {
    // Initialize page-specific functionality based on current page
    const body = document.body;
    
    if (body.classList.contains('dashboard-page')) {
        initializeDashboard();
    } else if (body.classList.contains('contest-page')) {
        initializeContest();
    } else if (body.classList.contains('ai-tutor-page')) {
        initializeAITutor();
    }
}

function initializeDashboard() {
    // Dashboard-specific initialization
    console.log('Dashboard initialized');
}

function initializeContest() {
    // Contest-specific initialization
    console.log('Contest page initialized');
}

function initializeAITutor() {
    // AI Tutor-specific initialization
    console.log('AI Tutor page initialized');
}

// =============================================================================
// GLOBAL FUNCTIONS (for backward compatibility)
// =============================================================================

function toggleTheme() {
    ThemeManager.toggleTheme();
}

function toggleDropdown(dropdownId) {
    const dropdown = document.getElementById(dropdownId);
    if (dropdown) {
        NotificationManager.toggleDropdown(dropdown);
    }
}

function toggleMobileMenu() {
    const menu = document.getElementById('mobileMenu');
    if (menu) {
        menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
    }
}

function copyToClipboard(text) {
    CodeTrack.utils.copyToClipboard(text).then(success => {
        if (success) {
            CodeTrack.utils.showToast('Copied to clipboard!', 'success');
        } else {
            CodeTrack.utils.showToast('Failed to copy', 'error');
        }
    });
}

// Export for use in other scripts
window.CodeTrack = CodeTrack;
window.NotificationManager = NotificationManager;
window.CodeEditor = CodeEditor;
window.ChartManager = ChartManager;
