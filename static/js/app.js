// Codestorm-Assistant main JavaScript file

document.addEventListener('DOMContentLoaded', function() {
    // Initialize app
    const app = {
        currentDirectory: '.',
        commandHistory: [],
        historyIndex: -1,
        
        // DOM elements
        elements: {
            instructionInput: document.getElementById('instruction-input'),
            executeBtn: document.getElementById('execute-btn'),
            commandDisplay: document.getElementById('command-display'),
            outputDisplay: document.getElementById('output-display'),
            fileExplorer: document.getElementById('file-explorer'),
            directoryPath: document.getElementById('directory-path'),
            statusIndicator: document.getElementById('status-indicator'),
            clearBtn: document.getElementById('clear-btn'),
            refreshBtn: document.getElementById('refresh-btn'),
            previousBtn: document.getElementById('previous-btn'),
            nextBtn: document.getElementById('next-btn')
        },
        
        init: function() {
            this.bindEvents();
            this.updateFileExplorer();
            this.checkServerStatus();
        },
        
        bindEvents: function() {
            // Execute button
            this.elements.executeBtn.addEventListener('click', () => this.processInstruction());
            
            // Clear button
            this.elements.clearBtn.addEventListener('click', () => this.clearTerminal());
            
            // Refresh button
            this.elements.refreshBtn.addEventListener('click', () => this.updateFileExplorer());
            
            // Command history navigation
            this.elements.previousBtn.addEventListener('click', () => this.navigateHistory(-1));
            this.elements.nextBtn.addEventListener('click', () => this.navigateHistory(1));
            
            // Enter key in textarea
            this.elements.instructionInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                    e.preventDefault();
                    this.processInstruction();
                }
            });
        },
        
        checkServerStatus: function() {
            fetch('/api/process_instructions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ instruction: 'echo "Hello"' })
            })
            .then(response => {
                if (response.ok) {
                    this.elements.statusIndicator.classList.remove('status-disconnected');
                    this.elements.statusIndicator.classList.add('status-connected');
                    this.elements.statusIndicator.title = 'Connected to server';
                } else {
                    throw new Error('Server error');
                }
            })
            .catch(error => {
                this.elements.statusIndicator.classList.remove('status-connected');
                this.elements.statusIndicator.classList.add('status-disconnected');
                this.elements.statusIndicator.title = 'Disconnected from server';
                console.error('Server status check failed:', error);
            });
        },
        
        processInstruction: function() {
            const instruction = this.elements.instructionInput.value.trim();
            if (!instruction) return;
            
            // Add loading indicator
            this.elements.executeBtn.classList.add('loading');
            
            // Save to history
            this.commandHistory.push(instruction);
            this.historyIndex = this.commandHistory.length;
            
            // Get the selected model (default to OpenAI)
            const modelSelect = document.getElementById('model-select');
            const selectedModel = modelSelect ? modelSelect.value : 'openai';
            
            // Process the instruction through the Flask backend
            fetch('/api/process_instructions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    instruction: instruction,
                    model: selectedModel
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    this.displayError(data.error);
                    return;
                }
                
                const command = data.command;
                this.elements.commandDisplay.textContent = command;
                
                // Execute the command
                return fetch('/api/execute_command', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ command: command })
                });
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    this.displayError(data.error);
                    return;
                }
                
                // Display command output
                let output = '';
                if (data.stdout) output += data.stdout;
                if (data.stderr) output += '\n' + data.stderr;
                
                this.elements.outputDisplay.textContent = output;
                
                // Update file explorer after command execution
                this.updateFileExplorer();
            })
            .catch(error => {
                console.error('Error:', error);
                this.displayError('Failed to process instruction: ' + error.message);
            })
            .finally(() => {
                // Remove loading indicator
                this.elements.executeBtn.classList.remove('loading');
            });
        },
        
        displayError: function(errorMessage) {
            const errorDiv = document.createElement('div');
            errorDiv.classList.add('alert', 'alert-danger', 'mt-2');
            errorDiv.textContent = errorMessage;
            
            this.elements.outputDisplay.textContent = '';
            this.elements.outputDisplay.appendChild(errorDiv);
        },
        
        clearTerminal: function() {
            this.elements.commandDisplay.textContent = '';
            this.elements.outputDisplay.textContent = '';
            this.elements.instructionInput.value = '';
        },
        
        updateFileExplorer: function() {
            fetch('/api/list_files', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ directory: this.currentDirectory })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    this.displayFileExplorerError(data.error);
                    return;
                }
                
                this.elements.directoryPath.textContent = this.currentDirectory;
                this.renderFileExplorer(data.files);
            })
            .catch(error => {
                console.error('Error fetching files:', error);
                this.displayFileExplorerError('Failed to fetch files: ' + error.message);
            });
        },
        
        renderFileExplorer: function(files) {
            const fileExplorer = this.elements.fileExplorer;
            fileExplorer.innerHTML = '';
            
            // Add parent directory navigation if not in root
            if (this.currentDirectory !== '.') {
                const parentItem = this.createFileItem('..', 'directory');
                parentItem.addEventListener('click', () => {
                    this.navigateToDirectory('..');
                });
                fileExplorer.appendChild(parentItem);
            }
            
            // Sort files - directories first, then alphabetically
            files.sort((a, b) => {
                if (a.type !== b.type) {
                    return a.type === 'directory' ? -1 : 1;
                }
                return a.name.localeCompare(b.name);
            });
            
            // Add file items
            files.forEach(file => {
                if (file.name === '.' || file.name === '..') return;
                
                const fileItem = this.createFileItem(file.name, file.type);
                
                // Add click handler
                fileItem.addEventListener('click', () => {
                    if (file.type === 'directory') {
                        this.navigateToDirectory(file.name);
                    } else {
                        // For files, we could implement a file viewer or editor in the future
                        this.elements.instructionInput.value = `cat "${this.currentDirectory}/${file.name}"`;
                        this.processInstruction();
                    }
                });
                
                fileExplorer.appendChild(fileItem);
            });
        },
        
        createFileItem: function(name, type) {
            const item = document.createElement('div');
            item.classList.add('file-item', 'd-flex', 'align-items-center');
            
            const icon = document.createElement('i');
            icon.classList.add('file-icon');
            
            if (type === 'directory') {
                icon.classList.add('bi', 'bi-folder-fill');
                item.classList.add('directory');
            } else {
                icon.classList.add('bi', 'bi-file-text');
                item.classList.add('file');
            }
            
            const nameSpan = document.createElement('span');
            nameSpan.textContent = name;
            
            item.appendChild(icon);
            item.appendChild(nameSpan);
            
            return item;
        },
        
        navigateToDirectory: function(dirName) {
            let newPath;
            
            if (dirName === '..') {
                // Navigate to parent directory
                const parts = this.currentDirectory.split('/');
                parts.pop();
                newPath = parts.join('/') || '.';
            } else if (dirName.startsWith('/')) {
                // Absolute path
                newPath = dirName;
            } else {
                // Relative path
                newPath = this.currentDirectory === '.' 
                    ? dirName 
                    : `${this.currentDirectory}/${dirName}`;
            }
            
            this.currentDirectory = newPath;
            this.updateFileExplorer();
        },
        
        displayFileExplorerError: function(errorMessage) {
            this.elements.fileExplorer.innerHTML = '';
            
            const errorDiv = document.createElement('div');
            errorDiv.classList.add('alert', 'alert-danger');
            errorDiv.textContent = errorMessage;
            
            this.elements.fileExplorer.appendChild(errorDiv);
        },
        
        navigateHistory: function(direction) {
            if (this.commandHistory.length === 0) return;
            
            this.historyIndex += direction;
            
            // Ensure index stays within bounds
            if (this.historyIndex < 0) this.historyIndex = 0;
            if (this.historyIndex >= this.commandHistory.length) {
                this.historyIndex = this.commandHistory.length - 1;
            }
            
            // Set the input value to the command at the current index
            this.elements.instructionInput.value = this.commandHistory[this.historyIndex];
        }
    };
    
    // Initialize the app
    app.init();
});
