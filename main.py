from connectors.lever import coletar_lever
from connectors.greenhouse import coletar_greenhouse
from connectors.smartrecruiter import coletar_smartrecruiters
from connectors.primeit import coletar_primeit
from scrapers.ltplabs import coletar_ltplabs
from scrapers.deloitte import coletar_deloitte
from scrapers.itjobs import coletar_itjobs
from scrapers.nttdata import coletar_nttdata
from database.db import criar_tabela, salvar_vagas

# cada fonte e independente: se uma falhar, as outras continuam
FONTES = [
    ("lever", coletar_lever),
    ("greenhouse", coletar_greenhouse),
    ("smartrecruiters", coletar_smartrecruiters),
    ("primeit", coletar_primeit),
    ("ltplabs", coletar_ltplabs),
    ("deloitte", coletar_deloitte),
    ("itjobs", coletar_itjobs),
    ("nttdata", coletar_nttdata),
]


def main():
    criar_tabela()

    vagas = []
    falhas = []
    vazias = []

    for nome, coletar in FONTES:
        try:
            resultado = coletar()
            # fonte que devolve zero nao levanta erro, mas quase sempre e problema:
            # site mudou de estrutura, bloqueou o IP, ou a pagina saiu do ar
            if not resultado:
                vazias.append(nome)
                print(f"{nome}: ATENCAO — nenhuma vaga encontrada")
            vagas.extend(resultado)
        except Exception as erro:
            falhas.append(nome)
            print(f"{nome}: FALHOU — {type(erro).__name__}: {erro}")

    salvar_vagas(vagas)

    print(f"\n{len(vagas)} vagas salvas no banco")
    if falhas:
        print(f"fontes com falha: {', '.join(falhas)}")
    if vazias:
        print(f"fontes sem resultado: {', '.join(vazias)}")


if __name__ == "__main__":
    main()
