document.addEventListener('DOMContentLoaded', function() {
    // Navigation buttons
    document.getElementById('edit-script-btn').addEventListener('click', function() {
        window.location.href = EDIT_URL;
    });
    
    document.getElementById('previous-btn').addEventListener('click', function() {
        window.location.href = EDIT_URL;
    });
    
    // Generate shorts button
    const generateShortsBtn = document.getElementById('generate-shorts-btn');
    const generatedShortsContainer = document.getElementById('generated-shorts-container');
    
    generateShortsBtn.addEventListener('click', function() {
        // Show loading state
        this.disabled = true;
        this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Generating...';
        
        // Get options
        const shortsCount = document.getElementById('shorts_count').value;
        const shortsDuration = document.getElementById('shorts_duration').value;
        
        const shortsFocus = [];
        document.querySelectorAll('input[name="shorts_focus[]"]:checked').forEach(checkbox => {
            shortsFocus.push(checkbox.value);
        });
        
        // Simulate API call delay
        setTimeout(() => {
            // Generate shorts based on the edited script
            let shortsHTML = '';
            
            // Create the specified number of shorts
            for (let i = 0; i < shortsCount; i++) {
                const shortNumber = i + 1;
                
                // Generate a mock short script based on the duration
                let shortScript = '';
                let wordCount = 0;
                
                if (shortsDuration === '15') {
                    wordCount = '30-40';
                } else if (shortsDuration === '30') {
                    wordCount = '60-80';
                } else {
                    wordCount = '120-150';
                }
                
                // Create sections based on selected focus areas
                let hookSection = '';
                let teaserSection = '';
                let ctaSection = '';
                
                if (shortsFocus.includes('hook')) {
                    hookSection = `HOOK:
Did you know that ${TOPIC} can completely transform how you approach your content? You're about to discover why...`;
                }
                
                if (shortsFocus.includes('teaser')) {
                    teaserSection = `TEASER:
In my full video, I break down the ${shortNumber} essential strategies for mastering ${TOPIC}. Strategy #${shortNumber} is something most creators completely overlook!

I'll show you exactly how to implement these techniques for your ${TARGET_AUDIENCE}.`;
                }
                
                if (shortsFocus.includes('cta')) {
                    ctaSection = `CALL TO ACTION:
Want to learn all ${shortsCount} strategies? Check out my full video now - link in bio!`;
                }
                
                // Combine sections with appropriate spacing
                shortScript = [hookSection, teaserSection, ctaSection].filter(Boolean).join('\n\n');
                
                // Create card for this short
                shortsHTML += `
                <div class="card short-video-card mb-4">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5 class="mb-0">Short #${shortNumber} (${shortsDuration} seconds, ~${wordCount} words)</h5>
                        <button type="button" class="btn btn-sm btn-outline-primary copy-short-btn" data-short-id="${shortNumber}">
                            <i class="bi bi-clipboard"></i> Copy
                        </button>
                    </div>
                    <div class="card-body position-relative">
                        <div class="short-video-script" id="short-script-${shortNumber}">
                            ${shortScript.replace(/HOOK:/g, '<span class="hook-section">HOOK:</span>')
                                       .replace(/TEASER:/g, '<span class="teaser-section">TEASER:</span>')
                                       .replace(/CALL TO ACTION:/g, '<span class="cta-section">CALL TO ACTION:</span>')}
                        </div>
                        <input type="hidden" name="generated_shorts[]" value="${shortScript.replace(/"/g, '&quot;')}">
                    </div>
                </div>`;
            }
            
            // Update the container
            generatedShortsContainer.innerHTML = shortsHTML;
            
            // Add event listeners to copy buttons
            document.querySelectorAll('.copy-short-btn').forEach(button => {
                button.addEventListener('click', function() {
                    const shortId = this.getAttribute('data-short-id');
                    const scriptElement = document.getElementById(`short-script-${shortId}`);
                    
                    // Create a temporary textarea to copy the text
                    const textarea = document.createElement('textarea');
                    textarea.value = scriptElement.textContent.trim();
                    document.body.appendChild(textarea);
                    textarea.select();
                    document.execCommand('copy');
                    document.body.removeChild(textarea);
                    
                    // Change button text temporarily
                    const originalText = this.innerHTML;
                    this.innerHTML = '<i class="bi bi-check"></i> Copied!';
                    setTimeout(() => {
                        this.innerHTML = originalText;
                    }, 2000);
                });
            });
            
            // Reset button state
            this.disabled = false;
            this.innerHTML = '<i class="bi bi-magic"></i> Generate YouTube Shorts';
            
            // Show success message
            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert alert-success alert-dismissible fade show mt-3';
            alertDiv.innerHTML = `
                <i class="bi bi-check-circle-fill"></i> Successfully generated ${shortsCount} YouTube Shorts! Review them below.
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
            generatedShortsContainer.before(alertDiv);
            
            // Auto-dismiss alert after 5 seconds
            setTimeout(() => {
                // Check if Bootstrap is available
                if (typeof bootstrap !== 'undefined') {
                    const bsAlert = new bootstrap.Alert(alertDiv);
                    bsAlert.close();
                } else {
                    // Fallback if Bootstrap is not available
                    alertDiv.style.display = 'none';
                }
            }, 5000);
        }, 2000);
    });
}); 