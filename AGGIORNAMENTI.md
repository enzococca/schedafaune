# Aggiornamenti e Nuove Funzionalità

## Problemi Risolti

### ✅ 1. Integrazione QGIS Funzionante
**Problema**: L'interfaccia non appariva quando lanciata da QGIS (console Python o Action)

**Soluzione**:
- Aggiunta variabile globale `_fauna_window` per prevenire garbage collection
- Impostati correttamente parent window e window flags
- Aggiunto messaggio di conferma nella message bar di QGIS
- Gestione corretta degli errori con traceback

**Come testare**:
```python
# Da console Python di QGIS:
import sys
sys.path.insert(0, '/Users/enzo/Desktop/schedafaune')
from qgis_integration import FaunaQGISIntegration
integration = FaunaQGISIntegration(iface)
integration.open_fauna_manager()
```

## Nuove Funzionalità

### ✨ 2. Selezione Database all'Avvio
**Nuovo**: Dialog per scegliere tra SQLite e PostgreSQL prima di avviare

**Caratteristiche**:
- Supporto **SQLite**: percorso file con browser integrato
- Supporto **PostgreSQL**: host, porta, database, user, password
- **Test connessione** con verifica tabella us_table
- Conta US presenti nel database
- Impostazioni predefinite per entrambi i tipi

**File**: `database_selector.py`

### ✨ 3. Supporto PostgreSQL
**Nuovo**: Fauna Manager ora funziona anche con database PostgreSQL

**Implementazione**:
- `fauna_db_wrapper.py`: Factory per creare connessione corretta
- `fauna_db_postgres.py`: Implementazione completa per PostgreSQL
- Stesse funzionalità di SQLite (CRUD, ricerca, vocabolari)
- Query parametriche per sicurezza

**Requisito**: `pip install psycopg2-binary`

### ✨ 4. Gestione Vocabolario Integrata
**Nuovo**: Interfaccia completa per gestire i vocabolari controllati

**Funzionalità**:
- ✏ **Aggiungi** nuovi valori al vocabolario
- 📝 **Modifica** valori esistenti
- 🗑 **Elimina** valori non più necessari
- 🔄 **Riordina** con campo ordinamento
- ✓/✗ **Attiva/Disattiva** valori
- 📝 Aggiunta **descrizione** ai valori

**Campi gestibili**:
- Metodologia recupero
- Contesto
- Connessione anatomica
- Specie
- Parti scheletriche
- Stati di conservazione
- E tutti gli altri 14 campi con vocabolario

**Accesso**: Bottone **📚 Gestione Vocabolario** nella toolbar

**File**: `vocabulary_manager.py`

### ✨ 5. Script di Avvio Automatici
**Nuovo**: Avvio con un click, installazione automatica dipendenze

**Windows**: `start_fauna_manager.bat`
- Verifica Python installato
- Controlla dipendenze (PyQt5, reportlab)
- Propone installazione automatica se mancanti
- Verifica database pyArchInit
- Installa tabelle fauna se necessario
- Avvia interfaccia

**Mac/Linux**: `start_fauna_manager.sh`
- Stesse funzionalità della versione Windows
- Output colorato per migliore leggibilità
- Supporto sia python3 che python

**Uso**:
```bash
# Mac/Linux
./start_fauna_manager.sh

# Windows
start_fauna_manager.bat
```

## Struttura Aggiornata del Progetto

```
schedafaune/
├── sql/                              # Schema database
│   ├── create_fauna_table.sql
│   └── create_fauna_voc.sql
│
├── fauna_db.py                       # Database SQLite (originale)
├── fauna_db_postgres.py              # [NUOVO] Database PostgreSQL
├── fauna_db_wrapper.py               # [NUOVO] Factory per DB
│
├── fauna_manager.py                  # [AGGIORNATO] Interfaccia principale
├── database_selector.py              # [NUOVO] Selezione database
├── vocabulary_manager.py             # [NUOVO] Gestione vocabolario
│
├── fauna_pdf.py                      # Esportazione PDF
├── qgis_integration.py               # [AGGIORNATO] Integrazione QGIS
│
├── install_db.py                     # Installazione database
├── test_fauna_system.py              # Test suite
├── esempi_uso.py                     # Esempi d'uso
│
├── start_fauna_manager.sh            # [NUOVO] Avvio Mac/Linux
├── start_fauna_manager.bat           # [NUOVO] Avvio Windows
│
├── README.md                         # Documentazione
├── INSTALLAZIONE_RAPIDA.md           # Guida rapida
├── AGGIORNAMENTI.md                  # Questo file
└── CLAUDE.md                         # Documentazione tecnica
```

## Istruzioni Aggiornate

### Primo Avvio

#### Metodo 1: Script Automatico (Consigliato)

**Mac/Linux**:
```bash
cd /Users/enzo/Desktop/schedafaune
./start_fauna_manager.sh
```

**Windows**:
```
cd C:\Users\...\schedafaune
start_fauna_manager.bat
```

Lo script:
1. ✓ Verifica Python
2. ✓ Installa dipendenze se mancanti
3. ✓ Installa tabelle database
4. ✓ Avvia interfaccia

#### Metodo 2: Manuale

```bash
# 1. Installa dipendenze
pip install -r requirements.txt

# 2. Installa tabelle (se necessario)
python install_db.py

# 3. Avvia interfaccia
python qgis_integration.py
```

### Integrazione QGIS (Aggiornata)

**Console Python QGIS**:
```python
import sys
sys.path.insert(0, '/Users/enzo/Desktop/schedafaune')
from qgis_integration import FaunaQGISIntegration

integration = FaunaQGISIntegration(iface)
integration.open_fauna_manager()
```

**Action su Layer**:
1. Layer `us_table` → Proprietà → Actions
2. Aggiungi Action Python:
```python
import sys
sys.path.insert(0, '/Users/enzo/Desktop/schedafaune')
from qgis_integration import open_fauna_manager_action
open_fauna_manager_action()
```

### Uso Vocabolario

1. **Apri Fauna Manager**
2. Clicca **📚 Gestione Vocabolario** nella toolbar
3. Seleziona il campo da gestire
4. **➕ Aggiungi** / **✏ Modifica** / **🗑 Elimina** valori
5. Chiudi per tornare all'interfaccia principale
6. I nuovi valori sono subito disponibili nelle combo box

### Uso con PostgreSQL

1. **Primo avvio**: Scegli "PostgreSQL (Server)"
2. Inserisci parametri connessione:
   - Host: `localhost` (o server remoto)
   - Porta: `5432`
   - Database: `pyarchinit`
   - User: `postgres`
   - Password: `tua_password`
3. Clicca **🔍 Test Connessione**
4. Se OK, clicca **OK** per procedere

**Nota**: Richiede `psycopg2-binary`:
```bash
pip install psycopg2-binary
```

## Compatibilità

✅ **Windows**: 7, 8, 10, 11
✅ **macOS**: 10.12+
✅ **Linux**: Ubuntu 18.04+, Debian, Fedora, etc.
✅ **Python**: 3.7, 3.8, 3.9, 3.10, 3.11
✅ **QGIS**: 3.x
✅ **Database**: SQLite 3, PostgreSQL 9.6+

## Dipendenze Aggiornate

**Obbligatorie**:
- PyQt5 >= 5.15.0

**Opzionali**:
- reportlab >= 3.6.0 (per PDF)
- psycopg2-binary >= 2.9.0 (per PostgreSQL)
- pandas >= 1.3.0 (per import/export Excel)
- openpyxl >= 3.0.0 (per file Excel)

## Risoluzione Problemi

### Finestra non appare in QGIS

**Verifica**:
1. Messaggio nella message bar di QGIS?
2. Errori nella console Python?
3. Finestra dietro altre finestre?

**Soluzioni**:
```python
# Riprova con questa versione aggiornata:
import sys
sys.path.insert(0, '/Users/enzo/Desktop/schedafaune')

# Rimuovi vecchie istanze
if 'fauna_manager' in sys.modules:
    del sys.modules['fauna_manager']
if 'qgis_integration' in sys.modules:
    del sys.modules['qgis_integration']

# Ricarica
from qgis_integration import FaunaQGISIntegration
integration = FaunaQGISIntegration(iface)
integration.open_fauna_manager()
```

### Database PostgreSQL non si connette

1. Verifica che PostgreSQL sia avviato
2. Controlla credenziali
3. Verifica firewall/permessi
4. Testa connessione:
```bash
psql -h localhost -U postgres -d pyarchinit
```

### Script bash non si avvia (Mac)

```bash
# Dai permessi di esecuzione
chmod +x start_fauna_manager.sh

# Lancia
./start_fauna_manager.sh
```

## Prossimi Sviluppi

- [ ] Export batch PDF multipli
- [ ] Import dati da Excel
- [ ] Statistiche e grafici integrati
- [ ] Sincronizzazione cloud
- [ ] App mobile companion

## Supporto

Per problemi:
1. Consulta `README.md`
2. Verifica `INSTALLAZIONE_RAPIDA.md`
3. Esegui test: `python test_fauna_system.py`
4. Controlla questo file per aggiornamenti

---

**Versione**: 2.0
**Data**: 2025-11-22
**Autore**: Sistema Fauna Manager - pyArchInit
