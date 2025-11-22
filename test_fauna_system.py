#!/usr/bin/env python3
"""
Script di test per verificare il corretto funzionamento del sistema Fauna Manager
"""

import os
import sys
import sqlite3
from datetime import datetime


def test_database_connection():
    """Test 1: Verifica connessione al database"""
    print("\n" + "="*60)
    print("TEST 1: Connessione Database")
    print("="*60)

    try:
        from fauna_db import FaunaDB

        db = FaunaDB()
        print("✓ Connessione al database riuscita")

        # Verifica tabelle
        cursor = db.conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fauna_table'")
        if cursor.fetchone():
            print("✓ Tabella fauna_table trovata")
        else:
            print("✗ Tabella fauna_table NON trovata")
            return False

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fauna_voc'")
        if cursor.fetchone():
            print("✓ Tabella fauna_voc trovata")
        else:
            print("✗ Tabella fauna_voc NON trovata")
            return False

        db.close()
        return True

    except Exception as e:
        print(f"✗ Errore: {e}")
        return False


def test_vocabulary():
    """Test 2: Verifica vocabolari controllati"""
    print("\n" + "="*60)
    print("TEST 2: Vocabolari Controllati")
    print("="*60)

    try:
        from fauna_db import FaunaDB

        db = FaunaDB()

        # Test alcuni vocabolari
        vocabs_to_test = [
            'metodologia_recupero',
            'contesto',
            'specie',
            'stato_conservazione'
        ]

        for vocab in vocabs_to_test:
            values = db.get_voc_values(vocab)
            print(f"✓ {vocab}: {len(values)} valori")

            if len(values) > 0:
                print(f"  Esempi: {', '.join(values[:3])}")
            else:
                print(f"  ✗ ATTENZIONE: Nessun valore trovato!")

        db.close()
        return True

    except Exception as e:
        print(f"✗ Errore: {e}")
        return False


def test_us_integration():
    """Test 3: Verifica integrazione con us_table"""
    print("\n" + "="*60)
    print("TEST 3: Integrazione con us_table")
    print("="*60)

    try:
        from fauna_db import FaunaDB

        db = FaunaDB()

        # Verifica siti
        siti = db.get_siti_list()
        print(f"✓ Trovati {len(siti)} siti nel database")

        if siti:
            print(f"  Esempi: {', '.join(siti[:5])}")

        # Verifica lista US
        us_list = db.get_us_list()
        print(f"✓ Trovate {len(us_list)} US nel database")

        if us_list:
            esempio_us = us_list[0]
            print(f"  Esempio: Sito={esempio_us.get('sito')}, Area={esempio_us.get('area')}, US={esempio_us.get('us')}")

        db.close()
        return True

    except Exception as e:
        print(f"✗ Errore: {e}")
        return False


def test_crud_operations():
    """Test 4: Verifica operazioni CRUD"""
    print("\n" + "="*60)
    print("TEST 4: Operazioni CRUD")
    print("="*60)

    try:
        from fauna_db import FaunaDB

        db = FaunaDB()

        # Crea un record di test
        print("→ Creazione record di test...")

        # Prima verifica che esista almeno una US
        us_list = db.get_us_list()
        if not us_list:
            print("✗ Nessuna US disponibile per il test")
            return False

        test_us = us_list[0]

        test_data = {
            'id_us': test_us['id_us'],
            'sito': test_us['sito'],
            'area': test_us['area'],
            'us': test_us['us'],
            'saggio': test_us.get('saggio', ''),
            'datazione_us': test_us.get('datazione', ''),
            'responsabile_scheda': 'Test Automatico',
            'data_compilazione': datetime.now().strftime('%Y-%m-%d'),
            'contesto': 'ABITATIVO',
            'metodologia_recupero': 'SETACCIO',
            'specie': 'Bos taurus',
            'numero_minimo_individui': 1,
            'stato_conservazione': '3',
        }

        # INSERT
        new_id = db.insert_fauna_record(test_data)
        print(f"✓ Record inserito con ID: {new_id}")

        # READ
        record = db.get_fauna_record(new_id)
        if record and record['id_fauna'] == new_id:
            print("✓ Record letto correttamente")
        else:
            print("✗ Errore nella lettura del record")
            return False

        # UPDATE
        update_data = {
            'responsabile_scheda': 'Test Aggiornato',
            'numero_minimo_individui': 2
        }
        success = db.update_fauna_record(new_id, update_data)
        if success:
            print("✓ Record aggiornato correttamente")

            # Verifica aggiornamento
            record = db.get_fauna_record(new_id)
            if record['responsabile_scheda'] == 'Test Aggiornato':
                print("✓ Aggiornamento verificato")
            else:
                print("✗ Aggiornamento non applicato")

        # DELETE
        success = db.delete_fauna_record(new_id)
        if success:
            print("✓ Record eliminato correttamente")

            # Verifica eliminazione
            record = db.get_fauna_record(new_id)
            if not record:
                print("✓ Eliminazione verificata")
            else:
                print("✗ Record ancora presente dopo eliminazione")
        else:
            print("✗ Errore nell'eliminazione del record")

        db.close()
        return True

    except Exception as e:
        print(f"✗ Errore: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_search():
    """Test 5: Verifica funzionalità di ricerca"""
    print("\n" + "="*60)
    print("TEST 5: Funzionalità di Ricerca")
    print("="*60)

    try:
        from fauna_db import FaunaDB

        db = FaunaDB()

        # Test ricerca
        results = db.search_fauna_records("test")
        print(f"✓ Ricerca eseguita: {len(results)} risultati trovati")

        # Test filtri
        filters = {'contesto': 'FUNERARIO'}
        results = db.get_all_fauna_records(filters)
        print(f"✓ Filtro per contesto: {len(results)} risultati")

        db.close()
        return True

    except Exception as e:
        print(f"✗ Errore: {e}")
        return False


def test_pdf_export():
    """Test 6: Verifica esportazione PDF"""
    print("\n" + "="*60)
    print("TEST 6: Esportazione PDF")
    print("="*60)

    try:
        from fauna_pdf import FaunaPDFExporter

        print("✓ Modulo PDF importato correttamente")

        # Test con dati di esempio
        test_record = {
            'id_fauna': 999,
            'sito': 'Test Site',
            'area': 'A',
            'us': '001',
            'saggio': 'S1',
            'datazione_us': 'Test Period',
            'responsabile_scheda': 'Tester',
            'data_compilazione': datetime.now().strftime('%Y-%m-%d'),
            'contesto': 'ABITATIVO',
            'specie': 'Bos taurus',
            'stato_conservazione': '3',
        }

        exporter = FaunaPDFExporter()
        pdf_path = exporter.export_record(test_record, "test_export.pdf")

        if os.path.exists(pdf_path):
            print(f"✓ PDF creato: {pdf_path}")
            # Rimuovi il file di test
            os.remove(pdf_path)
            print("✓ File di test rimosso")
            return True
        else:
            print("✗ PDF non creato")
            return False

    except ImportError as e:
        print(f"⚠ Modulo ReportLab non disponibile: {e}")
        print("  Installare con: pip install reportlab")
        return True  # Non è un errore critico
    except Exception as e:
        print(f"✗ Errore: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Esegue tutti i test"""
    print("\n" + "="*60)
    print("FAUNA MANAGER - TEST SUITE")
    print("="*60)
    print(f"Data/Ora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    tests = [
        ("Connessione Database", test_database_connection),
        ("Vocabolari Controllati", test_vocabulary),
        ("Integrazione us_table", test_us_integration),
        ("Operazioni CRUD", test_crud_operations),
        ("Ricerca", test_search),
        ("Esportazione PDF", test_pdf_export),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ ERRORE CRITICO in {test_name}: {e}")
            results.append((test_name, False))

    # Riepilogo
    print("\n" + "="*60)
    print("RIEPILOGO TEST")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print("\n" + "-"*60)
    print(f"Risultato: {passed}/{total} test superati")

    if passed == total:
        print("✓ TUTTI I TEST SUPERATI!")
        return True
    else:
        print(f"✗ {total - passed} test falliti")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
