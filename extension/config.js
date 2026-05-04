/* const vscode = require('vscode');

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
            case 'gemma':
                return 'gemma';
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
            case 'gemma':
                return 'https://api.gemma.ai/v1/chat/completions';
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
            case 'gemma':
                return this.gemmaApiKey;
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
        if ((this.aiProvider === 'ollama' || this.aiProvider === 'gemma') && !this.ollamaModel) {
        throw new Error('Ollama model missing');
        }

        }
    }

module.exports = Config;

*/

const vscode = require('vscode');

class Config {

    // =========================
    // SETTINGS BASE
    // =========================
    static get settings() {
        return vscode.workspace.getConfiguration();
    }

    static get aiProvider() {
        return this.settings.get('mn-analise.02.aiProvider')?.toLowerCase().trim();
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

    static get ollamaModel() {
        return this.settings.get('mn-analise.05.ollamaModel');
    }

    static get ollamaEndpoint() {
        return this.settings.get('mn-analise.06.ollamaEndpoint');
    }

    // =========================
    // PROMPT
    // =========================
    static get prompt() {
        return this.language === 'Português (BR)'
            ? 'Detecte vulnerabilidades no código e diga o tipo:'
            : 'Detect vulnerabilities in the code and say the type:';
    }

    // =========================
    // MODEL
    // =========================
    static get model() {
        switch (this.aiProvider) {

            case 'anthropic':
                return 'claude-3-haiku-20240307';

            case 'mistral':
                return 'mistral-small';

            case 'ollama':
                return this.ollamaModel || 'llama3';

            case 'gemma':
                return 'gemma3';

            default:
                return this.ollamaModel || 'llama3';
        }
    }

    // =========================
    // ENDPOINT
    // =========================
    static get endpoint() {
        switch (this.aiProvider) {

            case 'anthropic':
                return 'https://api.anthropic.com/v1/messages';

            case 'mistral':
                return 'https://api.mistral.ai/v1/chat/completions';

            case 'ollama':
                return this.ollamaEndpoint;

            case 'gemma':
                return 'http://localhost:11434/api/chat';

            default:
                return this.ollamaEndpoint;
        }
    }

    // =========================
    // API KEY
    // =========================
    static get apiKey() {
        switch (this.aiProvider) {

            case 'anthropic':
                return this.anthropicApiKey;

            case 'mistral':
                return this.mistralApiKey;

            default:
                return null;
        }
    }

    // =========================
    // VALIDATION
    // =========================
    static validate() {

        const provider = this.aiProvider;

        if (!provider) {
            throw new Error('AI provider not configured');
        }

        if (provider === 'anthropic' && !this.anthropicApiKey) {
            throw new Error('Anthropic API key missing');
        }

        if (provider === 'mistral' && !this.mistralApiKey) {
            throw new Error('Mistral API key missing');
        }

        if (provider === 'ollama' && !this.ollamaModel) {
            throw new Error('Ollama model missing (e.g. llama3, gemma3)');
        }
    }
}

module.exports = Config;