#!/usr/bin/env python3
"""
Script di migrazione per aggiungere i nuovi campi JSON alla tabella fauna_table.

Questo script:
1. Aggiunge il campo specie_psi (TEXT) per array JSON di specie/PSI
2. Modifica misure_ossa da NUMERIC a TEXT per array JSON di misure
3. Aggiunge i valori del vocabolario per elemento_anatomico

Eseguire questo script una volta per database che necessitano di aggiornamento.
"""

import os
import sys


def migrate_sqlite(db_path: str) -> bool:
    """Migra un database SQLite"""
    import sqlite3

    print(f"\n📦 Migrazione SQLite: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Verifica se la tabella esiste
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fauna_table'")
        if not cursor.fetchone():
            print("  ⚠ Tabella fauna_table non trovata - skip")
            return True

        # Verifica se il campo specie_psi esiste già
        cursor.execute("PRAGMA table_info(fauna_table)")
        columns = [col[1] for col in cursor.fetchall()]

        changes_made = False

        # Aggiungi specie_psi se non esiste
        if 'specie_psi' not in columns:
            print("  → Aggiunta colonna specie_psi...")
            cursor.execute("ALTER TABLE fauna_table ADD COLUMN specie_psi TEXT DEFAULT ''")
            changes_made = True
            print("  ✓ Colonna specie_psi aggiunta")
        else:
            print("  ✓ Colonna specie_psi già presente")

        # Per SQLite non possiamo modificare il tipo di colonna, ma TEXT accetta tutto
        # quindi verifichiamo solo se misure_ossa è TEXT o NUMERIC
        print("  → Verifica colonna misure_ossa...")
        cursor.execute("PRAGMA table_info(fauna_table)")
        for col in cursor.fetchall():
            if col[1] == 'misure_ossa':
                if 'TEXT' in col[2].upper():
                    print("  ✓ Colonna misure_ossa già TEXT")
                else:
                    # SQLite non permette ALTER COLUMN, ma accetta valori stringa in colonne numeriche
                    print(f"  ⚠ Colonna misure_ossa è {col[2]} (JSON funzionerà comunque)")
                break

        # Aggiungi vocabolario elemento_anatomico
        print("  → Aggiunta vocabolario elemento_anatomico...")
        elementi = [
            ('elemento_anatomico', 'Astragalo', 1),
            ('elemento_anatomico', 'Calcagno', 2),
            ('elemento_anatomico', 'Falange I', 3),
            ('elemento_anatomico', 'Falange II', 4),
            ('elemento_anatomico', 'Falange III', 5),
            ('elemento_anatomico', 'Femore', 6),
            ('elemento_anatomico', 'Metacarpo', 7),
            ('elemento_anatomico', 'Metatarso', 8),
            ('elemento_anatomico', 'Omero', 9),
            ('elemento_anatomico', 'Radio', 10),
            ('elemento_anatomico', 'Scapola', 11),
            ('elemento_anatomico', 'Tibia', 12),
            ('elemento_anatomico', 'Ulna', 13),
            ('elemento_anatomico', 'Atlante', 14),
            ('elemento_anatomico', 'Epistrofeo', 15),
            ('elemento_anatomico', 'Pelvi', 16),
            ('elemento_anatomico', 'Mandibola', 17),
            ('elemento_anatomico', 'Altro', 99),
        ]

        for campo, valore, ordine in elementi:
            try:
                cursor.execute(
                    "INSERT OR IGNORE INTO fauna_voc (campo, valore, ordinamento) VALUES (?, ?, ?)",
                    (campo, valore, ordine)
                )
            except Exception as e:
                print(f"  ⚠ Errore inserimento vocabolario {valore}: {e}")

        conn.commit()
        print("  ✓ Vocabolario elemento_anatomico aggiunto/aggiornato")

        conn.close()
        print("✅ Migrazione SQLite completata!")
        return True

    except Exception as e:
        print(f"❌ Errore migrazione SQLite: {e}")
        import traceback
        traceback.print_exc()
        return False


def migrate_postgres(config: dict) -> bool:
    """Migra un database PostgreSQL"""
    try:
        import psycopg2
    except ImportError:
        print("❌ psycopg2 non installato - impossibile migrare PostgreSQL")
        return False

    print(f"\n📦 Migrazione PostgreSQL: {config['host']}:{config['port']}/{config['database']}")

    try:
        conn = psycopg2.connect(
            host=config.get('host', 'localhost'),
            port=config.get('port', 5432),
            database=config.get('database', 'pyarchinit'),
            user=config.get('user', 'postgres'),
            password=config.get('password', '')
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # Verifica se la tabella esiste
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'fauna_table'
            )
        """)
        if not cursor.fetchone()[0]:
            print("  ⚠ Tabella fauna_table non trovata - skip")
            return True

        # Verifica colonne esistenti
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'fauna_table'
        """)
        columns = {row[0]: row[1] for row in cursor.fetchall()}

        # Aggiungi specie_psi se non esiste
        if 'specie_psi' not in columns:
            print("  → Aggiunta colonna specie_psi...")
            cursor.execute("ALTER TABLE fauna_table ADD COLUMN specie_psi TEXT DEFAULT ''")
            print("  ✓ Colonna specie_psi aggiunta")
        else:
            print("  ✓ Colonna specie_psi già presente")

        # Modifica misure_ossa in TEXT se non lo è già
        if 'misure_ossa' in columns:
            if columns['misure_ossa'] != 'text':
                print(f"  → Modifica colonna misure_ossa da {columns['misure_ossa']} a TEXT...")
                # Prima backup dei dati esistenti
                cursor.execute("ALTER TABLE fauna_table RENAME COLUMN misure_ossa TO misure_ossa_old")
                cursor.execute("ALTER TABLE fauna_table ADD COLUMN misure_ossa TEXT DEFAULT ''")
                cursor.execute("UPDATE fauna_table SET misure_ossa = misure_ossa_old::TEXT WHERE misure_ossa_old IS NOT NULL")
                cursor.execute("ALTER TABLE fauna_table DROP COLUMN misure_ossa_old")
                print("  ✓ Colonna misure_ossa convertita in TEXT")
            else:
                print("  ✓ Colonna misure_ossa già TEXT")

        # Aggiungi vocabolario elemento_anatomico
        print("  → Aggiunta vocabolario elemento_anatomico...")
        elementi = [
            ('elemento_anatomico', 'Astragalo', 1),
            ('elemento_anatomico', 'Calcagno', 2),
            ('elemento_anatomico', 'Falange I', 3),
            ('elemento_anatomico', 'Falange II', 4),
            ('elemento_anatomico', 'Falange III', 5),
            ('elemento_anatomico', 'Femore', 6),
            ('elemento_anatomico', 'Metacarpo', 7),
            ('elemento_anatomico', 'Metatarso', 8),
            ('elemento_anatomico', 'Omero', 9),
            ('elemento_anatomico', 'Radio', 10),
            ('elemento_anatomico', 'Scapola', 11),
            ('elemento_anatomico', 'Tibia', 12),
            ('elemento_anatomico', 'Ulna', 13),
            ('elemento_anatomico', 'Atlante', 14),
            ('elemento_anatomico', 'Epistrofeo', 15),
            ('elemento_anatomico', 'Pelvi', 16),
            ('elemento_anatomico', 'Mandibola', 17),
            ('elemento_anatomico', 'Altro', 99),
        ]

        for campo, valore, ordine in elementi:
            try:
                cursor.execute("""
                    INSERT INTO fauna_voc (campo, valore, ordinamento)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (campo, valore) DO NOTHING
                """, (campo, valore, ordine))
            except Exception as e:
                print(f"  ⚠ Errore inserimento vocabolario {valore}: {e}")

        print("  ✓ Vocabolario elemento_anatomico aggiunto/aggiornato")

        conn.close()
        print("✅ Migrazione PostgreSQL completata!")
        return True

    except Exception as e:
        print(f"❌ Errore migrazione PostgreSQL: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Funzione principale"""
    print("=" * 60)
    print("MIGRAZIONE DATABASE - Supporto JSON per Specie/PSI e Misure")
    print("=" * 60)

    # Cerca configurazione salvata
    config_path = os.path.expanduser("~/.pyarchinit/fauna_db_config.json")

    if os.path.exists(config_path):
        import json
        with open(config_path, 'r') as f:
            config = json.load(f)

        print(f"\n📂 Configurazione trovata: {config_path}")

        if config.get('type') == 'sqlite':
            db_path = config.get('path')
            if db_path and os.path.exists(db_path):
                migrate_sqlite(db_path)
            else:
                print(f"❌ Database SQLite non trovato: {db_path}")
        elif config.get('type') == 'postgres':
            migrate_postgres(config)
        else:
            print(f"❌ Tipo database non supportato: {config.get('type')}")
    else:
        # Default: prova percorso SQLite standard
        home = os.path.expanduser("~")
        default_path = os.path.join(home, "pyarchinit", "pyarchinit_DB_folder", "pyarchinit_db.sqlite")

        if os.path.exists(default_path):
            print(f"\n📂 Uso percorso predefinito: {default_path}")
            migrate_sqlite(default_path)
        else:
            print("\n❌ Nessun database trovato!")
            print("   Specifica il percorso manualmente o configura prima l'applicazione.")
            print("\n   Uso: python migrate_add_json_fields.py [percorso_database.sqlite]")

            if len(sys.argv) > 1:
                path = sys.argv[1]
                if os.path.exists(path):
                    migrate_sqlite(path)
                else:
                    print(f"❌ File non trovato: {path}")


if __name__ == '__main__':
    main()
