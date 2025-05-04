// Terminal integration code
document.addEventListener('DOMContentLoaded', function() {
    const term = new Terminal({
        cursorBlink: true,
        theme: {
            background: '#1a1a1a',
            foreground: '#f0f0f0',
            cursor: '#ffffff'
        }
    });

    const fitAddon = new FitAddon.FitAddon();
    term.loadAddon(fitAddon);

    // Initialize terminal
    const terminal = document.getElementById('terminal');
    term.open(terminal);
    fitAddon.fit();

    // Terminal state
    let currentLine = '';
    const terminalId = Date.now().toString();
    const userId = localStorage.getItem('user_id') || 'default';
    let commandHistory = [];
    let historyIndex = -1;

    // Socket connection
    const socket = io({
        transports: ['websocket'],
        reconnection: true
    });

    // Handle terminal input
    term.onKey(({ key, domEvent }) => {
        const printable = !domEvent.altKey && !domEvent.ctrlKey && !domEvent.metaKey;

        if (domEvent.keyCode === 13) { // Enter
            if (currentLine.trim()) {
                executeCommand(currentLine);
                commandHistory.push(currentLine);
                historyIndex = commandHistory.length;
            }
            currentLine = '';
            term.write('\r\n$ ');
        } else if (domEvent.keyCode === 8) { // Backspace
            if (currentLine.length > 0) {
                currentLine = currentLine.slice(0, -1);
                term.write('\b \b');
            }
        } else if (printable) {
            currentLine += key;
            term.write(key);
        }
    });

    // Command execution
    function executeCommand(command) {
        socket.emit('execute_command', {
            command: command,
            terminal_id: terminalId,
            user_id: userId
        });
    }

    // Handle command results
    socket.on('command_result', function(data) {
        if (data.terminal_id === terminalId) {
            term.write('\r\n' + data.output);

            if (data.success && isFileModifyingCommand(data.command)) {
                refreshFileExplorer();
            }

            term.write('\r\n$ ');
        }
    });

    // Check if command modifies files
    function isFileModifyingCommand(command) {
        const fileCommands = ['mkdir', 'touch', 'rm', 'cp', 'mv', 'echo'];
        const cmdParts = command.trim().split(' ');
        return fileCommands.includes(cmdParts[0]);
    }

    // Request file explorer update
    function refreshFileExplorer() {
        socket.emit('request_file_list', {
            user_id: userId
        });
    }

    // Handle window resize
    window.addEventListener('resize', () => {
        fitAddon.fit();
    });

    // Initial prompt
    term.write('$ ');


    // Configurar eventos para controles móviles
    const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
    const mobileFloatMenu = document.getElementById('mobile-float-menu');
    const mobileOverlay = document.getElementById('mobile-overlay');

    // Explorador
    const mobileExplorerToggle = document.getElementById('mobile-explorer-toggle');
    const explorerPanel = document.querySelector('.explorer-panel');

    // Asistente
    const mobileAssistantToggle = document.getElementById('mobile-assistant-toggle');
    const assistantContainer = document.querySelector('.assistant-container');

    // Paquetes
    const mobilePackagesToggle = document.getElementById('mobile-packages-toggle');
    const packagesPanel = document.querySelector('.package-install-panel');

    // Chat
    const mobileChatToggle = document.getElementById('mobile-chat-toggle');
    const chatPanel = document.getElementById('assistant-chat-panel');

    // Limpiar terminal
    const mobileClearTerminal = document.getElementById('mobile-clear-terminal');

    // Ajustar vista
    const mobileAdjustView = document.getElementById('mobile-adjust-view');
    const viewSettingsPanel = document.getElementById('view-settings-panel');
    const closeViewSettings = document.getElementById('close-view-settings');

    // Pantalla completa
    const toggleFullscreen = document.getElementById('toggle-fullscreen');

    // Abrir/cerrar menú flotante
    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', function() {
            mobileFloatMenu.classList.toggle('show');
        });
    }

    // Cerrar menú flotante al hacer clic fuera
    document.addEventListener('click', function(e) {
        if (mobileFloatMenu && mobileFloatMenu.classList.contains('show')) {
            if (!mobileMenuToggle.contains(e.target) && !mobileFloatMenu.contains(e.target)) {
                mobileFloatMenu.classList.remove('show');
            }
        }

        // También cerrar panel de ajustes si se hace clic fuera
        if (viewSettingsPanel && viewSettingsPanel.classList.contains('show')) {
            if (!viewSettingsPanel.contains(e.target) && !mobileAdjustView.contains(e.target)) {
                viewSettingsPanel.classList.remove('show');
            }
        }
    });

    // Función para ajustar la vista
    if (mobileAdjustView) {
        mobileAdjustView.addEventListener('click', function() {
            viewSettingsPanel.classList.toggle('show');
            mobileFloatMenu.classList.remove('show');
        });
    }

    // Cerrar panel de ajustes
    if (closeViewSettings) {
        closeViewSettings.addEventListener('click', function() {
            viewSettingsPanel.classList.remove('show');
        });
    }

    // Funcionalidad de pantalla completa
    if (toggleFullscreen) {
        toggleFullscreen.addEventListener('click', function() {
            if (!document.fullscreenElement) {
                document.documentElement.requestFullscreen().catch(err => {
                    console.log(`Error al intentar pantalla completa: ${err.message}`);
                });
            } else {
                if (document.exitFullscreen) {
                    document.exitFullscreen();
                }
            }
            mobileFloatMenu.classList.remove('show');
        });
    }

    // Limpiar Terminal
    if (mobileClearTerminal) {
        mobileClearTerminal.addEventListener('click', function() {
            if (window.terminalInterface && typeof window.terminalInterface.clear === 'function') {
                window.terminalInterface.clear();
            } else if (window.term && typeof window.term.clear === 'function') {
                window.term.clear();
            }
            mobileFloatMenu.classList.remove('show');
        });
    }

    // Controles de tamaño de fuente
    const decreaseFont = document.getElementById('decrease-font');
    const increaseFont = document.getElementById('increase-font');
    const currentFontSize = document.getElementById('current-font-size');
    let fontSize = 14; // Tamaño inicial

    if (decreaseFont && increaseFont) {
        // Inicializar el valor actual
        updateFontSize();

        decreaseFont.addEventListener('click', function() {
            if (fontSize > 8) {
                fontSize -= 1;
                updateFontSize();
            }
        });

        increaseFont.addEventListener('click', function() {
            if (fontSize < 24) {
                fontSize += 1;
                updateFontSize();
            }
        });
    }

    function updateFontSize() {
        if (window.term) {
            const xtermElements = document.querySelectorAll('.xterm');
            xtermElements.forEach(el => {
                el.style.fontSize = `${fontSize}px`;
            });

            // Aplicar tamaño a la terminal si es posible
            if (window.term.options) {
                window.term.options.fontSize = fontSize;

                // Algunas implementaciones requieren esto para refrescar
                if (typeof window.term.refresh === 'function') {
                    window.term.refresh(0, window.term.rows - 1);
                }
            }

            if (currentFontSize) {
                currentFontSize.textContent = `${fontSize}px`;
            }
        }
    }

    // Control de altura del terminal
    const terminalHeight = document.getElementById('terminal-height');
    const heightValue = document.getElementById('height-value');

    if (terminalHeight) {
        terminalHeight.addEventListener('input', function() {
            const height = this.value;
            const terminalContainer = document.querySelector('.terminal-container');
            if (terminalContainer) {
                terminalContainer.style.height = `${height}vh`;
                heightValue.textContent = `${height}%`;

                // Reajustar terminal si es necesario
                if (window.term && typeof window.term.fit === 'function') {
                    window.term.fit();
                }
            }
        });
    }

    // Botón de reset
    const resetView = document.getElementById('reset-view');
    if (resetView) {
        resetView.addEventListener('click', function() {
            // Restablecer tamaño de fuente
            fontSize = 14;
            updateFontSize();

            // Restablecer altura
            if (terminalHeight) {
                terminalHeight.value = 60;
                const terminalContainer = document.querySelector('.terminal-container');
                if (terminalContainer) {
                    terminalContainer.style.height = '60vh';
                    heightValue.textContent = '60%';
                }
            }

            // Ajustar terminal
            if (window.term && typeof window.term.fit === 'function') {
                window.term.fit();
            }
        });
    }

    // Ajustar automáticamente en carga para móviles
    function adjustForMobile() {
        if (window.innerWidth <= 768) {
            // Aumentar el tamaño de fuente en móviles por defecto
            fontSize = 16;
            updateFontSize();

            // Hacer que la terminal ocupe menos altura en modo vertical
            const terminalContainer = document.querySelector('.terminal-container');
            if (terminalContainer) {
                terminalContainer.style.height = '60vh';
                if (terminalHeight) {
                    terminalHeight.value = 60;
                    heightValue.textContent = '60%';
                }
            }

            // Ajustar el terminal al tamaño
            if (window.term && typeof window.term.fit === 'function') {
                setTimeout(() => {
                    window.term.fit();
                }, 300); // Retraso para permitir que se apliquen los estilos
            }
        }
    }

    // Ejecutar ajuste inicial
    adjustForMobile();

    // Ajustar cuando cambie la orientación del dispositivo
    window.addEventListener('resize', function() {
        if (window.term && typeof window.term.fit === 'function') {
            window.term.fit();
        }
    });
});