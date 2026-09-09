# Decisões técnicas

Registro das escolhas de arquitetura do projeto e do porquê de cada uma.

## Roadmap

| Sprint | Tema | Estado |
|--------|------|--------|
| 1 | Conector Lever (API) | ✅ concluído |
| 2 | Banco de dados SQLite | ✅ concluído |
| 3 | Automação com GitHub Actions + banco na nuvem | ✅ concluído |
| 4 | Conector Greenhouse | ✅ concluído |
| 5 | Conector SmartRecruiters (paginação + detalhe por vaga) | ✅ concluído |
| 6 | Web scraping (BeautifulSoup) | 🚧 próximo |
| 7 | Playwright (sites com JavaScript) | pendente |
| 8 | Limpeza de dados | pendente |
| 9 | Dashboard Streamlit + deploy | pendente |
| 10 | ML (classificador de senioridade, clustering) | pendente |
| 11 | Extração de skills com LLM | pendente |
| 12 | Agente analista (tool use + SQL) | pendente |
| 13 | Extras (série temporal, agente mentor, busca semântica) | pendente |

Marco de empregabilidade: fim do Sprint 9 — dashboard público no CV.

Motivo do SmartRecruiters: empresas grandes em Portugal (ex: Natixis) usam essa plataforma.
Cobertura local importa mais que volume, porque o objetivo é emprego lá.

## Decisões técnicas já tomadas

- **Schema único** em `SCHEMA.md`. Todo conector retorna esse formato.
- **Chave única**: `source + company + id`.
- **Datas**: sempre ISO 8601 em UTC.
- **`raw_json`**: guardar o JSON original de cada vaga, para reprocessar sem recoletar.
- **Campos derivados** (skills, senioridade) não entram no schema do conector —
  vão em tabela separada nas fases de análise.
- **Limpeza de HTML** fica para o Sprint 8, não nos conectores. O conector da Greenhouse
  só faz `html.unescape()` no `content`, para deixar as duas fontes no mesmo estado.
- **Campos que uma fonte não tem** ficam `None`. O schema é união das fontes, não interseção.
  A Greenhouse não fornece `country`, `team`, `commitment` nem `workplace_type`.
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
- **SmartRecruiters**: a listagem é paginada (`offset`/`limit`, teto de 100) e a descrição
  só existe no detalhe de cada vaga (padrão N+1). O filtro por país roda **antes** do loop
  de detalhes — corta ~88% das requisições.
- **Filtro por país no SmartRecruiters** (`PAISES = ["pt", "br"]`): a exceção à regra de
  coletar tudo. O motivo é custo de rede, não relevância, e o campo é estrutural.
- **Seções da descrição** (`SECOES`): só `jobDescription` e `qualifications`.
  `companyDescription` e `additionalInformation` são boilerplate.
- Scripts rodam **a partir da raiz do projeto** (`python connectors/lever.py`).

## Alvos de scraping — diagnóstico já feito

Fluxo de decisão usado em cada site: (1) o HTML tem as vagas? → BeautifulSoup.
(2) Existe requisição escondida com JSON? (DevTools → Network → Fetch/XHR → Ctrl+F
com um título de vaga) → `requests` direto. (3) Só aparece com JavaScript → Playwright.
Antes de qualquer coisa, conferir o `robots.txt`.

| Site | Diagnóstico | Situação |
|------|-------------|----------|
| LTPlabs | estático, 15 vagas, todas de dados/IA | **Sprint 6 — primeiro alvo** |
| Deloitte (`jobs.deloitte.pt/search/`) | estático, SuccessFactors, paginação `?startrow=` | Sprint 6 — segundo |
| Landing.jobs | estático, portal com muitas vagas, tem sitemap | Sprint 6 — terceiro |
| ITJobs | estático, portal; `Crawl-delay: 1` | Sprint 6 — quarto |
| PrimeIT | resolvido via API do key.work | conector escrito |
| KPMG | Workday | investigar — um conector Workday serve dezenas de empresas |
| Microsoft | Eightfold (aplicação JavaScript) | testado: nenhum endereço serve HTML com vagas. DevTools ou Playwright |
| Revolut | parcial: 6 destaques no HTML, resto por JavaScript | testar API escondida antes de Playwright |
| NTT Data | Salesforce Aura, 100% JavaScript | Sprint 7 (Playwright) |
| Critical Software, Caixa Mágica, Capgemini, ICT Strypes | não identificado | testar DevTools |
| The Data Scientists | estático e permitido, mas **sem vagas abertas** | quando publicarem |

Notas de robots.txt:
- **ITJobs**: `Content-Signal: ai-train=no` — reserva de direitos sob a diretiva europeia
  de copyright. Coletar e analisar é permitido; treinar modelo com o conteúdo, não.
  Também bloqueia `ClaudeBot`, então o Claude não deve fazer requisições ao site —
  o scraper dela, sim.
- **Landing.jobs**: bloqueia `/api/` e `/jobs/search`; as páginas de vaga são permitidas.
- **Deloitte**: bloqueia só áreas de candidatura; `/search/` é permitido.
- **The Data Scientists**: `Crawl-delay: 10`.

## Convenções

- Commits: `feat:`, `fix:`, `docs:`, `chore:`
- Um commit por assunto
- Código e comentários em português, exceto nomes de campos do schema (inglês)
