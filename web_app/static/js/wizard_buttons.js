document.addEventListener('DOMContentLoaded', function() {
    // Previous button handler - navigate to previous step
    const previousBtn = document.getElementById('previous-btn');
    if (previousBtn) {
        previousBtn.addEventListener('click', function(event) {
            event.preventDefault();
            // The PREVIOUS_URL will be set by the template
            if (typeof PREVIOUS_URL !== 'undefined') {
                window.location.href = PREVIOUS_URL;
            }
        });
    }
    
    // The next button should submit the form by default
    // If it's not inside a form, use the NEXT_URL to navigate
    const nextBtn = document.getElementById('next-btn');
    if (nextBtn && !nextBtn.closest('form')) {
        nextBtn.addEventListener('click', function(event) {
            event.preventDefault();
            // The NEXT_URL will be set by the template
            if (typeof NEXT_URL !== 'undefined') {
                window.location.href = NEXT_URL;
            }
        });
    }
}); 