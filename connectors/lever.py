import requests
from datetime import datetime, timezone
import json

EMPRESAS= ["jobgether","farfetch","swordhealth","xsolla","veeva","weloglobal","yuno","pipedrive"]



def ms_para_iso(ms):
    if ms is None:
        return None
    return datetime.fromtimestamp(ms/1000,tz=timezone.utc).isoformat()

def montar_descricao(job):
    partes=[]
    descricao=job.get("descriptionPlain") or job.get("description") or ""
    if descricao:
        partes.append(descricao)

    for secao in job.get("lists") or []:
        titulo=secao.get("text") or ""
        conteudo= secao.get("content") or ""
        partes.append(f"{titulo}\n{conteudo}")
    return "\n\n".join(partes)

def parse_lever_job(job, company,collected_at):
    categories = job.get("categories") or {}

    return {
        "source": "lever",
        "company": company,
        "id": str(job.get("id")),
        "title": job.get("text"),
        "created_at":ms_para_iso(job.get("createdAt")),          # job["createdAt"] vem em ms — converter
        "collected_at": collected_at,        # data de agora
        "country": job.get("country"),
        "location_raw": categories.get("location"),
        "location_normalized": None,   # Fase 3
        "department": categories.get("department"),
        "team": categories.get("team"),
        "commitment": categories.get("commitment"),
        "workplace_type": job.get("workplaceType"),
        "salary_min": None,
        "salary_max": None,
        "salary_currency": None,
        "hosted_url": job.get("hostedUrl"),
        "apply_url":job.get("applyUrl") ,
        "full_description": montar_descricao(job),    # descriptionPlain + lists
        "raw_json": json.dumps(job),            # JSON original inteiro
    }



def buscar_vagas_lever(company):
    url = f"https://api.lever.co/v0/postings/{company}?mode=json"
    return requests.get(url).json()


def coletar_lever(empresas=EMPRESAS):
    todas = []
    agora=datetime.now(timezone.utc).isoformat()
    for empresa in empresas:
        jobs = buscar_vagas_lever(empresa)

        if not isinstance(jobs, list):
            print(f"{empresa}: falhou — {jobs}")
            continue

        todas.extend(parse_lever_job(job, empresa,agora) for job in jobs)
        print(f"{empresa}: {len(jobs)} vagas")
    return todas


if __name__ == "__main__":
    vagas = coletar_lever()
    print(f"\nTotal: {len(vagas)} vagas")

    with open("data/lever_jobs.json", "w", encoding="utf-8") as f:
        json.dump(vagas, f, ensure_ascii=False, indent=2)

    print("Salvo em data/lever_jobs.json")