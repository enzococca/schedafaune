# 🚀 Guida Rapida Avvio Fauna Manager

## ✅ Soluzione al Problema Qt Plugin

Il problema `Could not find the Qt platform plugin "cocoa"` è stato risolto!

## Metodi di Avvio (3 opzioni)

### 🥇 Metodo 1: Script Python Diretto (CONSIGLIATO)

**Se hai già il virtual environment attivo** (vedi `(.venv)` nel prompt):

```bash
cd /Users/enzo/Desktop/schedafaune
python start_fauna.py
```

✅ **Più semplice e diretto**
✅ **Usa automaticamente il Python del venv**
✅ **Nessun problema con Qt plugins**

### 🥈 Metodo 2: Script Bash Aggiornato

Lo script bash è stato aggiornato per usare il venv automaticamente:

```bash
cd /Users/enzo/Desktop/schedafaune
./start_fauna_manager.sh
```

✅ **Attiva automaticamente .venv se presente**
✅ **Configura le variabili Qt corrette**
✅ **Installa dipendenze se mancanti**

### 🥉 Metodo 3: Manuale (se hai problemi)

```bash
cd /Users/enzo/Desktop/schedafaune

# 1. Attiva virtual environment
source .venv/bin/activate

# 2. Verifica installazioni
pip list | grep PyQt5

# 3. Avvia
python start_fauna.py
```

## 🔧 Risoluzione Problemi

### Problema: "Could not find the Qt platform plugin cocoa"

**Causa**: PyQt5 5.15.11 ha problemi con i plugin Qt su macOS

**Soluzione Automatica**:
```bash
# Usa lo script di fix automatico
./fix_pyqt5.sh
```

**Soluzione Manuale**:
```bash
# Assicurati di essere nel venv
source .venv/bin/activate

# Reinstalla PyQt5 versione stabile
pip uninstall -y PyQt5 PyQt5-Qt5 PyQt5-sip
pip install PyQt5==5.15.10

# Test
python -c "from PyQt5.QtWidgets import QApplication; print('OK')"

# Avvia
python start_fauna.py
```

### Problema: "No module named PyQt5"

**Soluzione**:
```bash
# Attiva venv
source .venv/bin/activate

# Installa dipendenze
pip install -r requirements.txt

# Avvia
python start_fauna.py
```

### Problema: "Database non trovato"

**Soluzione**:
```bash
# Installa tabelle (se non fatto)
python install_db.py

# Oppure all'avvio scegli il database manualmente
```

## 📋 Checklist Pre-Avvio

Prima di avviare, verifica:

- [ ] Sei nella directory corretta: `/Users/enzo/Desktop/schedafaune`
- [ ] Virtual environment attivato: vedi `(.venv)` nel prompt
- [ ] PyQt5 installato: `pip list | grep PyQt5` mostra versione
- [ ] Test passano: `python test_fauna_system.py` mostra tutti ✓

## 🎯 Avvio Passo-Passo (Foolproof)

```bash
# 1. Vai nella directory
cd /Users/enzo/Desktop/schedafaune

# 2. Attiva venv (se non attivo)
source .venv/bin/activate

# 3. Verifica che tutto sia OK
python test_fauna_system.py

# 4. Avvia (metodo semplice)
python start_fauna.py
```

## 🖥️ Da QGIS

**Console Python QGIS**:
```python
import sys
sys.path.insert(0, '/Users/enzo/Desktop/schedafaune')

# Rimuovi cache se hai problemi
if 'qgis_integration' in sys.modules:
    del sys.modules['qgis_integration']
if 'fauna_manager' in sys.modules:
    del sys.modules['fauna_manager']

# Avvia
from qgis_integration import open_fauna_manager_action
open_fauna_manager_action()
```

## ⚡ Quick Start (Una Riga)

Se hai già tutto installato e il venv attivo:

```bash
cd /Users/enzo/Desktop/schedafaune && python start_fauna.py
```

## 🆘 In Caso di Emergenza

Se nulla funziona:

```bash
# 1. Ricrea virtual environment
cd /Users/enzo/Desktop/schedafaune
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate

# 2. Reinstalla tutto
pip install --upgrade pip
pip install -r requirements.txt

# 3. Installa database
python install_db.py

# 4. Test
python test_fauna_system.py

# 5. Avvia
python start_fauna.py
```

## 📊 Verifica Installazione

```bash
# Attiva venv
source .venv/bin/activate

# Verifica versioni
python --version          # Dovrebbe essere 3.13.0 o simile
pip list | grep PyQt5     # Dovrebbe mostrare PyQt5 5.15.11

# Verifica Qt plugins
python -c "from PyQt5.QtCore import QLibraryInfo; print(QLibraryInfo.location(QLibraryInfo.PluginsPath))"

# Test completo
python test_fauna_system.py
```

## 🎉 Tutto Funziona?

Una volta avviato con successo:

1. **Selezione Database**: Scegli SQLite o PostgreSQL
2. **Test Connessione**: Verifica che il database sia accessibile
3. **OK**: L'interfaccia si apre
4. **📚 Gestione Vocabolario**: Disponibile nella toolbar
5. **Pronto!**: Inizia a inserire dati fauna

## 💡 Suggerimenti

- **Usa sempre `start_fauna.py`** quando sei nel venv
- **Usa lo script bash** solo se devi installare dipendenze
- **Da QGIS**: Usa la console Python (più affidabile delle Action)
- **Problemi Qt**: Sempre verificare di essere nel venv corretto

---

**Ultima Modifica**: 2025-11-22
**Script Aggiornati**: start_fauna.py, start_fauna_manager.sh
