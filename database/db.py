import gzip
import json
import sqlite3
from pathlib import Path
import os
from dotenv import load_dotenv
import turso_serverless

load_dotenv()


RAIZ = Path(__file__).resolve().parent.parent
DB_PATH = RAIZ / "data" / "jobs.db"
COLUNAS = [
    "source", "company", "id", "title", "created_at", "country",
    "location_raw", "location_normalized", "department", "team",
    "commitment", "workplace_type", "salary_min", "salary_max",
    "salary_currency", "hosted_url", "apply_url", "full_description",
    "raw_json", "first_seen", "last_seen",
]

# quantas vagas por requisicao ao banco remoto
# limite do SQLite: 999 valores por comando -> 999 / 21 colunas = 47
TAMANHO_LOTE = 45


def conectar():
    return turso_serverless.connect(
        os.environ["TURSO_URL"],
        auth_token=os.environ["TURSO_TOKEN"],
    )


def criar_tabela():
    conn = conectar()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS vagas (
            source              TEXT NOT NULL,
            company             TEXT NOT NULL,
            id                  TEXT NOT NULL,
            title               TEXT,
            created_at          TEXT,
            country             TEXT,
            location_raw        TEXT,
            location_normalized TEXT,
            department          TEXT,
            team                TEXT,
            commitment          TEXT,
            workplace_type      TEXT,
            salary_min          INTEGER,
            salary_max          INTEGER,
            salary_currency     TEXT,
            hosted_url          TEXT,
            apply_url           TEXT,
            full_description    TEXT,
            raw_json            BLOB,
            first_seen          TEXT,
            last_seen           TEXT,
            PRIMARY KEY (source, company, id)
        )
    """)
    conn.commit()
    conn.close()
    



def salvar_vagas(vagas):
    conn = conectar()

    



    # prepara os valores de todas as vagas, na ordem das colunas
    todos_valores = []
    for vaga in vagas:
        dados = dict(vaga)
        dados["first_seen"] = dados["collected_at"]
        dados["last_seen"] = dados["collected_at"]
        todos_valores.append([dados.get(coluna) for coluna in COLUNAS])

    nomes = ", ".join(COLUNAS)
    grupo = "(" + ", ".join("?" * len(COLUNAS)) + ")"

    # grava em lotes: um INSERT com varias linhas por requisicao
    for i in range(0, len(todos_valores), TAMANHO_LOTE):
        lote = todos_valores[i:i + TAMANHO_LOTE]

        sql = f"""
            INSERT INTO vagas ({nomes})
            VALUES {", ".join([grupo] * len(lote))}
            ON CONFLICT (source, company, id) DO UPDATE SET
                last_seen = excluded.last_seen
        """

        achatados = [valor for linha in lote for valor in linha]
        conn.execute(sql, achatados)

    conn.commit()
    conn.close()


def ler_raw_json(dados):
    """Descomprime o raw_json guardado no banco e devolve o dicionario original."""
    return json.loads(gzip.decompress(dados).decode())


if __name__ == "__main__":
    criar_tabela()
    vaga_teste = {
        "source": "lever",
        "company": "teste",
        "id": "999",
        "title": "Vaga de Teste",
        "collected_at": "2026-08-12T10:00:00+00:00",
    }

    salvar_vagas([vaga_teste])
    print("Vaga de teste salva")
    
    
