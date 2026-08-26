# Job Market Analyzer

Plataforma de análise do mercado de trabalho em Dados e IA. Coleta vagas de múltiplas
fontes, padroniza num schema único, armazena em banco e gera análises sobre
competências, tecnologias e tendências do mercado.

## O que já funciona

- **Conectores Lever, Greenhouse e SmartRecruiters** — coletam vagas de 21 empresas via API
  e traduzem para um schema único, apesar de as três APIs terem formatos bem diferentes
  (uma delas exige paginação e uma requisição por vaga)
- **Banco na nuvem** — SQLite hospedado (Turso), com inserção idempotente
- **Histórico de vagas** — campos `first_seen` e `last_seen` permitem saber quando uma vaga
  apareceu, se ainda está aberta e quanto tempo durou
- **Coleta automática** — GitHub Actions roda a coleta todos os dias, sem intervenção

Hoje o banco acompanha cerca de **12,8 mil vagas** de 21 empresas, em três plataformas —
das quais **1,3 mil em Portugal**.

## Como funciona

```
API Lever           ──>  parser  ──┐
API Greenhouse      ──>  parser  ──┼──>  schema único  ──>  Turso (nuvem)
API SmartRecruiters ──>  parser  ──┘                            ^
                                                GitHub Actions ─┘
                                                 (diário, 06:00 UTC)
```

Cada fonte tem seu próprio parser, que traduz o formato da API para o schema definido
em [SCHEMA.md](SCHEMA.md). O resto do projeto trabalha só com esse formato, o que permite
adicionar novas fontes sem alterar o banco nem as análises.

Decisões de projeto relevantes:

- **Chave única** `source + company + id`, com *upsert*: recoletar não duplica, só atualiza
- **JSON original preservado** de cada vaga (comprimido com gzip), permitindo reprocessar
  os dados sem precisar recoletar
- **Escrita em lote** para o banco remoto — reduziu a coleta completa de 27 para 3 minutos
- **Filtro antes da requisição cara** — o SmartRecruiters exige uma chamada por vaga, então
  as vagas são filtradas por país antes dessa etapa: 88% menos requisições
- **Credenciais fora do código**, em `.env` local e *secrets* no GitHub Actions

## Roadmap

| Fase | Etapa | Estado |
|------|-------|--------|
| Aquisição | Conector Lever | ✅ |
| Armazenamento | Banco SQLite → Turso | ✅ |
| Automação | GitHub Actions diário | ✅ |
| Aquisição | Conector Greenhouse | ✅ |
| Aquisição | Conector SmartRecruiters | ✅ |
| Aquisição | Web scraping (BeautifulSoup, Playwright) | em andamento |
| Tratamento | Limpeza e padronização | |
| Visualização | Dashboard Streamlit | |
| Análise | ML: senioridade e clustering de vagas | |
| Análise | Extração de competências com LLM | |
| Análise | Agente analista com acesso ao banco | |

## Tecnologias

Python · Requests · SQLite · Turso · GitHub Actions

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
