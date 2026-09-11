"""Scraper da NTT Data (Portugal).

O site e uma aplicacao Salesforce: o HTML que o servidor manda vem vazio, e as
vagas so aparecem depois do JavaScript rodar. Por isso usa Playwright, que abre
um navegador de verdade, em vez de requests.

A listagem mostra 3 vagas por pagina e a URL nao muda entre paginas — a
navegacao e por clique no botao seguinte.
"""

import gzip
import json
import re
import sys
from datetime import datetime, timezone

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

SITE = "https://careers.emeal.nttdata.com"
URL = f"{SITE}/s/jobs?language=pt_PT&pcountry=Portugal"
EMPRESA = "nttdata"
PAIS = "PT"          # a URL ja filtra Portugal

MAX_PAGINAS = 30     # limite de seguranca: hoje sao 18
ESPERA = 60000       # ms; o ambiente do GitHub Actions e mais lento que o local

# a mesma classe serve para campos diferentes, entao a distincao e pelo rotulo
ROTULOS = {
    "especializa": "area",
    "localiza": "local",
    "modalidade": "modalidade",
}


def extrair_vagas(html):
    """Cada vaga e um <div class="views-row"> da tabela."""
    sopa = BeautifulSoup(html, "html.parser")

    vagas = []
    for linha in sopa.select("div.views-row"):
        link = linha.select_one("div.views-field-title a")
        if not link or not link.get("href"):
            continue

        vaga = {
            "titulo": link.get_text(strip=True),
            "url": link["href"],
        }

        # os outros campos vem como "Rotulo: valor", e a classe nao os distingue
        for campo in linha.select("div.views-field"):
            texto = " ".join(campo.get_text(" ").split())
            if ":" not in texto:
                continue

            rotulo, valor = texto.split(":", 1)
            for chave, nome in ROTULOS.items():
                if chave in rotulo.lower():
                    vaga[nome] = valor.strip()
                    break

        vagas.append(vaga)

    return vagas


def coletar_paginas(pagina):
    """Le a pagina atual, clica no botao seguinte, repete ate acabar."""
    todas = []
    vistos = set()

    for _ in range(MAX_PAGINAS):
        for vaga in extrair_vagas(pagina.content()):
            if vaga["url"] not in vistos:
                vistos.add(vaga["url"])
                todas.append(vaga)

        # o "+" seleciona o irmao logo depois do botao atual
        seguinte = pagina.locator("a.paginate_button.current + a.paginate_button")
        if seguinte.count() == 0:
            break

        seguinte.first.click()
        pagina.wait_for_timeout(1200)

    return todas


def parse_nttdata_job(vaga, collected_at):
    # o id fica na URL: /s/offer/a1JKA000000UKad2AG
    achado = re.search(r"/offer/([A-Za-z0-9]+)", vaga["url"])

    return {
        "source": "nttdata",
        "company": EMPRESA,
        "id": achado.group(1) if achado else vaga["url"],
        "title": vaga["titulo"],
        "created_at": None,                     # a listagem nao mostra a data
        "collected_at": collected_at,
        "country": PAIS,
        "location_raw": vaga.get("local"),
        "location_normalized": None,            # Sprint 8
        "department": vaga.get("area"),         # ex: "DevOps", "Data Engineer"
        "team": None,
        "commitment": None,
        "workplace_type": vaga.get("modalidade"),
        "salary_min": None,
        "salary_max": None,
        "salary_currency": None,
        "hosted_url": vaga["url"],
        "apply_url": vaga["url"],
        "full_description": None,               # so na pagina da vaga
        "raw_json": gzip.compress(json.dumps(vaga, ensure_ascii=False).encode()),
    }


def coletar_nttdata():
    agora = datetime.now(timezone.utc).isoformat()

    with sync_playwright() as p:
        navegador = p.chromium.launch()
        pagina = navegador.new_page()

        # esperar a rede sossegar ("networkidle") e fragil: sites com telemetria
        # de fundo nunca ficam parados. Melhor esperar o que interessa aparecer.
        pagina.goto(URL, timeout=ESPERA, wait_until="domcontentloaded")
        pagina.wait_for_selector("div.views-row", timeout=ESPERA)

        vagas = coletar_paginas(pagina)
        navegador.close()

    print(f"nttdata: {len(vagas)} vagas")
    return [parse_nttdata_job(v, agora) for v in vagas]


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    vagas = coletar_nttdata()

    for campo, valor in vagas[0].items():
        if campo != "raw_json":
            print(f"  {campo}: {str(valor)[:70]}")

    print()
    print("areas:", sorted({v["department"] for v in vagas if v["department"]})[:12])
