/* const vscode = require('vscode');
const { GoogleGenerativeAI } = require('@google/generative-ai');
const Config = require('./config');

class CodeAnalyzerService {
    constructor() {
        this.logger = vscode.window.createOutputChannel('Code Analyzer');
    }

    logError(message) {
        this.logger.appendLine(`[ERROR] ${message}`);
    }

    logInfo(message) {
        this.logger.appendLine(`[INFO] ${message}`);
    }

    async analyzeWithChatGPT(code) {
        const request = {
            model: 'gpt-3.5-turbo',
            messages: [
                {
                    role: 'system',
                    content: `${Config.prompt} \n${code}\n`,
                },
            ],
        };

        const response = await fetch('https://api.openai.com/v1/chat/completions', {
            method: 'POST',
            headers: {
                Accept: 'application/json',
                'Content-Type': 'application/json',
                Authorization: `Bearer ${Config.openaiApiKey}`,
            },
            body: JSON.stringify(request),
        });

        const json = await response.json();

        if (!response.ok) {
            this.logError(`OpenAI API Error: ${json.error.message}`);
            throw new Error(json.error.message);
        }

        return json.choices[0].message.content;
    }

    async analyzeWithGemini(code) {
        const genAI = new GoogleGenerativeAI(Config.geminiApiKey);
        const model = genAI.getGenerativeModel({ model: 'gemini-2.5-flash' });

        const result = await model.generateContent(`${Config.prompt} \n${code}\n`);
        return result.response.text();
    }

    async analyzeWithOllama(code) {
        const endpoint = Config.ollamaEndpoint || 'http://localhost:11434';
        const model = Config.ollamaModel;

        const response = await fetch(`${endpoint}/api/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                model: model,
                prompt: `${Config.prompt} \n${code}\n`,
                stream: false
            }),
        });

        if (!response.ok) {
            const error = await response.text();
            this.logError(`Ollama API Error: ${error}`);
            throw new Error(`Ollama API Error: ${error}`);
        }

        const json = await response.json();
        return json.response;
    }

    async analyzeCode(code) {
        try {
            Config.validateApiKeys();
            this.logInfo('Starting code analysis...');

            let responseMessage;
            switch (Config.aiProvider) {
                case 'chatgpt':
                    responseMessage = await this.analyzeWithChatGPT(code);
                    break;
                case 'gemini':
                    responseMessage = await this.analyzeWithGemini(code);
                    break;
                case 'ollama':
                    responseMessage = await this.analyzeWithOllama(code);
                    break;
                default:
                    throw new Error('Invalid AI provider selected');
            }

            this.createResultPanel(responseMessage);
            this.logInfo('Analysis completed successfully');
            vscode.window.showInformationMessage('Vulnerability Analysis complete.');
        } catch (error) {
            this.logError(`Error during analysis: ${error.message}`);
            vscode.window.showErrorMessage(`Error analyzing code: ${error.message}`);
            throw error;
        }
    }

    createResultPanel(responseMessage) {
        const panel = vscode.window.createWebviewPanel(
            'vulnerabilityAnalysis',
            'Vulnerability Analysis',
            vscode.ViewColumn.Beside,
            {}
        );

        panel.webview.html = this.generateHtml(responseMessage);
    }

    generateHtml(responseMessage) {
        return `
            <html>
            <head>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        padding: 10px;
                    }
                    h1 {
                        padding: 10px;
                    }
                    .content {
                        font-size: 18px;
                    }
                    pre {
                        white-space: pre-wrap;
                        max-width: 100%;
                        overflow: auto;
                        padding: 10px;
                    }
                    .ai-provider {
                        font-size: 16px;
                        color: #555;
                        margin-bottom: 20px;
                    }
                </style>
                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/default.min.css">
                <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
                <script>hljs.highlightAll();</script>
            </head>
            <body>
                <h1>Vulnerability Analysis</h1>
                <div class="ai-provider">AI Provider: ${Config.aiProvider.toUpperCase()}</div>
                <div class="content">
                    <pre><code class="javascript">${responseMessage}</code></pre>
                </div>
            </body>
            </html>`;
    }
}

module.exports = CodeAnalyzerService;

const vscode = require('vscode');
const Config = require('./config');

class CodeAnalyzerService {
    constructor() {
        this.logger = vscode.window.createOutputChannel('Code Analyzer');
    }

    logError(message) {
        this.logger.appendLine(`[ERROR] ${message}`);
    }

    logInfo(message) {
        this.logger.appendLine(`[INFO] ${message}`);
    }

    // ==============================
    // Ollama
    // ==============================
    async analyzeWithOllama(code) {
        const endpoint = Config.ollamaEndpoint || 'http://localhost:11434/v1/messages';
        const model = Config.ollamaModel || 'llama3';

        const start = Date.now();

        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'x-api-key': 'ollama',
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json'
            },
            body: JSON.stringify({
                model: model,
                max_tokens: 1024,
                temperature: 0,
                messages: [
                    {
                        role: 'user',
                        content: `${Config.prompt}\n${code}`
                    }
                ]
            }),
        });

        const latency = Date.now() - start;
        this.logInfo(`Latency: ${latency} ms`);

        if (!response.ok) {
            const error = await response.text();
            this.logError(`Ollama API Error: ${error}`);
            throw new Error(`Ollama API Error: ${error}`);
        }

        const json = await response.json();

        if (!json.content) {
            throw new Error('Invalid response from Ollama');
        }

        return json.content[0].text;
    }

    // ==============================
    // analise principal
    // ==============================
    async analyzeCode(code) {
        try {
            this.logInfo('Starting code analysis with Ollama...');

            const responseMessage = await this.analyzeWithOllama(code);

            this.createResultPanel(responseMessage);

            this.logInfo('Analysis completed successfully');
            vscode.window.showInformationMessage('Vulnerability Analysis complete.');
        } catch (error) {
            this.logError(`Error during analysis: ${error.message}`);
            vscode.window.showErrorMessage(`Error analyzing code: ${error.message}`);
            throw error;
        }
    }

    // ==============================
    // UI
    // ==============================
    createResultPanel(responseMessage) {
        const panel = vscode.window.createWebviewPanel(
            'vulnerabilityAnalysis',
            'Vulnerability Analysis',
            vscode.ViewColumn.Beside,
            {}
        );

        panel.webview.html = this.generateHtml(responseMessage);
    }

    generateHtml(responseMessage) {
        return `
            <html>
            <head>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        padding: 10px;
                    }
                    h1 {
                        padding: 10px;
                    }
                    .content {
                        font-size: 16px;
                    }
                    pre {
                        white-space: pre-wrap;
                        max-width: 100%;
                        overflow: auto;
                        padding: 10px;
                        background: #1e1e1e;
                        color: #dcdcdc;
                        border-radius: 8px;
                    }
                    .ai-provider {
                        font-size: 14px;
                        color: #888;
                        margin-bottom: 10px;
                    }
                </style>
            </head>
            <body>
                <h1>Vulnerability Analysis</h1>
                <div class="ai-provider">AI Provider: OLLAMA (Anthropic Compatible)</div>
                <div class="content">
                    <pre>${responseMessage}</pre>
                </div>
            </body>
            </html>`;
    }
}

module.exports = CodeAnalyzerService;

const vscode = require('vscode');
const Config = require('./config');
const fetch = global.fetch || require('node-fetch');

class CodeAnalyzerService {
    constructor() {
        this.logger = vscode.window.createOutputChannel('Code Analyzer');
    }

    log(message) {
        this.logger.appendLine(message);
    }

    // ==============================
    // OLLAMA
    // ==============================
    async analyzeAnthropic(code) {
        const response = await fetch(Config.endpoint, {
            method: 'POST',
            headers: {
                'x-api-key': Config.apiKey,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json'
            },
            body: JSON.stringify({
                model: Config.model,
                max_tokens: 1024,
                messages: [
                    {
                        role: 'user',
                        content: `${Config.prompt}\n${code}`
                    }
                ]
            })
        });

        if (!response.ok) {
            throw new Error(await response.text());
        }

        const json = await response.json();
        return json.content?.[0]?.text || 'No response';
    }

    // ==============================
    // OPENAI (Mistral / DeepSeek)
    // ==============================
    async analyzeOpenAI(code) {
        const response = await fetch(Config.endpoint, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${Config.apiKey}`,
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
                temperature: 0
            })
        });

        if (!response.ok) {
            throw new Error(await response.text());
        }

        const json = await response.json();
        return json.choices?.[0]?.message?.content || 'No response';
    }

    // ==============================
    // MAIN
    // ==============================
    async analyzeCode(code) {
        try {
            Config.validate();

            this.log(`Provider: ${Config.aiProvider}`);
            this.log(`Model: ${Config.model}`);

            const start = Date.now();

            let result;

            if (Config.aiProvider === 'ollama') {
                result = await this.analyzeAnthropic(code);
            } else {
                result = await this.analyzeOpenAI(code);
            }

            const latency = Date.now() - start;
            this.log(`Latency: ${latency} ms`);

            this.showResult(result, latency);

        } catch (error) {
            vscode.window.showErrorMessage(error.message);
        }
    }

    // ==============================
    // UI
    // ==============================
    showResult(text, latency) {
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
            <p><b>Latency:</b> ${latency} ms</p>
            <pre>${text}</pre>
        </body>
        </html>`;
    }
}

module.exports = CodeAnalyzerService; 


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

    const start = Date.now();

    let response;

    console.log("Provider:", Config.aiProvider);

    // ===============================
    // OLLAMA (LOCAL)
    // ===============================
    if (Config.aiProvider === 'ollama') {

        response = await fetch(Config.endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: Config.model,
                prompt: `${Config.prompt}\n${code}`,
                stream: false
            })
        });

        if (!response.ok) {
            throw new Error(await response.text());
        }

        const json = await response.json();
        const result = json.response || 'No response';

        this.showResult(result, Date.now() - start);
        return;
    }

    // ===============================
    // ANTHROPIC (Claude)
    // ===============================
    if (Config.aiProvider === 'anthropic') {

        response = await fetch(Config.endpoint, {
            method: 'POST',
            headers: {
                'x-api-key': Config.apiKey,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json'
            },
            body: JSON.stringify({
                model: Config.model,
                max_tokens: 1024,
                messages: [
                    {
                        role: 'user',
                        content: `${Config.prompt}\n${code}`
                    }
                ]
            })
        });

        if (!response.ok) {
            throw new Error(await response.text());
        }

        const json = await response.json();
        const result = json.content?.[0]?.text || 'No response';

        this.showResult(result, Date.now() - start);
        return;
    }

    // ===============================
    // MISTRAL
    // ===============================
    if (Config.aiProvider === 'mistral') {

        response = await fetch(Config.endpoint, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${Config.apiKey}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: Config.model,
                messages: [
                    {
                        role: 'user',
                        content: `${Config.prompt}\n${code}`
                    }
                ]
            })
        });

        if (!response.ok) {
            throw new Error(await response.text());
        }

        const json = await response.json();
        const result = json.choices?.[0]?.message?.content || 'No response';

        this.showResult(result, Date.now() - start);
        return;
    }

    // ===============================
    // DEEPSEEK
    // ===============================
    if (Config.aiProvider === 'deepseek') {

    response = await fetch(Config.endpoint, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${Config.apiKey}`,
            'Content-Type': 'application/json',
            'HTTP-Referer': 'http://localhost',
            'X-Title': 'mn-analise'
        },
        body: JSON.stringify({
            model: Config.model,
            messages: [
                {
                    role: 'user',
                    content: `${Config.prompt}\n${code}`
                }
            ]
        })
    });

    if (!response.ok) {
        throw new Error(await response.text());
    }

    const json = await response.json();

    const result = json.choices?.[0]?.message?.content || 'No response';

    const latency = Date.now() - start;

    this.showResult(result, latency);
    return;
}

    // ===============================
    // FALLBACK
    // ===============================
    throw new Error(`Provider not supported: ${Config.aiProvider}`);
}

    showResult(text, latency) {

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
            <p><b>Latency:</b> ${latency} ms</p>
            <pre>${text}</pre>
        </body>
        </html>`;
    }
}

module.exports = CodeAnalyzerService;

*/

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
    const start = Date.now();

    let result;

    switch (Config.aiProvider) {

        case 'ollama':
            result = await this.callOllama(code);
            break;

        case 'anthropic':
            result = await this.callAnthropic(code);
            break;

        case 'mistral':
            result = await this.callMistral(code);
            break;

        case 'gemma':
            result = await this.callGemma(code);
            break;

        default:
            throw new Error(`Unsupported provider: ${Config.aiProvider}`);
    }

    this.showResult(result, Date.now() - start);
}

    // =========================
    // OLLAMA
    // =========================
    async callOllama(code) {

    const res = await fetch(Config.endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            model: Config.model, // 👈 AQUI GEMMA OU LLAMA
            prompt: `${Config.prompt}\n\n${code}`,
            stream: false
        })
    });

    const json = await res.json();

    console.log("OLLAMA RAW:", json);

    return (
        json?.response ||
        json?.message?.content ||
        json?.output ||
        "EMPTY_RESPONSE"
    );
}

    // =========================
    // ANTHROPIC
    // =========================
    async callAnthropic(code) {
        const res = await fetch(Config.endpoint, {
            method: 'POST',
            headers: {
                'x-api-key': Config.apiKey,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json'
            },
            body: JSON.stringify({
                model: Config.model,
                max_tokens: 1024,
                messages: [{
                    role: 'user',
                    content: `${Config.prompt}\n${code}`
                }]
            })
        });

        const json = await res.json();
        return json.content?.[0]?.text;
    }

    // =========================
    // MISTRAL
    // =========================
    async callMistral(code) {
        const res = await fetch(Config.endpoint, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${Config.apiKey}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: Config.model,
                messages: [{
                    role: 'user',
                    content: `${Config.prompt}\n${code}`
                }]
            })
        });

        const json = await res.json();
        return json.choices?.[0]?.message?.content;
    }

    // =========================
    // GEMMA
    // =========================
    async callGemma(code) {

    const res = await fetch(Config.endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            model: 'gemma3',
            messages: [
                {
                    role: 'user',
                    content: `${Config.prompt}\n\n${code}`
                }
            ],
            stream: false
        })
    });

    const json = await res.json();

    console.log("GEMMA RAW:", json);

    const result =
        json?.message?.content ??
        json?.response ??
        json?.output ??
        json?.choices?.[0]?.message?.content;

    if (!result) {
        console.log("UNKNOWN FORMAT:", json);
    }

    return result || "EMPTY_RESPONSE";
}
    // =========================
    // UI
    // =========================
    showResult(text, latency) {
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
            <p><b>Latency:</b> ${latency} ms</p>
            <pre>${text}</pre>
        </body>
        </html>`;
    }
}

module.exports = CodeAnalyzerService;