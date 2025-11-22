# Guida Rapida di Installazione

## Prerequisiti
- Python 3.7 o superiore installato
- pyArchInit già configurato con database in `~/pyarchinit/pyarchinit_DB_folder/pyarchinit_db.sqlite`
- QGIS 3.x (opzionale, per integrazione)

## Installazione in 5 Passi

### 1. Installare le dipendenze Python

```bash
cd /Users/enzo/Desktop/schedafaune
pip install -r requirements.txt
```

Oppure manualmente:
```bash
pip install PyQt5 reportlab
```

### 2. Installare le tabelle nel database

```bash
python install_db.py
```

Questo creerà:
- Tabella `fauna_table` (34 campi)
- Tabella `fauna_voc` (vocabolari controllati)
- Indici per ottimizzare le query

### 3. Verificare l'installazione

```bash
python install_db.py --verify
```

Dovresti vedere:
```
✓ Tabella fauna_table trovata
✓ Tabella fauna_voc trovata
✓ Vocabolario: XX valori
✓ Record fauna: 0
```

### 4. Testare il sistema

```bash
python test_fauna_system.py
```

Questo eseguirà 6 test per verificare:
- Connessione database
- Vocabolari
- Integrazione con us_table
- Operazioni CRUD
- Ricerca
- Esportazione PDF

### 5. Avviare l'interfaccia

**Modalità standalone:**
```bash
python fauna_manager.py
```

**Da QGIS (Console Python):**
```python
import sys
sys.path.insert(0, '/Users/enzo/Desktop/schedafaune')
from qgis_integration import FaunaQGISIntegration
integration = FaunaQGISIntegration(iface)
integration.open_fauna_manager()
```

## Primo Utilizzo

1. **Seleziona una US** dal menu a tendina
2. I campi Sito, Area, Saggio, Datazione si compilano automaticamente
3. **Compila i campi** nelle varie tab
4. **Salva** con il bottone 💾
5. **Naviga** tra i record con i bottoni ⏮ ◀ ▶ ⏭

## Integrazione con QGIS (Action)

1. Apri QGIS
2. Carica il layer `us_table`
3. Vai in **Proprietà Layer → Actions**
4. Aggiungi Action:
   - Tipo: **Python**
   - Nome: **Gestione Fauna**
   - Azione:
     ```python
     import sys
     sys.path.insert(0, '/Users/enzo/Desktop/schedafaune')
     from qgis_integration import open_fauna_manager_action
     open_fauna_manager_action()
     ```
5. Salva e chiudi

Ora puoi aprire Fauna Manager dal menu **Actions** del layer!

## Troubleshooting

**Errore: "Database non trovato"**
→ Verifica il percorso: `ls -la ~/pyarchinit/pyarchinit_DB_folder/pyarchinit_db.sqlite`

**Errore: "No module named PyQt5"**
→ Installa: `pip install PyQt5`

**Errore: "No module named reportlab"**
→ Installa: `pip install reportlab` (opzionale per PDF)

**Tabelle non create**
→ Riesegui: `python install_db.py`

## Esempi d'Uso

Vedi il file `esempi_uso.py` per esempi di:
- Inserimento record programmatico
- Ricerca e filtri
- Aggiornamento dati
- Uso dei vocabolari
- Statistiche
- Esportazione PDF

```bash
python esempi_uso.py
```

## Backup del Database

**Importante**: Prima di modifiche importanti, fai sempre un backup!

```bash
cp ~/pyarchinit/pyarchinit_DB_folder/pyarchinit_db.sqlite \
   ~/pyarchinit/pyarchinit_DB_folder/backup_$(date +%Y%m%d).sqlite
```

## Supporto

Per problemi:
1. Controlla README.md per documentazione completa
2. Esegui i test: `python test_fauna_system.py`
3. Verifica i log di errore nella console

## Link Utili

- **README completo**: `README.md`
- **Documentazione tecnica**: `CLAUDE.md`
- **Test**: `test_fauna_system.py`
- **Esempi**: `esempi_uso.py`
