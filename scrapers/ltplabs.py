"""Scraper da LTPlabs.

A pagina de carreiras e HTML estatico, entao os dados sao extraidos das
proprias tags com BeautifulSoup. O site tambem publica um bloco
<script type="application/ld+json"> com os mesmos dados; raspar as tags foi
escolha deliberada, para exercitar a tecnica.
"""

import gzip
import json
import sys
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

SITE = "https://ltplabs.com"
URL_CARREIRAS = f"{SITE}/pt/careers"
EMPRESA = "ltplabs"

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "pt-PT,pt;q=0.9",
}

# secoes que nao descrevem a vaga
SECOES_DESCARTAR = {"equal opportunities", "envie a sua candidatura"}

# palavras que aparecem coladas ao local: "Lisboa, PortoHibrido"
MODALIDADES = ["Híbrido", "Remoto", "Presencial", "Hybrid", "Remote", "On-site"]


def baixar(url):
    return requests.get(url, headers=HEADERS, timeout=30).text


def listar_vagas(html):
    """Na listagem, cada vaga e um link para /pt/careers/<slug> com um <h3> dentro."""
    sopa = BeautifulSoup(html, "html.parser")

    vagas = []
    for link in sopa.find_all("a", href=True):
        caminho = link["href"]

        if not caminho.startswith("/pt/careers/"):
            continue

        titulo = link.find("h3")
        if not titulo:
            continue

        vagas.append({
            "titulo": titulo.text.strip(),
            "slug": caminho.rsplit("/", 1)[-1],
            "url": SITE + caminho,
        })

    return vagas


def separar_local_modalidade(texto):
    """O site cola as duas coisas: "Lisboa, PortoHibrido" -> ("Lisboa, Porto", "Hibrido")."""
    if not texto:
        return None, None

    for modalidade in MODALIDADES:
        if texto.endswith(modalidade):
            return texto[: -len(modalidade)].strip(), modalidade

    return texto.strip(), None


def extrair_secoes(sopa):
    """Junta cada <h2> da vaga com o bloco de conteudo que vem logo depois."""
    partes = []

    for h2 in sopa.find_all("h2", class_="h3-bold"):
        classes = h2.get("class") or []
        if "text-center" in classes:          # e o formulario de candidatura
            continue

        titulo = h2.text.strip()
        if titulo.lower() in SECOES_DESCARTAR:
            continue

        # o conteudo da secao e o primeiro elemento irmao depois do titulo
        conteudo = h2.find_next_sibling()
        texto = " ".join(conteudo.get_text(" ").split()) if conteudo else ""

        if texto:
            partes.append(f"{titulo}\n{texto}")

    return "\n\n".join(partes)


def extrair_detalhe(html):
    """Le a pagina de uma vaga e devolve os campos que ela traz."""
    sopa = BeautifulSoup(html, "html.parser")

    h1 = sopa.find("h1")
    p_local = sopa.find("p", class_="body")

    local, modalidade = separar_local_modalidade(p_local.text.strip() if p_local else None)

    return {
        "titulo": h1.text.strip() if h1 else None,
        "local": local,
        "modalidade": modalidade,
        "descricao": extrair_secoes(sopa),
    }


def parse_ltplabs_job(vaga, detalhe, collected_at):
    return {
        "source": "ltplabs",
        "company": EMPRESA,
        "id": vaga["slug"],
        "title": detalhe.get("titulo") or vaga["titulo"],
        "created_at": None,                     # a pagina nao mostra a data
        "collected_at": collected_at,
        "country": None,                        # o site mistura paises no mesmo campo (Sprint 8)
        "location_raw": detalhe.get("local"),
        "location_normalized": None,            # Sprint 8
        "department": None,
        "team": None,
        "commitment": None,
        "workplace_type": detalhe.get("modalidade"),
        "salary_min": None,
        "salary_max": None,
        "salary_currency": None,
        "hosted_url": vaga["url"],
        "apply_url": vaga["url"],
        "full_description": detalhe.get("descricao"),
        "raw_json": gzip.compress(json.dumps({**vaga, **detalhe}, ensure_ascii=False).encode()),
    }


def coletar_ltplabs():
    agora = datetime.now(timezone.utc).isoformat()

    vagas = listar_vagas(baixar(URL_CARREIRAS))

    resultado = []
    for vaga in vagas:
        detalhe = extrair_detalhe(baixar(vaga["url"]))
        resultado.append(parse_ltplabs_job(vaga, detalhe, agora))

    print(f"ltplabs: {len(resultado)} vagas")
    return resultado


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    vagas = coletar_ltplabs()

    for campo, valor in vagas[0].items():
        if campo != "raw_json":
            print(f"{campo}: {str(valor)[:90]}")
