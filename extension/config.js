const vscode = require('vscode');

class Config {

    static get settings() {
        return vscode.workspace.getConfiguration('mn');
    }

    static get aiProvider() {
        return this.settings.get('provider');
    }

    static get endpoint() {
        return this.settings.get('endpoint');
    }

    static get apiKey() {
        return this.settings.get('apiKey');
    }

    static get model() {
        return this.settings.get('model');
    }

    static get prompt() {
        return this.language === 'Português (BR)'
            ? 'Detecte vulnerabilidades no código e diga o tipo:'
            : 'Detect vulnerabilities in the code and say the type:';
    }

    static validate() {

        if (!this.endpoint) {
            throw new Error('Endpoint not configured');
        }
    }
}

module.exports = Config;