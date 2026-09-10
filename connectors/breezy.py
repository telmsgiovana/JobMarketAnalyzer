"""Conector do Breezy HR.

Plataforma de recrutamento com listagem publica em JSON: basta pedir
{empresa}.breezy.hr/json — sem chave, sem paginacao.

Foi descoberta pelo site da Critical Software, que so mostrava um botao
"See Open Positions" apontando para la.
"""

import gzip
import json
import sys
from datetime import datetime, timezone

import requests

EMPRESAS = ["critical-software", "runtime-revolution", "bold"]

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"),
    "Accept": "application/json",
}


def buscar_vagas_breezy(company):
    """Devolve a lista de vagas da empresa, ou lista vazia se nao existir."""
    url = f"https://{company}.breezy.hr/json"
    try:
        dados = requests.get(url, headers=HEADERS, timeout=30).json()
    except Exception:
        return []
    return dados if isinstance(dados, list) else []


def iso_para_utc(texto):
    if not texto:
        return None
    return datetime.fromisoformat(texto.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat()


def montar_local(vaga):
    """A localizacao vem aninhada: {"country": {...}, "state": {...}, "city": ...}."""
    local = vaga.get("location") or {}
    partes = [
        local.get("city"),
        (local.get("state") or {}).get("name"),
        (local.get("country") or {}).get("name"),
    ]
    return ", ".join(p for p in partes if p) or None


def parse_breezy_job(vaga, company, collected_at):
    local = vaga.get("location") or {}
    pais = (local.get("country") or {}).get("id")

    return {
        "source": "breezy",
        "company": company,
        "id": str(vaga.get("id")),
        "title": vaga.get("name"),
        "created_at": iso_para_utc(vaga.get("published_date")),
        "collected_at": collected_at,
        "country": pais.upper() if pais else None,
        "location_raw": montar_local(vaga),
        "location_normalized": None,                     # Sprint 8
        "department": vaga.get("department"),
        "team": None,
        "commitment": (vaga.get("type") or {}).get("name"),   # ex: "Tempo integral"
        "workplace_type": None,
        "salary_min": None,
        "salary_max": None,
        # o campo vem como texto livre e costuma estar vazio; fica no raw_json
        "salary_currency": None,
        "hosted_url": vaga.get("url"),
        "apply_url": vaga.get("url"),
        "full_description": None,                        # so na pagina da vaga
        "raw_json": gzip.compress(json.dumps(vaga, ensure_ascii=False).encode()),
    }


def coletar_breezy(empresas=EMPRESAS):
    todas = []
    agora = datetime.now(timezone.utc).isoformat()

    for empresa in empresas:
        vagas = buscar_vagas_breezy(empresa)

        if not vagas:
            print(f"  {empresa}: falhou ou sem vagas")
            continue

        todas.extend(parse_breezy_job(v, empresa, agora) for v in vagas)
        print(f"  {empresa}: {len(vagas)} vagas")

    print(f"breezy: {len(todas)} vagas")
    return todas


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    vagas = coletar_breezy()
    print()

    for campo, valor in vagas[0].items():
        if campo != "raw_json":
            print(f"  {campo}: {str(valor)[:75]}")

    print()
    print("em Portugal:", sum(1 for v in vagas if v["country"] == "PT"))
