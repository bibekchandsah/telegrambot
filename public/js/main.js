// ===========================
// MeetGrid Landing Page JavaScript
// ===========================

(function() {
    'use strict';

    // ===========================
    // Utility Functions
    // ===========================

    const $ = (selector) => document.querySelector(selector);
    const $$ = (selector) => document.querySelectorAll(selector);

    // Debounce function for performance
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // ===========================
    // Mobile Menu Toggle
    // ===========================

    function initMobileMenu() {
        const menuToggle = $('.mobile-menu-toggle');
        const navMenu = $('.nav-menu');

        if (!menuToggle || !navMenu) return;

        menuToggle.addEventListener('click', () => {
            navMenu.classList.toggle('active');
            const isExpanded = navMenu.classList.contains('active');
            menuToggle.setAttribute('aria-expanded', isExpanded);

            // Animate toggle button
            menuToggle.classList.toggle('active');
        });

        // Close menu when clicking on a link
        $$('.nav-menu a').forEach(link => {
            link.addEventListener('click', () => {
                navMenu.classList.remove('active');
                menuToggle.classList.remove('active');
                menuToggle.setAttribute('aria-expanded', 'false');
            });
        });

        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!navMenu.contains(e.target) && !menuToggle.contains(e.target)) {
                navMenu.classList.remove('active');
                menuToggle.classList.remove('active');
                menuToggle.setAttribute('aria-expanded', 'false');
            }
        });
    }

    // ===========================
    // Smooth Scroll
    // ===========================

    function initSmoothScroll() {
        $$('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function(e) {
                const href = this.getAttribute('href');
                
                // Skip if href is just "#"
                if (href === '#') return;

                const target = $(href);
                if (target) {
                    e.preventDefault();
                    const offset = 80; // Navbar height
                    const targetPosition = target.offsetTop - offset;

                    window.scrollTo({
                        top: targetPosition,
                        behavior: 'smooth'
                    });
                }
            });
        });
    }

    // ===========================
    // Animated Counter
    // ===========================

    function animateCounter(element, start, end, duration) {
        const range = end - start;
        const increment = range / (duration / 16); // 60 FPS
        let current = start;

        const timer = setInterval(() => {
            current += increment;
            if (current >= end) {
                current = end;
                clearInterval(timer);
            }
            
            // Format number with commas
            const formatted = Math.floor(current).toLocaleString();
            element.textContent = formatted;
        }, 16);
    }

    // ===========================
    // Intersection Observer for Animations
    // ===========================

    function initIntersectionObserver() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in-up');
                    
                    // Animate counters when they come into view
                    if (entry.target.hasAttribute('data-count')) {
                        const target = parseInt(entry.target.getAttribute('data-count'));
                        animateCounter(entry.target, 0, target, 2000);
                        entry.target.removeAttribute('data-count'); // Prevent re-animation
                    }
                    
                    observer.unobserve(entry.target);
                }
            });
        }, observerOptions);

        // Observe feature cards
        $$('.feature-card, .step, .stat-card, .faq-item').forEach(el => {
            observer.observe(el);
        });

        // Observe stat numbers
        $$('[data-count]').forEach(el => {
            observer.observe(el);
        });
    }

    // ===========================
    // FAQ Accordion
    // ===========================

    function initFAQ() {
        const faqItems = $$('.faq-item');

        faqItems.forEach(item => {
            const question = item.querySelector('.faq-question');
            
            question.addEventListener('click', () => {
                const isActive = item.classList.contains('active');
                
                // Close all other items
                faqItems.forEach(otherItem => {
                    if (otherItem !== item) {
                        otherItem.classList.remove('active');
                        otherItem.querySelector('.faq-question').setAttribute('aria-expanded', 'false');
                    }
                });
                
                // Toggle current item
                if (isActive) {
                    item.classList.remove('active');
                    question.setAttribute('aria-expanded', 'false');
                } else {
                    item.classList.add('active');
                    question.setAttribute('aria-expanded', 'true');
                }
            });
        });
    }

    // ===========================
    // Back to Top Button
    // ===========================

    function initBackToTop() {
        const backToTopButton = $('#back-to-top');
        if (!backToTopButton) return;

        const toggleBackToTop = () => {
            if (window.scrollY > 300) {
                backToTopButton.classList.add('visible');
            } else {
                backToTopButton.classList.remove('visible');
            }
        };

        // Check on scroll
        window.addEventListener('scroll', debounce(toggleBackToTop, 100));

        // Scroll to top on click
        backToTopButton.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });

        // Initial check
        toggleBackToTop();
    }

    // ===========================
    // Navbar Scroll Effect
    // ===========================

    function initNavbarScroll() {
        const navbar = $('.navbar');
        if (!navbar) return;

        const handleScroll = () => {
            if (window.scrollY > 50) {
                navbar.style.boxShadow = 'var(--shadow-md)';
                navbar.style.background = 'rgba(255, 255, 255, 0.98)';
            } else {
                navbar.style.boxShadow = 'var(--shadow-sm)';
                navbar.style.background = 'rgba(255, 255, 255, 0.95)';
            }
        };

        window.addEventListener('scroll', debounce(handleScroll, 50));
        handleScroll(); // Initial check
    }

    // ===========================
    // Track Analytics Events
    // ===========================

    function trackEvent(eventName, eventData = {}) {
        // Google Analytics 4
        if (typeof gtag === 'function') {
            gtag('event', eventName, eventData);
        }

        // Console log for development
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            console.log('Analytics Event:', eventName, eventData);
        }
    }

    // ===========================
    // Track CTA Clicks
    // ===========================

    function initCTATracking() {
        // Track all "Start Chatting" button clicks
        $$('a[href*="t.me"]').forEach(button => {
            button.addEventListener('click', (e) => {
                const buttonText = button.textContent.trim();
                const buttonLocation = button.closest('section')?.id || 'unknown';
                
                trackEvent('cta_click', {
                    button_text: buttonText,
                    button_location: buttonLocation,
                    destination: button.href
                });
            });
        });

        // Track navigation clicks
        $$('.nav-menu a').forEach(link => {
            link.addEventListener('click', (e) => {
                trackEvent('navigation_click', {
                    link_text: link.textContent.trim(),
                    destination: link.getAttribute('href')
                });
            });
        });

        // Track FAQ interactions
        $$('.faq-question').forEach(question => {
            question.addEventListener('click', () => {
                trackEvent('faq_interaction', {
                    question: question.textContent.trim()
                });
            });
        });
    }

    // ===========================
    // Lazy Load Images (if any)
    // ===========================

    function initLazyLoading() {
        const images = $$('img[data-src]');
        
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                        imageObserver.unobserve(img);
                    }
                });
            });

            images.forEach(img => imageObserver.observe(img));
        } else {
            // Fallback for older browsers
            images.forEach(img => {
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
            });
        }
    }

    // ===========================
    // Form Validation (if newsletter form exists)
    // ===========================

    function initFormValidation() {
        const forms = $$('form');
        
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                const emailInput = form.querySelector('input[type="email"]');
                
                if (emailInput && !emailInput.value.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
                    e.preventDefault();
                    alert('Please enter a valid email address');
                    emailInput.focus();
                    return false;
                }
                
                trackEvent('form_submission', {
                    form_id: form.id || 'unknown'
                });
            });
        });
    }

    // ===========================
    // Detect Telegram App
    // ===========================

    function detectTelegramApp() {
        // Check if opened in Telegram in-app browser
        const isTelegramApp = /Telegram/i.test(navigator.userAgent);
        
        if (isTelegramApp) {
            // Modify CTA buttons to open bot directly
            $$('a[href*="t.me"]').forEach(link => {
                const botUsername = link.href.match(/t\.me\/([^/?]+)/);
                if (botUsername && botUsername[1]) {
                    // Use tg:// protocol for better Telegram integration
                    link.addEventListener('click', (e) => {
                        e.preventDefault();
                        window.location.href = `tg://resolve?domain=${botUsername[1]}`;
                    });
                }
            });
            
            trackEvent('telegram_app_detected');
        }
    }

    // ===========================
    // Performance Monitoring
    // ===========================

    function monitorPerformance() {
        // Monitor page load time
        window.addEventListener('load', () => {
            if ('performance' in window) {
                const perfData = performance.timing;
                const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart;
                
                trackEvent('page_performance', {
                    load_time: pageLoadTime,
                    dom_ready: perfData.domContentLoadedEventEnd - perfData.navigationStart
                });
            }
        });
    }

    // ===========================
    // Add Preload for Critical Resources
    // ===========================

    function preloadCriticalResources() {
        // Preload hero image or other critical assets
        const criticalImages = [
            // Add paths to critical images if any
        ];

        criticalImages.forEach(src => {
            const link = document.createElement('link');
            link.rel = 'preload';
            link.as = 'image';
            link.href = src;
            document.head.appendChild(link);
        });
    }

    // ===========================
    // Handle Offline State
    // ===========================

    function initOfflineHandler() {
        window.addEventListener('offline', () => {
            const offlineNotice = document.createElement('div');
            offlineNotice.id = 'offline-notice';
            offlineNotice.style.cssText = `
                position: fixed;
                top: 80px;
                left: 50%;
                transform: translateX(-50%);
                background: #ef4444;
                color: white;
                padding: 1rem 2rem;
                border-radius: 0.5rem;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                z-index: 9999;
                font-weight: 600;
            `;
            offlineNotice.textContent = '⚠️ No internet connection';
            document.body.appendChild(offlineNotice);
        });

        window.addEventListener('online', () => {
            const offlineNotice = $('#offline-notice');
            if (offlineNotice) {
                offlineNotice.remove();
            }
        });
    }

    // ===========================
    // Initialize Typing Animation in Hero
    // ===========================

    function initTypingAnimation() {
        const typingIndicator = $('.typing-indicator');
        if (!typingIndicator) return;

        // Show/hide typing indicator periodically
        setInterval(() => {
            typingIndicator.style.opacity = typingIndicator.style.opacity === '0' ? '1' : '0';
        }, 5000);
    }

    // ===========================
    // Add Schema.org Breadcrumbs
    // ===========================

    function addBreadcrumbSchema() {
        const breadcrumbSchema = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": 1,
                    "name": "Home",
                    "item": window.location.origin
                }
            ]
        };

        const script = document.createElement('script');
        script.type = 'application/ld+json';
        script.text = JSON.stringify(breadcrumbSchema);
        document.head.appendChild(script);
    }

    // ===========================
    // Copy Bot Username on Click
    // ===========================

    function initCopyBotUsername() {
        const botLinks = $$('.step-description strong');
        
        botLinks.forEach(link => {
            if (link.textContent.includes('@')) {
                link.style.cursor = 'pointer';
                link.title = 'Click to copy';
                
                link.addEventListener('click', () => {
                    const text = link.textContent;
                    navigator.clipboard.writeText(text).then(() => {
                        const originalText = link.textContent;
                        link.textContent = '✓ Copied!';
                        setTimeout(() => {
                            link.textContent = originalText;
                        }, 2000);
                        
                        trackEvent('bot_username_copied', { username: text });
                    });
                });
            }
        });
    }

    // ===========================
    // Initialize All Features
    // ===========================

    function init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', init);
            return;
        }

        // Initialize all features
        initMobileMenu();
        initSmoothScroll();
        initIntersectionObserver();
        initFAQ();
        initBackToTop();
        initNavbarScroll();
        initCTATracking();
        initLazyLoading();
        initFormValidation();
        detectTelegramApp();
        monitorPerformance();
        preloadCriticalResources();
        initOfflineHandler();
        initTypingAnimation();
        addBreadcrumbSchema();
        initCopyBotUsername();

        // Track page view
        trackEvent('page_view', {
            page_title: document.title,
            page_path: window.location.pathname
        });

        console.log('🎭 MeetGrid landing page initialized successfully!');
    }

    // Start initialization
    init();

    // ===========================
    // Service Worker Registration (Optional)
    // ===========================

    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            // Uncomment to enable PWA features
            // navigator.serviceWorker.register('/sw.js')
            //     .then(reg => console.log('Service Worker registered'))
            //     .catch(err => console.log('Service Worker registration failed'));
        });
    }

})();
