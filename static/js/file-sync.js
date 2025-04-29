
// File synchronization with WebSocket
const socket = io.connect();

// Conectar al servidor WebSocket
socket.on('connect', function() {
    console.log('Conectado al servidor WebSocket');
    
    // Unirse a la sala del workspace
    socket.emit('join_workspace', {workspace_id: 'default'});
});

// Escuchar eventos de cambio de archivos
socket.on('file_change', function(data) {
    console.log('Cambio de archivo detectado:', data);
    // Actualizar la vista del explorador
    refreshFileExplorer();
});

// Escuchar eventos genéricos de sincronización
socket.on('file_sync', function(data) {
    console.log('Sincronización solicitada:', data);
    if (data.refresh) {
        refreshFileExplorer();
    }
});

// Función para actualizar el explorador
function refreshFileExplorer() {
    // Código para recargar los archivos del directorio actual
    fetch('/api/files?directory=.')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Actualizar la UI con los nuevos archivos
                updateFileList(data.files);
            }
        })
        .catch(error => console.error('Error al actualizar explorador:', error));
}

// Actualizar la lista de archivos en la UI
function updateFileList(files) {
    const fileList = document.getElementById('file-list');
    if (!fileList) return;
    
    // Limpiar lista actual
    fileList.innerHTML = '';
    
    // Agregar archivos a la lista
    files.forEach(file => {
        const fileItem = document.createElement('div');
        fileItem.className = `file-item ${file.type}`;
        fileItem.innerHTML = `
            <span class="file-icon">${file.type === 'directory' ? '📁' : '📄'}</span>
            <span class="file-name">${file.name}</span>
        `;
        fileList.appendChild(fileItem);
    });
}
