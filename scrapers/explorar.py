"""Ferramenta de diagnostico para scraping.

Antes de escrever um scraper, roda isto para ver o mapa da pagina:
que tags existem, com que classes, e o que tem dentro.

Uso:
    python scrapers/explorar.py https://ltplabs.com/pt/careers/data-scientist
    python scrapers/explorar.py https://exemplo.com  h1 h2 p
"""

import sys

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "pt-PT,pt;q=0.9",
}

TAGS_PADRAO = ["h1", "h2", "h3", "p"]
LIMITE = 8          # quantos elementos mostrar por tag


def baixar(url):
    r = requests.get(url, headers=HEADERS, timeout=30)
    print(f"status {r.status_code} | {len(r.text)} caracteres de HTML\n")
    return r.text


def mostrar_tags(sopa, tags):
    """Lista os elementos de cada tag, com suas classes e o texto de dentro."""
    for tag in tags:
        elementos = sopa.find_all(tag)
        print(f"=== <{tag}> — {len(elementos)} na pagina ===")

        for el in elementos[:LIMITE]:
            classe = " ".join(el.get("class") or [])
            texto = " ".join(el.text.split())          # junta espacos e quebras de linha
            print(f"  class='{classe[:45]}'")
            print(f"     {texto[:75]}")

        if len(elementos) > LIMITE:
            print(f"  ... mais {len(elementos) - LIMITE}")
        print()


def procurar_texto(sopa, termo):
    """Mostra em que tag um texto aparece — util para achar onde fica um dado."""
    print(f"=== onde aparece {termo!r} ===")
    for el in sopa.find_all(string=lambda t: t and termo.lower() in t.lower()):
        pai = el.parent
        classe = " ".join(pai.get("class") or [])
        print(f"  <{pai.name} class='{classe[:40]}'>  {' '.join(el.split())[:60]}")
    print()


def listar_json_ld(sopa):
    """Alguns sites trazem os dados prontos em <script type='application/ld+json'>."""
    blocos = sopa.find_all("script", type="application/ld+json")
    print(f"=== blocos ld+json: {len(blocos)} ===")
    for b in blocos:
        trecho = " ".join((b.string or "").split())
        print(f"  {trecho[:150]}")
    print()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(1)

    url = sys.argv[1]
    tags = sys.argv[2:] or TAGS_PADRAO

    sopa = BeautifulSoup(baixar(url), "html.parser")

    listar_json_ld(sopa)
    mostrar_tags(sopa, tags)
