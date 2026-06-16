# SegAud

Repositório desenvolvido para a disciplina de **Segurança e Auditoria de Sistemas** do curso de **Bacharelado em Sistemas de Informação** do **Centro Federal de Educação Tecnológica Celso Suckow da Fonseca (CEFET/RJ)**, campus Nova Friburgo.

O projeto também fundamenta o artigo **"Benchmarking de LLMs Open Source para análise de segurança de código: uma abordagem comparativa"**, de **Maria Clara M. Pacheco** e **Yuri V. Carvalho**.

Contatos: `maria.pacheco@aluno.cefet-rj.br`, `yuri.carvalho@aluno.cefet-rj.br`

## Objetivo

O objetivo deste projeto é comparar modelos de linguagem open source na tarefa de identificar vulnerabilidades de segurança em trechos de código PHP. Para isso, o repositório reúne:

- uma suíte de testes com exemplos de código vulnerável;
- um script de benchmark executado localmente via Ollama;
- métricas quantitativas de avaliação, como accuracy, precision, recall e F1-score;
- geração de gráficos para apoiar a análise comparativa;
- uma extensão experimental para VS Code que envia código selecionado a um modelo local para análise de vulnerabilidades.

## Origem da Suíte de Vulnerabilidades

Os cenários de vulnerabilidade utilizados no arquivo `benchmark/security_php.yaml` foram obtidos a partir do repositório open source [rapticore/llm-security-benchmark](https://github.com/rapticore/llm-security-benchmark), criado pela Rapticore Security Research Team para avaliação de modelos de linguagem em tarefas de análise de segurança e detecção de vulnerabilidades em código.

Neste projeto, essa suíte foi usada como base para uma abordagem comparativa focada em LLMs open source executados localmente via Ollama.

## Estrutura do Repositório

```text
.
+-- benchmark/
|   +-- benchmark.py
|   +-- security_php.yaml
+-- extension/
|   +-- codeAnalyzerService.js
|   +-- config.js
|   +-- extension.js
|   +-- package.json
+-- README.md
```

## Benchmark

O benchmark está localizado em `benchmark/` e avalia a capacidade dos modelos de detectar vulnerabilidades presentes nos cenários definidos em `security_php.yaml`.

As categorias de vulnerabilidade incluem:

- SQL Injection;
- Code Injection;
- File Inclusion;
- Command Injection;
- XML External Entity (XXE);
- insegurança em desserialização;
- Type Juggling;
- Session Fixation;
- Cross-Site Request Forgery (CSRF);
- criptografia fraca;
- Path Traversal.

O script `benchmark.py` executa cada caso de teste contra os modelos configurados, avalia as respostas com expressões regulares e consolida os resultados em métricas de desempenho.

### Modelos Avaliados

Os modelos configurados no benchmark são:

- `granite4.1:3b`
- `gemma4:latest`
- `falcon3:latest`
- `deepseek-coder:latest`
- `yi-coder:latest`
- `stable-code:latest`
- `laguna-xs.2:latest`
- `exaone-deep:latest`

## Métricas e Saídas

Ao final da execução, o benchmark gera:

- `benchmark_results.csv`: tabela com métricas por modelo;
- `benchmark_f1.png`: gráfico de barras com F1-score;
- `benchmark_metrics.png`: gráfico comparativo de accuracy, precision, recall e F1-score;
- `benchmark_heatmap.png`: mapa de acertos e falhas por categoria de vulnerabilidade;
- `benchmark_radar.png`: gráfico radar das métricas do primeiro modelo listado.

As métricas utilizadas são calculadas a partir de verdadeiros positivos, falsos positivos e falsos negativos identificados na resposta de cada modelo.

## Requisitos

- Python 3.10 ou superior;
- Ollama instalado e em execução local;
- modelos previamente baixados no Ollama;
- dependências Python:
  - `requests`
  - `PyYAML`
  - `pandas`
  - `matplotlib`

Instalação das dependências:

```bash
pip install requests pyyaml pandas matplotlib
```

Antes de executar o benchmark, verifique se o Ollama está disponível em:

```text
http://localhost:11434/api/chat
```

## Execução do Benchmark

Entre no diretório `benchmark/` e execute:

```bash
python benchmark.py
```

O script carregará os testes de `security_php.yaml`, enviará os prompts para cada modelo configurado e salvará os resultados no próprio diretório `benchmark/`.

## Extensão para VS Code

O diretório `extension/` contém uma extensão experimental chamada **MN Analise**, voltada para análise de vulnerabilidades em código aberto no editor.

A extensão:

- lê o código selecionado no editor ou o arquivo inteiro;
- envia o conteúdo para o endpoint configurado do Ollama;
- exibe a resposta do modelo em uma WebView lateral;
- permite configurar provedor, endpoint e modelo nas configurações `mn.*` do VS Code.

Configurações principais:

- `mn.endpoint`: endpoint da API local, por padrão `http://localhost:11434/api/chat`;
- `mn.model`: modelo usado na análise;
- `mn.provider`: provedor/modelo selecionado para identificação na interface.

## Observações

Este repositório tem finalidade acadêmica e experimental. Os resultados do benchmark dependem dos modelos instalados, das versões disponíveis no Ollama, dos prompts utilizados e dos critérios definidos em `security_php.yaml`.

As análises produzidas por LLMs não substituem auditorias manuais, ferramentas SAST especializadas ou revisão de segurança conduzida por profissionais.
