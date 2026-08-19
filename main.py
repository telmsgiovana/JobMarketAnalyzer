from connectors.lever import coletar_lever
from connectors.greenhouse import coletar_greenhouse
from database.db import criar_tabela, salvar_vagas


def main():
    criar_tabela()

    vagas = coletar_lever() + coletar_greenhouse()
    salvar_vagas(vagas)

    print(f"\n{len(vagas)} vagas salvas no banco")


if __name__ == "__main__":
    main()
