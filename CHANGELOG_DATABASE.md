# 🔄 Changelog - Gestione Database e Memoria Connessione

## Data: 2025-11-22

## ✅ Modifiche Implementate

### 1. **Creazione Automatica Tabelle**
Le tabelle `fauna_table` e `fauna_voc` vengono ora create automaticamente quando ci si connette a un database che non le contiene.

**File modificati:**
- `fauna_db.py` (linee 40-103): Metodo `ensure_tables_exist()` migliorato
- `fauna_db_postgres.py` (linee 52-154): Metodo `ensure_tables_exist()` migliorato per PostgreSQL

**Comportamento:**
1. All'avvio o al cambio database, il sistema verifica se le tabelle esistono
2. Se mancanti, le crea automaticamente dai file SQL in `sql/`
3. Mostra messaggi informativi durante il processo:
   ```
   ⚠ Tabelle fauna non trovate nel database
   📦 Creazione tabelle in corso...
     → Creazione tabella fauna_voc...
     ✓ Tabella fauna_voc creata
     → Creazione tabella fauna_table...
     ✓ Tabella fauna_table creata
   ✅ Tabelle fauna create con successo!
   ```
4. Gestisce gli errori senza bloccare l'applicazione

---

### 2. **Memoria Ultima Connessione**
Il sistema ora ricorda l'ultima configurazione database utilizzata.

**Nuovo file:**
- `db_config_manager.py`: Gestisce salvataggio/caricamento configurazione

**Percorso configurazione:**
- `~/.pyarchinit/fauna_db_config.json`

**Formato file:**
```json
{
  "type": "sqlite",
  "path": "/Users/enzo/pyarchinit/pyarchinit_DB_folder/pyarchinit_db.sqlite"
}
```

oppure

```json
{
  "type": "postgres",
  "host": "localhost",
  "port": 5432,
  "database": "pyarchinit",
  "user": "postgres",
  "password": ""
}
```

**Nota Sicurezza:** La password PostgreSQL viene salvata vuota per sicurezza. Se vuoi salvarla, commenta la riga 34 in `db_config_manager.py`.

---

### 3. **Dialog Selezione Database Migliorato**
Il dialog ora carica automaticamente l'ultima configurazione salvata.

**File modificato:**
- `database_selector.py`

**Nuove funzionalità:**
- Metodo `load_saved_or_default_settings()`: Carica ultima config o default
- Metodo `load_config_to_ui()`: Popola il dialog con config salvata
- Metodo `on_accept()`: Salva la configurazione quando si clicca OK

**Comportamento:**
1. All'apertura, carica l'ultima configurazione usata
2. Pre-compila tutti i campi (tipo database, percorso, host, porta, ecc.)
3. Quando clicchi OK, salva la nuova configurazione

---

### 4. **Pulsante "Cambia Database" in Fauna Manager**
Aggiunto pulsante nella toolbar per cambiare database durante l'uso.

**File modificato:**
- `fauna_manager.py`

**Nuove funzionalità:**
- Pulsante `🔄 Cambia Database` nella toolbar
- Metodo `change_database()`: Gestisce il cambio database
- Metodo `format_db_config()`: Formatta info database per visualizzazione

**Comportamento:**
1. Click su `🔄 Cambia Database`
2. Si apre il dialog di selezione (pre-compilato con config corrente)
3. Scegli nuovo database e clicca OK
4. Conferma il cambio (avvisa che modifiche non salvate andranno perse)
5. Il sistema:
   - Chiude la connessione corrente
   - Si connette al nuovo database
   - Verifica/crea le tabelle automaticamente
   - Ricarica combo box e record
6. Mostra messaggio di conferma

---

### 5. **Caricamento Automatico Ultima Configurazione**
All'avvio, l'app carica automaticamente l'ultima configurazione.

**File modificato:**
- `qgis_integration.py`

**Comportamento:**
1. **Con configurazione salvata:**
   ```
   📂 Caricamento ultima configurazione database...
   ✓ Configurazione caricata da: ~/.pyarchinit/fauna_db_config.json
   ✓ Tabelle fauna già presenti nel database
   ```
   → Si apre direttamente Fauna Manager

2. **Senza configurazione salvata:**
   ```
   📝 Nessuna configurazione salvata, mostra dialog di selezione...
   ```
   → Si apre il dialog per selezionare il database

---

## 🎯 Flusso Completo

### Primo Avvio
1. Avvia `./start_fauna_manager.sh` o `python start_fauna.py`
2. Nessuna configurazione salvata → mostra dialog selezione database
3. Scegli SQLite o PostgreSQL, inserisci dati, clicca OK
4. La configurazione viene salvata in `~/.pyarchinit/fauna_db_config.json`
5. Il sistema verifica se le tabelle esistono nel database
6. Se mancano, le crea automaticamente
7. Si apre Fauna Manager

### Avvii Successivi
1. Avvia `./start_fauna_manager.sh` o `python start_fauna.py`
2. Configurazione trovata → carica automaticamente
3. Si connette al database salvato
4. Verifica le tabelle (le crea se necessarie)
5. Si apre Fauna Manager direttamente

### Cambio Database Durante l'Uso
1. Dentro Fauna Manager, clicca `🔄 Cambia Database`
2. Dialog pre-compilato con configurazione corrente
3. Modifica database/configurazione, clicca OK
4. Conferma il cambio
5. Nuova configurazione salvata
6. Connessione al nuovo database
7. Verifica/creazione tabelle automatica
8. Ricaricamento interfaccia

---

## 🧪 Test

### Test 1: Database SQLite Senza Tabelle
```bash
# Crea un database vuoto
sqlite3 ~/test_fauna.sqlite "CREATE TABLE us_table (id_us INTEGER PRIMARY KEY);"

# Avvia e connettiti a questo database
python start_fauna.py
```

**Risultato atteso:**
- Dialog si apre
- Selezioni SQLite e il file `~/test_fauna.sqlite`
- Clicchi OK
- Messaggio: "📦 Creazione tabelle in corso..."
- Le tabelle vengono create
- Fauna Manager si apre normalmente

### Test 2: Memoria Ultima Connessione
```bash
# Primo avvio
python start_fauna.py  # Seleziona database

# Chiudi e riavvia
python start_fauna.py  # Si connette automaticamente all'ultimo database
```

**Risultato atteso:**
- Al secondo avvio, nessun dialog
- Si connette direttamente al database precedente

### Test 3: Cambio Database Durante l'Uso
1. Apri Fauna Manager
2. Clicca `🔄 Cambia Database`
3. Cambia da SQLite a PostgreSQL (o viceversa)
4. Conferma
5. Verifica che i record si ricarichino

**Risultato atteso:**
- Cambio database senza crash
- Interfaccia si aggiorna
- Tabelle verificate/create nel nuovo database

---

## 📝 Note Tecniche

### Gestione Errori
- Se il file SQL non esiste, viene mostrato un avviso ma l'app continua
- Se la creazione tabelle fallisce, viene mostrato l'errore ma l'app non crasha
- Errori PostgreSQL (tabella già esistente) vengono filtrati e ignorati

### Adattamenti PostgreSQL
Il sistema adatta automaticamente la sintassi SQL da SQLite a PostgreSQL:
- `AUTOINCREMENT` → `GENERATED ALWAYS AS IDENTITY`
- `IF NOT EXISTS` viene rimosso (gestito via `information_schema`)
- `BOOLEAN DEFAULT` → rimane invariato
- `NUMERIC (6, 2)` → `NUMERIC(6, 2)` (rimuove spazi)

### Sicurezza
- La password PostgreSQL NON viene salvata di default
- Per salvarla (sconsigliato in ambienti condivisi), commenta la riga 34 in `db_config_manager.py`

---

## 🔧 File Modificati

1. ✅ `fauna_db.py` - Creazione automatica tabelle SQLite
2. ✅ `fauna_db_postgres.py` - Creazione automatica tabelle PostgreSQL
3. ✅ `database_selector.py` - Caricamento/salvataggio configurazione
4. ✅ `fauna_manager.py` - Pulsante cambio database
5. ✅ `qgis_integration.py` - Auto-caricamento ultima configurazione
6. ✨ `db_config_manager.py` - **NUOVO** - Gestione persistenza configurazione

---

## 🎉 Risultato Finale

**Problema risolto:**
- ✅ Le tabelle vengono create automaticamente se mancanti
- ✅ L'ultima connessione viene ricordata
- ✅ Si può cambiare database durante l'uso
- ✅ Nessun errore se database non ha le tabelle fauna
- ✅ Supporto completo SQLite e PostgreSQL

**Esperienza utente:**
1. Primo avvio → scegli database una volta
2. Avvii successivi → si apre direttamente
3. Cambio database → un click sulla toolbar
4. Database senza tabelle → create automaticamente
5. Tutto trasparente e senza errori!
