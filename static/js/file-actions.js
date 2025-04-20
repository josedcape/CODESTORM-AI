// Codestorm-Assistant - File Actions JavaScript
// These functions handle file creation, editing, and deletion

// Define fileActions object in the global scope
window.fileActions = {};

document.addEventListener('DOMContentLoaded', function() {
    // Add file action buttons to the file explorer
    window.fileActions.addFileActionButtons = function() {
        const fileExplorer = document.getElementById('file-explorer');
        if (!fileExplorer) return;
        
        // Get the directory header
        const directoryHeader = document.getElementById('file-explorer-header');
        if (!directoryHeader) return;
        
        // Clear any existing buttons
        const existingButtons = directoryHeader.querySelector('.file-actions');
        if (existingButtons) {
            existingButtons.remove();
        }
        
        // Create container for buttons
        const container = document.createElement('div');
        container.className = 'file-actions d-flex mt-2 mb-2';
        
        // New File button
        const newFileBtn = document.createElement('button');
        newFileBtn.className = 'btn btn-sm btn-outline-primary me-2';
        newFileBtn.innerHTML = '<i class="bi bi-file-earmark-plus"></i> Nuevo archivo';
        newFileBtn.addEventListener('click', () => createNewFile());
        
        // New Folder button
        const newFolderBtn = document.createElement('button');
        newFolderBtn.className = 'btn btn-sm btn-outline-secondary';
        newFolderBtn.innerHTML = '<i class="bi bi-folder-plus"></i> Nueva carpeta';
        newFolderBtn.addEventListener('click', () => createNewFolder());
        
        // Add buttons to container
        container.appendChild(newFileBtn);
        container.appendChild(newFolderBtn);
        
        // Add container to header
        directoryHeader.appendChild(container);
    }
    
    // Create a new file
    function createNewFile() {
        const fileName = prompt('Nombre del archivo:');
        if (!fileName || fileName.trim() === '') return;
        
        const currentDirectory = document.getElementById('directory-path')?.textContent || '/';
        const path = currentDirectory === '/' 
            ? fileName 
            : `${currentDirectory.replace(/^\//, '')}/${fileName}`;
            
        fetch('/api/create_file', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                file_path: path,
                content: ''
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Error del servidor: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                showNotification(data.error, 'danger');
                return;
            }
            
            showNotification('Archivo creado correctamente', 'success');
            
            // Redirect to edit the new file
            window.location.href = `/edit/${path}`;
        })
        .catch(error => {
            console.error('Error creating file:', error);
            showNotification('Error al crear archivo: ' + error.message, 'danger');
        });
    }
    
    // Create a new folder
    function createNewFolder() {
        const folderName = prompt('Nombre de la carpeta:');
        if (!folderName || folderName.trim() === '') return;
        
        const currentDirectory = document.getElementById('directory-path')?.textContent || '/';
        const path = currentDirectory === '/' 
            ? folderName 
            : `${currentDirectory.replace(/^\//, '')}/${folderName}`;
            
        fetch('/api/create_file', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                file_path: `${path}/.keep`,
                content: ''
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Error del servidor: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                showNotification(data.error, 'danger');
                return;
            }
            
            showNotification('Carpeta creada correctamente', 'success');
            
            // Refresh file explorer by reloading the page
            window.location.reload();
        })
        .catch(error => {
            console.error('Error creating folder:', error);
            showNotification('Error al crear carpeta: ' + error.message, 'danger');
        });
    }
    
    // Delete a file or folder
    function deleteFileOrFolder(path) {
        if (!confirm('¿Estás seguro de que quieres eliminar este elemento?')) {
            return;
        }
        
        fetch('/api/delete_file', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                file_path: path
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Error del servidor: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                showNotification(data.error, 'danger');
                return;
            }
            
            showNotification('Elemento eliminado correctamente', 'success');
            
            // Refresh file explorer
            window.location.reload();
        })
        .catch(error => {
            console.error('Error deleting file:', error);
            showNotification('Error al eliminar: ' + error.message, 'danger');
        });
    }
    
    // Show notification
    function showNotification(message, type = 'info') {
        const container = document.getElementById('notifications');
        if (!container) return;
        
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show`;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        container.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 5000);
    }
    
    // Add file action buttons on page load
    addFileActionButtons();
    
    // Add file context menu to file items
    function addFileContextMenu() {
        const fileItems = document.querySelectorAll('.file-item');
        
        fileItems.forEach(item => {
            // Right-click context menu
            item.addEventListener('contextmenu', function(e) {
                e.preventDefault();
                
                // Get file name and path
                const fileNameElem = item.querySelector('span');
                if (!fileNameElem) return; // Safety check
                
                const fileName = fileNameElem.textContent;
                const dirPathElem = document.getElementById('directory-path');
                const currentDirectory = dirPathElem ? dirPathElem.textContent : '/';
                const isDirectory = item.classList.contains('directory');
                
                // Don't add context menu for parent directory
                if (fileName === '..') return;
                
                const filePath = currentDirectory === '/' 
                    ? fileName 
                    : `${currentDirectory.replace(/^\//, '')}/${fileName}`;
                
                // Create context menu
                const contextMenu = document.createElement('div');
                contextMenu.className = 'file-context-menu';
                contextMenu.style.position = 'absolute';
                contextMenu.style.top = `${e.pageY}px`;
                contextMenu.style.left = `${e.pageX}px`;
                contextMenu.style.backgroundColor = '#212529';
                contextMenu.style.border = '1px solid #495057';
                contextMenu.style.borderRadius = '4px';
                contextMenu.style.padding = '0.5rem 0';
                contextMenu.style.zIndex = '1000';
                
                // Add menu items
                if (!isDirectory) {
                    const editItem = document.createElement('div');
                    editItem.className = 'context-menu-item';
                    editItem.innerHTML = '<i class="bi bi-pencil me-2"></i> Editar';
                    editItem.style.padding = '0.5rem 1rem';
                    editItem.style.cursor = 'pointer';
                    editItem.style.hoverBackgroundColor = '#343a40';
                    editItem.addEventListener('click', () => {
                        window.location.href = `/edit/${filePath}`;
                    });
                    contextMenu.appendChild(editItem);
                }
                
                const deleteItem = document.createElement('div');
                deleteItem.className = 'context-menu-item';
                deleteItem.innerHTML = '<i class="bi bi-trash me-2"></i> Eliminar';
                deleteItem.style.padding = '0.5rem 1rem';
                deleteItem.style.cursor = 'pointer';
                deleteItem.style.color = '#dc3545';
                deleteItem.addEventListener('click', () => {
                    deleteFileOrFolder(filePath);
                });
                contextMenu.appendChild(deleteItem);
                
                // Add context menu to document
                document.body.appendChild(contextMenu);
                
                // Remove context menu when clicked outside
                document.addEventListener('click', function removeMenu() {
                    contextMenu.remove();
                    document.removeEventListener('click', removeMenu);
                });
            });
        });
    }
    
    // Call addFileContextMenu when file explorer is updated
    // This needs to be called after the file list is rendered
    const fileExplorer = document.getElementById('file-explorer');
    if (fileExplorer) {
        // Use a MutationObserver to detect when file explorer content changes
        const observer = new MutationObserver(function(mutations) {
            addFileContextMenu();
        });
        
        observer.observe(fileExplorer, { childList: true });
    }
    
    // Export functions to global scope if they need to be called from other scripts
    window.fileActions.createNewFile = createNewFile;
    window.fileActions.createNewFolder = createNewFolder;
    window.fileActions.deleteFileOrFolder = deleteFileOrFolder;
    window.fileActions.showNotification = showNotification;
    
    // Automatically add file action buttons
    setTimeout(() => {
        if (window.fileActions && typeof window.fileActions.addFileActionButtons === 'function') {
            window.fileActions.addFileActionButtons();
        }
    }, 500);
});