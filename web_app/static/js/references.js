document.addEventListener('DOMContentLoaded', function() {
    // Navigation buttons
    document.getElementById('edit-context-btn').addEventListener('click', function() {
        window.location.href = CONTEXT_URL;
    });
    
    document.getElementById('previous-btn').addEventListener('click', function() {
        window.location.href = CONTEXT_URL;
    });
    
    // Web links functionality
    const webLinksContainer = document.getElementById('web-links-container');
    const addWebLinkButton = document.getElementById('add-web-link');
    
    // Add new web link fields
    addWebLinkButton.addEventListener('click', function() {
        const newLinkItem = document.createElement('div');
        newLinkItem.className = 'web-link-item mb-3';
        
        newLinkItem.innerHTML = `
            <div class="row g-2">
                <div class="col-md-8">
                    <input type="url" class="form-control" name="web_links[]" placeholder="https://example.com">
                </div>
                <div class="col-md-3">
                    <input type="text" class="form-control" name="web_link_descriptions[]" placeholder="Brief description">
                </div>
                <div class="col-md-1">
                    <button type="button" class="btn btn-outline-danger remove-link">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </div>
        `;
        webLinksContainer.appendChild(newLinkItem);
        
        // Show the first remove button if it was hidden
        const removeButtons = document.querySelectorAll('.remove-link');
        if (removeButtons.length > 1) {
            removeButtons.forEach(button => {
                button.style.display = 'block';
            });
        }
    });
    
    // Remove web link fields
    webLinksContainer.addEventListener('click', function(e) {
        if (e.target.closest('.remove-link')) {
            const linkItem = e.target.closest('.web-link-item');
            linkItem.remove();
            
            // Hide the remove button if only one link remains
            const removeButtons = document.querySelectorAll('.remove-link');
            if (removeButtons.length === 1) {
                removeButtons[0].style.display = 'none';
            }
        }
    });
    
    // Enhanced file upload functionality
    const fileInput = document.getElementById('reference_files');
    const uploadArea = document.getElementById('upload-area');
    const browseFiles = document.getElementById('browse-files');
    const filePreviewContainer = document.getElementById('file-preview-container');
    const filePreviewList = document.getElementById('file-preview-list');
    const filesToRemoveInput = document.getElementById('files-to-remove');
    const maxFileSize = 10 * 1024 * 1024; // 10MB
    const maxFiles = 5;
    
    // Click on browse files text - prevent default behavior
    browseFiles.addEventListener('click', function(e) {
        e.preventDefault(); // Prevent default behavior
        e.stopPropagation(); // Stop event propagation
        fileInput.click();
    });
    
    // Click on upload area - prevent default behavior
    uploadArea.addEventListener('click', function(e) {
        e.preventDefault(); // Prevent default behavior
        e.stopPropagation(); // Stop event propagation
        fileInput.click();
    });
    
    // Drag and drop functionality
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight() {
        uploadArea.classList.add('dragover');
    }
    
    function unhighlight() {
        uploadArea.classList.remove('dragover');
    }
    
    // Handle dropped files
    uploadArea.addEventListener('drop', function(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    });
    
    // Handle selected files
    fileInput.addEventListener('change', function() {
        handleFiles(this.files);
    });
    
    function handleFiles(files) {
        if (files.length > maxFiles) {
            alert(`You can upload a maximum of ${maxFiles} files.`);
            fileInput.value = '';
            return;
        }
        
        let validFiles = true;
        
        // Check each file
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            const fileExt = file.name.split('.').pop().toLowerCase();
            
            // Check file type
            if (!['pdf', 'doc', 'docx', 'jpg', 'png', 'jpeg'].includes(fileExt)) {
                alert(`File "${file.name}" is not a supported format. Please upload PDF, Word or image documents only.`);
                validFiles = false;
                break;
            }
            
            // Check file size
            if (file.size > maxFileSize) {
                alert(`File "${file.name}" exceeds the maximum file size of 10MB.`);
                validFiles = false;
                break;
            }
        }
        
        if (!validFiles) {
            fileInput.value = '';
            return;
        }
        
        // Display file previews
        filePreviewList.innerHTML = '';
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            const fileExt = file.name.split('.').pop().toLowerCase();
            const fileItem = document.createElement('div');
            fileItem.className = 'list-group-item file-preview-item';
            
            let iconClass = 'bi-file-earmark-text';
            if (fileExt === 'pdf') {
                iconClass = 'bi-file-earmark-pdf';
            } else if (['doc', 'docx'].includes(fileExt)) {
                iconClass = 'bi-file-earmark-word';
            } else if (['jpg', 'jpeg', 'png'].includes(fileExt)) {
                iconClass = 'bi-file-earmark-image';
            }
            
            fileItem.innerHTML = `
                <div>
                    <i class="bi ${iconClass} me-2"></i>
                    <span>${file.name}</span>
                </div>
                <button type="button" class="btn btn-sm btn-outline-danger remove-preview-file" data-index="${i}">
                    <i class="bi bi-x-lg"></i>
                </button>
            `;
            filePreviewList.appendChild(fileItem);
        }
        
        if (files.length > 0) {
            filePreviewContainer.classList.remove('d-none');
        } else {
            filePreviewContainer.classList.add('d-none');
        }
    }
    
    // Remove file from preview
    filePreviewList.addEventListener('click', function(e) {
        if (e.target.closest('.remove-preview-file')) {
            const button = e.target.closest('.remove-preview-file');
            const index = button.getAttribute('data-index');
            
            // Create a new FileList without the removed file
            const dt = new DataTransfer();
            const files = fileInput.files;
            
            for (let i = 0; i < files.length; i++) {
                if (i != index) {
                    dt.items.add(files[i]);
                }
            }
            
            fileInput.files = dt.files;
            
            // Update preview
            handleFiles(fileInput.files);
        }
    });
    
    // Remove already uploaded file
    const uploadedFilesList = document.getElementById('uploaded-files-list');
    if (uploadedFilesList) {
        uploadedFilesList.addEventListener('click', function(e) {
            if (e.target.closest('.remove-file')) {
                const button = e.target.closest('.remove-file');
                const filename = button.getAttribute('data-filename');
                const fileItem = button.closest('.file-item');
                
                // Add to the list of files to remove
                const currentFilesToRemove = filesToRemoveInput.value ? 
                    filesToRemoveInput.value.split(',') : [];
                currentFilesToRemove.push(filename);
                filesToRemoveInput.value = currentFilesToRemove.join(',');
                
                // Hide the file item (will be removed on form submit)
                fileItem.style.display = 'none';
            }
        });
    }
}); 