import gzip
import html
import json
from datetime import datetime, timezone

import requests

LIMITE_PAGINA = 100

EMPRESAS = ["Inetum2", "natixisinportugal", "boschgroup", "devoteam", "ceiia","continental"]
PAISES = ["pt", "br"]

# so as secoes que descrevem a vaga; companyDescription e additionalInformation
# sao texto institucional e processo seletivo
SECOES = ["jobDescription", "qualifications"]

BASE = "https://api.smartrecruiters.com/v1/companies"


def buscar_pagina(company, offset):
    url = f"{BASE}/{company}/postings?limit={LIMITE_PAGINA}&offset={offset}"
    return requests.get(url, timeout=30).json()


def buscar_vagas_smart(company):
    """Percorre todas as paginas da listagem e devolve todas as vagas."""
    todas = []
    offset = 0
    total = 1

    while offset < total:
        res = buscar_pagina(company, offset)
        total = res.get("totalFound", 0)
        content = res.get("content") or []

        if not content:
            break

        todas.extend(content)
        offset += len(content)

    return todas


def filtrar_paises(vagas):
    """Mantem so as vagas dos paises de interesse."""
    filtradas = []
    for vaga in vagas:
        localizacao = vaga.get("location") or {}
        if localizacao.get("country") in PAISES:
            filtradas.append(vaga)
    return filtradas


def buscar_detalhe(company, id_vaga):
    """A descricao nao vem na listagem: precisa de uma requisicao por vaga."""
    url = f"{BASE}/{company}/postings/{id_vaga}"
    try:
        return requests.get(url, timeout=30).json()
    except Exception:
        return {}


def iso_para_utc(texto):
    if not texto:
        return None
    return datetime.fromisoformat(texto).astimezone(timezone.utc).isoformat()


def montar_descricao(detalhe):
    """Junta as secoes que descrevem a vaga, na ordem de SECOES."""
    secoes = ((detalhe.get("jobAd") or {}).get("sections")) or {}

    partes = []
    for nome in SECOES:
        bloco = secoes.get(nome) or {}
        texto = bloco.get("text") or ""
        if texto:
            titulo = bloco.get("title") or nome
            partes.append(f"{titulo}\n{html.unescape(texto)}")

    return "\n\n".join(partes)


def descobrir_workplace_type(localizacao):
    """A fonte da dois booleanos; o schema quer uma palavra."""
    if localizacao.get("remote"):
        return "remote"
    if localizacao.get("hybrid"):
        return "hybrid"
    return "on-site"


def parse_smartrecruiters_job(vaga, detalhe, company, collected_at):
    localizacao = vaga.get("location") or {}
    pais = localizacao.get("country")

    return {
        "source": "smartrecruiters",
        "company": company,
        "id": str(vaga.get("id")),
        "title": vaga.get("name"),
        "created_at": iso_para_utc(vaga.get("releasedDate")),
        "collected_at": collected_at,
        "country": pais.upper() if pais else None,
        "location_raw": localizacao.get("fullLocation"),
        "location_normalized": None,                       # Sprint 8
        "department": (vaga.get("function") or {}).get("label"),
        "team": (vaga.get("department") or {}).get("label"),
        "commitment": (vaga.get("typeOfEmployment") or {}).get("label"),
        "workplace_type": descobrir_workplace_type(localizacao),
        "salary_min": None,
        "salary_max": None,
        "salary_currency": None,
        "hosted_url": detalhe.get("postingUrl"),
        "apply_url": detalhe.get("applyUrl"),
        "full_description": montar_descricao(detalhe),
        "raw_json": gzip.compress(json.dumps(detalhe or vaga).encode()),
    }


def coletar_smartrecruiters(empresas=EMPRESAS):
    todas = []
    agora = datetime.now(timezone.utc).isoformat()

    for empresa in empresas:
        vagas = filtrar_paises(buscar_vagas_smart(empresa))

        for i, vaga in enumerate(vagas, 1):
            detalhe = buscar_detalhe(empresa, vaga.get("id"))
            todas.append(parse_smartrecruiters_job(vaga, detalhe, empresa, agora))

            if i % 100 == 0:
                print(f"  {empresa}: {i}/{len(vagas)}")

        print(f"{empresa}: {len(vagas)} vagas")

    return todas


if __name__ == "__main__":
    vagas = coletar_smartrecruiters(["ceiia"])
    print(f"\nTotal: {len(vagas)} vagas\n")

    for campo, valor in vagas[0].items():
        if campo != "raw_json":
            print(f"{campo}: {str(valor)[:80]}")
