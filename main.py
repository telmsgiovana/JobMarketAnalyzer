from connectors.lever import coletar_lever
from database.db import criar_tabela, salvar_vagas


def main():
    criar_tabela()

    vagas = coletar_lever()
    salvar_vagas(vagas)

    print("Coleta finalizada")


if __name__ == "__main__":
    main()
