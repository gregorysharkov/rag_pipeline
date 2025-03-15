// Main JavaScript file for YouTube Script Generator

document.addEventListener('DOMContentLoaded', function() {
    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
    
    // Character counter for textareas
    const textareas = document.querySelectorAll('textarea[data-max-chars]');
    
    textareas.forEach(textarea => {
        const maxChars = parseInt(textarea.getAttribute('data-max-chars'));
        const counterElement = document.getElementById(`${textarea.id}-counter`);
        
        if (counterElement) {
            textarea.addEventListener('input', () => {
                const remaining = maxChars - textarea.value.length;
                counterElement.textContent = `${remaining} characters remaining`;
                
                if (remaining < 0) {
                    counterElement.classList.add('text-danger');
                } else {
                    counterElement.classList.remove('text-danger');
                }
            });
            
            // Initial count
            const remaining = maxChars - textarea.value.length;
            counterElement.textContent = `${remaining} characters remaining`;
        }
    });
}); 