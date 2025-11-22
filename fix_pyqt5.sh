#!/bin/bash
#
# Script per fixare problemi PyQt5 su macOS
#

echo "🔧 Fix PyQt5 - Fauna Manager"
echo ""

# Attiva venv
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "✓ Virtual environment attivato"
else
    echo "✗ Virtual environment .venv non trovato!"
    echo "  Crealo con: python3 -m venv .venv"
    exit 1
fi

echo ""
echo "📦 Disinstallazione PyQt5 esistente..."
pip uninstall -y PyQt5 PyQt5-Qt5 PyQt5-sip

echo ""
echo "📥 Installazione PyQt5 5.15.10 (versione stabile)..."
pip install PyQt5==5.15.10

echo ""
echo "🧪 Test installazione..."
python -c "from PyQt5.QtWidgets import QApplication; app = QApplication([]); print('✓ PyQt5 funziona correttamente!'); app.quit()"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ PyQt5 fixato con successo!"
    echo ""
    echo "Puoi ora avviare con:"
    echo "  python start_fauna.py"
else
    echo ""
    echo "✗ Qualcosa è andato storto. Contatta il supporto."
    exit 1
fi
