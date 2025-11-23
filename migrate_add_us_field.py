#!/usr/bin/env python3
"""
Script di migrazione per aggiungere il campo 'us' alla tabella fauna_table
se non è già presente.

Questo script funziona sia per SQLite che per PostgreSQL.
"""

import sys
import os

# Aggiungi la directory corrente al path per importare i moduli
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fauna_db_wrapper import create_fauna_db
from db_config_manager import DBConfigManager


def check_column_exists_sqlite(db, table_name, column_name):
    """Verifica se una colonna esiste in una tabella SQLite"""
    cursor = db.conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    cursor.close()

    # columns è una lista di tuple: (cid, name, type, notnull, dflt_value, pk)
    column_names = [col[1] for col in columns]
    return column_name in column_names


def check_column_exists_postgres(db, table_name, column_name):
    """Verifica se una colonna esiste in una tabella PostgreSQL"""
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = %s
            AND column_name = %s
        )
    """, (table_name, column_name))
    result = cursor.fetchone()
    exists = result['exists'] if result else False
    cursor.close()
    return exists


def add_us_column_sqlite(db):
    """Aggiunge la colonna 'us' alla tabella fauna_table in SQLite"""
    cursor = db.conn.cursor()

    try:
        print("  → Aggiunta colonna 'us' a fauna_table...")
        cursor.execute("""
            ALTER TABLE fauna_table
            ADD COLUMN us TEXT
        """)
        db.conn.commit()
        print("  ✓ Colonna 'us' aggiunta con successo!")

        # Crea anche l'indice
        print("  → Creazione indice idx_fauna_us...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_fauna_us ON fauna_table(us)
        """)
        db.conn.commit()
        print("  ✓ Indice creato con successo!")

        return True

    except Exception as e:
        print(f"  ✗ Errore durante l'aggiunta della colonna: {e}")
        db.conn.rollback()
        return False

    finally:
        cursor.close()


def add_us_column_postgres(db):
    """Aggiunge la colonna 'us' alla tabella fauna_table in PostgreSQL"""
    cursor = db.conn.cursor()

    try:
        print("  → Aggiunta colonna 'us' a fauna_table...")
        cursor.execute("""
            ALTER TABLE fauna_table
            ADD COLUMN us TEXT
        """)
        db.conn.commit()
        print("  ✓ Colonna 'us' aggiunta con successo!")

        # Crea anche l'indice
        print("  → Creazione indice idx_fauna_us...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_fauna_us ON fauna_table(us)
        """)
        db.conn.commit()
        print("  ✓ Indice creato con successo!")

        return True

    except Exception as e:
        print(f"  ✗ Errore durante l'aggiunta della colonna: {e}")
        db.conn.rollback()
        return False

    finally:
        cursor.close()


def populate_us_fields(db):
    """
    Popola i campi 'sito', 'area', 'saggio', 'us' nei record esistenti
    estraendo i valori dalla tabella us_table tramite la foreign key id_us
    """
    cursor = db.conn.cursor()

    try:
        print("\n  → Popolamento campi US (sito, area, saggio, us) per record esistenti...")

        # Verifica quanti record hanno id_us ma non hanno campi popolati
        if hasattr(db, 'db_type') and db.db_type == 'postgres':
            cursor.execute("""
                SELECT COUNT(*)
                FROM fauna_table
                WHERE id_us IS NOT NULL
                AND (sito IS NULL OR sito = '' OR
                     area IS NULL OR area = '' OR
                     saggio IS NULL OR saggio = '' OR
                     us IS NULL OR us = '')
            """)
        else:
            cursor.execute("""
                SELECT COUNT(*)
                FROM fauna_table
                WHERE id_us IS NOT NULL
                AND (sito IS NULL OR sito = '' OR
                     area IS NULL OR area = '' OR
                     saggio IS NULL OR saggio = '' OR
                     us IS NULL OR us = '')
            """)

        result = cursor.fetchone()
        count_to_update = result['count'] if (result and hasattr(result, 'get')) else (result[0] if result else 0)

        if count_to_update == 0:
            print("  ℹ Nessun record da aggiornare")
            return True

        print(f"  ℹ Trovati {count_to_update} record da aggiornare")

        # Aggiorna i record
        if hasattr(db, 'db_type') and db.db_type == 'postgres':
            cursor.execute("""
                UPDATE fauna_table
                SET
                    sito = us_table.sito,
                    area = us_table.area,
                    saggio = us_table.saggio,
                    us = us_table.us
                FROM us_table
                WHERE fauna_table.id_us = us_table.id_us
                AND (fauna_table.sito IS NULL OR fauna_table.sito = '' OR
                     fauna_table.area IS NULL OR fauna_table.area = '' OR
                     fauna_table.saggio IS NULL OR fauna_table.saggio = '' OR
                     fauna_table.us IS NULL OR fauna_table.us = '')
            """)
        else:
            cursor.execute("""
                UPDATE fauna_table
                SET
                    sito = (SELECT us_table.sito FROM us_table WHERE us_table.id_us = fauna_table.id_us),
                    area = (SELECT us_table.area FROM us_table WHERE us_table.id_us = fauna_table.id_us),
                    saggio = (SELECT us_table.saggio FROM us_table WHERE us_table.id_us = fauna_table.id_us),
                    us = (SELECT us_table.us FROM us_table WHERE us_table.id_us = fauna_table.id_us)
                WHERE id_us IS NOT NULL
                AND (sito IS NULL OR sito = '' OR
                     area IS NULL OR area = '' OR
                     saggio IS NULL OR saggio = '' OR
                     us IS NULL OR us = '')
            """)

        db.conn.commit()

        # Verifica quanti record sono stati aggiornati
        updated = cursor.rowcount
        print(f"  ✓ Aggiornati {updated} record (campi: sito, area, saggio, us)")

        return True

    except Exception as e:
        print(f"  ✗ Errore durante il popolamento: {e}")
        db.conn.rollback()
        return False

    finally:
        cursor.close()


def migrate_database(db_config=None):
    """Esegue la migrazione sul database specificato"""
    print("=" * 70)
    print("MIGRAZIONE DATABASE - Aggiunta campo 'us'")
    print("=" * 70)

    try:
        # Connetti al database
        if db_config is None:
            # Usa la configurazione salvata
            config_manager = DBConfigManager()
            db_config = config_manager.load_config()

            if not db_config:
                print("\n✗ Nessuna configurazione database trovata!")
                print("  Esegui prima fauna_manager.py per configurare il database.")
                return False

        print(f"\n📊 Database: {db_config.get('type', 'unknown')}")

        if db_config['type'] == 'sqlite':
            print(f"   Path: {db_config.get('path', 'N/A')}")
        else:
            print(f"   Host: {db_config.get('host', 'N/A')}:{db_config.get('port', 'N/A')}")
            print(f"   Database: {db_config.get('database', 'N/A')}")

        # Crea connessione
        print("\n🔌 Connessione al database...")
        db = create_fauna_db(db_config=db_config)
        print("✓ Connesso!")

        # Determina il tipo di database
        db_type = db_config['type']

        # Verifica se la tabella fauna_table esiste
        print("\n🔍 Verifica esistenza tabella fauna_table...")

        if db_type == 'sqlite':
            cursor = db.conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='fauna_table'
            """)
            table_exists = cursor.fetchone() is not None
            cursor.close()
        else:
            cursor = db.conn.cursor()
            cursor.execute("""
                SELECT count(*)
                FROM information_schema.tables
                WHERE table_name = 'fauna_table'
            """)
            result = cursor.fetchone()
            table_exists = (result and result['count'] > 0) if result else False
            cursor.close()

        if not table_exists:
            print("✗ Tabella fauna_table non trovata!")
            print("  Esegui prima fauna_manager.py per creare le tabelle.")
            return False

        print("✓ Tabella fauna_table trovata")

        # Verifica se la colonna 'us' esiste già
        print("\n🔍 Verifica esistenza colonna 'us'...")

        if db_type == 'sqlite':
            column_exists = check_column_exists_sqlite(db, 'fauna_table', 'us')
        else:
            column_exists = check_column_exists_postgres(db, 'fauna_table', 'us')

        if column_exists:
            print("ℹ La colonna 'us' esiste già!")
            print("  Verifica popolamento...")

            # Anche se esiste, popola eventuali record vuoti
            populate_us_fields(db)

        else:
            print("⚠ La colonna 'us' non esiste")
            print("\n📝 Avvio migrazione...")

            # Aggiungi la colonna
            if db_type == 'sqlite':
                success = add_us_column_sqlite(db)
            else:
                success = add_us_column_postgres(db)

            if not success:
                print("\n✗ Migrazione fallita!")
                return False

            # Popola i valori esistenti
            populate_us_fields(db)

        # Chiudi connessione
        db.close()

        print("\n" + "=" * 70)
        print("✓ MIGRAZIONE COMPLETATA CON SUCCESSO!")
        print("=" * 70)

        return True

    except Exception as e:
        print(f"\n✗ Errore durante la migrazione: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Funzione principale"""
    print("Script di migrazione - Aggiunta campo 'us' a fauna_table\n")

    # Chiedi conferma
    response = input("Vuoi procedere con la migrazione? [s/N]: ")

    if response.lower() != 's':
        print("\n✗ Migrazione annullata dall'utente")
        return

    # Esegui migrazione
    success = migrate_database()

    if success:
        print("\n✓ Puoi ora usare fauna_manager.py con il campo 'Nome US' completo!")
    else:
        print("\n✗ La migrazione ha riscontrato problemi. Verifica i messaggi di errore sopra.")


if __name__ == '__main__':
    main()