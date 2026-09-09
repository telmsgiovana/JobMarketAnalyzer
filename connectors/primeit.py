"""Conector do PrimeIT.

O site nao entrega as vagas no HTML: elas vem de uma funcao de servidor
(_serverFn) que o JavaScript chama. A resposta usa um formato serializado
proprio do framework (TanStack), decodificado em `decodificar`.
"""

import gzip
import json
import sys
import urllib.parse
from datetime import datetime, timezone

import requests

EMPRESA = "primeit"
PAIS = "PT"          # o board so publica vagas em Portugal

# o hash faz parte da rota da funcao de servidor e muda se o site for reconstruido
URL = ("https://www.primeit.pt/_serverFn/"
       "0e4b0c5c13c11e813d86c8893336ab22f45b551f303b7b6339385bce960ca80e")

# sem estes dois cabecalhos o servidor responde 200 com corpo vazio
HEADERS = {
    "accept": "application/x-tss-framed, application/x-ndjson, application/json",
    "accept-language": "pt-PT,pt;q=0.9",
    "referer": "https://www.primeit.pt/pt/carreiras",
    "user-agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36"),
    "x-tsr-serverfn": "true",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
}


def montar_payload(pagina):
    """Monta o parametro que a funcao de servidor espera, para uma pagina."""
    filtros_vazios = [{"t": 9, "i": 3 + n, "a": [], "o": 0} for n in range(4)]

    return json.dumps({
        "t": {"t": 10, "i": 0, "p": {"k": ["data"], "v": [
            {"t": 10, "i": 1, "p": {
                "k": ["locale", "page", "filters"],
                "v": [
                    {"t": 1, "s": "pt"},
                    {"t": 0, "s": pagina},
                    {"t": 10, "i": 2, "p": {
                        "k": ["location", "contract", "work_model", "sector"],
                        "v": filtros_vazios,
                    }, "o": 0},
                ],
            }, "o": 0},
        ]}, "o": 0},
        "f": 63,
        "m": [],
    }, separators=(",", ":"))


def decodificar(no):
    """Converte o formato serializado do TanStack em estruturas Python.

    t=0 numero, t=1 texto, t=9 lista, t=10 objeto (k = chaves, v = valores).
    """
    if not isinstance(no, dict) or "t" not in no:
        return no

    tipo = no["t"]
    if tipo in (0, 1):
        return no.get("s")
    if tipo == 9:
        return [decodificar(item) for item in no.get("a", [])]
    if tipo == 10:
        return {k: decodificar(v) for k, v in zip(no["p"]["k"], no["p"]["v"])}
    return no.get("s", no)


def buscar_pagina(pagina):
    """Devolve (vagas, total_de_paginas) de uma pagina."""
    r = requests.get(URL, params={"payload": montar_payload(pagina)},
                     headers=HEADERS, timeout=30)
    resultado = decodificar(r.json()).get("result") or {}
    paginacao = resultado.get("pagination") or {}
    return resultado.get("data") or [], paginacao.get("pageCount", 0)


def buscar_vagas_primeit():
    """Percorre todas as paginas."""
    todas, pagina, total_paginas = [], 1, 1

    while pagina <= total_paginas:
        vagas, total_paginas = buscar_pagina(pagina)
        if not vagas:
            break
        todas.extend(vagas)
        pagina += 1

    return todas


def limpar_descricao(texto):
    """A descricao vem com escapes de JavaScript: a sequencia barra-x3C no lugar de <."""
    if not texto:
        return ""
    return texto.replace(chr(92) + "x3C", "<").replace(chr(92) + "x3E", ">")


def primeiro(lista):
    """Varios campos vem como lista de um item so."""
    return lista[0] if lista else None


def parse_primeit_job(vaga, collected_at):
    return {
        "source": "primeit",
        "company": EMPRESA,
        "id": str(vaga.get("id")),
        "title": (vaga.get("title") or "").strip(),
        "created_at": vaga.get("date") or None,
        "collected_at": collected_at,
        "country": PAIS,
        "location_raw": ", ".join(vaga.get("location") or []) or None,
        "location_normalized": None,                     # Sprint 8
        "department": primeiro(vaga.get("contract")),    # traz a area: Programador, Suporte...
        "team": primeiro(vaga.get("sector")),
        "commitment": None,
        "workplace_type": primeiro(vaga.get("work_model")),
        "salary_min": None,
        "salary_max": None,
        "salary_currency": None,
        "hosted_url": vaga.get("externalUrl"),
        "apply_url": vaga.get("externalUrl"),
        "full_description": limpar_descricao(vaga.get("description")),
        "raw_json": gzip.compress(json.dumps(vaga, ensure_ascii=False).encode()),
    }


def coletar_primeit():
    agora = datetime.now(timezone.utc).isoformat()
    vagas = buscar_vagas_primeit()
    print(f"primeit: {len(vagas)} vagas")
    return [parse_primeit_job(v, agora) for v in vagas]


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    vagas = coletar_primeit()
    print(f"\nTotal: {len(vagas)}\n")

    for campo, valor in vagas[0].items():
        if campo != "raw_json":
            print(f"{campo}: {str(valor)[:80]}")
