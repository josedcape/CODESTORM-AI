/**
 * CODESTORM - Procesador de Comandos en Lenguaje Natural
 * Este módulo permite interpretar instrucciones en lenguaje natural y convertirlas en comandos ejecutables
 */

class NaturalCommandProcessor {
    constructor() {
        this.commandHistory = [];
        this.supportedCommands = {
            file: ['crear', 'nuevo', 'editar', 'abrir', 'eliminar', 'borrar', 'mostrar', 'ver', 'leer'],
            directory: ['crear', 'nuevo', 'eliminar', 'borrar', 'listar', 'mostrar', 'cambiar a', 'ir a'],
            package: ['instalar', 'desinstalar', 'actualizar'],
            system: ['ejecutar', 'correr', 'iniciar', 'detener', 'reiniciar', 'status']
        };

        // Patrones de reconocimiento para comandos comunes
        this.patterns = {
            createFile: [
                /crear\s+(?:un\s+)?(?:nuevo\s+)?archivo\s+(?:llamado\s+)?["']?([^"']+)["']?/i,
                /nuevo\s+archivo\s+(?:llamado\s+)?["']?([^"']+)["']?/i,
                /crear\s+(?:el\s+)?archivo\s+["']?([^"']+)["']?/i,
                /generar\s+(?:un\s+)?archivo\s+(?:llamado\s+)?["']?([^"']+)["']?/i
            ],
            createFileWithContent: [
                /crear\s+(?:un\s+)?(?:nuevo\s+)?archivo\s+(?:llamado\s+)?["']?([^"']+)["']?\s+(?:con\s+(?:el\s+)?contenido\s+["'](.+?)["']|con\s+(?:el\s+)?contenido\s+(.+)$)/i,
                /nuevo\s+archivo\s+(?:llamado\s+)?["']?([^"']+)["']?\s+(?:con\s+(?:el\s+)?contenido\s+["'](.+?)["']|con\s+(?:el\s+)?contenido\s+(.+)$)/i
            ],
            createDirectory: [
                /crear\s+(?:un\s+)?(?:nuevo\s+)?(?:directorio|carpeta)\s+(?:llamad[oa]\s+)?["']?([^"']+)["']?/i,
                /nuev[oa]\s+(?:directorio|carpeta)\s+(?:llamad[oa]\s+)?["']?([^"']+)["']?/i
            ],
            deleteFile: [
                /(?:eliminar|borrar)\s+(?:el\s+)?archivo\s+(?:llamado\s+)?["']?([^"']+)["']?/i,
                /(?:eliminar|borrar)\s+["']?([^"']+)["']?/i
            ],
            deleteDirectory: [
                /(?:eliminar|borrar)\s+(?:el\s+)?(?:directorio|carpeta)\s+(?:llamad[oa]\s+)?["']?([^"']+)["']?/i
            ],
            listFiles: [
                /(?:listar|mostrar|ver)\s+(?:los\s+)?archivos/i,
                /listar\s+(?:el\s+)?(?:directorio|carpeta)/i,
                /mostrar\s+(?:el\s+)?contenido\s+(?:del\s+)?(?:directorio|carpeta)/i
            ],
            changeDirectory: [
                /(?:cambiar|ir)\s+(?:al|a)\s+(?:directorio|carpeta)\s+["']?([^"']+)["']?/i,
                /(?:cambiar|ir)\s+(?:al|a)\s+["']?([^"']+)["']?/i,
                /cd\s+["']?([^"']+)["']?/i
            ],
            installPackage: [
                /instalar\s+(?:el\s+)?(?:paquete|librería|biblioteca|módulo)\s+["']?([^"']+)["']?/i,
                /instalar\s+["']?([^"']+)["']?/i,
                /npm\s+install\s+["']?([^"']+)["']?/i,
                /pip\s+install\s+["']?([^"']+)["']?/i
            ],
            uninstallPackage: [
                /(?:desinstalar|eliminar|quitar)\s+(?:el\s+)?(?:paquete|librería|biblioteca|módulo)\s+["']?([^"']+)["']?/i,
                /npm\s+(?:uninstall|remove)\s+["']?([^"']+)["']?/i,
                /pip\s+(?:uninstall|remove)\s+["']?([^"']+)["']?/i
            ],
            executeCommand: [
                /ejecutar\s+(?:el\s+)?comando\s+["']?(.+?)["']?$/i,
                /correr\s+(?:el\s+)?comando\s+["']?(.+?)["']?$/i,
                /ejecutar\s+["']?(.+?)["']?$/i
            ]
        };
    }

    /**
     * Procesa una instrucción en lenguaje natural y la convierte en un comando ejecutable
     * @param {string} instruction - Instrucción en lenguaje natural
     * @param {string} currentDirectory - Directorio actual
     * @returns {object} Objeto con el comando y metadatos
     */
    processInstruction(instruction, currentDirectory = '.') {
        // Normalizar directorio actual
        currentDirectory = currentDirectory === '/' ? '.' : currentDirectory;

        // Intentar identificar el tipo de instrucción
        let result = this.identifyCommand(instruction, currentDirectory);

        // Si no se pudo identificar con patrones, intentar con análisis semántico básico
        if (!result.command) {
            result = this.semanticAnalysis(instruction, currentDirectory);
        }

        // Si aún no hay comando, intentar ejecutar directamente como comando del sistema
        if (!result.command && instruction.trim()) {
            result = {
                type: 'direct',
                command: instruction.trim(),
                description: 'Ejecutar comando directo',
                success: true
            };
        }

        // Agregar a historial si es un comando válido
        if (result.command) {
            this.commandHistory.push({
                instruction: instruction,
                command: result.command,
                timestamp: new Date()
            });
        }

        return result;
    }

    /**
     * Identifica el tipo de comando basado en patrones predefinidos
     * @param {string} instruction - Instrucción en lenguaje natural
     * @param {string} currentDirectory - Directorio actual
     * @returns {object} Objeto con el comando y metadatos
     */
    identifyCommand(instruction, currentDirectory) {
        let result = {
            type: null,
            command: null,
            description: null,
            success: false,
            fileUpdated: false
        };

        // Crear archivo con contenido
        for (const pattern of this.patterns.createFileWithContent) {
            const match = instruction.match(pattern);
            if (match) {
                const fileName = match[1];
                const content = match[2] || match[3] || '';

                // Escapar contenido para shell
                const escapedContent = content.replace(/"/g, '\\"');

                result = {
                    type: 'file_create',
                    command: `echo "${escapedContent}" > ${this.joinPath(currentDirectory, fileName)}`,
                    description: `Crear archivo '${fileName}' con contenido`,
                    fileName: fileName,
                    path: this.joinPath(currentDirectory, fileName),
                    success: true,
                    fileUpdated: true
                };
                return result;
            }
        }

        // Crear archivo vacío
        for (const pattern of this.patterns.createFile) {
            const match = instruction.match(pattern);
            if (match) {
                const fileName = match[1];
                result = {
                    type: 'file_create',
                    command: `touch ${this.joinPath(currentDirectory, fileName)}`,
                    description: `Crear archivo vacío '${fileName}'`,
                    fileName: fileName,
                    path: this.joinPath(currentDirectory, fileName),
                    success: true,
                    fileUpdated: true
                };
                return result;
            }
        }

        // Crear directorio
        for (const pattern of this.patterns.createDirectory) {
            const match = instruction.match(pattern);
            if (match) {
                const dirName = match[1];
                result = {
                    type: 'directory_create',
                    command: `mkdir -p ${this.joinPath(currentDirectory, dirName)}`,
                    description: `Crear directorio '${dirName}'`,
                    dirName: dirName,
                    path: this.joinPath(currentDirectory, dirName),
                    success: true,
                    fileUpdated: true
                };
                return result;
            }
        }

        // Eliminar archivo
        for (const pattern of this.patterns.deleteFile) {
            const match = instruction.match(pattern);
            if (match) {
                const fileName = match[1];
                // Verificar que es un archivo y no un directorio
                if (!fileName.includes('/') || fileName.includes('.')) {
                    result = {
                        type: 'file_delete',
                        command: `rm ${this.joinPath(currentDirectory, fileName)}`,
                        description: `Eliminar archivo '${fileName}'`,
                        fileName: fileName,
                        path: this.joinPath(currentDirectory, fileName),
                        success: true,
                        fileUpdated: true
                    };
                    return result;
                }
            }
        }

        // Eliminar directorio
        for (const pattern of this.patterns.deleteDirectory) {
            const match = instruction.match(pattern);
            if (match) {
                const dirName = match[1];
                result = {
                    type: 'directory_delete',
                    command: `rm -rf ${this.joinPath(currentDirectory, dirName)}`,
                    description: `Eliminar directorio '${dirName}'`,
                    dirName: dirName,
                    path: this.joinPath(currentDirectory, dirName),
                    success: true,
                    fileUpdated: true
                };
                return result;
            }
        }

        // Listar archivos
        for (const pattern of this.patterns.listFiles) {
            if (pattern.test(instruction)) {
                result = {
                    type: 'list_files',
                    command: `ls -la ${currentDirectory}`,
                    description: 'Listar archivos y directorios',
                    success: true,
                    fileUpdated: false
                };
                return result;
            }
        }

        // Cambiar directorio
        for (const pattern of this.patterns.changeDirectory) {
            const match = instruction.match(pattern);
            if (match) {
                const dirName = match[1];
                result = {
                    type: 'change_directory',
                    command: `cd ${dirName}`,
                    description: `Cambiar al directorio '${dirName}'`,
                    dirName: dirName,
                    success: true,
                    fileUpdated: false
                };
                return result;
            }
        }

        // Instalar paquete
        for (const pattern of this.patterns.installPackage) {
            const match = instruction.match(pattern);
            if (match) {
                const packageName = match[1];

                // Detectar tipo de paquete (npm o pip)
                let command;
                if (instruction.toLowerCase().includes('pip') || 
                    packageName.endsWith('.whl') || 
                    instruction.toLowerCase().includes('python')) {
                    command = `pip install ${packageName}`;
                } else if (instruction.toLowerCase().includes('apt') || 
                           instruction.toLowerCase().includes('ubuntu') || 
                           instruction.toLowerCase().includes('debian')) {
                    command = `apt-get install -y ${packageName}`;
                } else {
                    // Por defecto usar npm
                    command = `npm install ${packageName}`;
                }

                result = {
                    type: 'install_package',
                    command: command,
                    description: `Instalar paquete '${packageName}'`,
                    packageName: packageName,
                    success: true,
                    fileUpdated: false
                };
                return result;
            }
        }

        // Desinstalar paquete
        for (const pattern of this.patterns.uninstallPackage) {
            const match = instruction.match(pattern);
            if (match) {
                const packageName = match[1];

                // Detectar tipo de paquete (npm o pip)
                let command;
                if (instruction.toLowerCase().includes('pip') || 
                    packageName.endsWith('.whl') || 
                    instruction.toLowerCase().includes('python')) {
                    command = `pip uninstall -y ${packageName}`;
                } else if (instruction.toLowerCase().includes('apt') || 
                           instruction.toLowerCase().includes('ubuntu') || 
                           instruction.toLowerCase().includes('debian')) {
                    command = `apt-get remove -y ${packageName}`;
                } else {
                    // Por defecto usar npm
                    command = `npm uninstall ${packageName}`;
                }

                result = {
                    type: 'uninstall_package',
                    command: command,
                    description: `Desinstalar paquete '${packageName}'`,
                    packageName: packageName,
                    success: true,
                    fileUpdated: false
                };
                return result;
            }
        }

        // Ejecutar comando directo
        for (const pattern of this.patterns.executeCommand) {
            const match = instruction.match(pattern);
            if (match) {
                const cmd = match[1];
                result = {
                    type: 'execute_command',
                    command: cmd,
                    description: `Ejecutar comando: ${cmd}`,
                    success: true,
                    fileUpdated: false
                };
                return result;
            }
        }

        return result;
    }

    /**
     * Realiza un análisis semántico básico de la instrucción
     * @param {string} instruction - Instrucción en lenguaje natural
     * @param {string} currentDirectory - Directorio actual
     * @returns {object} Objeto con el comando y metadatos
     */
    semanticAnalysis(instruction, currentDirectory) {
        const words = instruction.toLowerCase().split(/\s+/);
        let result = {
            type: null,
            command: null,
            description: null,
            success: false,
            fileUpdated: false
        };

        // Buscar verbos de acción y sustantivos relevantes
        const actionVerbs = words.filter(word => 
            this.supportedCommands.file.includes(word) || 
            this.supportedCommands.directory.includes(word) || 
            this.supportedCommands.package.includes(word) || 
            this.supportedCommands.system.includes(word)
        );

        if (actionVerbs.length === 0) {
            return result;
        }

        const primaryAction = actionVerbs[0];

        // Detectar comandos básicos del sistema
        if (instruction.toLowerCase().includes('pwd') || 
            instruction.toLowerCase().includes('directorio actual') || 
            instruction.toLowerCase().includes('donde estoy')) {
            return {
                type: 'system',
                command: 'pwd',
                description: 'Mostrar directorio actual',
                success: true,
                fileUpdated: false
            };
        }

        if (instruction.toLowerCase().includes('ls') || 
            (instruction.toLowerCase().includes('listar') && !instruction.toLowerCase().includes('directorio'))) {
            return {
                type: 'system',
                command: 'ls -la',
                description: 'Listar archivos',
                success: true,
                fileUpdated: false
            };
        }

        // Si parece un comando directo, devolverlo como tal
        if (instruction.startsWith('git ') || 
            instruction.startsWith('npm ') || 
            instruction.startsWith('pip ') || 
            instruction.startsWith('python ') || 
            instruction.startsWith('node ') ||
            instruction.startsWith('./') ||
            /^[a-z]+\s+-[a-z]+/.test(instruction)) { // Patrones comunes de comandos

            return {
                type: 'direct',
                command: instruction,
                description: 'Ejecutar comando directo',
                success: true,
                fileUpdated: false
            };
        }

        return result;
    }

    /**
     * Une rutas de forma segura
     * @param {string} base - Ruta base
     * @param {string} path - Ruta a unir
     * @returns {string} Ruta unida
     */
    joinPath(base, path) {
        if (base === '.' || base === './') {
            return path;
        }
        // Eliminar slash final si existe
        base = base.endsWith('/') ? base.slice(0, -1) : base;
        // Eliminar slash inicial si existe
        path = path.startsWith('/') ? path.slice(1) : path;
        return `${base}/${path}`;
    }

    /**
     * Obtiene el historial de comandos
     * @returns {Array} Historial de comandos
     */
    getCommandHistory() {
        return this.commandHistory;
    }

    /**
     * Limpia el historial de comandos
     */
    clearCommandHistory() {
        this.commandHistory = [];
    }
}

// Exportar la clase para uso en otros módulos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NaturalCommandProcessor;
} else {
    // Para uso en navegador
    window.NaturalCommandProcessor = NaturalCommandProcessor;
}
