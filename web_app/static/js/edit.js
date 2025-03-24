document.addEventListener('DOMContentLoaded', function() {
    // Master Select All functionality
    const selectAllOptions = document.getElementById('select-all-options');
    const selectAllCheckboxes = document.querySelectorAll('.select-all');
    const scriptCheckboxes = document.querySelectorAll('.script-enhancements');
    const visualCheckboxes = document.querySelectorAll('.visual-elements');
    
    // Set up Select All options for the master checkbox
    selectAllOptions.addEventListener('change', function() {
        const isChecked = this.checked;
        
        // Update all checkboxes in both groups
        document.querySelectorAll('.script-enhancements, .visual-elements').forEach(cb => {
            cb.checked = isChecked;
        });
        
        // Also update the group select-all checkboxes
        selectAllCheckboxes.forEach(cb => {
            cb.checked = isChecked;
        });
    });
    
    // Set up event listeners for group Select All checkboxes
    selectAllCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const group = this.dataset.group;
            const isChecked = this.checked;
            
            // Update all checkboxes in this group
            document.querySelectorAll(`.${group}`).forEach(cb => {
                cb.checked = isChecked;
            });
            
            // Update the master checkbox
            updateMasterSelectAll();
        });
    });
    
    // Add event listeners to all individual checkboxes to update their group's Select All
    scriptCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            updateGroupSelectAll('select-all-script', 'script-enhancements');
            updateMasterSelectAll();
        });
    });
    
    visualCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            updateGroupSelectAll('select-all-visual', 'visual-elements');
            updateMasterSelectAll();
        });
    });
    
    // Function to update a group's Select All checkbox state
    function updateGroupSelectAll(selectAllId, groupClass) {
        const selectAll = document.getElementById(selectAllId);
        const groupCheckboxes = document.querySelectorAll(`.${groupClass}`);
        const allChecked = Array.from(groupCheckboxes).every(cb => cb.checked);
        
        selectAll.checked = allChecked;
    }
    
    // Function to update the master Select All checkbox state
    function updateMasterSelectAll() {
        const allCheckboxes = document.querySelectorAll('.script-enhancements, .visual-elements');
        const allChecked = Array.from(allCheckboxes).every(cb => cb.checked);
        
        selectAllOptions.checked = allChecked;
    }
    
    // Initialize all Select All checkboxes on page load
    function initializeSelectAll() {
        updateGroupSelectAll('select-all-script', 'script-enhancements');
        updateGroupSelectAll('select-all-visual', 'visual-elements');
        updateMasterSelectAll();
    }
    
    // Run initialization
    initializeSelectAll();
    
    // Navigation buttons
    document.getElementById('edit-script-btn').addEventListener('click', function(event) {
        event.preventDefault();
        event.stopPropagation();
        
        // Navigate to the script page
        window.location.href = SCRIPT_URL;
    });
    
    document.getElementById('edit-context-btn').addEventListener('click', function(event) {
        event.preventDefault();
        event.stopPropagation();
        
        // Navigate to the context page
        window.location.href = CONTEXT_URL;
    });
    
    document.getElementById('edit-plan-btn').addEventListener('click', function(event) {
        event.preventDefault();
        event.stopPropagation();
        
        // Navigate to the plan page
        window.location.href = PLAN_URL;
    });
    
    // Previous button handler
    document.getElementById('previous-btn').addEventListener('click', function(event) {
        event.preventDefault();
        event.stopPropagation();
        
        // Navigate to the script page
        window.location.href = SCRIPT_URL;
    });
    
    // Form submission handler - ensure edited_script has content
    document.querySelector('form').addEventListener('submit', function(event) {
        // Only process for the actual form submission (Next button)
        // Skip if the event was triggered by other buttons
        if (event.submitter && event.submitter.id !== 'previous-btn' && event.submitter.id !== 'generate-edit-btn') {
            const editedScriptTextarea = document.getElementById('edited_script');
            
            // Make the textarea visible
            editedScriptTextarea.classList.remove('d-none');
            
            // If the textarea is empty, populate it with the original script content
            if (!editedScriptTextarea.value.trim()) {
                // The original script content is passed from the Flask template
                editedScriptTextarea.value = ORIGINAL_SCRIPT;
                console.log("Auto-populated edited script with original content");
            }
        }
    });
    
    // Handle collapsible sections
    const collapsibleHeaders = document.querySelectorAll('.collapsible-section .card-header');
    
    collapsibleHeaders.forEach(header => {
        const icon = header.querySelector('.collapse-icon');
        const targetId = header.getAttribute('data-bs-target');
        const targetElement = document.querySelector(targetId);
        
        header.addEventListener('click', function(e) {
            // Don't toggle if they clicked on the edit button
            if (e.target.closest('.btn')) {
                return;
            }
            
            // Toggle the collapse state
            const bsCollapse = new bootstrap.Collapse(targetElement, {
                toggle: true
            });
            
            // Toggle the icon rotation
            if (icon) {
                icon.classList.toggle('collapsed');
            }
        });
    });
    
    // Generate edited script button
    document.getElementById('generate-edit-btn').addEventListener('click', function(event) {
        event.preventDefault();
        event.stopPropagation();
        
        // Show loading state
        const button = this;
        const originalText = button.innerHTML;
        button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Generating...';
        button.disabled = true;
        
        // Get all selected editing options
        const editOptions = [];
        const checkboxes = document.querySelectorAll('input[name="edit_options[]"]:checked');
        checkboxes.forEach(checkbox => {
            editOptions.push(checkbox.value);
        });
        
        // Get additional instructions
        const additionalInstructions = document.getElementById('additional_instructions').value;
        
        // Call the API to edit the script
        fetch(EDIT_SCRIPT_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                edit_options: editOptions,
                additional_instructions: additionalInstructions
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            console.log("API Response:", data);
            
            // Update the hidden textarea with the edited script
            const editedScriptTextarea = document.getElementById('edited_script');
            editedScriptTextarea.value = data.edited_script;
            
            // Update the preview
            const editedScriptContainer = document.getElementById('edited-script-container');
            editedScriptContainer.innerHTML = '';
            
            // Process the edited script to add formatting
            const sections = data.edited_script.split(/\*\*\[(.*?)\]\*\*/g);
            console.log("Parsed sections:", sections);
            
            // Only process if we have valid sections
            if (sections.length > 1) {
                for (let i = 1; i < sections.length; i += 2) {
                    const sectionTitle = sections[i];
                    let sectionContent = '';
                    
                    if (i+1 < sections.length) {
                        sectionContent = sections[i+1].trim();
                    }
                    
                    console.log("Section", i, "Title:", sectionTitle);
                    console.log("Section", i, "Content length:", sectionContent ? sectionContent.length : 0);
                    
                    // Create section title
                    const titleElement = document.createElement('h5');
                    titleElement.className = 'section-title';
                    titleElement.textContent = sectionTitle;
                    editedScriptContainer.appendChild(titleElement);
                    
                    // Create section content
                    const contentElement = document.createElement('div');
                    contentElement.className = 'section-content';
                    
                    // Format special elements (scene descriptions, visual cues, etc.)
                    const formattedContent = formatSpecialElements(sectionContent);
                    contentElement.innerHTML = formattedContent;
                    
                    editedScriptContainer.appendChild(contentElement);
                }
            } else {
                // If no sections found, just display the entire content
                console.log("No sections found, displaying raw content");
                const contentElement = document.createElement('div');
                contentElement.className = 'section-content';
                contentElement.innerHTML = formatSpecialElements(data.edited_script);
                editedScriptContainer.appendChild(contentElement);
            }
            
            // Make the edited script visible
            document.getElementById('edited-script-section').classList.remove('d-none');
            
            // Reset button
            button.innerHTML = originalText;
            button.disabled = false;
            
            // Scroll to the edited script section
            document.getElementById('edited-script-section').scrollIntoView({ behavior: 'smooth' });
        })
        .catch(error => {
            console.error('Error editing script:', error);
            
            // Show error message
            alert(`Error editing script: ${error.message}`);
            
            // Reset button
            button.innerHTML = originalText;
            button.disabled = false;
        });
    });
    
    // Function to format special elements in the script
    function formatSpecialElements(content) {
        if (!content) return '';
        
        // Handle escaped newlines
        content = content.replace(/\\n/g, '\n');
        
        // Replace scene descriptions [SCENE: description]
        content = content.replace(/\[SCENE\s*:\s*(.*?)\]/g, '<div class="scene-description"><i class="bi bi-camera"></i> $1</div>');
        
        // Replace visual cues [VISUAL: description]
        content = content.replace(/\[VISUAL\s*:\s*(.*?)\]/g, '<div class="visual-cue"><i class="bi bi-eye"></i> $1</div>');
        
        // Replace camera cuts [CUT TO: description]
        content = content.replace(/\[CUT TO\s*:\s*(.*?)\]/g, '<div class="camera-cut"><i class="bi bi-scissors"></i> $1</div>');
        
        // Replace B-roll suggestions [B-ROLL: description]
        content = content.replace(/\[B-ROLL\s*:\s*(.*?)\]/g, '<div class="b-roll"><i class="bi bi-film"></i> $1</div>');
        
        // Replace graphics suggestions [GRAPHIC: description]
        content = content.replace(/\[GRAPHIC\s*:\s*(.*?)\]/g, '<div class="on-screen-text"><i class="bi bi-text-left"></i> $1</div>');
        
        // Format paragraphs with proper handling of special elements
        const paragraphs = content.split('\n');
        let formattedContent = '';
        
        paragraphs.forEach(paragraph => {
            if (paragraph.trim()) {
                // Check if paragraph already has HTML formatting
                if (paragraph.includes('<div class="')) {
                    formattedContent += paragraph + '\n';
                } else {
                    formattedContent += '<p>' + paragraph + '</p>\n';
                }
            } else {
                formattedContent += '<br>\n';
            }
        });
        
        return formattedContent;
    }
}); 