"""
CloudBrowser - Navegador con privacidad mejorada via Cloudflare 1.1.1.1
"""
import os
import sys

# Debe configurarse ANTES de crear QApplication
# --no-sandbox: necesario en ejecutables PyInstaller donde el sandbox de
#   Chromium no puede inicializarse correctamente, causando ERR_CONNECTION_RESET
# --disable-dev-shm-usage: evita fallos por memoria compartida limitada en Windows
# DoH: DNS sobre HTTPS apuntando a Cloudflare 1.1.1.1
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
    "--no-sandbox "
    "--disable-dev-shm-usage "
    "--dns-over-https-servers=https://cloudflare-dns.com/dns-query "
    "--enable-features=DnsOverHttps "
    "--disable-features=DnsOverHttpsUpgrade"
)

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
