#!/usr/bin/env python3
"""
Esempi d'uso del sistema Fauna Manager
Mostra come usare il sistema programmaticamente
"""

from fauna_db import FaunaDB
from datetime import datetime


def esempio_1_inserimento_record():
    """
    Esempio 1: Inserimento di un nuovo record fauna
    """
    print("\n=== ESEMPIO 1: Inserimento Record ===\n")

    # Connetti al database
    db = FaunaDB()

    # Recupera la lista delle US disponibili
    us_list = db.get_us_list()
    print(f"US disponibili: {len(us_list)}")

    if not us_list:
        print("Nessuna US disponibile!")
        return

    # Usa la prima US disponibile
    us = us_list[0]
    print(f"Usando US: {us['sito']} - {us['area']} - US {us['us']}")

    # Prepara i dati del record
    nuovo_record = {
        # Dati da US (automatici tramite join)
        'id_us': us['id_us'],
        'sito': us['sito'],
        'area': us['area'],
        'us': us['us'],
        'saggio': us.get('saggio', ''),
        'datazione_us': us.get('datazione', ''),

        # Dati deposizionali
        'responsabile_scheda': 'Dr. Mario Rossi',
        'data_compilazione': datetime.now().strftime('%Y-%m-%d'),
        'documentazione_fotografica': 'IMG_001-IMG_050',
        'metodologia_recupero': 'SETACCIO',
        'contesto': 'ABITATIVO',
        'descrizione_contesto': 'Livello di abbandono con resti di pasto',

        # Dati archeozoologici
        'resti_connessione_anatomica': 'NO',
        'tipologia_accumulo': 'RESTI SPORADICI',
        'deposizione': 'DEPOSIZIONE SECONDARIA',
        'numero_stimato_resti': 'Discreti (10-30)',
        'numero_minimo_individui': 2,
        'specie': 'Sus scrofa domesticus',
        'parti_scheletriche': 'Mandibola, Coste, Vertebre',
        'misure_ossa': 0,

        # Dati tafonomici
        'stato_frammentazione': 'SI',
        'tracce_combustione': 'SCARSE',
        'combustione_altri_materiali_us': False,
        'tipo_combustione': 'ANTROPICA',
        'segni_tafonomici_evidenti': 'SI',
        'caratterizzazione_segni_tafonomici': 'ANTROPICA',
        'stato_conservazione': '3',
        'alterazioni_morfologiche': '',

        # Dati contestuali
        'note_terreno_giacitura': 'Terreno sabbioso-argilloso',
        'campionature_effettuate': '',
        'affidabilita_stratigrafica': 'Media',
        'classi_reperti_associazione': 'Ceramica comune, ceramica da cucina',
        'osservazioni': 'Presenza di tracce di macellazione',
        'interpretazione': 'Resti di consumo alimentare',
    }

    # Inserisci il record
    new_id = db.insert_fauna_record(nuovo_record)
    print(f"\n✓ Record inserito con ID: {new_id}")

    db.close()
    return new_id


def esempio_2_lettura_e_ricerca():
    """
    Esempio 2: Lettura e ricerca record
    """
    print("\n=== ESEMPIO 2: Lettura e Ricerca ===\n")

    db = FaunaDB()

    # Leggi tutti i record
    tutti_record = db.get_all_fauna_records()
    print(f"Totale record nel database: {len(tutti_record)}")

    # Ricerca per termine
    risultati = db.search_fauna_records("Sus")
    print(f"\nRicerca 'Sus': {len(risultati)} risultati")

    for record in risultati:
        print(f"  - ID {record['id_fauna']}: {record['specie']} "
              f"({record['sito']}, US {record['us']})")

    # Filtri specifici
    filtri = {
        'contesto': 'FUNERARIO',
        'specie': 'Bos taurus'
    }

    risultati_filtrati = db.get_all_fauna_records(filtri)
    print(f"\nFiltro (contesto=FUNERARIO, specie=Bos taurus): "
          f"{len(risultati_filtrati)} risultati")

    db.close()


def esempio_3_aggiornamento():
    """
    Esempio 3: Aggiornamento di un record esistente
    """
    print("\n=== ESEMPIO 3: Aggiornamento Record ===\n")

    db = FaunaDB()

    # Trova un record
    records = db.get_all_fauna_records()

    if not records:
        print("Nessun record da aggiornare")
        return

    record = records[0]
    record_id = record['id_fauna']

    print(f"Aggiornamento record ID: {record_id}")
    print(f"Specie attuale: {record.get('specie', 'N/A')}")

    # Dati da aggiornare
    aggiornamenti = {
        'numero_minimo_individui': 3,
        'osservazioni': f"Aggiornato il {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        'stato_conservazione': '4'
    }

    # Esegui aggiornamento
    success = db.update_fauna_record(record_id, aggiornamenti)

    if success:
        print("✓ Record aggiornato con successo")

        # Rileggi il record
        record_aggiornato = db.get_fauna_record(record_id)
        print(f"NMI aggiornato: {record_aggiornato['numero_minimo_individui']}")
    else:
        print("✗ Errore nell'aggiornamento")

    db.close()


def esempio_4_vocabolari():
    """
    Esempio 4: Uso dei vocabolari controllati
    """
    print("\n=== ESEMPIO 4: Vocabolari Controllati ===\n")

    db = FaunaDB()

    # Vocabolari disponibili
    vocabolari = [
        'metodologia_recupero',
        'contesto',
        'specie',
        'parti_scheletriche',
        'stato_conservazione'
    ]

    for vocab in vocabolari:
        valori = db.get_voc_values(vocab)
        print(f"\n{vocab}:")
        print(f"  Valori disponibili: {len(valori)}")
        if len(valori) <= 10:
            for val in valori:
                print(f"    - {val}")
        else:
            for val in valori[:5]:
                print(f"    - {val}")
            print(f"    ... e altri {len(valori) - 5}")

    db.close()


def esempio_5_statistiche():
    """
    Esempio 5: Statistiche sui dati
    """
    print("\n=== ESEMPIO 5: Statistiche ===\n")

    db = FaunaDB()

    # Statistiche generali
    tutti_record = db.get_all_fauna_records()
    print(f"Totale record: {len(tutti_record)}")

    if tutti_record:
        # Conta per specie
        specie_count = {}
        for record in tutti_record:
            specie = record.get('specie', 'Indeterminata')
            specie_count[specie] = specie_count.get(specie, 0) + 1

        print("\nDistribuzione per specie:")
        for specie, count in sorted(specie_count.items(), key=lambda x: x[1], reverse=True):
            if specie:
                print(f"  {specie}: {count}")

        # Conta per contesto
        contesto_count = {}
        for record in tutti_record:
            contesto = record.get('contesto', 'Non specificato')
            contesto_count[contesto] = contesto_count.get(contesto, 0) + 1

        print("\nDistribuzione per contesto:")
        for contesto, count in sorted(contesto_count.items(), key=lambda x: x[1], reverse=True):
            if contesto:
                print(f"  {contesto}: {count}")

        # Conta per sito
        sito_count = {}
        for record in tutti_record:
            sito = record.get('sito', 'Non specificato')
            sito_count[sito] = sito_count.get(sito, 0) + 1

        print("\nDistribuzione per sito:")
        for sito, count in sorted(sito_count.items(), key=lambda x: x[1], reverse=True):
            if sito:
                print(f"  {sito}: {count}")

    db.close()


def esempio_6_esportazione_pdf():
    """
    Esempio 6: Esportazione in PDF
    """
    print("\n=== ESEMPIO 6: Esportazione PDF ===\n")

    try:
        from fauna_pdf import FaunaPDFExporter

        db = FaunaDB()

        # Recupera un record
        records = db.get_all_fauna_records()

        if not records:
            print("Nessun record da esportare")
            return

        record = records[0]

        # Crea l'esportatore
        exporter = FaunaPDFExporter()

        # Esporta
        filename = f"Esempio_Scheda_FR_{record['sito']}_US{record['us']}.pdf"
        pdf_path = exporter.export_record(record, filename)

        print(f"✓ PDF esportato: {pdf_path}")

        db.close()

    except ImportError:
        print("⚠ Modulo reportlab non installato")
        print("  Installare con: pip install reportlab")


def esempio_7_eliminazione():
    """
    Esempio 7: Eliminazione record
    """
    print("\n=== ESEMPIO 7: Eliminazione Record ===\n")

    db = FaunaDB()

    # Trova record creati per test
    records = db.search_fauna_records("Test")

    if not records:
        print("Nessun record di test da eliminare")
        return

    print(f"Trovati {len(records)} record di test")

    # Elimina singolo record
    if len(records) > 0:
        record_id = records[0]['id_fauna']
        print(f"\nEliminazione record ID {record_id}...")

        success = db.delete_fauna_record(record_id)

        if success:
            print("✓ Record eliminato")
        else:
            print("✗ Errore nell'eliminazione")

    # Elimina multipli record
    if len(records) > 1:
        ids_to_delete = [r['id_fauna'] for r in records[1:]]
        print(f"\nEliminazione multipla di {len(ids_to_delete)} record...")

        deleted = db.delete_multiple_fauna_records(ids_to_delete)
        print(f"✓ {deleted} record eliminati")

    db.close()


def main():
    """
    Funzione principale - esegue tutti gli esempi
    """
    print("="*60)
    print("FAUNA MANAGER - ESEMPI D'USO")
    print("="*60)

    esempi = [
        esempio_1_inserimento_record,
        esempio_2_lettura_e_ricerca,
        esempio_3_aggiornamento,
        esempio_4_vocabolari,
        esempio_5_statistiche,
        esempio_6_esportazione_pdf,
        # esempio_7_eliminazione,  # Commentato per non eliminare dati reali
    ]

    for esempio in esempi:
        try:
            esempio()
        except Exception as e:
            print(f"\n✗ Errore nell'esempio: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*60)
    print("Fine esempi")
    print("="*60)


if __name__ == '__main__':
    main()
