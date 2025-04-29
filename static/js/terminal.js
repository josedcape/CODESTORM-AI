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
});