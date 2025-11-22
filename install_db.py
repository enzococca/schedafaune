#!/usr/bin/env python3
"""
Script per installare le tabelle fauna nel database pyarchinit
"""

import os
import sys
import sqlite3


def install_fauna_tables(db_path=None):
    """
    Installa le tabelle fauna_table e fauna_voc nel database

    Args:
        db_path: percorso del database. Se None, usa il default di pyarchinit
    """
    if db_path is None:
        home = os.path.expanduser("~")
        db_path = os.path.join(home, "pyarchinit", "pyarchinit_DB_folder", "pyarchinit_db.sqlite")

    if not os.path.exists(db_path):
        print(f"ERRORE: Database non trovato in {db_path}")
        print("Verifica il percorso del database pyarchinit")
        return False

    print(f"Connessione al database: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Verifica se le tabelle esistono già
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fauna_table'")
        if cursor.fetchone():
            print("ATTENZIONE: La tabella fauna_table esiste già!")
            risposta = input("Vuoi sovrascriverla? (s/n): ")
            if risposta.lower() != 's':
                print("Installazione annullata")
                return False

            # Elimina le tabelle esistenti
            print("Eliminazione tabelle esistenti...")
            cursor.execute("DROP TABLE IF EXISTS fauna_table")
            cursor.execute("DROP TABLE IF EXISTS fauna_voc")
            conn.commit()

        # Percorso degli script SQL
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sql_dir = os.path.join(script_dir, "sql")

        # Esegui script per fauna_voc
        print("Creazione tabella fauna_voc...")
        voc_sql_path = os.path.join(sql_dir, "create_fauna_voc.sql")

        if not os.path.exists(voc_sql_path):
            print(f"ERRORE: File SQL non trovato: {voc_sql_path}")
            return False

        with open(voc_sql_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
            cursor.executescript(sql_script)

        print("✓ Tabella fauna_voc creata")

        # Esegui script per fauna_table
        print("Creazione tabella fauna_table...")
        table_sql_path = os.path.join(sql_dir, "create_fauna_table.sql")

        if not os.path.exists(table_sql_path):
            print(f"ERRORE: File SQL non trovato: {table_sql_path}")
            return False

        with open(table_sql_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
            cursor.executescript(sql_script)

        print("✓ Tabella fauna_table creata")

        # Commit delle modifiche
        conn.commit()

        # Verifica installazione
        cursor.execute("SELECT COUNT(*) FROM fauna_voc")
        voc_count = cursor.fetchone()[0]
        print(f"✓ Vocabolario controllato: {voc_count} valori inseriti")

        cursor.execute("PRAGMA table_info(fauna_table)")
        fields = cursor.fetchall()
        print(f"✓ Tabella fauna_table: {len(fields)} campi")

        conn.close()

        print("\n" + "="*60)
        print("INSTALLAZIONE COMPLETATA CON SUCCESSO!")
        print("="*60)
        print(f"\nLe tabelle sono state create in: {db_path}")
        print("\nPuoi ora:")
        print("1. Avviare l'interfaccia con: python fauna_manager.py")
        print("2. Integrare con QGIS usando le Action sulle proprietà del layer")

        return True

    except sqlite3.Error as e:
        print(f"\nERRORE DATABASE: {e}")
        return False
    except Exception as e:
        print(f"\nERRORE: {e}")
        return False


def verify_installation(db_path=None):
    """
    Verifica che le tabelle fauna siano installate correttamente

    Args:
        db_path: percorso del database
    """
    if db_path is None:
        home = os.path.expanduser("~")
        db_path = os.path.join(home, "pyarchinit", "pyarchinit_DB_folder", "pyarchinit_db.sqlite")

    if not os.path.exists(db_path):
        print(f"Database non trovato: {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Verifica fauna_table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fauna_table'")
        if not cursor.fetchone():
            print("✗ Tabella fauna_table NON trovata")
            return False
        print("✓ Tabella fauna_table trovata")

        # Verifica fauna_voc
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fauna_voc'")
        if not cursor.fetchone():
            print("✗ Tabella fauna_voc NON trovata")
            return False
        print("✓ Tabella fauna_voc trovata")

        # Conta record vocabolario
        cursor.execute("SELECT COUNT(*) FROM fauna_voc")
        voc_count = cursor.fetchone()[0]
        print(f"✓ Vocabolario: {voc_count} valori")

        # Conta record fauna
        cursor.execute("SELECT COUNT(*) FROM fauna_table")
        fauna_count = cursor.fetchone()[0]
        print(f"✓ Record fauna: {fauna_count}")

        conn.close()
        return True

    except Exception as e:
        print(f"Errore nella verifica: {e}")
        return False


if __name__ == '__main__':
    print("="*60)
    print("INSTALLAZIONE TABELLE FAUNA - pyArchInit")
    print("="*60)
    print()

    # Controlla se è stato fornito un percorso personalizzato
    db_path = None
    if len(sys.argv) > 1:
        db_path = sys.argv[1]

    # Se viene passato --verify, esegue solo la verifica
    if '--verify' in sys.argv:
        verify_installation(db_path)
    else:
        install_fauna_tables(db_path)