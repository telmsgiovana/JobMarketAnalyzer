# Job Market Analyzer

Plataforma de análise do mercado de trabalho em Dados e IA. Coleta vagas de múltiplas
fontes, padroniza num schema único, armazena em banco e gera análises sobre
competências, tecnologias e tendências do mercado.

## O que já funciona

- **Sete fontes de dados** — quatro APIs (Lever, Greenhouse, SmartRecruiters, PrimeIT) e
  três scrapers (ITJobs, Deloitte, LTPlabs), todas traduzidas para um schema único
  apesar de formatos completamente diferentes
- **Banco na nuvem** — SQLite hospedado (Turso), com inserção idempotente
- **Histórico de vagas** — os campos `first_seen` e `last_seen` permitem saber quando uma
  vaga apareceu, se ainda está aberta e quanto tempo durou
- **Coleta automática** — GitHub Actions roda todos os dias, sem intervenção

Cerca de **22 mil vagas** acompanhadas, das quais **1,6 mil em Portugal**.

## Como funciona

```
APIs         Lever · Greenhouse · SmartRecruiters · PrimeIT   ──┐
                                                                ├──> schema único ──> Turso
Scrapers     ITJobs · Deloitte · LTPlabs                      ──┘         ^
                                                       GitHub Actions ────┘
                                                        (diário, 06:00 UTC)
```

Cada fonte tem seu próprio tradutor para o schema definido em [SCHEMA.md](SCHEMA.md). O
resto do projeto trabalha só com esse formato — o banco não sabe se uma vaga veio de uma
API ou de uma página raspada. Foi isso que permitiu passar de uma para oito fontes sem
alterar o armazenamento nem a automação.

As decisões de arquitetura e o porquê de cada uma estão em [DECISOES.md](DECISOES.md).
Algumas das principais:

- **Chave única** `source + company + id`, com *upsert*: recoletar não duplica, só atualiza
- **JSON original preservado** de cada vaga (comprimido com gzip), permitindo reprocessar
  sem recoletar
- **Escrita em lote** no banco remoto — reduziu a coleta de 27 para 3 minutos
- **Filtro antes da requisição cara** — quando uma API exige uma chamada por vaga, as vagas
  são filtradas por país antes dessa etapa: 88% menos requisições
- **Falha isolada por fonte** — um scraper quebrado não derruba a coleta das outras, e
  fonte que devolve zero vagas é sinalizada no log em vez de passar despercebida
- **`robots.txt` respeitado**, incluindo `Crawl-delay` e restrições de uso declaradas

## Sobre o scraping

Antes de escrever cada scraper, o site passa por um diagnóstico: o HTML já traz as vagas?
Existe um bloco `ld+json`? Há uma requisição escondida devolvendo JSON? Só depende de
JavaScript? Cada resposta leva a uma ferramenta diferente — e evita escrever código que
não funcionaria.

O diagnóstico de doze sites está registrado em [DECISOES.md](DECISOES.md), com a
ferramenta usada (`scrapers/explorar.py`) e as restrições de `robots.txt` de cada um.

## Roadmap

| Fase | Etapa | Estado |
|------|-------|--------|
| Aquisição | Conectores de API (4 plataformas) | ✅ |
| Armazenamento | Banco SQLite → Turso | ✅ |
| Automação | GitHub Actions diário | ✅ |
| Aquisição | Web scraping com BeautifulSoup (3 sites) | ✅ |
| Aquisição | Playwright para sites com JavaScript | em andamento |
| Tratamento | Limpeza e normalização | |
| Visualização | Dashboard Streamlit | |
| Análise | ML: senioridade e clustering de vagas | |
| Análise | Extração de competências com LLM | |
| Análise | Agente analista com acesso ao banco | |

## Tecnologias

Python · Requests · BeautifulSoup · SQLite · Turso · GitHub Actions

## Como rodar

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Criar um arquivo `.env` na raiz com as credenciais do banco:

```
TURSO_URL=...
TURSO_TOKEN=...
```

E executar a partir da raiz do projeto:

```bash
python main.py
```
