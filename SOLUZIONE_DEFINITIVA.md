# 🎯 SOLUZIONE DEFINITIVA - Problema Qt su macOS

## 🔍 Diagnosi Finale

**Problema**: PyQt5 5.15.10 non funziona con Python 3.13 su macOS ARM64 nel venv, probabilmente per conflitto con conda (base) attivo.

**Evidenze**:
- ✅ Plugin `libqcocoa.dylib` esiste
- ✅ File non corrotto
- ✅ Permessi corretti
- ❌ QApplication fallisce sempre con "Could not find Qt platform plugin cocoa"
- ❌ Anche dopo aver impostato correttamente `QT_PLUGIN_PATH`

## ✅ SOLUZIONI (3 opzioni)

### Soluzione 1: Disattiva Conda (VELOCE)

```bash
# 1. Disattiva completamente conda
conda deactivate

# 2. Riavvia il terminale o esegui
exec $SHELL

# 3. Attiva solo il venv
cd /Users/enzo/Desktop/schedafaune
source .venv/bin/activate

# 4. Reinstalla PyQt5
pip uninstall -y PyQt5 PyQt5-Qt5 PyQt5-sip
pip install PyQt5==5.15.10

# 5. Test
python -c "from PyQt5.QtWidgets import QApplication; app = QApplication([]); print('✓ OK'); app.quit()"

# 6. Avvia
python start_fauna.py
```

### Soluzione 2: Usa PySide6 (CONSIGLIATA)

PySide6 è più moderno e funziona meglio con Python 3.13:

```bash
cd /Users/enzo/Desktop/schedafaune
source .venv/bin/activate

# Installa PySide6
pip install PySide6

# Test
python -c "from PySide6.QtWidgets import QApplication; app = QApplication([]); print('✓ OK'); app.quit()"
```

**Nota**: Dovrai modificare gli import nel codice da `PyQt5` a `PySide6` (quasi identico).

### Soluzione 3: Usa Python di Sistema (NON venv)

```bash
cd /Users/enzo/Desktop/schedafaune

# Disattiva venv
deactivate

# Usa Python di sistema
python3 -m pip install --user PyQt5==5.15.10

# Test
python3 -c "from PyQt5.QtWidgets import QApplication; app = QApplication([]); print('✓ OK'); app.quit()"

# Avvia
python3 start_fauna.py
```

## 🎬 Procedura Raccomandata

**Scelta: Soluzione 1 (Disattiva Conda)**

Più veloce e mantiene tutto il codice PyQt5 esistente:

```bash
# 1. CHIUDI TUTTI I TERMINALI

# 2. Apri nuovo terminale

# 3. PRIMA di attivare conda, fai
cd /Users/enzo/Desktop/schedafaune
python3 -m venv .venv --clear  # Ricrea venv pulito
source .venv/bin/activate

# 4. Reinstalla
pip install --upgrade pip
pip install -r requirements.txt

# 5. Test
python test_fauna_system.py

# 6. Avvia
python start_fauna.py
```

## 📋 Verifica Prima di Avviare

```bash
# Nel terminale, NON deve esserci (base)
# Deve esserci solo (.venv)

# Verifica:
which python  # Deve essere .venv/bin/python
echo $CONDA_DEFAULT_ENV  # Deve essere vuoto

# Se vedi (base), esegui:
conda config --set auto_activate_base false
```

## 🐍 Alternative: Usa Python 3.11 o 3.12

PyQt5 funziona meglio con Python <= 3.12:

```bash
# Installa Python 3.12 (se non ce l'hai)
brew install python@3.12

# Ricrea venv con Python 3.12
cd /Users/enzo/Desktop/schedafaune
rm -rf .venv
python3.12 -m venv .venv
source .venv/bin/activate

# Installa dipendenze
pip install -r requirements.txt

# Test e avvia
python test_fauna_system.py
python start_fauna.py
```

## 🆘 Se Nulla Funziona

Usa l'app Python in modalità headless (senza GUI) o accedi tramite QGIS:

```python
# Da QGIS Console Python (QGIS ha Qt già funzionante)
import sys
sys.path.insert(0, '/Users/enzo/Desktop/schedafaune')

# QGIS usa già Qt, quindi funzionerà
from qgis_integration import open_fauna_manager_action
open_fauna_manager_action()
```

## 📊 Riepilogo Compatibilità

| Configurazione | Stato | Note |
|---|---|---|
| PyQt5 + Python 3.13 + conda (base) | ❌ | Non funziona |
| PyQt5 + Python 3.13 + solo venv | ⚠️ | Da verificare |
| PyQt5 + Python 3.11/3.12 | ✅ | Funziona |
| PySide6 + Python 3.13 | ✅ | Funziona |
| QGIS Console | ✅ | Funziona sempre |

## 🎯 Azione Immediata

**PROVA QUESTO ORA**:

```bash
# 1. Chiudi terminale
# 2. Apri nuovo terminale
# 3. NON attivare conda
# 4. Esegui:

cd /Users/enzo/Desktop/schedafaune
source .venv/bin/activate

# Verifica che NON ci sia (base):
echo "Python: $(which python)"
echo "Conda: $CONDA_DEFAULT_ENV"

# Se è pulito, prova:
python start_fauna.py
```

Se funziona, aggiungi a `~/.zshrc` o `~/.bash_profile`:

```bash
# Disabilita auto-attivazione conda
conda config --set auto_activate_base false
```

---

**Ultima Modifica**: 2025-11-22
**Problema**: Conflitto conda/venv + PyQt5/Python 3.13
**Soluzione Finale**: Disattiva conda O usa PySide6 O usa Python 3.12
