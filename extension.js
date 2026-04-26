const vscode = require("vscode");
const { analyzeCode } = require("./codeAnalyzerService");

function activate(context) {

  let disposable = vscode.commands.registerCommand(
    "code-analyzer.analyze",
    async function () {

      const editor = vscode.window.activeTextEditor;

      if (!editor) {
        vscode.window.showErrorMessage("Nenhum arquivo aberto.");
        return;
      }

      const selection = editor.document.getText(editor.selection);

      if (!selection) {
        vscode.window.showWarningMessage("Selecione um trecho de código.");
        return;
      }

      vscode.window.showInformationMessage("Analisando código...");

      const result = await analyzeCode(selection);

      vscode.window.showInformationMessage("Análise concluída.");

      const panel = vscode.window.createOutputChannel("Code Analyzer");
      panel.clear();
      panel.appendLine(result);
      panel.show(true);
    }
  );

  context.subscriptions.push(disposable);
}

function deactivate() {}

module.exports = {
  activate,
  deactivate
};