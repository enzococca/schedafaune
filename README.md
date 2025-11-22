# Fauna Manager per pyArchInit

Sistema completo per la gestione delle schede fauna (SCHEDA FR) integrato con pyArchInit e QGIS.

## Descrizione

Questo sistema permette di:
- Gestire dati faunistici (archeozoologici) da scavi archeologici
- Integrarsi con il database pyArchInit tramite join con la tabella `us_table`
- Inserire, modificare, eliminare e ricercare record
- Utilizzare vocabolari controllati per garantire standardizzazione dei dati
- Esportare schede in formato PDF conforme allo standard SCHEDA FR
- Integrarsi con QGIS tramite Action sui layer

## Struttura del Progetto

```
schedafaune/
├── sql/
│   ├── create_fauna_table.sql      # Schema tabella fauna_table
│   └── create_fauna_voc.sql        # Schema vocabolario controllato
├── fauna_db.py                     # Modulo gestione database
├── fauna_manager.py                # Interfaccia Qt principale
├── fauna_pdf.py                    # Modulo esportazione PDF
├── qgis_integration.py             # Integrazione con QGIS
├── install_db.py                   # Script installazione database
└── README.md                       # Questo file
```

## Requisiti

### Software Necessario
- Python 3.7+
- PyQt5
- SQLite3
- QGIS 3.x (opzionale, per integrazione)
- pyArchInit installato e configurato

### Librerie Python
```bash
pip install PyQt5
pip install reportlab  # Per esportazione PDF
```

## Installazione

### 1. Preparazione

Assicurati che pyArchInit sia installato e che il database `pyarchinit_db.sqlite` esista in:
```
~/pyarchinit/pyarchinit_DB_folder/pyarchinit_db.sqlite
```

### 2. Installazione Tabelle Database

Esegui lo script di installazione:

```bash
cd /Users/enzo/Desktop/schedafaune
python install_db.py
```

Questo script:
- Crea la tabella `fauna_table` con tutti i campi della SCHEDA FR
- Crea la tabella `fauna_voc` con i vocabolari controllati
- Popola i vocabolari con i valori standard
- Crea gli indici per ottimizzare le performance

Per verificare l'installazione:
```bash
python install_db.py --verify
```

### 3. Test dell'Interfaccia

Testa l'interfaccia in modalità standalone:

```bash
python fauna_manager.py
```

## Utilizzo

### Modalità Standalone

Lancia l'interfaccia direttamente:

```bash
python fauna_manager.py
```

### Integrazione con QGIS

#### Metodo 1: Tramite Action sul Layer

1. Apri QGIS e carica il layer `us_table` dal database pyArchInit
2. Vai in **Proprietà Layer → Actions**
3. Aggiungi una nuova action:
   - **Tipo**: Python
   - **Nome**: Gestione Fauna
   - **Azione**:
     ```python
     import sys
     sys.path.insert(0, '/Users/enzo/Desktop/schedafaune')
     from qgis_integration import open_fauna_manager_action
     open_fauna_manager_action()
     ```
4. Clicca OK e salva

Ora puoi aprire Fauna Manager dal menu Actions del layer.

#### Metodo 2: Da Console Python di QGIS

```python
import sys
sys.path.insert(0, '/Users/enzo/Desktop/schedafaune')
from qgis_integration import FaunaQGISIntegration

integration = FaunaQGISIntegration(iface)
integration.open_fauna_manager()
```

### Funzionalità dell'Interfaccia

#### Toolbar di Navigazione
- **⏮ Primo**: Va al primo record
- **◀ Precedente**: Va al record precedente
- **Successivo ▶**: Va al record successivo
- **Ultimo ⏭**: Va all'ultimo record

#### Gestione Record
- **➕ Nuovo**: Crea un nuovo record vuoto
- **💾 Salva**: Salva il record corrente
- **🗑 Elimina**: Elimina il record corrente (con conferma)

#### Ricerca
- **🔍 Cerca**: Apre il dialog di ricerca avanzata
  - Ricerca testuale su tutti i campi
  - Filtri per Sito, Contesto, Specie

#### Esportazione
- **📄 Esporta PDF**: Genera un PDF della scheda corrente

### Organizzazione dei Dati

I dati sono organizzati in 4 tab:

1. **Dati Identificativi**: Informazioni da US (sito, area, saggio, US, datazione) + dati deposizionali
2. **Dati Archeozoologici**: NMI, specie, parti scheletriche, ecc.
3. **Dati Tafonomici**: Frammentazione, combustione, conservazione
4. **Dati Contestuali**: Note, osservazioni, interpretazione

### Join con us_table

I primi 6 campi della scheda fauna sono automaticamente recuperati dalla tabella `us_table`:
1. Sito
2. Area
3. Saggio
4. US
5. Datazione US

Per collegare un record fauna a una US:
1. Seleziona la US dal menu a tendina "US"
2. I campi sito, area, saggio e datazione vengono compilati automaticamente
3. Compila i campi specifici della fauna
4. Salva il record

## Struttura Database

### Tabella fauna_table

Campi principali:
- `id_fauna`: Chiave primaria (auto-incremento)
- `id_us`: Foreign key verso `us_table.id_us`
- Campi SCHEDA FR (34 campi totali, vedi Excel)

### Tabella fauna_voc

Vocabolario controllato con i campi:
- `campo`: Nome del campo (es. 'specie', 'contesto')
- `valore`: Valore del vocabolario
- `descrizione`: Descrizione opzionale
- `ordinamento`: Ordine di visualizzazione

## Esportazione PDF

Per esportare una scheda in PDF:

1. Seleziona il record da esportare
2. Clicca su **📄 Esporta PDF**
3. Il PDF viene salvato sul Desktop con nome:
   ```
   Scheda_FR_{sito}_{area}_US{us}.pdf
   ```

Il PDF generato è conforme al formato SCHEDA FR standard.

## Vocabolari Controllati

I seguenti campi utilizzano vocabolari controllati:

- **Metodologia di Recupero**: A MANO, SETACCIO, FLOTTAZIONE
- **Contesto**: FUNERARIO, ABITATIVO, PRODUTTIVO, IPOGEO, CULTUALE, ALTRO
- **Connessione Anatomica**: SI, NO, PARZIALE
- **Deposizione**: PRIMARIA, SECONDARIA, RIMANEGGIATA
- **Numero Stimato Resti**: Pochi (1-10), Discreti (10-30), Numerosi (30-100), Abbondanti (>100)
- **Specie**: Lista estendibile (Bos taurus, Sus scrofa, etc.)
- **Parti Scheletriche**: Lista anatomica completa
- **Stato Conservazione**: 0-5 (Pessimo → Ottimo)

### Aggiungere Nuove Specie

Per aggiungere nuove specie al vocabolario:

```sql
INSERT INTO fauna_voc (campo, valore, ordinamento)
VALUES ('specie', 'Nome Scientifico', 100);
```

Oppure usa le ComboBox editabili nell'interfaccia.

## Backup e Manutenzione

### Backup del Database

```bash
cp ~/pyarchinit/pyarchinit_DB_folder/pyarchinit_db.sqlite \
   ~/pyarchinit/pyarchinit_DB_folder/backup/pyarchinit_db_$(date +%Y%m%d).sqlite
```

### Verifica Integrità

```bash
sqlite3 ~/pyarchinit/pyarchinit_DB_folder/pyarchinit_db.sqlite "PRAGMA integrity_check;"
```

### Statistiche

```bash
sqlite3 ~/pyarchinit/pyarchinit_DB_folder/pyarchinit_db.sqlite << EOF
SELECT 'Record Fauna:', COUNT(*) FROM fauna_table;
SELECT 'Vocabolari:', COUNT(*) FROM fauna_voc;
SELECT 'Specie diverse:', COUNT(DISTINCT specie) FROM fauna_table WHERE specie != '';
EOF
```

## Troubleshooting

### Problema: "Database non trovato"

Verifica il percorso del database pyArchInit:
```bash
ls -la ~/pyarchinit/pyarchinit_DB_folder/pyarchinit_db.sqlite
```

### Problema: "Tabelle fauna non trovate"

Riesegui l'installazione:
```bash
python install_db.py
```

### Problema: "Errore PyQt5"

Installa PyQt5:
```bash
pip install PyQt5
```

### Problema: "Errore esportazione PDF"

Installa ReportLab:
```bash
pip install reportlab
```

## Sviluppi Futuri

Possibili estensioni:
- [ ] Plugin QGIS completo
- [ ] Import da Excel
- [ ] Export verso altri formati (CSV, shapefile)
- [ ] Integrazione con database online
- [ ] Analisi statistiche integrate
- [ ] Generazione automatica report

## Licenza

Compatibile con la licenza di pyArchInit.

## Autori

Sviluppato per l'integrazione con pyArchInit
Basato sullo standard SCHEDA FR del Ministero dell'Università e della Ricerca

## Supporto

Per problemi o domande:
1. Verifica la documentazione
2. Controlla i log di errore
3. Verifica che pyArchInit sia correttamente installato

## Riferimenti

- pyArchInit: https://github.com/pyarchinit/pyarchinit
- QGIS: https://qgis.org
- Standard SCHEDA FR: Ministero dell'Università e della Ricerca, Progetto ItaliaDomani
