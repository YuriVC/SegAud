const vscode = require('vscode');

class Config {

    // ==============================
    // Anthropic
    // ==============================
    static get anthropicApiKey() {
        return vscode.workspace.getConfiguration().get('mn-analise.03.anthropicApiKey');
    }

    // ==============================
    // Ollama
    // ==============================
    static get ollamaModel() {
        return vscode.workspace.getConfiguration().get('mn-analise.05.ollamaModel');
    }

    static get ollamaEndpoint() {
        return vscode.workspace.getConfiguration().get('mn-analise.06.ollamaEndpoint');
    }

    // ==============================
    // config
    // ==============================
    static get preferredLanguage() {
        return vscode.workspace.getConfiguration().get('mn-analise.01.language');
    }

    static get aiProvider() {
        return vscode.workspace.getConfiguration().get('mn-analise.02.aiProvider');
    }

    // ==============================
    // prompt
    // ==============================
    static get prompt() {
        return this.preferredLanguage === 'Português (BR)'
            ? 'Detecte as vulnerabilidades no código e explique, se houver alguma: '
            : 'Detect the vulnerabilities in the code and explain, if there is any: ';
    }

    // ==============================
    // endpoint
    // ==============================
    static get endpoint() {
        if (this.aiProvider === 'anthropic') {
            return 'https://api.anthropic.com/v1/messages';
        }

        if (this.aiProvider === 'ollama') {
            return this.ollamaEndpoint || 'http://localhost:11434/v1/messages';
        }

        return '';
    }

    // ==============================
    // modelo
    // ==============================
    static get model() {
        if (this.aiProvider === 'anthropic') {
            return 'claude-3-haiku-20240307';
        }

        if (this.aiProvider === 'ollama') {
            return this.ollamaModel || 'llama3';
        }

        return '';
    }

    // ==============================
    // api key dinamica
    // ==============================
    static get apiKey() {
        if (this.aiProvider === 'anthropic') {
            return this.anthropicApiKey;
        }

        if (this.aiProvider === 'ollama') {
            return 'ollama'; // api key falso
        }

        return '';
    }

    // ==============================
    // validação
    // ==============================
    static validateApiKeys() {

        if (this.aiProvider === 'anthropic' && !this.anthropicApiKey) {
            throw new Error('Please set your Anthropic API Key in the settings of the MN-analise.');
        }

        if (this.aiProvider === 'ollama' && !this.ollamaModel) {
            throw new Error('Please set your Ollama model in the settings of the MN-analise.');
        }
    }
}

module.exports = Config;