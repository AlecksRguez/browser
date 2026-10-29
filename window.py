"""
Ventana principal de CloudBrowser con soporte de pestañas múltiples.
"""
import sys

from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QToolBar, QLineEdit,
    QPushButton, QAction, QWidget, QVBoxLayout,
    QLabel, QSizePolicy, QShortcut, QMessageBox,
    QProgressBar, QHBoxLayout,
)
from PyQt5.QtWebEngineWidgets import (
    QWebEngineView, QWebEnginePage, QWebEngineProfile, QWebEngineSettings,
)
from PyQt5.QtCore import QUrl, Qt, QSize
from PyQt5.QtGui import QKeySequence, QFont, QIcon

from interceptor import AdBlockInterceptor

HOME_URL = "https://www.google.com"
DEFAULT_ZOOM = 1.0


# ---------------------------------------------------------------------------
# Pestaña individual
# ---------------------------------------------------------------------------

class BrowserTab(QWidget):
    """Widget de una sola pestaña: contiene el QWebEngineView."""

    def __init__(self, profile: QWebEngineProfile, parent=None):
        super().__init__(parent)
        self.webview = QWebEngineView()
        page = QWebEnginePage(profile, self.webview)
        self.webview.setPage(page)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.webview)


# ---------------------------------------------------------------------------
# Ventana principal
# ---------------------------------------------------------------------------

class BrowserWindow(QMainWindow):
    """Ventana principal del navegador con barra de pestañas y toolbar."""

    def __init__(self, profile: QWebEngineProfile = None,
                 interceptor: AdBlockInterceptor = None,
                 private: bool = False):
        super().__init__()
        title = "CloudBrowser — Navegación Privada 🕵️" if private else "CloudBrowser"
        self.setWindowTitle(title)
        self.resize(1366, 800)

        # Perfil de navegación con interceptor de anuncios
        if profile is None:
            self.profile = QWebEngineProfile.defaultProfile()
            self.interceptor = AdBlockInterceptor()
        else:
            self.profile = profile
            self.interceptor = interceptor
        self.profile.setUrlRequestInterceptor(self.interceptor)

        # Configuración del motor web
        s = self.profile.settings()
        s.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        s.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        s.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        s.setAttribute(QWebEngineSettings.ScrollAnimatorEnabled, True)
        s.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, False)
        s.setAttribute(QWebEngineSettings.XSSAuditingEnabled, True)
        s.setAttribute(QWebEngineSettings.HyperlinkAuditingEnabled, False)

        self._build_toolbar()
        self._build_tabs()
        self._build_menu()
        self._build_shortcuts()

        # Abrir pestaña inicial
        self.add_tab(HOME_URL)

    # ------------------------------------------------------------------
    # Construcción de la UI
    # ------------------------------------------------------------------

    def _build_toolbar(self):
        self.toolbar = QToolBar("Navegación")
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QSize(16, 16))
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.addToolBar(self.toolbar)

        def btn(text, tip, slot):
            a = QAction(text, self)
            a.setToolTip(tip)
            a.triggered.connect(slot)
            self.toolbar.addAction(a)
            return a

        self.act_back    = btn("◀", "Atrás (Alt+←)",     self._go_back)
        self.act_forward = btn("▶", "Adelante (Alt+→)",  self._go_forward)
        self.act_reload  = btn("↺", "Recargar (F5)",      self._reload)
        self.act_stop    = btn("✕", "Detener (Esc)",      self._stop)
        btn("⌂", "Inicio", lambda: self._navigate(HOME_URL))

        self.toolbar.addSeparator()

        # Barra de dirección
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Escribe una URL o busca en Google…")
        self.url_bar.returnPressed.connect(self._navigate_from_bar)
        self.url_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.url_bar.setMinimumHeight(30)
        self.toolbar.addWidget(self.url_bar)

        self.toolbar.addSeparator()

        # Indicador DNS
        dns_label = QLabel(" 🛡️ 1.1.1.1 ")
        dns_label.setToolTip(
            "DNS sobre HTTPS (DoH) activo\n"
            "Servidor: Cloudflare 1.1.1.1\n"
            "Endpoint: https://cloudflare-dns.com/dns-query"
        )
        dns_label.setStyleSheet("color: #a6e3a1; font-size: 12px; font-weight: bold;")
        self.toolbar.addWidget(dns_label)

        # Barra de progreso (debajo del toolbar)
        self.progress = QProgressBar()
        self.progress.setMaximumHeight(3)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet(
            "QProgressBar { background: transparent; border: none; }"
            "QProgressBar::chunk { background-color: #89b4fa; }"
        )
        self.progress.setVisible(False)
        # Se añade al layout general al construir las pestañas

    def _build_tabs(self):
        # Contenedor central
        central = QWidget()
        self.setCentralWidget(central)
        vbox = QVBoxLayout(central)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)
        vbox.addWidget(self.progress)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self._close_tab)
        self.tabs.currentChanged.connect(self._tab_changed)
        vbox.addWidget(self.tabs)

        # Botón "+" para nueva pestaña
        new_btn = QPushButton("+")
        new_btn.setFixedSize(28, 28)
        new_btn.setToolTip("Nueva pestaña (Ctrl+T)")
        new_btn.setStyleSheet(
            "QPushButton { background:#313244; border:none; border-radius:4px;"
            " color:#cdd6f4; font-size:16px; }"
            "QPushButton:hover { background:#45475a; }"
        )
        new_btn.clicked.connect(lambda: self.add_tab())
        self.tabs.setCornerWidget(new_btn, Qt.TopRightCorner)

        # Barra de estado
        self.status_bar = self.statusBar()
        self.status_bar.setFixedHeight(22)

    def _build_menu(self):
        mb = self.menuBar()

        # Archivo
        fm = mb.addMenu("Archivo")
        fm.addAction("Nueva pestaña",         lambda: self.add_tab(),      QKeySequence("Ctrl+T"))
        fm.addAction("Nueva ventana privada",  self._new_private_window)
        fm.addAction("Cerrar pestaña",         self._close_current,         QKeySequence("Ctrl+W"))
        fm.addSeparator()
        fm.addAction("Salir",                  self.close,                  QKeySequence("Ctrl+Q"))

        # Ver
        vm = mb.addMenu("Ver")
        vm.addAction("Recargar",               self._reload,                QKeySequence("F5"))
        vm.addAction("Pantalla completa",       self._fullscreen,            QKeySequence("F11"))
        vm.addSeparator()
        vm.addAction("Zoom +",                 lambda: self._zoom(+0.1),    QKeySequence("Ctrl++"))
        vm.addAction("Zoom −",                 lambda: self._zoom(-0.1),    QKeySequence("Ctrl+-"))
        vm.addAction("Zoom normal (100%)",     lambda: self._zoom(0),       QKeySequence("Ctrl+0"))

        # Herramientas
        tm = mb.addMenu("Herramientas")
        tm.addAction("Estadísticas de sesión",          self._show_stats)
        tm.addAction("Activar / Desactivar bloqueador", self._toggle_adblock)
        tm.addSeparator()
        tm.addAction("Configurar DNS 1.1.1.1 en sistema",   self._set_system_dns)
        tm.addAction("Restaurar DNS del sistema (DHCP)",    self._restore_system_dns)

        # Ayuda
        hm = mb.addMenu("Ayuda")
        hm.addAction("Acerca de CloudBrowser", self._about)

    def _build_shortcuts(self):
        def sc(key, slot):
            QShortcut(QKeySequence(key), self).activated.connect(slot)

        sc("Ctrl+T",        lambda: self.add_tab())
        sc("Ctrl+W",        self._close_current)
        sc("Ctrl+L",        lambda: (self.url_bar.setFocus(), self.url_bar.selectAll()))
        sc("F5",            self._reload)
        sc("Ctrl+R",        self._reload)
        sc("Escape",        self._stop)
        sc("F11",           self._fullscreen)
        sc("Alt+Left",      self._go_back)
        sc("Alt+Right",     self._go_forward)
        sc("Ctrl++",        lambda: self._zoom(+0.1))
        sc("Ctrl+=",        lambda: self._zoom(+0.1))
        sc("Ctrl+-",        lambda: self._zoom(-0.1))
        sc("Ctrl+0",        lambda: self._zoom(0))
        sc("Ctrl+1",        lambda: self.tabs.setCurrentIndex(0))
        sc("Ctrl+2",        lambda: self.tabs.setCurrentIndex(1))
        sc("Ctrl+3",        lambda: self.tabs.setCurrentIndex(2))
        sc("Ctrl+4",        lambda: self.tabs.setCurrentIndex(3))
        sc("Ctrl+5",        lambda: self.tabs.setCurrentIndex(4))
        sc("Ctrl+Tab",      self._next_tab)
        sc("Ctrl+Shift+Tab", self._prev_tab)

    # ------------------------------------------------------------------
    # Gestión de pestañas
    # ------------------------------------------------------------------

    def add_tab(self, url: str = HOME_URL) -> BrowserTab:
        tab = BrowserTab(self.profile)
        wv = tab.webview

        wv.urlChanged.connect(lambda u, t=tab: self._on_url_changed(u, t))
        wv.titleChanged.connect(lambda title, t=tab: self._on_title_changed(title, t))
        wv.loadStarted.connect(self._on_load_started)
        wv.loadProgress.connect(self._on_load_progress)
        wv.loadFinished.connect(self._on_load_finished)

        # Manejar solicitudes de nueva ventana como nueva pestaña
        wv.page().windowCloseRequested.connect(
            lambda t=tab: self._close_tab(self.tabs.indexOf(t))
        )

        idx = self.tabs.addTab(tab, "Nueva pestaña")
        self.tabs.setCurrentIndex(idx)
        wv.load(QUrl(url))
        return tab

    def _close_tab(self, idx: int):
        if self.tabs.count() > 1:
            self.tabs.removeTab(idx)
        else:
            self.close()

    def _close_current(self):
        self._close_tab(self.tabs.currentIndex())

    def _next_tab(self):
        n = self.tabs.count()
        self.tabs.setCurrentIndex((self.tabs.currentIndex() + 1) % n)

    def _prev_tab(self):
        n = self.tabs.count()
        self.tabs.setCurrentIndex((self.tabs.currentIndex() - 1) % n)

    def _tab_changed(self, idx: int):
        tab = self.tabs.widget(idx)
        if tab:
            url_str = tab.webview.url().toString()
            self.url_bar.setText(url_str if url_str != "about:blank" else "")
            t = tab.webview.title()
            self.setWindowTitle(f"{t} — CloudBrowser" if t else "CloudBrowser")

    # ------------------------------------------------------------------
    # Señales del WebView
    # ------------------------------------------------------------------

    def _on_url_changed(self, url: QUrl, tab: BrowserTab):
        if tab is self.tabs.currentWidget():
            s = url.toString()
            self.url_bar.setText(s if s != "about:blank" else "")

    def _on_title_changed(self, title: str, tab: BrowserTab):
        idx = self.tabs.indexOf(tab)
        if idx >= 0:
            short = (title[:28] + "…") if len(title) > 28 else title
            self.tabs.setTabText(idx, short or "Nueva pestaña")
        if tab is self.tabs.currentWidget():
            self.setWindowTitle(f"{title} — CloudBrowser" if title else "CloudBrowser")

    def _on_load_started(self):
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.status_bar.showMessage("Cargando…")

    def _on_load_progress(self, pct: int):
        self.progress.setValue(pct)

    def _on_load_finished(self, ok: bool):
        self.progress.setVisible(False)
        blocked = self.interceptor.blocked_count
        icon = "✓" if ok else "⚠"
        self.status_bar.showMessage(
            f"{icon} Listo  ·  🛡️ {blocked} anuncios bloqueados  ·  DNS: Cloudflare 1.1.1.1"
        )

    # ------------------------------------------------------------------
    # Navegación
    # ------------------------------------------------------------------

    def _current_view(self):
        tab = self.tabs.currentWidget()
        return tab.webview if tab else None

    def _go_back(self):
        v = self._current_view()
        if v:
            v.back()

    def _go_forward(self):
        v = self._current_view()
        if v:
            v.forward()

    def _reload(self):
        v = self._current_view()
        if v:
            v.reload()

    def _stop(self):
        v = self._current_view()
        if v:
            v.stop()

    def _navigate(self, url: str):
        v = self._current_view()
        if v:
            v.load(QUrl(url))

    def _navigate_from_bar(self):
        text = self.url_bar.text().strip()
        if not text:
            return
        if text.startswith(("http://", "https://", "file://", "ftp://", "about:")):
            url = text
        elif "." in text and " " not in text and len(text) > 3:
            url = "https://" + text
        else:
            q = text.replace(" ", "+")
            url = f"https://www.google.com/search?q={q}"
        self._navigate(url)

    # ------------------------------------------------------------------
    # Zoom y pantalla completa
    # ------------------------------------------------------------------

    def _zoom(self, delta: float):
        v = self._current_view()
        if not v:
            return
        if delta == 0:
            v.setZoomFactor(DEFAULT_ZOOM)
        else:
            v.setZoomFactor(max(0.25, min(5.0, v.zoomFactor() + delta)))

    def _fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    # ------------------------------------------------------------------
    # Ventana privada (perfil separado sin cookies persistentes)
    # ------------------------------------------------------------------

    def _new_private_window(self):
        private_profile = QWebEngineProfile(self)   # perfil sin cookies persistentes
        win = BrowserWindow(profile=private_profile,
                            interceptor=self.interceptor,
                            private=True)
        win.show()

    # ------------------------------------------------------------------
    # DNS del sistema
    # ------------------------------------------------------------------

    def _set_system_dns(self):
        if sys.platform != "win32":
            QMessageBox.information(
                self, "Solo Windows",
                "La configuración del DNS del sistema solo está disponible en Windows.\n\n"
                "El navegador ya usa DNS sobre HTTPS (DoH) con Cloudflare 1.1.1.1 de forma automática.",
            )
            return
        from dns_setup import set_windows_dns_elevated
        set_windows_dns_elevated(self)

    def _restore_system_dns(self):
        if sys.platform != "win32":
            QMessageBox.information(self, "Solo Windows",
                                    "Esta función solo está disponible en Windows.")
            return
        from dns_setup import restore_windows_dns
        restore_windows_dns(self)

    # ------------------------------------------------------------------
    # Estadísticas y ajustes
    # ------------------------------------------------------------------

    def _toggle_adblock(self):
        self.interceptor.enabled = not self.interceptor.enabled
        state = "ACTIVADO ✓" if self.interceptor.enabled else "DESACTIVADO"
        self.status_bar.showMessage(f"Bloqueador de anuncios: {state}")

    def _show_stats(self):
        v = self._current_view()
        zoom_pct = int((v.zoomFactor() if v else DEFAULT_ZOOM) * 100)
        QMessageBox.information(
            self, "Estadísticas de sesión — CloudBrowser",
            f"🛡️  Anuncios bloqueados:      {self.interceptor.blocked_count}\n"
            f"📋  Dominios en lista negra:  {len(self.interceptor.blocked_domains)}\n"
            f"🔒  Bloqueador activo:        {'Sí' if self.interceptor.enabled else 'No'}\n"
            f"🔍  Zoom actual:              {zoom_pct}%\n\n"
            f"🌐  DNS activo:  Cloudflare 1.1.1.1 (DoH)\n"
            f"🔗  Endpoint:    https://cloudflare-dns.com/dns-query\n"
            f"🏷️   Protocolo:  DNS sobre HTTPS (RFC 8484)",
        )

    def _about(self):
        QMessageBox.about(
            self, "Acerca de CloudBrowser",
            "<h3>CloudBrowser v1.0</h3>"
            "<p>Navegador de privacidad potenciado por <b>Cloudflare 1.1.1.1</b>.</p>"
            "<ul>"
            "<li>🛡️ Bloqueo de anuncios integrado</li>"
            "<li>🔒 DNS sobre HTTPS (DoH) con Cloudflare</li>"
            "<li>⚡ Motor Chromium vía QtWebEngine</li>"
            "<li>🎨 Interfaz oscura moderna</li>"
            "</ul>"
            "<p><small>Basado en PyQt5 + QtWebEngine</small></p>",
        )

