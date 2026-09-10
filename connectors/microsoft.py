"""Conector da Microsoft.

O site de carreiras e uma aplicacao JavaScript, mas por tras dela ha uma API
REST publica, encontrada no painel Network do navegador:

    apply.careers.microsoft.com/api/pcsx/search

A API tem limite de uso agressivo (429 depois de poucas chamadas seguidas),
por isso a pausa entre requisicoes e a nova tentativa em caso de bloqueio.
"""

import gzip
import json
import sys
import time
from datetime import datetime, timezone

import requests

API = "https://apply.careers.microsoft.com/api/pcsx/search"
SITE = "https://apply.careers.microsoft.com"
EMPRESA = "microsoft"

LOCAIS = ["Portugal"]      # a API filtra por localizacao
PAUSA = 5                  # segundos entre chamadas
TENTATIVAS = 3

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"),
    "Accept": "application/json",
    "Referer": "https://apply.careers.microsoft.com/",
}


def buscar_vagas_microsoft(local):
    """Uma chamada por localizacao, com nova tentativa se levar 429."""
    params = {"domain": "microsoft.com", "location": local, "start": 0}

    for tentativa in range(TENTATIVAS):
        r = requests.get(API, params=params, headers=HEADERS, timeout=30)

        if r.status_code == 200:
            return (r.json().get("data") or {}).get("positions") or []

        if r.status_code == 429:
            espera = PAUSA * (tentativa + 1)     # espera mais a cada tentativa
            print(f"  microsoft: limite atingido, aguardando {espera}s")
            time.sleep(espera)
            continue

        return []

    return []


def ts_para_iso(segundos):
    """postedTs vem como timestamp Unix em segundos."""
    if not segundos:
        return None
    return datetime.fromtimestamp(segundos, tz=timezone.utc).isoformat()


def parse_microsoft_job(vaga, collected_at):
    locais = vaga.get("locations") or []

    return {
        "source": "microsoft",
        "company": EMPRESA,
        "id": str(vaga.get("id")),
        "title": vaga.get("name"),
        "created_at": ts_para_iso(vaga.get("postedTs")),
        "collected_at": collected_at,
        "country": None,             # o local vem como texto composto (Sprint 8)
        "location_raw": "; ".join(locais) or None,
        "location_normalized": None,
        "department": vaga.get("department"),
        "team": None,
        "commitment": None,
        "workplace_type": vaga.get("workLocationOption"),   # onsite, remote, hybrid
        "salary_min": None,
        "salary_max": None,
        "salary_currency": None,
        "hosted_url": SITE + (vaga.get("positionUrl") or ""),
        "apply_url": SITE + (vaga.get("positionUrl") or ""),
        "full_description": None,     # exigiria uma chamada por vaga
        "raw_json": gzip.compress(json.dumps(vaga, ensure_ascii=False).encode()),
    }


def coletar_microsoft(locais=LOCAIS):
    todas = []
    vistos = set()
    agora = datetime.now(timezone.utc).isoformat()

    for i, local in enumerate(locais):
        if i:
            time.sleep(PAUSA)

        for vaga in buscar_vagas_microsoft(local):
            if vaga.get("id") in vistos:
                continue
            vistos.add(vaga.get("id"))
            todas.append(parse_microsoft_job(vaga, agora))

    print(f"microsoft: {len(todas)} vagas")
    return todas


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    vagas = coletar_microsoft()
    print()
    for campo, valor in vagas[0].items():
        if campo != "raw_json":
            print(f"  {campo}: {str(valor)[:75]}")
