from connectors.lever import coletar_lever
from connectors.greenhouse import coletar_greenhouse
from connectors.smartrecruiter import coletar_smartrecruiters
from connectors.primeit import coletar_primeit
from scrapers.ltplabs import coletar_ltplabs
from scrapers.deloitte import coletar_deloitte
from scrapers.landingjobs import coletar_landingjobs
from scrapers.itjobs import coletar_itjobs
from database.db import criar_tabela, salvar_vagas

# cada fonte e independente: se uma falhar, as outras continuam
FONTES = [
    ("lever", coletar_lever),
    ("greenhouse", coletar_greenhouse),
    ("smartrecruiters", coletar_smartrecruiters),
    ("primeit", coletar_primeit),
    ("ltplabs", coletar_ltplabs),
    ("deloitte", coletar_deloitte),
    ("landingjobs", coletar_landingjobs),
    ("itjobs", coletar_itjobs),
]


def main():
    criar_tabela()

    vagas = []
    falhas = []

    for nome, coletar in FONTES:
        try:
            vagas.extend(coletar())
        except Exception as erro:
            falhas.append(nome)
            print(f"{nome}: FALHOU — {type(erro).__name__}: {erro}")

    salvar_vagas(vagas)

    print(f"\n{len(vagas)} vagas salvas no banco")
    if falhas:
        print(f"fontes com falha: {', '.join(falhas)}")


if __name__ == "__main__":
    main()
