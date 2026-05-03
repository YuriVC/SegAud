const vscode = require('vscode');
const CodeAnalyzerService = require('./codeAnalyzerService');

function activate(context) {

    const service = new CodeAnalyzerService();

    const disposable = vscode.commands.registerCommand(
        'mn-analise.analyzeCodeCommand',
        () => {
            const editor = vscode.window.activeTextEditor;

            if (!editor) {
                vscode.window.showErrorMessage('No code selected');
                return;
            }

            const code = editor.document.getText(editor.selection)
                || editor.document.getText();

            service.analyze(code);
        }
    );

    context.subscriptions.push(disposable);
}

function deactivate() {}

module.exports = {
    activate,
    deactivate
};