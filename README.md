# Benchmark de LLMs open source via Ollama para análise de segurança de código PHP.

Repositório desenvolvido para a disciplina de **Segurança e Auditoria de Sistemas** do curso de **Bacharelado em Sistemas de Informação** do **Centro Federal de Educação Tecnológica Celso Suckow da Fonseca (CEFET/RJ)**, campus Nova Friburgo.

O projeto também fundamenta o artigo **"Benchmarking de LLMs Open Source para análise de segurança de código: uma abordagem comparativa"**, de **Maria Clara M. Pacheco** e **Yuri V. Carvalho**.

Contatos: `maria.pacheco@aluno.cefet-rj.br`, `yuri.carvalho@aluno.cefet-rj.br`

## Objetivo

O objetivo deste projeto é comparar modelos de linguagem open source disponíveis e executados localmente por meio do **Ollama** na tarefa de identificar vulnerabilidades de segurança em trechos de código PHP. Para isso, o repositório reúne:

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

### Modelos Ollama Avaliados

Os modelos configurados no benchmark são modelos executados localmente via Ollama:

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
pip install -r requirements.txt
```

Antes de executar o benchmark, verifique se o Ollama está disponível em:

```text
http://localhost:11434/api/chat
```

## Reprodutibilidade Automatizada

O repositório inclui dois scripts `.sh` para preparar o ambiente de execução.

### Como usar no Linux e macOS

No Linux ou macOS, abra um terminal na raiz do repositório e execute:

```bash
bash setup_minimal_reproducibility.sh
```

Se quiser permitir a instalação automática do Ollama:

```bash
INSTALL_OLLAMA=1 bash setup_minimal_reproducibility.sh
```

Também é possível dar permissão de execução ao script e rodar diretamente:

```bash
chmod +x setup_minimal_reproducibility.sh
./setup_minimal_reproducibility.sh
```

Para a reprodução completa no Linux ou macOS:

```bash
INSTALL_OLLAMA=1 PULL_MODELS=1 RUN_BENCHMARK=1 bash setup_reproducibility.sh
```

### Como usar no Windows

No Windows, recomenda-se usar **Git Bash** ou **WSL**, pois os scripts foram escritos em Bash.

Com Git Bash, abra o terminal na raiz do repositório e execute:

```bash
bash setup_minimal_reproducibility.sh
```

Para permitir a instalação automática do Ollama pelo `winget`:

```bash
INSTALL_OLLAMA=1 bash setup_minimal_reproducibility.sh
```

Se estiver usando PowerShell para chamar o Bash, defina as variáveis assim:

```powershell
$env:INSTALL_OLLAMA="1"
bash setup_minimal_reproducibility.sh
```

Para rodar sem executar o benchmark no PowerShell:

```powershell
$env:RUN_BENCHMARK="0"
bash setup_minimal_reproducibility.sh
```

Para limpar uma variável depois do uso no PowerShell:

```powershell
Remove-Item Env:INSTALL_OLLAMA
Remove-Item Env:RUN_BENCHMARK
```

Para a reprodução completa no Windows via Git Bash:

```bash
INSTALL_OLLAMA=1 PULL_MODELS=1 RUN_BENCHMARK=1 bash setup_reproducibility.sh
```

No Windows via PowerShell:

```powershell
$env:INSTALL_OLLAMA="1"
$env:PULL_MODELS="1"
$env:RUN_BENCHMARK="1"
bash setup_reproducibility.sh
```

### Reprodutibilidade mínima

Para reproduzir o projeto com apenas um modelo, use:

```bash
bash setup_minimal_reproducibility.sh
```

Por padrão, esse script:

- cria o ambiente virtual `.venv-minimal`;
- instala as dependências Python do benchmark;
- instala as dependências da extensão em `extension/`, se `npm` estiver disponível;
- verifica o Ollama;
- baixa o modelo `deepseek-coder:latest`;
- executa o benchmark usando somente esse modelo.

Se o download do modelo falhar, o script registra um aviso e continua. Nesse caso, o benchmark marca o modelo como `skipped` se ele não estiver disponível localmente no Ollama.

Para permitir que o script tente instalar o Ollama automaticamente:

```bash
INSTALL_OLLAMA=1 bash setup_minimal_reproducibility.sh
```

Para preparar o ambiente mínimo sem executar o benchmark:

```bash
RUN_BENCHMARK=0 bash setup_minimal_reproducibility.sh
```

Para trocar o modelo mínimo:

```bash
MINIMAL_MODEL=deepseek-coder:6.7b bash setup_minimal_reproducibility.sh
```

### Espaço em disco para reprodução mínima

Estimativa recomendada para a reprodução mínima com `deepseek-coder:latest`:

- modelo Ollama `deepseek-coder:latest`: aproximadamente **776 MB**, conforme a [biblioteca oficial do Ollama](https://ollama.com/library/deepseek-coder);
- ambiente virtual Python e pacotes: aproximadamente **500 MB a 1 GB**;
- dependências Node da extensão: normalmente menos de **100 MB**;
- arquivos de saída do benchmark: poucos MB.

Recomendação prática: reservar pelo menos **3 GB livres** para a reprodução mínima. Para evitar falhas por cache, logs, versões de pacotes e expansão temporária de downloads, **5 GB livres** é uma margem mais confortável.

### Reprodutibilidade completa

Para preparar o ambiente completo:

```bash
bash setup_reproducibility.sh
```

Para tentar instalar Ollama, baixar todos os modelos listados no benchmark e executar a avaliação completa:

```bash
INSTALL_OLLAMA=1 PULL_MODELS=1 RUN_BENCHMARK=1 bash setup_reproducibility.sh
```

A reprodução completa exige bem mais espaço em disco, pois baixa todos os modelos configurados em `benchmark/benchmark.py`. Recomenda-se reservar dezenas de GB livres antes de usar `PULL_MODELS=1`.

Se algum `ollama pull` falhar durante a reprodução completa, o script continua com os demais modelos. Durante a execução, modelos indisponíveis são registrados como `skipped` nos resultados e o benchmark segue para o próximo modelo.

### Espaço em disco para reprodução completa

A reprodução completa é pesada porque baixa **8 modelos locais** pelo Ollama. A maior parte do espaço usado vem dos pesos dos modelos, não do código do projeto.

Estimativa dos modelos usados pelo benchmark completo:

| Modelo | Espaço aproximado |
| --- | ---: |
| `granite4.1:3b` | 2.1 GB |
| `gemma4:latest` | 9.6 GB |
| `falcon3:latest` | 4.6 GB |
| `deepseek-coder:latest` | 776 MB |
| `yi-coder:latest` | 5.0 GB |
| `stable-code:latest` | 1.6 GB |
| `laguna-xs.2:latest` | 23 GB |
| `exaone-deep:latest` | 4.8 GB |

Somente os modelos somam aproximadamente **51,5 GB**. Além disso, ainda há:

- instalação do Ollama;
- ambiente virtual Python e pacotes;
- dependências Node da extensão;
- cache de download;
- arquivos de resultado do benchmark.

Recomendação prática para a reprodução completa:

- **60 GB livres**: mínimo aproximado;
- **80 GB livres ou mais**: recomendado para evitar falhas por cache, downloads temporários ou mudanças nos tamanhos das tags `latest`.

Os tamanhos dos modelos podem mudar com o tempo, especialmente nos modelos referenciados como `latest`. Por isso, para máquinas com pouco espaço, recomenda-se usar a reprodução mínima com `setup_minimal_reproducibility.sh`.

## Execução do Benchmark

Entre no diretório `benchmark/` e execute:

```bash
python benchmark.py
```

O script carregará os testes de `security_php.yaml`, enviará os prompts para cada modelo configurado e salvará os resultados no próprio diretório `benchmark/`.

Quando um modelo configurado não está instalado ou não pode ser carregado pelo Ollama, ele é marcado como `skipped` e o benchmark passa para o próximo modelo. O arquivo `benchmark_results.csv` inclui as colunas `Status` e `Error` para indicar esse caso.

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
