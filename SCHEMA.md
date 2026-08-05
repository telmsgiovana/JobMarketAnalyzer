# Schema da vaga

Formato único que todos os conectores devem retornar.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| source | str | Plataforma de origem (lever, greenhouse...) |
| company | str | Empresa |
| id | str | ID da vaga na plataforma |
| title | str | Título da vaga |
| created_at | str | Data de publicação (ISO 8601) |
| collected_at | str | Data da coleta (ISO 8601) |
| country | str | País |
| location_raw | str | Localização como veio da fonte |
| location_normalized | str | Localização padronizada (fase 3) |
| department | str | Departamento |
| team | str | Equipa |
| commitment | str | Tipo de contrato (full-time, intern...) |
| workplace_type | str | Remote / Hybrid / On-site |
| salary_min | int/None | Salário mínimo, se disponível |
| salary_max | int/None | Salário máximo, se disponível |
| salary_currency | str/None | Moeda |
| hosted_url | str | URL da vaga |
| apply_url | str | URL de candidatura |
| full_description | str | Descrição completa concatenada |

Chave única: `source + company + id`

## Campos derivados (não fazem parte do conector)

Skills, senioridade e nível de experiência são **extraídos da descrição** nas fases
posteriores (5 — keywords, 7 — LLM) e guardados em tabela separada, ligada pela
chave única. Motivo: manter o dado bruto intacto e permitir reprocessar quando o
método de extração melhorar.