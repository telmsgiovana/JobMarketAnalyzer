"""Scraper da Deloitte Portugal.

O site usa SuccessFactors: a listagem e uma tabela em HTML estatico, paginada
por ?startrow=. Cada linha ja traz titulo, local e data; a descricao exige
entrar na pagina da vaga.
"""

import gzip
import json
import sys
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

SITE = "https://jobs.deloitte.pt"
URL_BUSCA = f"{SITE}/search/"
EMPRESA = "deloitte"

POR_PAGINA = 25          # quantas vagas o site devolve por pagina

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "pt-PT,pt;q=0.9",
}


def baixar(url):
    return requests.get(url, headers=HEADERS, timeout=30).text


def texto_da_celula(linha, classe):
    """Le uma <td> da linha pela classe e devolve o texto limpo."""
    celula = linha.find("td", class_=classe)
    if not celula:
        return None
    return " ".join(celula.get_text(" ").split()) or None


def data_para_iso(texto):
    """A tabela mostra 09/09/2026; o schema quer ISO em UTC."""
    if not texto:
        return None
    try:
        d = datetime.strptime(texto.strip(), "%d/%m/%Y")
        return d.replace(tzinfo=timezone.utc).isoformat()
    except ValueError:
        return None


def listar_pagina(html):
    """Cada vaga e uma <tr class="data-row"> da tabela de resultados."""
    sopa = BeautifulSoup(html, "html.parser")

    vagas = []
    for linha in sopa.find_all("tr", class_="data-row"):
        link = linha.find("a", class_="jobTitle-link")
        if not link or not link.get("href"):
            continue

        caminho = link["href"]

        vagas.append({
            # o id fica no fim da URL: /job/Braga-SAP-.../1164983055/
            "id": caminho.strip("/").rsplit("/", 1)[-1],
            "titulo": link.text.strip(),
            "local": (texto_da_celula(linha, "colLocation") or "").replace("+2 mais…", "").strip(),
            "data": data_para_iso(texto_da_celula(linha, "colDate")),
            "url": SITE + caminho,
        })

    return vagas


def listar_vagas():
    """Percorre as paginas ate uma delas nao trazer vaga nova."""
    todas = []
    vistos = set()
    startrow = 0

    while True:
        vagas = listar_pagina(baixar(f"{URL_BUSCA}?startrow={startrow}"))

        novas = [v for v in vagas if v["id"] not in vistos]
        if not novas:
            break

        for v in novas:
            vistos.add(v["id"])
        todas.extend(novas)

        startrow += POR_PAGINA

    return todas


def extrair_descricao(html):
    sopa = BeautifulSoup(html, "html.parser")
    corpo = sopa.find("span", class_="jobdescription")
    return " ".join(corpo.get_text(" ").split()) if corpo else ""


def parse_deloitte_job(vaga, descricao, collected_at):
    return {
        "source": "deloitte",
        "company": EMPRESA,
        "id": vaga["id"],
        "title": vaga["titulo"],
        "created_at": vaga["data"],
        "collected_at": collected_at,
        "country": None,                 # o local vem como "Braga, PT" (Sprint 8)
        "location_raw": vaga["local"],
        "location_normalized": None,
        "department": None,
        "team": None,
        "commitment": None,
        "workplace_type": None,
        "salary_min": None,
        "salary_max": None,
        "salary_currency": None,
        "hosted_url": vaga["url"],
        "apply_url": vaga["url"],
        "full_description": descricao,
        "raw_json": gzip.compress(json.dumps(vaga, ensure_ascii=False).encode()),
    }


def coletar_deloitte():
    agora = datetime.now(timezone.utc).isoformat()

    vagas = listar_vagas()

    resultado = []
    for i, vaga in enumerate(vagas, 1):
        descricao = extrair_descricao(baixar(vaga["url"]))
        resultado.append(parse_deloitte_job(vaga, descricao, agora))

        if i % 25 == 0:
            print(f"  deloitte: {i}/{len(vagas)}")

    print(f"deloitte: {len(resultado)} vagas")
    return resultado


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    vagas = coletar_deloitte()

    for campo, valor in vagas[0].items():
        if campo != "raw_json":
            print(f"{campo}: {str(valor)[:90]}")
