"""Scraper do Landing.jobs.

Portal portugues de vagas de tecnologia. Cada vaga e um <article class="lj-jobcard-static">
que ja traz empresa, local, modalidade, contrato, categoria e skills — nao e preciso
entrar na pagina da vaga.

Limite: o site tem 54 vagas em 2 paginas, mas ?page=2 devolve o mesmo HTML —
a segunda pagina e montada por JavaScript no navegador. Coletamos as 50 da
listagem (93% do total). O robots.txt tambem bloqueia /jobs/search, que e por
onde essa busca provavelmente passa.
"""

import gzip
import json
import sys
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

SITE = "https://landing.jobs"
URL_VAGAS = f"{SITE}/jobs"

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "pt-PT,pt;q=0.9",
}

CLASSE = "lj-jobcard-static"      # prefixo das classes do card


def baixar(url):
    return requests.get(url, headers=HEADERS, timeout=30).text


def texto(card, sufixo):
    """Le um pedaco do card pela classe: texto(card, 'company') -> 'ANNEA'."""
    el = card.find(class_=f"{CLASSE}__{sufixo}")
    if not el:
        return None
    return " ".join(el.get_text(" ").split()) or None


def listar_vagas(html):
    sopa = BeautifulSoup(html, "html.parser")

    vagas = []
    for card in sopa.find_all("article", class_=CLASSE):
        link = card.find("a", class_=f"{CLASSE}__link")
        if not link or not link.get("href"):
            continue

        caminho = link["href"]

        vagas.append({
            # a URL tem a forma /at/<empresa>/<slug>
            "id": caminho.strip("/").replace("/", "-"),
            "titulo": link.text.strip(),
            "empresa": texto(card, "company"),
            "local": texto(card, "location"),
            "modalidade": texto(card, "badge"),
            "contrato": texto(card, "contract"),
            "categoria": texto(card, "category"),
            "skills": [s.get_text(strip=True)
                       for s in card.find_all(class_=f"{CLASSE}__skill")],
            "url": SITE + caminho,
        })

    return vagas


def parse_landingjobs_job(vaga, collected_at):
    return {
        "source": "landingjobs",
        # portal: a empresa muda a cada vaga, ao contrario dos outros scrapers
        "company": vaga["empresa"] or "desconhecida",
        "id": vaga["id"],
        "title": vaga["titulo"],
        "created_at": None,                  # a listagem nao mostra a data
        "collected_at": collected_at,
        "country": None,                     # vem dentro de "Lisbon , PT" (Sprint 8)
        "location_raw": vaga["local"],
        "location_normalized": None,
        "department": vaga["categoria"],     # ex: "Full-stack Developer"
        "team": None,
        "commitment": vaga["contrato"],      # ex: "Permanent"
        "workplace_type": vaga["modalidade"],  # ex: "Hybrid"
        "salary_min": None,
        "salary_max": None,
        "salary_currency": None,
        "hosted_url": vaga["url"],
        "apply_url": vaga["url"],
        # a listagem nao traz descricao; as skills sao o que ha de conteudo
        "full_description": ", ".join(vaga["skills"]) or None,
        "raw_json": gzip.compress(json.dumps(vaga, ensure_ascii=False).encode()),
    }


def coletar_landingjobs():
    agora = datetime.now(timezone.utc).isoformat()

    vagas = listar_vagas(baixar(URL_VAGAS))

    print(f"landingjobs: {len(vagas)} vagas")
    return [parse_landingjobs_job(v, agora) for v in vagas]


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    vagas = coletar_landingjobs()

    for campo, valor in vagas[0].items():
        if campo != "raw_json":
            print(f"{campo}: {str(valor)[:80]}")

    print()
    print("empresas diferentes:", len({v["company"] for v in vagas}))
