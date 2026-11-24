"""
CloudBrowser - Navegador con privacidad mejorada via Cloudflare 1.1.1.1

Arquitectura de bypass DNS:
  1. proxy_server.py arranca un proxy HTTP local en 127.0.0.1:8899.
  2. Chromium se configura para usar ese proxy con --proxy-server.
  3. Para cada petición el proxy resuelve el hostname via DoH a 1.1.1.1:443
     (no usa el DNS del sistema, que el firewall intercepta).
  4. El firewall no puede bloquear las consultas DoH porque van cifradas
     por el puerto 443, igual que cualquier HTTPS normal.
"""
import os
import sys

# Arrancar el proxy DoH ANTES de cualquier import de Qt
from proxy_server import DoHProxyServer as _DoHProxyServer
_proxy = _DoHProxyServer()
_proxy_running = _proxy.start()

# Chromium debe usar nuestro proxy local para que el DNS pase por DoH.
# --proxy-server: todo el tráfico del navegador pasa por 127.0.0.1:8899.
# --proxy-bypass-list: localhost y 127.x no usan el proxy (evita bucles).
# --no-sandbox: necesario en ejecutables empaquetados con PyInstaller.
_proxy_flag = "--proxy-server=http://127.0.0.1:8899 " if _proxy_running else ""
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
    f"{_proxy_flag}"
    "--proxy-bypass-list=localhost;127.0.0.1;::1 "
    "--no-sandbox "
    "--disable-dev-shm-usage"
).strip()

# Habilita soporte para pantallas HiDPI
os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")
os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from window import BrowserWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("CloudBrowser")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("CloudBrowser")
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # Estilo oscuro moderno
    app.setStyleSheet("""
        QMainWindow, QWidget {
            background-color: #1e1e2e;
            color: #cdd6f4;
        }
        QToolBar {
            background-color: #181825;
            border-bottom: 1px solid #313244;
            padding: 4px 6px;
            spacing: 4px;
        }
        QToolBar QToolButton {
            color: #cdd6f4;
            background: transparent;
            border: none;
            border-radius: 4px;
            padding: 4px 8px;
            font-size: 14px;
        }
        QToolBar QToolButton:hover {
            background-color: #313244;
        }
        QToolBar QToolButton:pressed {
            background-color: #45475a;
        }
        QLineEdit {
            background-color: #313244;
            color: #cdd6f4;
            border: 1px solid #45475a;
            border-radius: 6px;
            padding: 5px 10px;
            font-size: 13px;
            selection-background-color: #89b4fa;
        }
        QLineEdit:focus {
            border: 1px solid #89b4fa;
        }
        QTabWidget::pane {
            border: none;
            background-color: #1e1e2e;
        }
        QTabBar {
            background-color: #181825;
        }
        QTabBar::tab {
            background-color: #181825;
            color: #a6adc8;
            border: none;
            padding: 7px 16px;
            font-size: 12px;
            min-width: 120px;
            max-width: 220px;
        }
        QTabBar::tab:selected {
            background-color: #1e1e2e;
            color: #cdd6f4;
            border-top: 2px solid #89b4fa;
        }
        QTabBar::tab:hover:!selected {
            background-color: #313244;
            color: #cdd6f4;
        }
        QTabBar::close-button {
            image: none;
            subcontrol-position: right;
        }
        QStatusBar {
            background-color: #181825;
            color: #6c7086;
            font-size: 11px;
            border-top: 1px solid #313244;
        }
        QMenuBar {
            background-color: #181825;
            color: #cdd6f4;
            border-bottom: 1px solid #313244;
        }
        QMenuBar::item:selected {
            background-color: #313244;
        }
        QMenu {
            background-color: #1e1e2e;
            color: #cdd6f4;
            border: 1px solid #45475a;
        }
        QMenu::item:selected {
            background-color: #313244;
        }
        QMenu::separator {
            background-color: #45475a;
            height: 1px;
            margin: 3px 0;
        }
        QPushButton {
            background-color: #313244;
            color: #cdd6f4;
            border: 1px solid #45475a;
            border-radius: 4px;
            padding: 4px 10px;
        }
        QPushButton:hover {
            background-color: #45475a;
        }
        QLabel {
            color: #cdd6f4;
        }
        QMessageBox {
            background-color: #1e1e2e;
            color: #cdd6f4;
        }
    """)

    window = BrowserWindow()
    window.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
