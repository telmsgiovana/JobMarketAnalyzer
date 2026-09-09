"""Scraper do ITJobs.pt.

Portal portugues de vagas de tecnologia. Cada vaga e um <li> dentro de
<ul class="list-unstyled listing">, com o titulo num <a class="title">.

O robots.txt permite (Disallow vazio) mas pede Crawl-delay: 1 — por isso a
pausa entre requisicoes. Tambem declara Content-Signal: ai-train=no, ou seja:
coletar e analisar e permitido, treinar modelos com o conteudo nao.
"""

import gzip
import json
import re
import sys
import time
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

SITE = "https://www.itjobs.pt"
URL_VAGAS = f"{SITE}/emprego"

PAUSA = 1          # segundos entre requisicoes, como pede o robots.txt

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "pt-PT,pt;q=0.9",
}


def baixar(url):
    html = requests.get(url, headers=HEADERS, timeout=30).text
    time.sleep(PAUSA)
    return html


MODALIDADES = ["Híbrido", "Remoto", "Presencial"]


def separar_detalhes(texto):
    """"Açores Presencial €14 000 - €16 800" -> local, modalidade, salario."""
    if not texto:
        return None, None, None

    salario = None
    if "€" in texto:
        corte = texto.index("€")
        salario = texto[corte:].strip()
        texto = texto[:corte].strip()

    modalidade = None
    for m in MODALIDADES:
        if texto.endswith(m):
            modalidade = m
            texto = texto[: -len(m)].strip()
            break

    return texto or None, modalidade, salario


def texto_de(elemento, classe):
    el = elemento.find(class_=classe)
    if not el:
        return None
    return " ".join(el.get_text(" ").split()) or None


def listar_pagina(html):
    """Cada vaga e um <li> da lista principal."""
    sopa = BeautifulSoup(html, "html.parser")

    # a pagina tem varios blocos de listagem (diarios, promovidos)
    vagas = []
    for item in sopa.select("ul.listing > li"):
        link = item.find("a", class_="title")
        if not link or not link.get("href"):
            continue

        caminho = link["href"]
        numero = re.search(r"/oferta/(\d+)", caminho)

        vagas.append({
            "id": numero.group(1) if numero else caminho.strip("/"),
            "titulo": link.get("title") or link.text.strip(),
            "empresa": texto_de(item, "list-name"),
            "detalhes": texto_de(item, "list-details"),
            "url": SITE + caminho,
        })

    return vagas


def listar_vagas(max_paginas=20):
    """Percorre as paginas ate nao vir vaga nova (ou ate o limite)."""
    todas, vistos = [], set()

    for pagina in range(1, max_paginas + 1):
        url = URL_VAGAS if pagina == 1 else f"{URL_VAGAS}?page={pagina}"
        novas = [v for v in listar_pagina(baixar(url)) if v["id"] not in vistos]

        if not novas:
            break

        for v in novas:
            vistos.add(v["id"])
        todas.extend(novas)

    return todas


def parse_itjobs_job(vaga, collected_at):
    local, modalidade, salario = separar_detalhes(vaga["detalhes"])

    return {
        "source": "itjobs",
        "company": vaga["empresa"] or "desconhecida",
        "id": vaga["id"],
        "title": vaga["titulo"],
        "created_at": None,
        "collected_at": collected_at,
        "country": "PT",                      # o portal e so de Portugal
        "location_raw": local,
        "location_normalized": None,          # Sprint 8
        "department": None,
        "team": None,
        "commitment": None,
        "workplace_type": modalidade,
        "salary_min": None,                   # o texto do salario fica no raw_json (Sprint 8)
        "salary_max": None,
        "salary_currency": "EUR" if salario else None,
        "hosted_url": vaga["url"],
        "apply_url": vaga["url"],
        "full_description": None,             # so na pagina da vaga
        "raw_json": gzip.compress(json.dumps(vaga, ensure_ascii=False).encode()),
    }


def coletar_itjobs():
    agora = datetime.now(timezone.utc).isoformat()
    vagas = listar_vagas()
    print(f"itjobs: {len(vagas)} vagas")
    return [parse_itjobs_job(v, agora) for v in vagas]


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    # diagnostico: mostra o que foi encontrado em cada campo
    vagas = listar_vagas(max_paginas=3)
    print(f"{len(vagas)} vagas encontradas\n")

    for v in vagas[:5]:
        print(f"  id       {v['id']}")
        print(f"  titulo   {v['titulo'][:55]}")
        print(f"  empresa  {v['empresa']}")
        print(f"  detalhes {v['detalhes']}")
        print(f"  url      {v['url'][:70]}")
        print()
