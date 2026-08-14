import sqlite3
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DB_PATH = RAIZ / "data" / "jobs.db"
COLUNAS = [
    "source", "company", "id", "title", "created_at", "country",
    "location_raw", "location_normalized", "department", "team",
    "commitment", "workplace_type", "salary_min", "salary_max",
    "salary_currency", "hosted_url", "apply_url", "full_description",
    "raw_json", "first_seen", "last_seen",
]


def conectar():
    return sqlite3.connect(DB_PATH)


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
            raw_json            TEXT,
            first_seen          TEXT,
            last_seen           TEXT,
            PRIMARY KEY (source, company, id)
        )
    """)
    conn.commit()
    conn.close()
    



def salvar_vagas(vagas):
    conn = conectar()
    nomes=", ".join(COLUNAS)
    marcadores= ", ".join("?" * len(COLUNAS))

    sql=f"""
        INSERT INTO vagas ({nomes})
        VALUES ({marcadores})
        ON CONFLICT (source, company,id) DO UPDATE SET
            last_seen=excluded.last_seen
            """

    for vaga in vagas:
        dados= dict(vaga)
        dados["first_seen"]= dados["collected_at"]
        dados["last_seen"] = dados["collected_at"]

        valores=[dados.get(coluna) for coluna in COLUNAS]
        conn.execute(sql,valores)


    conn.commit()
    conn.close()

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
    
    
