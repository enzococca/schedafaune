#!/usr/bin/env python3
"""
Script per popolare i campi sito, area, saggio, us nei record fauna esistenti
prendendo i valori dalla tabella us_table tramite la foreign key id_us
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fauna_db_wrapper import create_fauna_db
from db_config_manager import DBConfigManager


def populate_us_fields():
    """Popola i campi US nei record fauna esistenti"""
    print("=" * 70)
    print("POPOLAMENTO CAMPI US IN FAUNA_TABLE")
    print("=" * 70)

    try:
        # Carica configurazione
        config_manager = DBConfigManager()
        db_config = config_manager.load_config()

        if not db_config:
            print("\n✗ Nessuna configurazione database trovata!")
            return False

        print(f"\n📊 Database: {db_config.get('type', 'unknown')}")
        if db_config['type'] == 'sqlite':
            print(f"   Path: {db_config.get('path', 'N/A')}")
        else:
            print(f"   Host: {db_config.get('host', 'N/A')}:{db_config.get('port', 'N/A')}")
            print(f"   Database: {db_config.get('database', 'N/A')}")

        # Connetti al database
        print("\n🔌 Connessione al database...")
        db = create_fauna_db(db_config=db_config)
        print("✓ Connesso!")

        cursor = db.conn.cursor()

        # Verifica quanti record hanno id_us ma campi vuoti
        print("\n🔍 Verifica record da aggiornare...")

        if db_config['type'] == 'postgres':
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
        if db_config['type'] == 'postgres':
            count = result['count'] if (result and hasattr(result, 'get')) else 0
        else:
            count = result[0] if result else 0

        if count == 0:
            print("ℹ Nessun record da aggiornare")
            cursor.close()
            db.close()
            return True

        print(f"✓ Trovati {count} record da aggiornare")

        # Aggiorna i record
        print("\n📝 Aggiornamento campi...")

        if db_config['type'] == 'postgres':
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
            # Per SQLite serve un approccio diverso
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

        updated = cursor.rowcount
        print(f"✓ Aggiornati {updated} record")

        # Verifica risultato
        print("\n🔍 Verifica finale...")

        if db_config['type'] == 'postgres':
            cursor.execute("""
                SELECT
                    COUNT(*) FILTER (WHERE sito IS NOT NULL AND sito != '') as with_sito,
                    COUNT(*) FILTER (WHERE area IS NOT NULL AND area != '') as with_area,
                    COUNT(*) FILTER (WHERE saggio IS NOT NULL AND saggio != '') as with_saggio,
                    COUNT(*) FILTER (WHERE us IS NOT NULL AND us != '') as with_us,
                    COUNT(*) as total
                FROM fauna_table
                WHERE id_us IS NOT NULL
            """)
            result = cursor.fetchone()
            print(f"✓ Record con sito: {result['with_sito']}/{result['total']}")
            print(f"✓ Record con area: {result['with_area']}/{result['total']}")
            print(f"✓ Record con saggio: {result['with_saggio']}/{result['total']}")
            print(f"✓ Record con us: {result['with_us']}/{result['total']}")
        else:
            cursor.execute("""
                SELECT COUNT(*) FROM fauna_table WHERE id_us IS NOT NULL
            """)
            total = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*) FROM fauna_table
                WHERE id_us IS NOT NULL AND sito IS NOT NULL AND sito != ''
            """)
            with_sito = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*) FROM fauna_table
                WHERE id_us IS NOT NULL AND area IS NOT NULL AND area != ''
            """)
            with_area = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*) FROM fauna_table
                WHERE id_us IS NOT NULL AND saggio IS NOT NULL AND saggio != ''
            """)
            with_saggio = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*) FROM fauna_table
                WHERE id_us IS NOT NULL AND us IS NOT NULL AND us != ''
            """)
            with_us = cursor.fetchone()[0]

            print(f"✓ Record con sito: {with_sito}/{total}")
            print(f"✓ Record con area: {with_area}/{total}")
            print(f"✓ Record con saggio: {with_saggio}/{total}")
            print(f"✓ Record con us: {with_us}/{total}")

        cursor.close()
        db.close()

        print("\n" + "=" * 70)
        print("✓ POPOLAMENTO COMPLETATO!")
        print("=" * 70)

        return True

    except Exception as e:
        print(f"\n✗ Errore: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("Script di popolamento campi US\n")
    response = input("Vuoi procedere? [s/N]: ")

    if response.lower() != 's':
        print("\n✗ Operazione annullata")
    else:
        success = populate_us_fields()
        if success:
            print("\n✓ Ora le statistiche mostreranno correttamente siti, aree e saggi!")
        else:
            print("\n✗ Si sono verificati problemi. Controlla i messaggi sopra.")