#!/usr/bin/env python3
"""
Script semplice per avviare Fauna Manager
Usa questo se hai già attivato il virtual environment
"""

import sys
import os

# IMPORTANTE: Configura Qt PRIMA di qualsiasi import PyQt5
# Questo risolve il problema "Could not find the Qt platform plugin cocoa"

# Aggiungi la directory corrente al path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Imposta il plugin path basandosi sulla struttura standard di PyQt5
# Questo DEVE essere fatto prima di qualsiasi import Qt
venv_path = sys.prefix
possible_plugin_paths = [
    os.path.join(venv_path, 'lib', f'python{sys.version_info.major}.{sys.version_info.minor}', 'site-packages', 'PyQt5', 'Qt5', 'plugins'),
    os.path.join(venv_path, 'lib', 'python3', 'site-packages', 'PyQt5', 'Qt5', 'plugins'),
]

for path in possible_plugin_paths:
    if os.path.exists(path):
        os.environ['QT_PLUGIN_PATH'] = path
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(path, 'platforms')
        print(f"✓ Qt plugin path configurato: {path}")
        break

# Altre configurazioni Qt
os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '0'
os.environ['QT_MAC_WANTS_LAYER'] = '1'  # Fix per macOS

# Imposta DYLD per le librerie Qt (necessario per @rpath)
qt_lib_path = os.path.join(venv_path, 'lib', f'python{sys.version_info.major}.{sys.version_info.minor}', 'site-packages', 'PyQt5', 'Qt5', 'lib')
if os.path.exists(qt_lib_path):
    current_dyld = os.environ.get('DYLD_LIBRARY_PATH', '')
    if current_dyld:
        os.environ['DYLD_LIBRARY_PATH'] = f"{qt_lib_path}:{current_dyld}"
    else:
        os.environ['DYLD_LIBRARY_PATH'] = qt_lib_path
    print(f"✓ Qt library path configurato: {qt_lib_path}")

# Ora importa PyQt5
try:
    from PyQt5.QtWidgets import QApplication, QMessageBox
except ImportError:
    print("\n❌ Errore: PyQt5 non installato!")
    print("\n📦 Installa con:")
    print("   pip install -r requirements.txt")
    print("\n   oppure:")
    print("   pip install PyQt5==5.15.10")
    sys.exit(1)

# Importa e avvia
try:
    from qgis_integration import FaunaQGISIntegration

    print("\n" + "="*60)
    print("  Fauna Manager - pyArchInit")
    print("  Gestione Schede Faunistiche")
    print("="*60 + "\n")

    # Crea applicazione Qt se non esiste
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # Avvia Fauna Manager
    print("🚀 Avvio interfaccia...\n")

    integration = FaunaQGISIntegration(iface=None)
    integration.open_fauna_manager()

    # Esegui event loop
    sys.exit(app.exec_())

except Exception as e:
    print(f"\n❌ Errore: {e}")

    import traceback
    traceback.print_exc()

    # Mostra dialog errore se possibile
    try:
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        QMessageBox.critical(
            None,
            "Errore Avvio",
            f"Impossibile avviare Fauna Manager:\n\n{str(e)}\n\nControlla la console per dettagli."
        )
    except:
        pass

    sys.exit(1)
