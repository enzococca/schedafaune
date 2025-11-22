#!/usr/bin/env python3
"""
Script per pulire le tabelle fauna dal database PostgreSQL
"""

try:
    import psycopg2

    # Connetti al database
    conn = psycopg2.connect(
        host='localhost',
        port=5433,
        database='pyarchinit',
        user='postgres',
        password='Shadowhunters1$'
    )

    cursor = conn.cursor()

    # Elimina le tabelle se esistono
    print("🗑 Eliminazione tabelle fauna...")
    cursor.execute("DROP TABLE IF EXISTS fauna_table CASCADE")
    print("  ✓ fauna_table eliminata")

    cursor.execute("DROP TABLE IF EXISTS fauna_voc CASCADE")
    print("  ✓ fauna_voc eliminata")

    conn.commit()
    conn.close()

    print("✅ Cleanup completato!")

except Exception as e:
    print(f"❌ Errore: {e}")
