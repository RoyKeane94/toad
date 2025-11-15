// Mobile Menu Toggle
function toggleMobileMenu() {
    const menu = document.getElementById('mobile-menu');
    menu.classList.toggle('hidden');
}

// Template Gallery Functionality
document.addEventListener('DOMContentLoaded', function() {
    // Only run template gallery code if we're on the templates page
    const templateGalleryContainer = document.getElementById('variation-tags-container');
    if (!templateGalleryContainer) return;

    // Template Data - Student-focused
    const templates = {
        generic: {
            title: 'Student Job Application Tracker',
            subtitle: 'Perfect for internships, graduate schemes, and part-time work.',
            headers: ['Company / Role', 'Research & Networking', 'Application Tasks', 'Next Steps'],
            rows: [
                {
                    company: 'Microsoft<br><i>Software Engineering Intern</i>',
                    tasks: [
                        [
                            { text: 'Research company culture', completed: true },
                            { text: 'Find LinkedIn connections', completed: false }
                        ],
                        [
                            { text: 'Submit online application', completed: true },
                            { text: 'Tailor CV for tech role', completed: false }
                        ],
                        [
                            { text: 'Prepare coding questions', completed: false },
                            { text: 'Practice behavioral interviews', completed: false }
                        ]
                    ]
                },
                {
                    company: 'Local Coffee Shop<br><i>Part-time Barista</i>',
                    tasks: [
                        [
                            { text: 'Visit location', completed: true },
                            { text: 'Speak to manager', completed: false }
                        ],
                        [
                            { text: 'Drop off CV in person', completed: false },
                            { text: 'Follow up after 1 week', completed: false }
                        ],
                        [
                            { text: 'Prepare for informal chat', completed: false },
                            { text: 'Confirm availability', completed: false }
                        ]
                    ]
                }
            ]
        },
        accounting: {
            title: 'Accounting Student Job Tracker',
            subtitle: 'Target the Big 4 and top accounting firms with this focused tracker.',
            headers: ['Firm / Programme', 'Deadlines & Research', 'Application Requirements', 'Interview Prep'],
            rows: [
                {
                    company: 'Deloitte<br><i>Summer Internship Programme</i>',
                    tasks: [
                        [
                            { text: 'Application deadline: Nov 30', completed: true },
                            { text: 'Research recent deals', completed: false }
                        ],
                        [
                            { text: 'Online application form', completed: false },
                            { text: 'Cover letter (500 words)', completed: false },
                            { text: 'Academic transcript', completed: true }
                        ],
                        [
                            { text: 'Numerical reasoning test', completed: false },
                            { text: 'Case study practice', completed: false }
                        ]
                    ]
                },
                {
                    company: 'PwC<br><i>Graduate Training Scheme</i>',
                    tasks: [
                        [
                            { text: 'Application deadline: Dec 15', completed: true },
                            { text: 'Attend virtual info session', completed: true }
                        ],
                        [
                            { text: 'Complete strengths assessment', completed: false },
                            { text: 'Upload CV and cover letter', completed: false }
                        ],
                        [
                            { text: 'Partner interview prep', completed: false },
                            { text: 'Technical accounting questions', completed: false }
                        ]
                    ]
                }
            ]
        },
        consulting: {
            title: 'Consulting Student Job Tracker',
            subtitle: 'Break into top consulting firms with structured preparation.',
            headers: ['Firm / Programme', 'Networking & Events', 'Application Process', 'Case Interview Prep'],
            rows: [
                {
                    company: 'McKinsey & Company<br><i>Summer Business Analyst</i>',
                    tasks: [
                        [
                            { text: 'Attend university presentation', completed: true },
                            { text: 'Connect with alumni on LinkedIn', completed: false }
                        ],
                        [
                            { text: 'Online application', completed: false },
                            { text: 'Academic transcript', completed: true }
                        ],
                        [
                            { text: 'Market sizing cases', completed: false },
                            { text: 'Profitability frameworks', completed: false }
                        ]
                    ]
                },
                {
                    company: 'Boston Consulting Group<br><i>Associate Intern</i>',
                    tasks: [
                        [
                            { text: 'BCG campus coffee chats', completed: true },
                            { text: 'Follow BCG on social media', completed: true }
                        ],
                        [
                            { text: 'CV and cover letter', completed: false },
                            { text: 'University grades', completed: true }
                        ],
                        [
                            { text: 'Framework practice', completed: false },
                            { text: 'Case competitions', completed: false }
                        ]
                    ]
                }
            ]
        },
        marketing: {
            title: 'Marketing Student Job Tracker',
            subtitle: 'Land internships and graduate roles in top marketing companies.',
            headers: ['Company / Role', 'Portfolio & Experience', 'Application Strategy', 'Interview Focus'],
            rows: [
                {
                    company: 'Unilever<br><i>Brand Management Intern</i>',
                    tasks: [
                        [
                            { text: 'Create portfolio of projects', completed: true },
                            { text: 'Include university campaigns', completed: false }
                        ],
                        [
                            { text: 'Future Leaders Programme', completed: false },
                            { text: 'Research Unilever brands', completed: true }
                        ],
                        [
                            { text: 'Brand strategy questions', completed: false },
                            { text: 'Consumer insights', completed: false }
                        ]
                    ]
                },
                {
                    company: 'Google<br><i>Marketing Intern</i>',
                    tasks: [
                        [
                            { text: 'Build digital portfolio', completed: true },
                            { text: 'Show data analytics skills', completed: false }
                        ],
                        [
                            { text: 'Online application', completed: false },
                            { text: 'Academic transcript', completed: true }
                        ],
                        [
                            { text: 'Digital marketing trends', completed: false },
                            { text: 'Analytics understanding', completed: false }
                        ]
                    ]
                }
            ]
        }
    };

    // DOM Elements
    const previewContainer = document.getElementById('template-preview-container');
    const previewTitle = document.getElementById('preview-title');
    const previewSubtitle = document.getElementById('preview-subtitle');
    const tagsContainer = document.getElementById('variation-tags-container');

    // Helper function to create task HTML
    function createTaskHTML(task, taskId) {
        return `
            <div class="group flex items-center justify-between w-full p-2 rounded-lg hover:bg-[var(--grid-header-bg)] transition-all duration-200"
                 data-task-id="${taskId}"
                 id="task-${taskId}">
                <div class="flex items-center space-x-3 min-w-0 flex-1">
                    <div class="flex-shrink-0">
                        <input type="checkbox" 
                               id="checkbox-${taskId}"
                               name="completed" 
                               ${task.completed ? 'checked' : ''}
                               disabled
                               class="w-4 h-4 rounded border-gray-300 text-[var(--primary-action-bg)] focus:ring-[var(--primary-action-bg)] cursor-pointer ${task.completed ? 'checkbox-completed' : ''}">
                    </div>
                    <div id="task-text-${taskId}" class="text-sm task-text ${task.completed ? 'task-completed-strikethrough' : ''} leading-relaxed">${task.text}</div>
                </div>
            </div>`;
    }

    // Functions
    function renderPreview(templateKey) {
        const template = templates[templateKey];
        if (!template) return;

        // Update titles
        previewTitle.textContent = template.title;
        previewSubtitle.textContent = template.subtitle;

        // Check if mobile view
        const isMobile = window.innerWidth < 768;

        // Build table HTML matching project grid structure exactly, with mobile optimizations
        let tableHTML = `
            <div class="grid-with-controls" style="background: var(--container-bg);">
                <div class="grid-container-wrapper" style="display: flex;">
                    <!-- Fixed Category Column -->
                    <div class="grid-table-fixed-col">
                        <table class="grid-table-fixed">
                            <colgroup>
                                <col class="category-column" style="width: ${isMobile ? '140px' : '300px'};">
                            </colgroup>
                            <thead>
                                <tr>
                                    <th class="p-2 md:p-4" style="background-color: var(--container-bg) !important;"></th>
                                </tr>
                            </thead>
                            <tbody>`;
        
        // Add row headers (company names) in the fixed column
        template.rows.forEach(row => {
            tableHTML += `
                                <tr>
                                    <td class="p-2 md:p-4">
                                        <div class="flex items-center justify-between">
                                            <span class="text-green-600 font-semibold truncate text-xs md:text-sm">${row.company}</span>
                                        </div>
                                    </td>
                                </tr>`;
        });

        tableHTML += `
                            </tbody>
                        </table>
                    </div>
                    
                    <!-- Scrollable Data Columns -->
                    <div class="grid-table-scrollable" style="overflow-x: auto;">
                        <table class="grid-table" data-total-data-columns="${template.headers.length - 1}">
                            <colgroup>`;
        
        // Add column definitions (skip first header as it's in the fixed column) - ensuring consistent widths
        for (let i = 1; i < template.headers.length; i++) {
            tableHTML += `<col class="data-column" style="width: ${isMobile ? '200px' : '280px'};">`;
        }
        
        tableHTML += `
                            </colgroup>
                            <thead>
                                <tr>`;
        
        // Add column headers (skip first header as it's in the fixed column)
        for (let i = 1; i < template.headers.length; i++) {
            tableHTML += `
                                    <th class="p-2 md:p-4 font-medium" style="background-color: var(--container-bg) !important;">
                                        <div class="flex items-center justify-between">
                                            <span class="text-green-600 font-semibold truncate text-xs md:text-sm">${template.headers[i]}</span>
                                        </div>
                                    </th>`;
        }
        
        tableHTML += `
                                </tr>
                            </thead>
                            <tbody>`;
        
        // Add data rows (skip first column as it's in the fixed column)
        template.rows.forEach((row, rowIndex) => {
            tableHTML += '<tr>';
            for (let i = 1; i < template.headers.length; i++) {
                const cellTasks = row.tasks[i - 1] || [];
                let tasksHTML = '';
                
                cellTasks.forEach((task, taskIndex) => {
                    const taskId = `template-${templateKey}-${rowIndex}-${i}-${taskIndex}`;
                    tasksHTML += createTaskHTML(task, taskId);
                });

                tableHTML += `
                                <td class="relative" style="min-height: ${isMobile ? '140px' : '180px'}; vertical-align: top;">
                                    <div class="space-y-2 pb-12 md:pb-16 p-1 md:p-2" style="min-height: calc(100% - ${isMobile ? '40px' : '60px'});">
                                        ${tasksHTML}
                                    </div>
                                    <div class="absolute bottom-2 md:bottom-3 left-2 md:left-3 right-2 md:right-3 pt-2 md:pt-3 border-t border-[var(--border-color)]/30 bg-[var(--container-bg)]" style="height: ${isMobile ? '40px' : '60px'}; display: flex; align-items: center;">
                                        <div class="w-full">
                                            <button type="button" class="w-full text-left py-1.5 md:py-2 px-2 md:px-3 text-[var(--primary-action-bg)] hover:text-[var(--primary-action-hover-bg)] hover:bg-[var(--grid-header-bg)] transition-all duration-200 text-xs md:text-sm cursor-pointer rounded-md" style="height: ${isMobile ? '28px' : '36px'};">
                                                <i class="fas fa-plus text-xs mr-1 md:mr-2"></i>Add task...
                                            </button>
                                        </div>
                                    </div>
                                </td>`;
            }
            tableHTML += '</tr>';
        });

        tableHTML += `
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>`;

        // Smooth update with fade effect
        previewContainer.classList.add('fade-out');
        setTimeout(() => {
            previewContainer.innerHTML = tableHTML;
            previewContainer.classList.remove('fade-out');
        }, 150);
    }

    function handleTagClick(event) {
        const clickedTag = event.target;
        if (!clickedTag.classList.contains('variation-tag')) return;

        // Update active state on tags
        tagsContainer.querySelectorAll('.variation-tag').forEach(tag => {
            tag.classList.remove('active');
            tag.classList.remove('bg-[var(--primary-action-bg)]', 'text-[var(--primary-action-text)]');
            tag.classList.add('bg-[var(--grid-header-bg)]', 'text-[var(--text-secondary)]');
        });
        
        clickedTag.classList.add('active');
        clickedTag.classList.remove('bg-[var(--grid-header-bg)]', 'text-[var(--text-secondary)]');
        clickedTag.classList.add('bg-[var(--primary-action-bg)]', 'text-[var(--primary-action-text)]');

        // Render the corresponding template
        const templateKey = clickedTag.dataset.template;
        renderPreview(templateKey);
    }

    // Re-render on resize for mobile optimization
    let resizeTimeout;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(function() {
            const activeTag = tagsContainer.querySelector('.variation-tag.active');
            if (activeTag) {
                renderPreview(activeTag.dataset.template);
            }
        }, 250);
    });

    // Initialize template gallery
    if (tagsContainer && previewContainer && previewTitle && previewSubtitle) {
        // Add event listener
        tagsContainer.addEventListener('click', handleTagClick);
        
        // Initial render of the generic template
        renderPreview('generic');
    }
    

    
    // === Contact Page Functionality ===
    // Handle form submission success
    document.body.addEventListener('htmx:afterSwap', function(event) {
        if (event.detail.target.querySelector('.success-message')) {
            // Scroll to top of form
            event.detail.target.scrollIntoView({ behavior: 'smooth' });
        }
    });
    
    // === Privacy Policy Page Functionality ===
    // Scroll to top button
    const scrollToTopBtn = document.getElementById('scrollToTop');
    
    if (scrollToTopBtn) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 300) {
                scrollToTopBtn.classList.remove('opacity-0', 'invisible');
                scrollToTopBtn.classList.add('opacity-100', 'visible');
            } else {
                scrollToTopBtn.classList.add('opacity-0', 'invisible');
                scrollToTopBtn.classList.remove('opacity-100', 'visible');
            }
        });
        
        scrollToTopBtn.addEventListener('click', function() {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }
    
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
    
    // === Home Page Animations ===
    // Only run home page animations if we're on the home page
    const logoContainer = document.getElementById('logo-container');
    const headlineContainer = document.getElementById('headline-container');
    const typewriterText = document.getElementById('typewriter-text');
    
    if (logoContainer && headlineContainer && typewriterText) {
        console.log('Home page animations found, starting...');
        
        // Reset initial states
        logoContainer.style.opacity = '0';
        headlineContainer.style.opacity = '0';
        
        // Logo animation
        setTimeout(() => {
            logoContainer.style.opacity = '1';
            logoContainer.style.transform = 'scale(1) translateY(0)';
            logoContainer.style.transition = 'opacity 1.2s ease-out, transform 1.2s ease-out';
        }, 100);

        // Headline animation
        setTimeout(() => {
            headlineContainer.style.opacity = '1';
            headlineContainer.style.transform = 'scale(1) translateY(0)';
            headlineContainer.style.transition = 'opacity 1.2s ease-out, transform 1.2s ease-out';
        }, 700);

        // Typewriter effect
        const text = typewriterText.textContent;
        typewriterText.textContent = '';
        typewriterText.style.width = '0';
        typewriterText.style.overflow = 'hidden';
        typewriterText.style.whiteSpace = 'nowrap';
        
        setTimeout(() => {
            let i = 0;
            const typeInterval = setInterval(() => {
                if (i < text.length) {
                    typewriterText.textContent += text.charAt(i);
                    i++;
                } else {
                    clearInterval(typeInterval);
                }
            }, 50);
        }, 1400);
    }
    // Wedding landing page helpers
    const weddingPage = document.querySelector('[data-page="tw-weddings"]');
    if (weddingPage) {
        document.body.classList.add('tw-weddings-page');
    }

    const twAnimateEls = document.querySelectorAll('[data-tw-animate]');
    if (twAnimateEls.length) {
        twAnimateEls.forEach(el => el.classList.add('tw-animate-init'));
        const observer = new IntersectionObserver((entries, obs) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('tw-animate-in');
                    obs.unobserve(entry.target);
                }
            });
        }, { threshold: 0.2 });

        twAnimateEls.forEach(el => observer.observe(el));
    }
});
