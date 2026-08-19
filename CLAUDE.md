# Instruções do projeto

## Sobre o projeto

**Job Market Analyzer** — plataforma de análise do mercado de trabalho em Dados e IA.
Coleta vagas de APIs e web scrapers, padroniza num schema único, armazena em banco,
e gera análises com ML e LLMs.

Objetivo duplo: **aprender** (APIs, scraping, automação, ML, agentes) e **construir
portfólio** para conseguir emprego na área.

## Sobre quem está desenvolvendo

Estudante de IA e Ciência de Dados, último ano. Está aprendendo enquanto constrói.
Conhece Python básico. Não conhece a fundo: git/GitHub, SQL, APIs, scraping, ML aplicado.

## Como se comunicar comigo

**Seja didático. Explique o porquê antes do como.**

1. **Um assunto por vez.** Não misture temas. Se estamos na Lever, não fale de
   Greenhouse. Se estamos no parser, não fale do banco.

2. **Não antecipe sprints futuros.** Cada coisa no seu sprint. Se algo pode esperar,
   diga que espera e siga.

3. **Explique antes de mostrar código.** O que a coisa faz, por que ela é necessária,
   e só então o código.

4. **Não dê tudo mastigado.** Prefira:
   - esqueleto com partes para eu completar
   - dica de qual função/conceito usar
   - deixar eu errar e depois revisar

   Dou o código pronto só quando eu pedir explicitamente ou quando estou travada
   há várias mensagens.

5. **Explique termos técnicos na primeira vez.** Não assuma que conheço.
   (`.get()`, `extend`, f-string, timestamp, staging, etc.)

6. **Ritmo devagar.** Um passo, eu executo, eu confirmo, próximo passo.
   Não liste 8 passos de uma vez.

7. **Quando eu apontar um erro seu**, corrija de forma direta e siga. Sem se estender.

8. **Antes de adicionar dependência nova** (biblioteca, ferramenta), explique por que
   é necessária e se dá para evitar.

## Git — regras obrigatórias

- **Nunca assinar os commits.** Não incluir `Co-Authored-By`, "Generated with Claude",
  nem qualquer menção ao Claude na mensagem de commit ou no corpo de PRs.
  Os commits são meus e devem aparecer só com o meu nome.

- **Nunca fazer `git commit`, `git push` ou qualquer operação que altere o histórico
  sem minha autorização explícita.** Pode sugerir o comando e me dizer quando é hora
  de commitar — quem executa sou eu, a menos que eu peça diretamente
  ("faz o commit pra mim").

## Roadmap

| Sprint | Tema | Estado |
|--------|------|--------|
| 1 | Conector Lever (API) | ✅ concluído |
| 2 | Banco de dados SQLite | ✅ concluído |
| 3 | Automação com GitHub Actions + banco na nuvem | ✅ concluído |
| 4 | Conector Greenhouse | 🚧 próximo |
| 5 | Web scraping (BeautifulSoup) | pendente |
| 6 | Playwright (sites com JavaScript) | pendente |
| 7 | Limpeza de dados | pendente |
| 8 | Dashboard Streamlit + deploy | pendente |
| 9 | ML (classificador de senioridade, clustering) | pendente |
| 10 | Extração de skills com LLM | pendente |
| 11 | Agente analista (tool use + SQL) | pendente |
| 12 | Extras (série temporal, agente mentor, busca semântica) | pendente |

Marco de empregabilidade: fim do Sprint 8 — dashboard público no CV.

## Decisões técnicas já tomadas

- **Schema único** em `SCHEMA.md`. Todo conector retorna esse formato.
- **Chave única**: `source + company + id`.
- **Datas**: sempre ISO 8601 em UTC.
- **`raw_json`**: guardar o JSON original de cada vaga, para reprocessar sem recoletar.
- **Campos derivados** (skills, senioridade) não entram no schema do conector —
  vão em tabela separada nas fases de análise.
- **Limpeza de HTML** fica para o Sprint 7, não nos conectores.
- **`data/*.json` e o banco** não sobem para o git.
- **Banco na nuvem: Turso** (SQLite hospedado). Escolhido pelo espaço gratuito de 5 GB
  e por manter o mesmo SQL do SQLite local. Migração para Postgres fica como exercício futuro.
- **`raw_json` guardado comprimido** com `gzip` em coluna `BLOB`. Reduziu o banco de
  145 MB para 65 MB. Ler de volta com `ler_raw_json()`.
- **Gravação em lote** (`TAMANHO_LOTE = 45`): um `INSERT` com várias linhas por requisição.
  Pela rede, um `execute` por vaga levava 27 min; em lote, 3 min.
- **Credenciais**: `.env` local (fora do git) e *secrets* no GitHub Actions.
  Os nomes das variáveis são iguais nos dois: `TURSO_URL` e `TURSO_TOKEN`.
- **Coleta automática**: `.github/workflows/coleta.yml`, todo dia às 06:00 UTC,
  com botão de execução manual (`workflow_dispatch`).
- Scripts rodam **a partir da raiz do projeto** (`python connectors/lever.py`).

## Convenções

- Commits: `feat:`, `fix:`, `docs:`, `chore:`
- Um commit por assunto
- Código e comentários em português, exceto nomes de campos do schema (inglês)
