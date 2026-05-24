const vscode = require('vscode');
const fetch = global.fetch || require('node-fetch');
const Config = require('./config');

class CodeAnalyzerService {

    constructor() {
        this.logger = vscode.window.createOutputChannel('Code Analyzer');
    }

    log(msg) {
        this.logger.appendLine(msg);
    }

    async analyze(code) {

        Config.validate();

        const result = await this.callOllama(code);

        this.showResult(result);
    }

    // =====================================
    // OLLAMA
    // =====================================
    async callOllama(code) {

        const res = await fetch(Config.endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: Config.model,
                messages: [
                    {
                        role: 'user',
                        content: `${Config.prompt}\n${code}`
                    }
                ],
                stream: false
            })
        });

        if (!res.ok) {
            throw new Error(await res.text());
        }

        const json = await res.json();

        console.log('OLLAMA RAW:', json);

        return (
            json?.message?.content ||
            json?.response ||
            json?.output ||
            'EMPTY_RESPONSE'
        );
    }

    // =====================================
    // UI
    // =====================================
    showResult(text) {

        const panel = vscode.window.createWebviewPanel(
            'analysis',
            'Vulnerability Analysis',
            vscode.ViewColumn.Beside,
            {}
        );

        panel.webview.html = `
        <html>
        <body style="font-family: Arial; padding: 10px;">

            <h2>Vulnerability Analysis</h2>

            <p><b>Provider:</b> ${Config.aiProvider}</p>
            <p><b>Model:</b> ${Config.model}</p>

            <pre>${text}</pre>

        </body>
        </html>`;
    }
}

module.exports = CodeAnalyzerService;