"""Scraper da Caixa Magica.

A pagina de oportunidades carrega as vagas por JavaScript, e so depois de
rolar a pagina — por isso Playwright, e por isso a rolagem antes de ler.

Cada vaga e um <div class="rbox-opening-li"> com titulo, localizacao e tipo
de contrato. O link e uma ancora na propria pagina (#op-NNNNN-slug).
"""

import gzip
import json
import re
import sys
from datetime import datetime, timezone

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

URL = "https://caixamagica.pt/pt/oportunidades/"
EMPRESA = "caixamagica"
PAIS = "PT"

ROLAGENS = 3        # a lista so aparece depois de rolar


def texto_de(card, classe):
    el = card.find(class_=classe)
    if not el:
        return None
    return " ".join(el.get_text(" ").split()) or None


def extrair_vagas(html):
    sopa = BeautifulSoup(html, "html.parser")

    vagas = []
    for card in sopa.select("div.rbox-opening-li"):
        link = card.find("a", href=re.compile(r"#op-\d+"))
        if not link:
            continue

        href = link["href"]
        numero = re.search(r"#op-(\d+)", href)

        # o rotulo vem junto: "Location: Lisboa, Portugal"
        curta = texto_de(card, "rbox-job-shortdesc") or ""
        local = None
        achado = re.search(r"Location:\s*(.+?)(?:\s+Full-time|\s+Part-time|$)", curta)
        if achado:
            local = achado.group(1).strip()

        vagas.append({
            "id": numero.group(1) if numero else href,
            "titulo": texto_de(card, "rbox-opening-li-title") or link.get_text(strip=True),
            "local": local,
            "contrato": texto_de(card, "rbox-opening-position-type"),
            "url": href if href.startswith("http") else URL + href,
        })

    return vagas


def buscar_html():
    """Abre a pagina num navegador e rola ate a lista de vagas aparecer."""
    with sync_playwright() as p:
        navegador = p.chromium.launch()
        pagina = navegador.new_page()

        pagina.goto(URL, timeout=60000, wait_until="domcontentloaded")
        pagina.wait_for_timeout(4000)

        for _ in range(ROLAGENS):
            pagina.mouse.wheel(0, 5000)
            pagina.wait_for_timeout(2500)

        html = pagina.content()
        navegador.close()

    return html


def parse_caixamagica_job(vaga, collected_at):
    return {
        "source": "caixamagica",
        "company": EMPRESA,
        "id": vaga["id"],
        "title": vaga["titulo"],
        "created_at": None,                  # a listagem nao mostra a data
        "collected_at": collected_at,
        "country": PAIS,
        "location_raw": vaga["local"],
        "location_normalized": None,         # Sprint 8
        "department": None,
        "team": None,
        "commitment": vaga["contrato"],      # ex: "Full-time"
        "workplace_type": None,
        "salary_min": None,
        "salary_max": None,
        "salary_currency": None,
        "hosted_url": vaga["url"],
        "apply_url": vaga["url"],
        "full_description": None,
        "raw_json": gzip.compress(json.dumps(vaga, ensure_ascii=False).encode()),
    }


def coletar_caixamagica():
    agora = datetime.now(timezone.utc).isoformat()
    vagas = extrair_vagas(buscar_html())

    print(f"caixamagica: {len(vagas)} vagas")
    return [parse_caixamagica_job(v, agora) for v in vagas]


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    vagas = coletar_caixamagica()
    print()
    for campo, valor in vagas[0].items():
        if campo != "raw_json":
            print(f"  {campo}: {str(valor)[:70]}")
    print()
    print("titulos:", [v["title"][:26] for v in vagas[:6]])
