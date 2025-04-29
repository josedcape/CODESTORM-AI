
// Código para integrar en tu archivo de terminal
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar cuando el DOM esté cargado
    console.log("Iniciando integración de terminal...");

    // Variable para almacenar el gestor de paquetes
    let packageManager = null;

    // Referencia al elemento de entrada de la terminal
    const terminalInput = document.getElementById('terminal-input');

    // Historial de comandos
    let commandHistory = [];
    let historyIndex = -1;

    // Función para ejecutar un comando
    function executeCommand(command) {
        if (!command.trim()) return;

        // Añadir al historial
        commandHistory.push(command);
        historyIndex = commandHistory.length;

        // Mostrar comando en la terminal
        appendToTerminal(`$ ${command}`, 'command');

        // Lista de comandos que modifican el sistema de archivos
        const fileModifyingCommands = ['mkdir', 'touch', 'rm', 'cp', 'mv', 'echo', 'cat', 'npm', 'pip'];
        const shouldUpdateExplorer = fileModifyingCommands.some(cmd => command.startsWith(cmd));

        // Ejecutar comando y notificar al explorador
        if (window.executeTerminalCommand) {
            window.executeTerminalCommand(command);
        } else {
            // Fallback si la función global no está disponible
            fetch('/api/execute_command', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    command: command,
                    user_id: localStorage.getItem('user_id') || 'default'
                })
            })
            .then(response => response.json())
            .then(data => {
                // Mostrar salida en la terminal
                if (data.success) {
                    appendToTerminal(data.output || 'Comando ejecutado', 'output');

                    // Si el comando modifica archivos, actualizar explorador múltiples veces
                    if (shouldUpdateExplorer) {
                        // Actualización inmediata
                        if (window.refreshFileExplorer) {
                            window.refreshFileExplorer();
                        }
                        
                        // Actualizaciones posteriores para asegurar sincronización
                        [500, 1000, 2000].forEach(delay => {
                            setTimeout(() => {
                                if (window.refreshFileExplorer) {
                                    window.refreshFileExplorer();
                                }
                            }, delay);
                        });

                        // Emitir evento para otros componentes
                        const event = new CustomEvent('file_system_changed', {
                            detail: { command, timestamp: Date.now() }
                        });
                        window.dispatchEvent(event);
                    }
                } else {
                    appendToTerminal(`Error: ${data.error}`, 'error');
                }
            })
            .catch(error => {
                appendToTerminal(`Error: ${error.message}`, 'error');
            });
        }

        // Limpiar entrada
        terminalInput.value = '';
    }

    // Función para añadir texto a la terminal
    function appendToTerminal(text, className) {
        const terminalOutput = document.getElementById('terminal-output');
        if (terminalOutput) {
            const line = document.createElement('div');
            line.className = `terminal-line ${className || ''}`;
            line.textContent = text;
            terminalOutput.appendChild(line);
            terminalOutput.scrollTop = terminalOutput.scrollHeight;
        }
    }

    // Manejar envío de comandos
    if (terminalInput) {
        terminalInput.addEventListener('keydown', function(event) {
            if (event.key === 'Enter') {
                event.preventDefault();
                const command = terminalInput.value;
                executeCommand(command);
            } else if (event.key === 'ArrowUp') {
                // Navegar historial hacia atrás
                if (historyIndex > 0) {
                    historyIndex--;
                    terminalInput.value = commandHistory[historyIndex];
                }
                event.preventDefault();
            } else if (event.key === 'ArrowDown') {
                // Navegar historial hacia adelante
                if (historyIndex < commandHistory.length - 1) {
                    historyIndex++;
                    terminalInput.value = commandHistory[historyIndex];
                } else {
                    historyIndex = commandHistory.length;
                    terminalInput.value = '';
                }
                event.preventDefault();
            }
        });
    }

    // Cuando el socket esté listo, notificar a otros componentes
    document.addEventListener('socket_ready', function(event) {
        console.log('Terminal: Socket conectado y listo');

        // Inicializar gestor de paquetes con el socket
        if (window.PackageManager) {
            packageManager = new PackageManager({
                socket: window.socketClient,
                onInstallStart: function(data) {
                    console.log("Instalación iniciada:", data);
                    // Actualizar interfaz si es necesario
                    const terminalOutput = document.querySelector('.terminal-output');
                    if (terminalOutput) {
                        const message = document.createElement('div');
                        message.className = 'message system';
                        message.textContent = `Instalando paquete: ${data.package} (${data.manager})...`;
                        terminalOutput.appendChild(message);
                        terminalOutput.scrollTop = terminalOutput.scrollHeight;
                    }
                },
                onInstallProgress: function(data, installation) {
                    // Mostrar salida en la terminal
                    const terminalOutput = document.querySelector('.terminal-output');
                    if (terminalOutput) {
                        const message = document.createElement('div');
                        message.className = data.is_error ? 'message error' : 'message output';
                        message.textContent = data.line;
                        terminalOutput.appendChild(message);
                        terminalOutput.scrollTop = terminalOutput.scrollHeight;
                    }
                },
                onInstallComplete: function(data, installation) {
                    console.log("Instalación completada:", data);
                    // Actualizar interfaz
                    const terminalOutput = document.querySelector('.terminal-output');
                    if (terminalOutput) {
                        const message = document.createElement('div');
                        message.className = data.success ? 'message success' : 'message error';
                        message.textContent = data.success 
                            ? `✅ Paquete ${data.package} instalado correctamente.` 
                            : `❌ Error al instalar ${data.package}.`;
                        terminalOutput.appendChild(message);
                        terminalOutput.scrollTop = terminalOutput.scrollHeight;

                        // Mostrar prompt para indicar que puede seguir escribiendo
                        const terminalPrompt = document.querySelector('.terminal-prompt');
                        if (terminalPrompt) {
                            terminalPrompt.style.display = 'flex';
                        }
                    }

                    // Actualizar explorador de archivos
                    if (window.refreshFileExplorer) {
                        setTimeout(window.refreshFileExplorer, 500);
                        setTimeout(window.refreshFileExplorer, 2000);
                    }
                },
                onInstallError: function(data) {
                    console.error("Error en instalación:", data);
                    // Mostrar error en la terminal
                    const terminalOutput = document.querySelector('.terminal-output');
                    if (terminalOutput) {
                        const message = document.createElement('div');
                        message.className = 'message error';
                        message.textContent = `Error: ${data.error || 'Error desconocido'}`;
                        terminalOutput.appendChild(message);
                        terminalOutput.scrollTop = terminalOutput.scrollHeight;

                        // Mostrar prompt
                        const terminalPrompt = document.querySelector('.terminal-prompt');
                        if (terminalPrompt) {
                            terminalPrompt.style.display = 'flex';
                        }
                    }
                }
            });

            // Exponer el gestor de paquetes globalmente
            window.packageManager = packageManager;
        }
    });

    // Escuchar eventos WebSocket para actualizar la terminal
    document.addEventListener('socket_ready', function() {
        if (window.socketClient) {
            window.socketClient.on('command_result', function(data) {
                appendToTerminal(data.output || 'Comando ejecutado', data.success ? 'output' : 'error');
            });

            window.socketClient.on('error', function(data) {
                appendToTerminal(`Error: ${data.message}`, 'error');
            });
        }
    });

    // Exponer funciones globalmente
    window.terminalExecuteCommand = executeCommand;
    window.terminalAppendOutput = appendToTerminal;


    // Función para mostrar salida en la terminal
    function appendOutput(output, isError = false, type = 'output') {
        if (!output) return;

        const lines = typeof output === 'string' ? output.split('\n') : [output];

        lines.forEach(line => {
            if (line.trim()) {
                const outputLine = document.createElement('div');

                // Determinar clase según tipo
                if (isError) {
                    outputLine.className = 'message error';
                } else if (type === 'system') {
                    outputLine.className = 'message system';
                } else if (type === 'success') {
                    outputLine.className = 'message success';
                } else {
                    outputLine.className = 'message output';
                }

                outputLine.textContent = line;
                terminalOutput.appendChild(outputLine);
            }
        });

        // Scroll al final
        terminalOutput.scrollTop = terminalOutput.scrollHeight;
    }

    function processCommand(command) {
        // Procesar comandos
        if (!command) return;

        command = command.trim();

        // Mostrar comando en la salida
        const commandOutput = document.createElement('div');
        commandOutput.className = 'command-entry';
        commandOutput.innerHTML = `<span class="prompt">$</span> <span class="command-text">${command}</span>`;
        terminalOutput.appendChild(commandOutput);

        // Limpiar input después de ejecutar
        terminalInput.value = '';

        // Manejar comandos especiales en cliente
        if (command === 'clear' || command === 'cls') {
            terminalOutput.innerHTML = '';
            return;
        }

        // Procesar comandos de instalación de paquetes
        const parts = command.split(' ');
        const cmd = parts[0].toLowerCase();

        // Comandos de npm
        if (cmd === 'npm' && packageManager) {
            if (parts[1] === 'install' || parts[1] === 'i') {
                // npm install <package> [options]
                const packageName = parts[2];
                const options = parts.slice(3);

                if (!packageName) {
                    appendOutput('Error: Nombre de paquete requerido', true);
                    return;
                }

                appendOutput(`Instalando paquete npm: ${packageName}...`, false, 'system');
                packageManager.installPackage('npm', packageName, options, currentDirectory);
                return;
            }
        }

        // Comandos de pip
        if (cmd === 'pip' && packageManager) {
            if (parts[1] === 'install') {
                // pip install <package> [options]
                const packageName = parts[2];
                const options = parts.slice(3);

                if (!packageName) {
                    appendOutput('Error: Nombre de paquete requerido', true);
                    return;
                }

                appendOutput(`Instalando paquete pip: ${packageName}...`, false, 'system');
                packageManager.installPackage('pip', packageName, options, currentDirectory);
                return;
            }
        }

        // Comandos de yarn
        if (cmd === 'yarn' && packageManager) {
            if (parts[1] === 'add') {
                // yarn add <package> [options]
                const packageName = parts[2];
                const options = parts.slice(3);

                if (!packageName) {
                    appendOutput('Error: Nombre de paquete requerido', true);
                    return;
                }

                appendOutput(`Instalando paquete yarn: ${packageName}...`, false, 'system');
                packageManager.installPackage('yarn', packageName, options, currentDirectory);
                return;
            }
        }

        // Comandos de composer
        if (cmd === 'composer' && packageManager) {
            if (parts[1] === 'require') {
                // composer require <package> [options]
                const packageName = parts[2];
                const options = parts.slice(3);

                if (!packageName) {
                    appendOutput('Error: Nombre de paquete requerido', true);
                    return;
                }

                appendOutput(`Instalando paquete composer: ${packageName}...`, false, 'system');
                packageManager.installPackage('composer', packageName, options, currentDirectory);
                return;
            }
        }

        // Enviar comando al servidor
        if (window.socketClient) {
            window.socketClient.emit('terminal_command', {
                command: command,
                cwd: currentDirectory
            });

            // También hacer solicitud HTTP para mayor fiabilidad
            fetch('/api/execute_command', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    command: command,
                    cwd: currentDirectory
                })
            })
            .then(response => response.json())
            .then(data => {
                console.log("Respuesta del servidor:", data);
                // Si hay algún cambio de directorio, actualizar
                if (data.cwd && data.cwd !== currentDirectory) {
                    currentDirectory = data.cwd;
                    updatePrompt();
                }

                // Si hay salida directa, mostrarla
                if (data.output) {
                    appendOutput(data.output, data.error);
                }

                // Si el comando modifica archivos, forzar actualización del explorador
                if (data.file_change || data.refresh_explorer) {
                    if (window.refreshFileExplorer) {
                        setTimeout(window.refreshFileExplorer, 300);
                    }
                }
            })
            .catch(error => {
                console.error("Error al ejecutar comando:", error);
                appendOutput(`Error al ejecutar comando: ${error.message}`, true);
            });
        } else {
            appendOutput("No hay conexión con el servidor", true);
        }
    }
});
