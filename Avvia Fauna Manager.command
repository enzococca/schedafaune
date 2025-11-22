#!/bin/bash
#
# Launcher macOS per Fauna Manager
# Doppio click per avviare
#

# Vai alla directory dello script
cd "$(dirname "$0")"

# Attiva virtual environment
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo "❌ Virtual environment non trovato!"
    echo "Esegui prima: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    read -p "Premi ENTER per chiudere..."
    exit 1
fi

# Banner
clear
echo "============================================================"
echo "  Fauna Manager - pyArchInit"
echo "  Gestione Schede Faunistiche"
echo "============================================================"
echo ""

# Imposta variabili Qt
export QT_PLUGIN_PATH=".venv/lib/python3.13/site-packages/PyQt5/Qt5/plugins"
export QT_QPA_PLATFORM_PLUGIN_PATH="$QT_PLUGIN_PATH/platforms"
export QT_AUTO_SCREEN_SCALE_FACTOR=0
export QT_MAC_WANTS_LAYER=1

echo "✓ Virtual environment attivato"
echo "✓ Variabili Qt configurate"
echo ""
echo "🚀 Avvio interfaccia..."
echo ""

# Avvia con exec per sostituire il processo bash
exec python qgis_integration.py
