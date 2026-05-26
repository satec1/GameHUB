import sys
import os
from PyQt6.QtWidgets import QApplication
from ui.hud_window import HUDWindow
from workers.system_worker import SystemStatsWorker

def load_stylesheet(app, filepath):
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            app.setStyleSheet(f.read())
    else:
        print(f"Warning: Stylesheet not found at {filepath}")

def main():
    app = QApplication(sys.argv)
    
    # Load stylesheet
    style_path = os.path.join(os.path.dirname(__file__), "resources", "style.qss")
    load_stylesheet(app, style_path)
    
    # Create main window
    hud = HUDWindow()
    hud.show()
    
    # Setup worker
    worker = SystemStatsWorker(update_interval=1.0)
    worker.stats_updated.connect(hud.update_stats)
    worker.start()
    
    # Ensure worker stops when app exits
    app.aboutToQuit.connect(worker.stop)
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
