/**
 * CODESTORM - Procesador de Comandos en Lenguaje Natural
 * Este módulo permite interpretar instrucciones en lenguaje natural y convertirlas en comandos ejecutables
 * Versión optimizada con mejor manejo de patrones y análisis contextual
 */

class NaturalCommandProcessor {
    constructor() {
        this.commandHistory = [];

        // Categorías de comandos con sus verbos asociados
        this.commandCategories = {
            file: {
                verbs: ['crear', 'nuevo', 'editar', 'abrir', 'eliminar', 'borrar', 'mostrar', 'ver', 'leer', 'guardar', 'modificar'],
                nouns: ['archivo', 'fichero', 'documento', 'texto']
            },
            directory: {
                verbs: ['crear', 'nuevo', 'eliminar', 'borrar', 'listar', 'mostrar', 'cambiar a', 'ir a', 'navegar'],
                nouns: ['directorio', 'carpeta', 'folder', 'ruta']
            },
            package: {
                verbs: ['instalar', 'desinstalar', 'actualizar', 'añadir', 'quitar', 'remover'],
                nouns: ['paquete', 'librería', 'biblioteca', 'módulo', 'dependencia']
            },
            system: {
                verbs: ['ejecutar', 'correr', 'iniciar', 'detener', 'parar', 'reiniciar', 'mostrar', 'ver'],
                nouns: ['comando', 'proceso', 'servicio', 'sistema', 'estado']
            }
        };

        // Patrones de reconocimiento para comandos comunes
        this.patterns = {
            // Patrones para archivos
            createFile: [
                /crear\s+(?:un\s+)?(?:nuevo\s+)?archivo\s+(?:llamado\s+)?["']?([^"']+)["']?/i,
                /nuevo\s+archivo\s+(?:llamado\s+)?["']?([^"']+)["']?/i,
                /crear\s+(?:el\s+)?archivo\s+["']?([^"']+)["']?/i,
                /generar\s+(?:un\s+)?archivo\s+(?:llamado\s+)?["']?([^"']+)["']?/i,
                /hacer\s+(?:un\s+)?archivo\s+(?:llamado\s+)?["']?([^"']+)["']?/i
            ],
            createFileWithContent: [
                /crear\s+(?:un\s+)?(?:nuevo\s+)?archivo\s+(?:llamado\s+)?["']?([^"']+)["']?\s+(?:con\s+(?:el\s+)?contenido\s+["'](.+?)["']|con\s+(?:el\s+)?contenido\s+(.+)$)/i,
                /nuevo\s+archivo\s+(?:llamado\s+)?["']?([^"']+)["']?\s+(?:con\s+(?:el\s+)?contenido\s+["'](.+?)["']|con\s+(?:el\s+)?contenido\s+(.+)$)/i,
                /generar\s+(?:un\s+)?archivo\s+(?:llamado\s+)?["']?([^"']+)["']?\s+(?:con\s+(?:el\s+)?contenido\s+["'](.+?)["']|con\s+(?:el\s+)?contenido\s+(.+)$)/i,
                /crear\s+["']?([^"']+)["']?\s+(?:con\s+(?:el\s+)?contenido\s+["'](.+?)["']|con\s+(?:el\s+)?contenido\s+(.+)$)/i
            ],
            openFile: [
                /(?:abrir|ver|mostrar|leer)\s+(?:el\s+)?archivo\s+(?:llamado\s+)?["']?([^"']+)["']?/i,
                /(?:abrir|ver|mostrar|leer)\s+["']?([^"']+)["']?/i
            ],

            // Patrones para directorios
            createDirectory: [
                /crear\s+(?:un\s+)?(?:nuevo\s+)?(?:directorio|carpeta)\s+(?:llamad[oa]\s+)?["']?([^"']+)["']?/i,
                /nuev[oa]\s+(?:directorio|carpeta)\s+(?:llamad[oa]\s+)?["']?([^"']+)["']?/i,
                /hacer\s+(?:un[oa]\s+)?(?:directorio|carpeta)\s+(?:llamad[oa]\s+)?["']?([^"']+)["']?/i
            ],
            deleteFile: [
                /(?:eliminar|borrar|quitar|remover)\s+(?:el\s+)?archivo\s+(?:llamado\s+)?["']?([^"']+)["']?/i,
                /(?:eliminar|borrar|quitar|remover)\s+["']?([^"']+)["']?/i
            ],
            deleteDirectory: [
                /(?:eliminar|borrar|quitar|remover)\s+(?:el\s+)?(?:directorio|carpeta)\s+(?:llamad[oa]\s+)?["']?([^"']+)["']?/i,
                /(?:eliminar|borrar|quitar|remover)\s+(?:la\s+)?(?:directorio|carpeta)\s+(?:llamad[oa]\s+)?["']?([^"']+)["']?/i
            ],
            listFiles: [
                /(?:listar|mostrar|ver|enumerar)\s+(?:los\s+)?archivos/i,
                /listar\s+(?:el\s+)?(?:directorio|carpeta)/i,
                /mostrar\s+(?:el\s+)?contenido\s+(?:del\s+)?(?:directorio|carpeta)/i,
                /ver\s+(?:el\s+)?contenido\s+(?:del\s+)?(?:directorio|carpeta)/i,
                /ls/i
            ],
            changeDirectory: [
                /(?:cambiar|ir)\s+(?:al|a)\s+(?:directorio|carpeta)\s+["']?([^"']+)["']?/i,
                /(?:cambiar|ir)\s+(?:al|a)\s+["']?([^"']+)["']?/i,
                /cd\s+["']?([^"']+)["']?/i,
                /navegar\s+(?:a|hacia)\s+["']?([^"']+)["']?/i
            ],

            // Patrones para paquetes
            installPackage: [
                /instalar\s+(?:el\s+)?(?:paquete|librería|biblioteca|módulo|dependencia)\s+["']?([^"']+)["']?/i,
                /instalar\s+["']?([^"']+)["']?/i,
                /añadir\s+(?:el\s+)?(?:paquete|librería|biblioteca|módulo|dependencia)\s+["']?([^"']+)["']?/i,
                /npm\s+install\s+["']?([^"']+)["']?/i,
                /pip\s+install\s+["']?([^"']+)["']?/i
            ],
            uninstallPackage: [
                /(?:desinstalar|eliminar|quitar|remover)\s+(?:el\s+)?(?:paquete|librería|biblioteca|módulo|dependencia)\s+["']?([^"']+)["']?/i,
                /npm\s+(?:uninstall|remove)\s+["']?([^"']+)["']?/i,
                /pip\s+(?:uninstall|remove)\s+["']?([^"']+)["']?/i
            ],

            // Patrones para comandos del sistema
            executeCommand: [
                /ejecutar\s+(?:el\s+)?comando\s+["']?(.+?)["']?$/i,
                /correr\s+(?:el\s+)?comando\s+["']?(.+?)["']?$/i,
                /ejecutar\s+["']?(.+?)["']?$/i,
                /correr\s+["']?(.+?)["']?$/i,
                /iniciar\s+["']?(.+?)["']?$/i
            ],

            // Comandos de utilidad
            currentDirectory: [
                /(?:mostrar|ver|cuál\s+es)\s+(?:el\s+)?directorio\s+actual/i,
                /(?:dónde|donde)\s+estoy/i,
                /pwd/i,
                /ubicación\s+actual/i
            ]
        };

        // Comandos directos que no necesitan procesamiento
        this.directCommands = [
            'git', 'npm', 'pip', 'python', 'node', 'java', 'javac', 
            'gcc', 'make', 'docker', 'kubectl', 'terraform', 'ansible'
        ];
    }

    /**
     * Procesa una instrucción en lenguaje natural y la convierte en un comando ejecutable
     * @param {string} instruction - Instrucción en lenguaje natural
     * @param {string} currentDirectory - Directorio actual
     * @returns {object} Objeto con el comando y metadatos
     */
    processInstruction(instruction, currentDirectory = '.') {
        if (!instruction || instruction.trim() === '') {
            return {
                type: null,
                command: null,
                description: "Instrucción vacía",
                success: false
            };
        }

        // Normalizar directorio actual
        currentDirectory = currentDirectory === '/' ? '.' : currentDirectory;

        // Normalizar la instrucción
        const normalizedInstruction = instruction.trim();

        // Verificar si es un comando directo
        if (this.isDirectCommand(normalizedInstruction)) {
            const result = {
                type: 'direct',
                command: normalizedInstruction,
                description: 'Ejecutar comando directo',
                success: true,
                fileUpdated: false
            };
            this.addToHistory(instruction, result.command);
            return result;
        }

        // Intentar identificar el tipo de instrucción con patrones
        let result = this.identifyCommand(normalizedInstruction, currentDirectory);

        // Si no se pudo identificar con patrones, intentar con análisis semántico
        if (!result.command) {
            result = this.semanticAnalysis(normalizedInstruction, currentDirectory);
        }

        // Si aún no hay comando, intentar ejecutar directamente
        if (!result.command && normalizedInstruction) {
            result = {
                type: 'direct',
                command: normalizedInstruction,
                description: 'Ejecutar comando directo',
                success: true,
                fileUpdated: false
            };
        }

        // Agregar a historial si es un comando válido
        if (result.command) {
            this.addToHistory(instruction, result.command);
        }

        return result;
    }

    /**
     * Verifica si la instrucción es un comando directo que no necesita procesamiento
     * @param {string} instruction - Instrucción a verificar
     * @returns {boolean} Verdadero si es un comando directo
     */
    isDirectCommand(instruction) {
        // Verificar si comienza con alguno de los comandos directos conocidos
        return this.directCommands.some(cmd => 
            instruction.startsWith(`${cmd} `) || instruction === cmd
        ) || 
        // O si tiene formato de comando con opciones
        /^[a-z]+\s+-[a-z]+/.test(instruction) ||
        // O si es un script ejecutable
        instruction.startsWith('./') ||
        // O si es un comando con pipe
        instruction.includes(' | ');
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

        // Verificar directorio actual
        for (const pattern of this.patterns.currentDirectory) {
            if (pattern.test(instruction)) {
                result = {
                    type: 'system',
                    command: 'pwd',
                    description: 'Mostrar directorio actual',
                    success: true,
                    fileUpdated: false
                };
                return result;
            }
        }

        // Crear archivo con contenido
        for (const pattern of this.patterns.createFileWithContent) {
            const match = instruction.match(pattern);
            if (match) {
                const fileName = match[1];
                const content = match[2] || match[3] || '';

                // Escapar contenido para shell
                const escapedContent = this.escapeShellContent(content);

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

        // Abrir/mostrar archivo
        for (const pattern of this.patterns.openFile) {
            const match = instruction.match(pattern);
            if (match) {
                const fileName = match[1];
                result = {
                    type: 'file_open',
                    command: `cat ${this.joinPath(currentDirectory, fileName)}`,
                    description: `Mostrar contenido del archivo '${fileName}'`,
                    fileName: fileName,
                    path: this.joinPath(currentDirectory, fileName),
                    success: true,
                    fileUpdated: false
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
                // Verificar que parece un archivo y no un directorio
                if (!fileName.endsWith('/') && (fileName.includes('.') || !this.looksLikeDirectory(fileName))) {
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
                const packageManager = this.detectPackageManager(instruction, packageName);

                result = {
                    type: 'install_package',
                    command: packageManager.installCmd,
                    description: `Instalar paquete '${packageName}' usando ${packageManager.name}`,
                    packageName: packageName,
                    packageManager: packageManager.name,
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
                const packageManager = this.detectPackageManager(instruction, packageName);

                result = {
                    type: 'uninstall_package',
                    command: packageManager.uninstallCmd,
                    description: `Desinstalar paquete '${packageName}' usando ${packageManager.name}`,
                    packageName: packageName,
                    packageManager: packageManager.name,
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
     * Detecta el gestor de paquetes apropiado basado en la instrucción
     * @param {string} instruction - Instrucción completa
     * @param {string} packageName - Nombre del paquete
     * @returns {object} Información del gestor de paquetes
     */
    detectPackageManager(instruction, packageName) {
        const instructionLower = instruction.toLowerCase();

        // Python/pip
        if (instructionLower.includes('pip') || 
            packageName.endsWith('.whl') || 
            instructionLower.includes('python') ||
            instructionLower.includes('librería python') ||
            instructionLower.includes('módulo python')) {
            return {
                name: 'pip',
                installCmd: `pip install ${packageName}`,
                uninstallCmd: `pip uninstall -y ${packageName}`
            };
        } 
        // Sistema operativo (apt)
        else if (instructionLower.includes('apt') || 
                 instructionLower.includes('ubuntu') || 
                 instructionLower.includes('debian') ||
                 instructionLower.includes('paquete del sistema')) {
            return {
                name: 'apt',
                installCmd: `apt-get install -y ${packageName}`,
                uninstallCmd: `apt-get remove -y ${packageName}`
            };
        }
        // Yarn
        else if (instructionLower.includes('yarn')) {
            return {
                name: 'yarn',
                installCmd: `yarn add ${packageName}`,
                uninstallCmd: `yarn remove ${packageName}`
            };
        }
        // Por defecto usar npm
        else {
            return {
                name: 'npm',
                installCmd: `npm install ${packageName}`,
                uninstallCmd: `npm uninstall ${packageName}`
            };
        }
    }

    /**
     * Realiza un análisis semántico avanzado de la instrucción
     * @param {string} instruction - Instrucción en lenguaje natural
     * @param {string} currentDirectory - Directorio actual
     * @returns {object} Objeto con el comando y metadatos
     */
    semanticAnalysis(instruction, currentDirectory) {
        const instructionLower = instruction.toLowerCase();
        const words = instructionLower.split(/\s+/);

        let result = {
            type: null,
            command: null,
            description: null,
            success: false,
            fileUpdated: false
        };

        // Detectar verbos de acción
        const actionVerbs = new Set();
        const targetNouns = new Set();

        // Buscar verbos y sustantivos en las categorías
        Object.entries(this.commandCategories).forEach(([category, data]) => {
            data.verbs.forEach(verb => {
                if (words.includes(verb)) actionVerbs.add(verb);
                // Comprobar verbos compuestos (ej: "cambiar a")
                if (verb.includes(' ') && instructionLower.includes(verb)) actionVerbs.add(verb);
            });

            data.nouns.forEach(noun => {
                if (words.includes(noun)) targetNouns.add(noun);
            });
        });

        // Si no hay verbos de acción reconocidos, no podemos procesar
        if (actionVerbs.size === 0) {
            return result;
        }

        // Comandos comunes sin patrones específicos
        if (instructionLower.match(/(?:ver|mostrar|cuál\s+es)\s+(?:la\s+)?fecha/)) {
            return {
                type: 'system',
                command: 'date',
                description: 'Mostrar fecha y hora actual',
                success: true,
                fileUpdated: false
            };
        }

        if (instructionLower.match(/(?:ver|mostrar|listar)\s+(?:los\s+)?procesos/)) {
            return {
                type: 'system',
                command: 'ps aux',
                description: 'Mostrar procesos en ejecución',
                success: true,
                fileUpdated: false
            };
        }

        if (instructionLower.match(/(?:ver|mostrar)\s+(?:el\s+)?uso\s+(?:de\s+)?(?:memoria|ram)/)) {
            return {
                type: 'system',
                command: 'free -h',
                description: 'Mostrar uso de memoria',
                success: true,
                fileUpdated: false
            };
        }

        if (instructionLower.match(/(?:ver|mostrar)\s+(?:el\s+)?uso\s+(?:de\s+)?(?:disco|almacenamiento)/)) {
            return {
                type: 'system',
                command: 'df -h',
                description: 'Mostrar uso de disco',
                success: true,
                fileUpdated: false
            };
        }

        // Extraer nombres de archivos o directorios
        const fileMatch = instruction.match(/["']([^"']+)["']|(\S+\.\S+)/);
        const fileName = fileMatch ? (fileMatch[1] || fileMatch[2]) : null;

        // Determinar acción basada en verbos y sustantivos
        if (actionVerbs.has('crear') || actionVerbs.has('nuevo')) {
            if (targetNouns.has('archivo') || targetNouns.has('fichero') || targetNouns.has('documento')) {
                if (fileName) {
                    return {
                        type: 'file_create',
                        command: `touch ${this.joinPath(currentDirectory, fileName)}`,
                        description: `Crear archivo vacío '${fileName}'`,
                        fileName: fileName,
                        path: this.joinPath(currentDirectory, fileName),
                        success: true,
                        fileUpdated: true
                    };
                }
            } else if (targetNouns.has('directorio') || targetNouns.has('carpeta')) {
                if (fileName) {
                    return {
                        type: 'directory_create',
                        command: `mkdir -p ${this.joinPath(currentDirectory, fileName)}`,
                        description: `Crear directorio '${fileName}'`,
                        dirName: fileName,
                        path: this.joinPath(currentDirectory, fileName),
                        success: true,
                        fileUpdated: true
                    };
                }
            }
        } else if (actionVerbs.has('eliminar') || actionVerbs.has('borrar') || actionVerbs.has('quitar')) {
            if (targetNouns.has('archivo') || targetNouns.has('fichero') || targetNouns.has('documento')) {
                if (fileName) {
                    return {
                        type: 'file_delete',
                        command: `rm ${this.joinPath(currentDirectory, fileName)}`,
                        description: `Eliminar archivo '${fileName}'`,
                        fileName: fileName,
                        path: this.joinPath(currentDirectory, fileName),
                        success: true,
                        fileUpdated: true
                    };
                }
            } else if (targetNouns.has('directorio') || targetNouns.has('carpeta')) {
                if (fileName) {
                    return {
                        type: 'directory_delete',
                        command: `rm -rf ${this.joinPath(currentDirectory, fileName)}`,
                        description: `Eliminar directorio '${fileName}'`,
                        dirName: fileName,
                        path: this.joinPath(currentDirectory, fileName),
                        success: true,
                        fileUpdated: true
                    };
                }
            }
        } else if (actionVerbs.has('mostrar') || actionVerbs.has('ver') || actionVerbs.has('listar')) {
            if (targetNouns.has('archivo') || targetNouns.has('fichero') || targetNouns.has('documento')) {
                if (fileName) {
                    return {
                        type: 'file_open',
                        command: `cat ${this.joinPath(currentDirectory, fileName)}`,
                        description: `Mostrar contenido del archivo '${fileName}'`,
                        fileName: fileName,
                        path: this.joinPath(currentDirectory, fileName),
                        success: true,
                        fileUpdated: false
                    };
                }
            } else if (targetNouns.has('directorio') || targetNouns.has('carpeta')) {
                return {
                    type: 'list_files',
                    command: `ls -la ${currentDirectory}`,
                    description: 'Listar archivos y directorios',
                    success: true,
                    fileUpdated: false
                };
            }
        }

        return result;
    }

    /**
     * Determina si un nombre parece ser un directorio
     * @param {string} name - Nombre a verificar
     * @returns {boolean} Verdadero si parece un directorio
     */
    looksLikeDirectory(name) {
        return !name.includes('.') || 
               name.endsWith('/') || 
               ['bin', 'etc', 'var', 'usr', 'lib', 'home', 'tmp', 'opt', 'src', 'dist', 'node_modules'].includes(name);
    }

    /**
     * Escapa contenido para uso seguro en shell
     * @param {string} content - Contenido a escapar
     * @returns {string} Contenido escapado
     */
    escapeShellContent(content) {
        return content
            .replace(/"/g, '\\"')
            .replace(/\$/g, '\\$')
            .replace(/`/g, '\\`')
            .replace(/\\/g, '\\\\');
    }

    /**
     * Une rutas de forma segura
     * @param {string} base - Ruta base
     * @param {string} path - Ruta a unir
     * @returns {string} Ruta unida
     */
    joinPath(base, path) {
        if (path.startsWith('/')) {
            return path; // Ruta absoluta
        }

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
     * Agrega un comando al historial
     * @param {string} instruction - Instrucción original
     * @param {string} command - Comando ejecutado
     */
    addToHistory(instruction, command) {
        this.commandHistory.push({
            instruction: instruction,
            command: command,
            timestamp: new Date
                    /**
                     * Agrega un comando al historial
                     * @param {string} instruction - Instrucción original
                     * @param {string} command - Comando ejecutado
                     */
                    addToHistory(instruction, command) {
                        this.commandHistory.push({
                            instruction: instruction,
                            command: command,
                            timestamp: new Date()
                        });

                        // Mantener el historial a un tamaño razonable
                        if (this.commandHistory.length > 100) {
                            this.commandHistory.shift(); // Eliminar el comando más antiguo
                        }
                    }

                    /**
                     * Obtiene el historial de comandos
                     * @param {number} limit - Número máximo de comandos a devolver (opcional)
                     * @returns {Array} Historial de comandos
                     */
                    getCommandHistory(limit = 0) {
                        if (limit > 0) {
                            return this.commandHistory.slice(-limit);
                        }
                        return [...this.commandHistory];
                    }

                    /**
                     * Busca en el historial de comandos
                     * @param {string} searchTerm - Término de búsqueda
                     * @returns {Array} Comandos que coinciden con la búsqueda
                     */
                    searchCommandHistory(searchTerm) {
                        if (!searchTerm) return [];

                        const term = searchTerm.toLowerCase();
                        return this.commandHistory.filter(entry => 
                            entry.instruction.toLowerCase().includes(term) || 
                            entry.command.toLowerCase().includes(term)
                        );
                    }

                    /**
                     * Limpia el historial de comandos
                     */
                    clearCommandHistory() {
                        this.commandHistory = [];
                    }

                    /**
                     * Sugiere comandos basados en una entrada parcial
                     * @param {string} partialInput - Entrada parcial del usuario
                     * @returns {Array} Lista de sugerencias de comandos
                     */
                    suggestCommands(partialInput) {
                        if (!partialInput || partialInput.length < 2) return [];

                        const input = partialInput.toLowerCase();
                        const suggestions = [];

                        // Buscar en el historial de comandos
                        const historySuggestions = this.commandHistory
                            .filter(entry => entry.instruction.toLowerCase().startsWith(input))
                            .map(entry => entry.instruction)
                            .slice(-5); // Limitar a 5 sugerencias del historial

                        suggestions.push(...historySuggestions);

                        // Sugerencias basadas en patrones comunes
                        if (input.startsWith('crear') || input.startsWith('nuevo')) {
                            suggestions.push('crear archivo');
                            suggestions.push('crear directorio');
                            suggestions.push('crear archivo con contenido');
                        } else if (input.startsWith('eliminar') || input.startsWith('borrar')) {
                            suggestions.push('eliminar archivo');
                            suggestions.push('eliminar directorio');
                        } else if (input.startsWith('mostrar') || input.startsWith('ver')) {
                            suggestions.push('mostrar archivos');
                            suggestions.push('mostrar directorio actual');
                            suggestions.push('mostrar contenido del archivo');
                        } else if (input.startsWith('instalar')) {
                            suggestions.push('instalar paquete');
                            suggestions.push('instalar dependencia');
                        }

                        // Eliminar duplicados y devolver las sugerencias únicas
                        return [...new Set(suggestions)];
                    }
                }

                // Exportar la clase para uso en otros módulos
                if (typeof module !== 'undefined' && module.exports) {
                    module.exports = NaturalCommandProcessor;
                } else {
                    // Para uso en navegador
                    window.NaturalCommandProcessor = NaturalCommandProcessor;
                }

