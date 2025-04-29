/**
 * File Actions - Gestión de archivos optimizada
 * Incluye operaciones CRUD y caché para mejor rendimiento
 */

(function() {
    // Caché de archivos para mejorar rendimiento entre navegaciones
    const fileCache = {
        directories: {},
        settings: {
            enabled: true,
            ttl: 300000 // Time to live: 5 minutos en milisegundos
        },
        set: function(path, data) {
            if (!this.settings.enabled) return;
            
            this.directories[path] = {
                data: data,
                timestamp: Date.now()
            };
            
            // Guardar en sessionStorage para persistencia entre recargas
            try {
                sessionStorage.setItem('fileCache', JSON.stringify(this.directories));
            } catch (e) {
                console.warn('No se pudo guardar la caché en sessionStorage:', e);
            }
        },
        get: function(path) {
            if (!this.settings.enabled) return null;
            
            const cached = this.directories[path];
            if (!cached) return null;
            
            // Verificar si la caché expiró
            if (Date.now() - cached.timestamp > this.settings.ttl) {
                delete this.directories[path];
                return null;
            }
            
            return cached.data;
        },
        clear: function() {
            this.directories = {};
            try {
                sessionStorage.removeItem('fileCache');
            } catch (e) {
                console.warn('No se pudo limpiar la caché en sessionStorage:', e);
            }
        },
        init: function() {
            // Cargar caché desde sessionStorage
            try {
                const storedCache = sessionStorage.getItem('fileCache');
                if (storedCache) {
                    this.directories = JSON.parse(storedCache);
                }
            } catch (e) {
                console.warn('Error al cargar caché desde sessionStorage:', e);
            }
        }
    };
    
    // Inicializar caché
    fileCache.init();
    
    // Módulo principal de acciones de archivos
    const fileActions = {
        // Crear un nuevo archivo
        createNewFile: function() {
            // Obtener la ruta actual
            const currentDirectory = document.getElementById('directory-path').textContent || '/';
            
            // Preguntar por el nombre del archivo
            const fileName = prompt('Ingrese el nombre del nuevo archivo:');
            if (!fileName) return; // Cancelado
            
            // Construir ruta completa
            const filePath = currentDirectory === '/' ? fileName : `${currentDirectory}/${fileName}`;
            
            // Validaciones básicas
            if (fileName.trim() === '') {
                this.showNotification('El nombre del archivo no puede estar vacío', 'danger');
                return;
            }
            
            // Crear archivo en el servidor
            fetch('/api/create_file', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    file_path: filePath,
                    content: '',
                    is_directory: false
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
                    this.showNotification(data.error, 'danger');
                    return;
                }
                
                this.showNotification('Archivo creado exitosamente', 'success');
                
                // Invalidar caché para esta ruta
                fileCache.clear();
                
                // Redirigir al editor
                window.location.href = `/edit/${filePath}`;
            })
            .catch(error => {
                console.error('Error al crear archivo:', error);
                this.showNotification('Error al crear archivo: ' + error.message, 'danger');
            });
        },
        
        // Crear una nueva carpeta
        createNewFolder: function() {
            // Obtener la ruta actual
            const currentDirectory = document.getElementById('directory-path').textContent || '/';
            
            // Preguntar por el nombre de la carpeta
            const folderName = prompt('Ingrese el nombre de la nueva carpeta:');
            if (!folderName) return; // Cancelado
            
            // Validaciones básicas
            if (folderName.trim() === '') {
                this.showNotification('El nombre de la carpeta no puede estar vacío', 'danger');
                return;
            }
            
            // Construir ruta completa
            const folderPath = currentDirectory === '/' ? folderName : `${currentDirectory}/${folderName}`;
            
            // Crear carpeta en el servidor
            fetch('/api/create_file', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    file_path: folderPath,
                    is_directory: true
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
                    this.showNotification(data.error, 'danger');
                    return;
                }
                
                this.showNotification('Carpeta creada exitosamente', 'success');
                
                // Invalidar caché para esta ruta
                fileCache.clear();
                
                // Recargar el explorador de archivos
                this.refreshFileExplorer();
            })
            .catch(error => {
                console.error('Error al crear carpeta:', error);
                this.showNotification('Error al crear carpeta: ' + error.message, 'danger');
            });
        },
        
        // Eliminar un archivo o carpeta
        deleteFileOrFolder: function(filePath) {
            if (!filePath) return;
            
            // Confirmar eliminación
            if (!confirm('¿Está seguro de que desea eliminar este elemento? Esta acción no se puede deshacer.')) {
                return;
            }
            
            // Mostrar indicador de progreso
            this.showNotification('Eliminando elemento...', 'info', false);
            
            // Eliminar en el servidor
            fetch('/api/file/delete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ file_path: filePath })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Error del servidor: ${response.status} ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (!data.success) {
                    this.showNotification(data.error || 'Error al eliminar', 'danger');
                    return;
                }
                
                this.showNotification(data.message || 'Elemento eliminado exitosamente', 'success');
                
                // Invalidar caché para todas las rutas
                fileCache.clear();
                
                // Recargar el explorador de archivos
                this.refreshFileExplorer();
                
                // Emitir evento para notificar a otros componentes
                document.dispatchEvent(new CustomEvent('file_deleted', {
                    detail: { path: filePath }
                }));
            })
            .catch(error => {
                console.error('Error al eliminar:', error);
                this.showNotification('Error al eliminar: ' + error.message, 'danger');
            });
        },
        
        // Editar un archivo
        editFile: function(filePath, content) {
            if (!filePath) return;
            
            // Mostrar indicador de progreso
            this.showNotification('Guardando cambios...', 'info', false);
            
            // Editar en el servidor
            fetch('/api/file/edit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    file_path: filePath,
                    content: content
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Error del servidor: ${response.status} ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (!data.success) {
                    this.showNotification(data.error || 'Error al editar archivo', 'danger');
                    return;
                }
                
                this.showNotification(data.message || 'Archivo editado exitosamente', 'success');
                
                // Invalidar caché para esta ruta
                fileCache.clear();
                
                // Emitir evento para notificar a otros componentes
                document.dispatchEvent(new CustomEvent('file_edited', {
                    detail: { path: filePath }
                }));
            })
            .catch(error => {
                console.error('Error al editar archivo:', error);
                this.showNotification('Error al editar archivo: ' + error.message, 'danger');
            });
        },
        
        // Instalar un paquete o dependencia
        installPackage: function(packageName, packageManager = 'pip') {
            if (!packageName) return;
            
            // Mostrar indicador de progreso
            this.showNotification(`Instalando paquete ${packageName}...`, 'info', false);
            
            // Enviar solicitud al servidor
            fetch('/api/package/install', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    package: packageName,
                    manager: packageManager
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Error del servidor: ${response.status} ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (!data.success) {
                    this.showNotification(data.error || `Error al instalar ${packageName}`, 'danger');
                    console.error('Error de instalación:', data.stderr);
                    return;
                }
                
                this.showNotification(`Paquete ${packageName} instalado correctamente`, 'success');
                
                // Mostrar un modal con la salida detallada si está disponible
                if (data.stdout || data.stderr) {
                    // Crear un modal para mostrar la salida
                    const modalId = 'package-install-modal';
                    let modal = document.getElementById(modalId);
                    
                    if (!modal) {
                        modal = document.createElement('div');
                        modal.id = modalId;
                        modal.className = 'modal fade';
                        modal.innerHTML = `
                            <div class="modal-dialog modal-lg">
                                <div class="modal-content bg-dark text-light">
                                    <div class="modal-header">
                                        <h5 class="modal-title">Instalación de paquete: ${packageName}</h5>
                                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                                    </div>
                                    <div class="modal-body">
                                        <div class="output-container">
                                            ${data.stdout ? `<h6>Salida:</h6><pre class="text-light">${data.stdout}</pre>` : ''}
                                            ${data.stderr ? `<h6>Errores/Advertencias:</h6><pre class="text-warning">${data.stderr}</pre>` : ''}
                                        </div>
                                    </div>
                                    <div class="modal-footer">
                                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                                    </div>
                                </div>
                            </div>
                        `;
                        document.body.appendChild(modal);
                    } else {
                        // Actualizar contenido del modal existente
                        modal.querySelector('.modal-title').textContent = `Instalación de paquete: ${packageName}`;
                        modal.querySelector('.output-container').innerHTML = `
                            ${data.stdout ? `<h6>Salida:</h6><pre class="text-light">${data.stdout}</pre>` : ''}
                            ${data.stderr ? `<h6>Errores/Advertencias:</h6><pre class="text-warning">${data.stderr}</pre>` : ''}
                        `;
                    }
                    
                    // Mostrar el modal
                    if (typeof bootstrap !== 'undefined') {
                        new bootstrap.Modal(modal).show();
                    } else {
                        modal.style.display = 'block';
                    }
                }
            })
            .catch(error => {
                console.error('Error al instalar paquete:', error);
                this.showNotification('Error al instalar paquete: ' + error.message, 'danger');
            });
        },
        
        // Renombrar un archivo o carpeta
        renameFileOrFolder: function(filePath) {
            if (!filePath) return;
            
            // Obtener el nombre actual del archivo/carpeta
            const currentName = filePath.split('/').pop();
            
            // Solicitar nuevo nombre
            const newName = prompt('Ingrese el nuevo nombre:', currentName);
            if (!newName || newName === currentName) return;
            
            // Renombrar en el servidor
            fetch('/api/file/rename', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    file_path: filePath,
                    new_name: newName 
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Error del servidor: ${response.status} ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (!data.success) {
                    this.showNotification(data.error || 'Error al renombrar', 'danger');
                    return;
                }
                
                this.showNotification(data.message || 'Elemento renombrado exitosamente', 'success');
                
                // Invalidar caché para todas las rutas
                fileCache.clear();
                
                // Recargar el explorador de archivos
                this.refreshFileExplorer();
            })
            .catch(error => {
                console.error('Error al renombrar:', error);
                this.showNotification('Error al renombrar: ' + error.message, 'danger');
            });
        },
        
        // Actualizar el explorador de archivos sin recargar la página
        refreshFileExplorer: function() {
            console.log("Actualizando explorador de archivos...");
            
            // Obtener elementos del DOM
            const fileExplorerContent = document.getElementById('file-explorer-content');
            const directoryPath = document.getElementById('directory-path');
            const currentDirectory = directoryPath.textContent || '/';
            
            // Mostrar indicador de carga
            fileExplorerContent.innerHTML = `
                <div class="p-4 text-center text-muted">
                    <div class="spinner-border" role="status">
                        <span class="visually-hidden">Cargando...</span>
                    </div>
                    <p class="mt-2">Cargando archivos...</p>
                </div>
            `;
            
            // Limpiar caché para esta ruta específica
            try {
                const cachedData = fileCache.get(currentDirectory);
                if (cachedData) {
                    // Si hay caché, actualizar la interfaz inmediatamente
                    this.renderFileList(cachedData.files, cachedData.current_dir);
                    this.updateBreadcrumb(cachedData.current_dir);
                }
            } catch (e) {
                console.warn('Error al leer caché:', e);
            }
            
            // Hacer la solicitud al servidor
            fetch('/api/list_files', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ directory: currentDirectory })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Error del servidor: ${response.status} ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    this.showNotification(data.error, 'warning');
                    return;
                }
                
                // Actualizar la caché
                fileCache.set(currentDirectory, data);
                
                // Actualizar UI
                if (window.renderFileList && typeof window.renderFileList === 'function') {
                    window.renderFileList(data.files, data.current_dir);
                }
                
                if (window.updateBreadcrumb && typeof window.updateBreadcrumb === 'function') {
                    window.updateBreadcrumb(data.current_dir);
                }
                
                // Actualizar el path actual
                directoryPath.textContent = data.current_dir;
            })
            .catch(error => {
                console.error('Error al actualizar archivos:', error);
                this.showNotification('Error al cargar archivos: ' + error.message, 'danger');
                
                fileExplorerContent.innerHTML = `
                    <div class="p-4 text-center text-danger">
                        <i class="bi bi-exclamation-triangle" style="font-size: 2rem;"></i>
                        <p class="mt-2">${error.message}</p>
                        <button class="btn btn-sm btn-outline-primary mt-3" onclick="window.fileActions.refreshFileExplorer()">
                            <i class="bi bi-arrow-repeat"></i> Intentar nuevamente
                        </button>
                    </div>
                `;
            });
        },
        
        // Mostrar notificaciones
        showNotification: function(message, type = 'info') {
            const notificationsContainer = document.getElementById('notifications');
            if (!notificationsContainer) return;
            
            const toast = document.createElement('div');
            toast.className = `toast align-items-center border-0 bg-${type} text-white`;
            toast.setAttribute('role', 'alert');
            toast.setAttribute('aria-live', 'assertive');
            toast.setAttribute('aria-atomic', 'true');
            
            toast.innerHTML = `
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Cerrar"></button>
                </div>
            `;
            
            notificationsContainer.appendChild(toast);
            
            // Verificar si bootstrap está disponible
            if (typeof bootstrap !== 'undefined') {
                const bsToast = new bootstrap.Toast(toast, {
                    autohide: true,
                    delay: 5000
                });
                bsToast.show();
            } else {
                // Fallback si bootstrap no está disponible
                setTimeout(() => {
                    toast.classList.add('show');
                }, 100);
                
                // Auto-hide after 5 seconds
                setTimeout(() => {
                    toast.classList.remove('show');
                    setTimeout(() => toast.remove(), 500);
                }, 5000);
            }
            
            // Eliminar después de ocultarse
            toast.addEventListener('hidden.bs.toast', function() {
                toast.remove();
            });
        },
        
        // Funciones auxiliares (se exponen para que las páginas puedan usarlas)
        updateBreadcrumb: function(path) {
            if (window.updateBreadcrumb && typeof window.updateBreadcrumb === 'function') {
                window.updateBreadcrumb(path);
            }
        },
        
        renderFileList: function(files, currentDir) {
            if (window.renderFileList && typeof window.renderFileList === 'function') {
                window.renderFileList(files, currentDir);
            }
        }
    };
    
    // Mostrar menú contextual para un archivo o carpeta
    fileActions.showContextMenu = function(event, filePath, isDirectory) {
        event.preventDefault();
        event.stopPropagation();
        
        // Eliminar cualquier menú contextual existente
        document.querySelectorAll('.file-context-menu').forEach(menu => menu.remove());
        
        // Crear menú contextual
        const contextMenu = document.createElement('div');
        contextMenu.className = 'file-context-menu';
        contextMenu.style.position = 'absolute';
        contextMenu.style.left = `${event.pageX}px`;
        contextMenu.style.top = `${event.pageY}px`;
        contextMenu.style.backgroundColor = '#1e1e2e';
        contextMenu.style.border = '1px solid #333';
        contextMenu.style.borderRadius = '4px';
        contextMenu.style.boxShadow = '0 2px 10px rgba(0,0,0,0.3)';
        contextMenu.style.zIndex = '1000';
        
        // Opciones del menú
        const options = [];
        
        // Opción: Editar (solo para archivos)
        if (!isDirectory) {
            options.push({
                text: 'Editar',
                icon: 'bi-pencil',
                action: () => {
                    window.location.href = `/edit_file?path=${encodeURIComponent(filePath)}`;
                }
            });
        }
        
        // Opción: Renombrar
        options.push({
            text: 'Renombrar',
            icon: 'bi-pencil-square',
            action: () => fileActions.renameFileOrFolder(filePath)
        });
        
        // Opción: Eliminar
        options.push({
            text: 'Eliminar',
            icon: 'bi-trash',
            action: () => fileActions.deleteFileOrFolder(filePath)
        });
        
        // Crear elementos del menú
        options.forEach(option => {
            const menuItem = document.createElement('div');
            menuItem.className = 'file-context-menu-item';
            menuItem.style.padding = '8px 12px';
            menuItem.style.cursor = 'pointer';
            menuItem.style.color = '#f0f0f0';
            menuItem.style.display = 'flex';
            menuItem.style.alignItems = 'center';
            
            menuItem.innerHTML = `<i class="bi ${option.icon}" style="margin-right: 8px;"></i> ${option.text}`;
            
            menuItem.addEventListener('click', function() {
                option.action();
                contextMenu.remove();
            });
            
            menuItem.addEventListener('mouseover', function() {
                this.style.backgroundColor = '#2a2a3c';
            });
            
            menuItem.addEventListener('mouseout', function() {
                this.style.backgroundColor = 'transparent';
            });
            
            contextMenu.appendChild(menuItem);
        });
        
        // Agregar al DOM
        document.body.appendChild(contextMenu);
        
        // Cerrar menú al hacer clic fuera
        setTimeout(() => {
            document.addEventListener('click', function closeMenu(e) {
                if (!contextMenu.contains(e.target)) {
                    contextMenu.remove();
                    document.removeEventListener('click', closeMenu);
                }
            });
        }, 0);
        
        return false;
    };
    
    // Función para mejorar la representación de archivos con opciones de edición/eliminación
    fileActions.enhanceFileDisplay = function() {
        // Seleccionar todos los elementos de archivo/carpeta
        const fileItems = document.querySelectorAll('.file-item');
        
        fileItems.forEach(item => {
            // Verificar si ya está mejorado
            if (item.dataset.enhanced === 'true') return;
            
            // Marcar como mejorado
            item.dataset.enhanced = 'true';
            
            // Obtener datos del archivo
            const filePath = item.dataset.path;
            const isDirectory = item.classList.contains('directory');
            
            if (!filePath) return;
            
            // Añadir evento de clic derecho
            item.addEventListener('contextmenu', function(e) {
                fileActions.showContextMenu(e, filePath, isDirectory);
            });
            
            // Añadir ícono de opciones
            const actionsIcon = document.createElement('span');
            actionsIcon.className = 'file-actions-icon';
            actionsIcon.innerHTML = '<i class="bi bi-three-dots-vertical"></i>';
            actionsIcon.style.marginLeft = 'auto';
            actionsIcon.style.cursor = 'pointer';
            actionsIcon.style.opacity = '0.7';
            actionsIcon.style.display = 'none';
            
            actionsIcon.addEventListener('click', function(e) {
                e.stopPropagation();
                fileActions.showContextMenu(e, filePath, isDirectory);
            });
            
            // Mostrar ícono al pasar el mouse
            item.addEventListener('mouseover', function() {
                actionsIcon.style.display = 'block';
            });
            
            item.addEventListener('mouseout', function() {
                actionsIcon.style.display = 'none';
            });
            
            // Agregar el ícono al elemento
            item.appendChild(actionsIcon);
        });
    };
    
    // Exponer funciones al ámbito global
    window.fileActions = fileActions;
    
    // Inicializar context menu para elementos del explorador
    document.addEventListener('DOMContentLoaded', function() {
        // Agregar listeners para clicks fuera de menus contextuales
        document.addEventListener('click', function(e) {
            const contextMenus = document.querySelectorAll('.file-context-menu');
            contextMenus.forEach(menu => {
                if (!menu.contains(e.target)) {
                    menu.remove();
                }
            });
        });
        
        // Mejorar la visualización inicial de archivos
        setTimeout(fileActions.enhanceFileDisplay, 500);
        
        // Observer para mejorar dinámicamente los nuevos elementos de archivo que se añadan
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.addedNodes.length) {
                    setTimeout(fileActions.enhanceFileDisplay, 100);
                }
            });
        });
        
        // Configurar y comenzar la observación
        const explorerContainer = document.getElementById('file-explorer') || 
                                 document.getElementById('explorer-container') || 
                                 document.querySelector('.explorer-content');
        
        if (explorerContainer) {
            observer.observe(explorerContainer, { childList: true, subtree: true });
        }
    });
})();