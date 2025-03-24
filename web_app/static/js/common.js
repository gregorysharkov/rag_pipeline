// Common JavaScript functions for the YouTube Script Generator

// Add custom validation for forms
document.addEventListener('DOMContentLoaded', function() {
    'use strict';
    
    // Fetch all forms that need validation
    var forms = document.querySelectorAll('.needs-validation');
    
    // Loop and prevent submission
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
    
    // Monitor character counts for textareas with max-chars data attribute
    const textAreas = document.querySelectorAll('textarea[data-max-chars]');
    textAreas.forEach(textarea => {
        const maxChars = parseInt(textarea.getAttribute('data-max-chars'));
        const counterId = textarea.id + '-counter';
        const counter = document.getElementById(counterId);
        
        if (counter) {
            textarea.addEventListener('input', function() {
                const remaining = maxChars - this.value.length;
                counter.textContent = remaining + ' characters remaining';
                
                // Add visual feedback when approaching or exceeding limit
                if (remaining < 0) {
                    counter.classList.add('text-danger');
                    counter.classList.remove('text-warning', 'text-muted');
                } else if (remaining < 50) {
                    counter.classList.add('text-warning');
                    counter.classList.remove('text-danger', 'text-muted');
                } else {
                    counter.classList.add('text-muted');
                    counter.classList.remove('text-danger', 'text-warning');
                }
            });
        }
    });
}); 