
// File synchronization with WebSocket
const socket = io({
    transports: ['websocket'],
    reconnection: true,
    reconnectionAttempts: 5
});

// Estado de conexión
let isConnected = false;

// Conectar al servidor WebSocket
socket.on('connect', function() {
    console.log('Conectado al servidor WebSocket');
    isConnected = true;
    updateConnectionStatus('connected');
    
    // Unirse a la sala del workspace
    socket.emit('join_workspace', {workspace_id: 'default'});
    
    // Cargar archivos iniciales
    refreshFileExplorer();
});

socket.on('disconnect', function() {
    console.log('Desconectado del servidor WebSocket');
    isConnected = false;
    updateConnectionStatus('disconnected');
});

// Escuchar eventos de cambio de archivos
socket.on('file_change', function(data) {
    console.log('Cambio de archivo detectado:', data);
    refreshFileExplorer();
});

// Escuchar eventos genéricos de sincronización
socket.on('file_sync', function(data) {
    console.log('Sincronización solicitada:', data);
    if (data.refresh) {
        refreshFileExplorer();
    }
});

// Escuchar comandos ejecutados
socket.on('command_executed', function(data) {
    console.log('Comando ejecutado:', data);
    if (data.success) {
        refreshFileExplorer();
    }
});

// Función para actualizar el explorador
function refreshFileExplorer() {
    console.log('Actualizando explorador de archivos...');
    const explorerContainer = document.getElementById('explorer-container');
    if (!explorerContainer) {
        console.warn('No se encontró el contenedor del explorador');
        return;
    }

    // Mostrar indicador de carga
    explorerContainer.innerHTML = `
        <div class="loading-indicator">
            <div class="spinner"></div>
            <span>Actualizando...</span>
        </div>
    `;

    // Mostrar indicador de carga
    explorerContainer.innerHTML = `
        <div class="text-center p-3">
            <div class="spinner-border spinner-border-sm text-primary" role="status">
                <span class="visually-hidden">Cargando...</span>
            </div>
            <p class="mt-2 text-muted">Actualizando archivos...</p>
        </div>
    `;

    // Obtener directorio actual
    const currentPath = document.getElementById('directory-path')?.textContent || '.';

    fetch('/api/files?directory=' + encodeURIComponent(currentPath))
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateFileList(data.files);
            } else {
                throw new Error(data.error || 'Error al cargar archivos');
            }
        })
        .catch(error => {
            console.error('Error al actualizar explorador:', error);
            explorerContainer.innerHTML = `
                <div class="alert alert-danger">
                    Error al cargar archivos: ${error.message}
                    <button class="btn btn-sm btn-outline-danger mt-2" onclick="refreshFileExplorer()">
                        <i class="bi bi-arrow-clockwise"></i> Reintentar
                    </button>
                </div>
            `;
        });
}

// Actualizar la lista de archivos en la UI
function updateFileList(files) {
    const explorerContainer = document.getElementById('explorer-container');
    if (!explorerContainer) return;

    if (!files || files.length === 0) {
        explorerContainer.innerHTML = `
            <div class="text-center text-muted p-3">
                <i class="bi bi-folder2-open"></i>
                <p>No hay archivos en este directorio</p>
            </div>
        `;
        return;
    }

    const fileList = document.createElement('div');
    fileList.className = 'file-list';

    files.forEach(file => {
        const fileItem = document.createElement('div');
        fileItem.className = `file-item ${file.type}`;
        fileItem.innerHTML = `
            <span class="file-icon">
                <i class="bi ${file.type === 'directory' ? 'bi-folder-fill' : 'bi-file-earmark-text'}"></i>
            </span>
            <span class="file-name">${file.name}</span>
            <span class="file-meta">${formatFileSize(file.size)}</span>
        `;
        fileList.appendChild(fileItem);
    });

    explorerContainer.innerHTML = '';
    explorerContainer.appendChild(fileList);
}

// Utilidades
function formatFileSize(size) {
    if (size < 1024) return size + ' B';
    if (size < 1024 * 1024) return (size / 1024).toFixed(1) + ' KB';
    return (size / (1024 * 1024)).toFixed(1) + ' MB';
}

function updateConnectionStatus(status) {
    const indicator = document.getElementById('status-indicator');
    if (!indicator) return;

    indicator.className = 'status-indicator';
    indicator.classList.add(`status-${status}`);
}

// Configurar actualizaciones periódicas como respaldo
setInterval(() => {
    if (isConnected) {
        refreshFileExplorer();
    }
}, 5000);

// Exportar funciones necesarias
window.refreshFileExplorer = refreshFileExplorer;
