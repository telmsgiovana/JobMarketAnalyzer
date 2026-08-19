import gzip
import html
import json
from datetime import datetime, timezone

import requests

EMPRESAS = ["figma","gocardless","pandadoc","iterable","fluxon","enhesa","five9","singlestore"]


def iso_para_utc(texto):
    """A Greenhouse manda data em ISO mas com fuso local. Converte para UTC."""
    if not texto:
        return None
    return datetime.fromisoformat(texto).astimezone(timezone.utc).isoformat()


def montar_descricao(job):
    """A descricao vem toda em 'content', como HTML escapado."""
    conteudo = job.get("content") or ""
    return html.unescape(conteudo)


def juntar_departamentos(job):
    """departments e uma lista de dicts. Junta os nomes numa string."""
    departamentos = job.get("departments") or []
    nomes = [d.get("name") for d in departamentos if d.get("name")]
    return ", ".join(nomes) or None


def parse_greenhouse_job(job, company, collected_at):
    localizacao = job.get("location") or {}

    return {
        "source": "greenhouse",
        "company": company,
        "id": str(job.get("id")),
        "title": job.get("title"),
        "created_at": iso_para_utc(job.get("first_published")),
        "collected_at": collected_at,
        "country": None,                       # Greenhouse nao separa o pais
        "location_raw": localizacao.get("name"),
        "location_normalized": None,           # Sprint 7
        "department": juntar_departamentos(job),
        "team": None,                          # nao existe na Greenhouse
        "commitment": None,                    # nao existe na Greenhouse
        "workplace_type": None,                # nao existe na Greenhouse
        "salary_min": None,
        "salary_max": None,
        "salary_currency": None,
        "hosted_url": job.get("absolute_url"),
        "apply_url": job.get("absolute_url"),  # a Greenhouse usa a mesma URL
        "full_description": montar_descricao(job),
        "raw_json": gzip.compress(json.dumps(job).encode()),
    }


def buscar_vagas_greenhouse(company):
    """Devolve a lista de vagas, ou None se a empresa nao existir."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs?content=true"
    dados = requests.get(url).json()
    return dados.get("jobs")


def coletar_greenhouse(empresas=EMPRESAS):
    todas = []
    agora = datetime.now(timezone.utc).isoformat()

    for empresa in empresas:
        jobs = buscar_vagas_greenhouse(empresa)

        if not isinstance(jobs, list):
            print(f"{empresa}: falhou")
            continue

        todas.extend(parse_greenhouse_job(job, empresa, agora) for job in jobs)
        print(f"{empresa}: {len(jobs)} vagas")

    return todas


if __name__ == "__main__":
    vagas = coletar_greenhouse()
    print(f"\nTotal: {len(vagas)} vagas")

    for campo, valor in vagas[0].items():
        if campo != "raw_json":
            print(f"{campo}: {str(valor)[:80]}")
