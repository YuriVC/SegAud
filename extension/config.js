const vscode = require('vscode');

class Config {

    static get settings() {
        return vscode.workspace.getConfiguration();
    }

    static get aiProvider() {
        return this.settings.get('mn-analise.02.aiProvider');
    }

    static get language() {
        return this.settings.get('mn-analise.01.language');
    }

    static get anthropicApiKey() {
        return this.settings.get('mn-analise.03.anthropicApiKey');
    }

    static get mistralApiKey() {
        return this.settings.get('mn-analise.04.mistralApiKey');
    }

    static get qwenApiKey() {
        return this.settings.get('mn-analise.07.qwenApiKey');
    }

    static get ollamaModel() {
        return this.settings.get('mn-analise.05.ollamaModel');
    }

    static get ollamaEndpoint() {
        return this.settings.get('mn-analise.06.ollamaEndpoint');
    }

    static get prompt() {
        return this.language === 'Português (BR)'
            ? 'Detecte vulnerabilidades no código e diga o tipo:'
            : 'Detect vulnerabilities in the code and say the type:';
    }

    static get model() {
        switch (this.aiProvider) {
            case 'anthropic':
                return 'claude-3-haiku-20240307';
            case 'mistral':
                return 'mistral-small';
            case 'qwen':
                return 'qwen-plus';
            case 'ollama':
                return this.ollamaModel;
        }
    }

    static get endpoint() {
        switch (this.aiProvider) {
            case 'anthropic':
                return 'https://api.anthropic.com/v1/messages';
            case 'mistral':
                return 'https://api.mistral.ai/v1/chat/completions';
            case 'qwen':
                return 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation';
            case 'ollama':
                return this.ollamaEndpoint;
        }
    }

    static get apiKey() {
        switch (this.aiProvider) {
            case 'anthropic':
                return this.anthropicApiKey;
            case 'mistral':
                return this.mistralApiKey;
            case 'qwen':
                return this.qwenApiKey;
            default:
                return null;
        }
    }

    static validate() {
        if (this.aiProvider === 'anthropic' && !this.anthropicApiKey) {
            throw new Error('Anthropic API key missing');
        }
        if (this.aiProvider === 'mistral' && !this.mistralApiKey) {
            throw new Error('Mistral API key missing');
        }
        if (this.aiProvider === 'qwen' && !this.qwenApiKey) {
            throw new Error('Qwen API key missing');
        }
        if (this.aiProvider === 'ollama' && !this.ollamaModel) {
            throw new Error('Ollama model missing');
        }
    }
}

module.exports = Config;