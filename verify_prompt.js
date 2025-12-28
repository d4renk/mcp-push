const { spawn } = require('child_process');
const path = require('path');

const serverPath = path.join(__dirname, 'apps/mcp-server/build/index.js');
console.log('Starting server at:', serverPath);
const server = spawn('node', [serverPath], {
    cwd: '/home/sun/mcp-push'
});

let buffer = '';

server.stdout.on('data', (data) => {
    const chunk = data.toString();
    // console.log('RAW:', chunk);
    buffer += chunk;

    const lines = buffer.split('\n');
    buffer = lines.pop(); // Keep incomplete line

    for (const line of lines) {
        if (!line.trim()) continue;
        try {
            const msg = JSON.parse(line);
            console.log('Received:', JSON.stringify(msg, null, 2));

            if (msg.id === 1 && msg.result) {
                // List prompts result
                console.log('Prompts listed successfully.');
                // Now get the prompt
                const getPrompt = {
                    jsonrpc: '2.0',
                    id: 2,
                    method: 'prompts/get',
                    params: { name: 'mcp-push-usage' }
                };
                server.stdin.write(JSON.stringify(getPrompt) + '\n');
            } else if (msg.id === 2 && msg.result) {
                console.log('Prompt content retrieved successfully.');
                if (msg.result.messages[0].content[0].text.includes('mcp-push')) {
                    console.log('Verification PASSED: Found "mcp-push" in prompt text.');
                } else {
                    console.log('Verification FAILED: Prompt text does not look right.');
                }
                process.exit(0);
            }
        } catch (e) {
            // Not JSON or partial JSON
        }
    }
});

server.stderr.on('data', (data) => {
    console.error(`STDERR: ${data}`);
});

const listPrompts = {
    jsonrpc: '2.0',
    id: 1,
    method: 'prompts/list',
    params: {}
};

// Wait a bit for server to start
setTimeout(() => {
    console.log('Sending list prompts request...');
    server.stdin.write(JSON.stringify(listPrompts) + '\n');
}, 2000);

setTimeout(() => {
    console.log('Timeout reached, killing server.');
    server.kill();
}, 10000);
