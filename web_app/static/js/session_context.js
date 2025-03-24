document.addEventListener('DOMContentLoaded', function() {
    // Initialize collapsible sections for session context
    const collapsibleHeaders = document.querySelectorAll('.collapsible-section .card-header[data-bs-toggle="collapse"]');
    
    collapsibleHeaders.forEach(header => {
        const icon = header.querySelector('.collapse-icon');
        const targetId = header.getAttribute('data-bs-target');
        const targetElement = document.querySelector(targetId);
        
        // Set initial state
        if (targetElement && targetElement.classList.contains('show')) {
            icon.classList.remove('bi-chevron-down');
            icon.classList.add('bi-chevron-up');
        }
        
        header.addEventListener('click', function(e) {
            // Don't toggle if they clicked on the edit button
            if (e.target.closest('.btn')) {
                return;
            }
            
            // Toggle the collapse state using Bootstrap's collapse functionality
            const bsCollapse = new bootstrap.Collapse(targetElement, {
                toggle: true
            });
            
            // Toggle the icon
            if (icon) {
                icon.classList.toggle('bi-chevron-down');
                icon.classList.toggle('bi-chevron-up');
            }
        });
    });
}); 