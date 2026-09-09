from connectors.lever import coletar_lever
from connectors.greenhouse import coletar_greenhouse
from connectors.smartrecruiter import coletar_smartrecruiters
from connectors.primeit import coletar_primeit
from scrapers.ltplabs import coletar_ltplabs
from scrapers.deloitte import coletar_deloitte
from scrapers.landingjobs import coletar_landingjobs
from scrapers.itjobs import coletar_itjobs
from database.db import criar_tabela, salvar_vagas


def main():
    criar_tabela()

    vagas = (coletar_lever() + coletar_greenhouse()
             + coletar_smartrecruiters() + coletar_primeit()
             + coletar_ltplabs() + coletar_deloitte()
             + coletar_landingjobs() + coletar_itjobs())
    salvar_vagas(vagas)

    print(f"\n{len(vagas)} vagas salvas no banco")


if __name__ == "__main__":
    main()
