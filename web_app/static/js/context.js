function updateTargetAudience(value) {
    const customInput = document.getElementById('target_audience');
    
    if (value === 'custom') {
        // Show the custom input field
        customInput.style.display = 'block';
        customInput.focus();
        customInput.value = '';
    } else {
        // Hide the custom input field and set its value to the selected option
        customInput.style.display = 'none';
        customInput.value = value;
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Check if there's a previously selected value
    const audienceSelect = document.getElementById('audience_select');
    const targetAudience = document.getElementById('target_audience');
    
    // If there's a value in the hidden input that doesn't match any option,
    // select "custom" and show the input
    const audienceValue = targetAudience.value;
    if (audienceValue) {
        let found = false;
        for (let i = 0; i < audienceSelect.options.length; i++) {
            if (audienceSelect.options[i].value === audienceValue) {
                audienceSelect.selectedIndex = i;
                found = true;
                break;
            }
        }
        
        if (!found && audienceValue !== '') {
            // Select the "custom" option
            for (let i = 0; i < audienceSelect.options.length; i++) {
                if (audienceSelect.options[i].value === 'custom') {
                    audienceSelect.selectedIndex = i;
                    break;
                }
            }
            // Show the custom input
            targetAudience.style.display = 'block';
        }
    }
    
    // Handle cancel button click
    const cancelBtn = document.getElementById('cancel-btn');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function() {
            window.location.href = INDEX_URL;
        });
    }
}); 