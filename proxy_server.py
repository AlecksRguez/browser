"""
Proxy HTTP local con resolución DNS-over-HTTPS (DoH) via Cloudflare 1.1.1.1.

Cómo funciona:
  1. El navegador está configurado para usar este proxy en 127.0.0.1:8899.
  2. Para cada petición HTTPS, el navegador envía:
       CONNECT youtube.com:443 HTTP/1.1
     (el hostname, no la IP — el proxy hace la resolución).
  3. Este proxy resuelve "youtube.com" usando DoH a 1.1.1.1:443 (HTTPS),
     lo que evita el bloqueo DNS del firewall porque va por el puerto 443
     y no es una consulta DNS estándar.
  4. El proxy conecta a la IP obtenida y crea un túnel TCP bidireccional.

No requiere permisos de administrador ni cambios en el sistema.
"""

import http.client
import json
import logging
import select
import socket
import ssl
import threading
import time
from typing import Optional

PROXY_HOST = "127.0.0.1"
PROXY_PORT = 8899

# IP directa de Cloudflare — no necesita DNS para resolver el resolvedor
CLOUDFLARE_IP = "1.1.1.1"
DOH_PATH = "/dns-query"

BUFFER = 65536
TUNNEL_TIMEOUT = 90  # segundos

# Cache DNS: hostname -> (ip_str, expiry_timestamp)
_cache: dict[str, tuple[str, float]] = {}
_cache_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Resolución DoH
# ---------------------------------------------------------------------------

def _resolve_doh(hostname: str) -> Optional[str]:
    """
    Resuelve un hostname consultando Cloudflare DoH en 1.1.1.1:443.
    Conecta por IP para evitar depender del DNS del sistema.
    Incluye caché con TTL.
    """
    # Revisar caché
    with _cache_lock:
        entry = _cache.get(hostname)
        if entry and time.monotonic() < entry[1]:
            return entry[0]

    try:
        ctx = ssl.create_default_context()
        # Conecta directamente a 1.1.1.1 (sin DNS), con verificación TLS normal
        # (Cloudflare tiene cert válido para 1.1.1.1 como SAN)
        conn = http.client.HTTPSConnection(CLOUDFLARE_IP, context=ctx, timeout=5)
        conn.request(
            "GET",
            f"{DOH_PATH}?name={hostname}&type=A",
            headers={"Accept": "application/dns-json"},
        )
        resp = conn.getresponse()
        if resp.status == 200:
            data = json.loads(resp.read())
            for answer in data.get("Answer", []):
                if answer.get("type") == 1:  # tipo A = IPv4
                    ip = answer["data"]
                    ttl = max(int(answer.get("TTL", 300)), 30)
                    with _cache_lock:
                        _cache[hostname] = (ip, time.monotonic() + ttl)
                    conn.close()
                    return ip
        conn.close()
    except Exception as exc:
        logging.debug("DoH falló para %s: %s", hostname, exc)
    return None


def _resolve(host: str) -> Optional[str]:
    """Resuelve host: DoH primero, sistema como fallback."""
    # Si ya es una IP, devolverla directamente
    try:
        socket.inet_aton(host)
        return host
    except OSError:
        pass
    ip = _resolve_doh(host)
    if ip:
        return ip
    # Fallback al DNS del sistema (cubre casos donde no se bloquea)
    try:
        return socket.gethostbyname(host)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Túnel bidireccional
# ---------------------------------------------------------------------------

def _tunnel(a: socket.socket, b: socket.socket) -> None:
    """Reenvía datos en ambas direcciones entre dos sockets hasta que cierren."""
    a.setblocking(False)
    b.setblocking(False)
    try:
        while True:
            r, _, _ = select.select([a, b], [], [], TUNNEL_TIMEOUT)
            if not r:
                break
            for s in r:
                other = b if s is a else a
                try:
                    chunk = s.recv(BUFFER)
                    if not chunk:
                        return
                    other.sendall(chunk)
                except OSError:
                    return
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Manejo de conexiones
# ---------------------------------------------------------------------------

def _handle(client: socket.socket) -> None:
    """Procesa una conexión entrante del navegador."""
    remote: Optional[socket.socket] = None
    try:
        raw = client.recv(4096)
        if not raw:
            return

        first_line = raw.split(b"\r\n", 1)[0]
        parts = first_line.split(b" ")
        if len(parts) < 2:
            return

        method = parts[0].upper()

        if method == b"CONNECT":
            # Petición HTTPS: CONNECT hostname:port HTTP/1.1
            host_port = parts[1].decode("ascii", errors="replace")
            host, _, port_s = host_port.rpartition(":")
            port = int(port_s)

            ip = _resolve(host)
            if not ip:
                client.sendall(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
                return

            remote = socket.create_connection((ip, port), timeout=10)
            client.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            _tunnel(client, remote)

        else:
            # Petición HTTP plana
            from urllib.parse import urlparse
            url = parts[1].decode("ascii", errors="replace")
            parsed = urlparse(url)
            host = parsed.hostname or ""
            port = parsed.port or 80

            ip = _resolve(host)
            if not ip:
                client.sendall(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
                return

            remote = socket.create_connection((ip, port), timeout=10)
            remote.sendall(raw)
            _tunnel(client, remote)

    except Exception as exc:
        logging.debug("Error en proxy: %s", exc)
    finally:
        for s in (client, remote):
            if s:
                try:
                    s.close()
                except Exception:
                    pass


# ---------------------------------------------------------------------------
# Servidor proxy
# ---------------------------------------------------------------------------

class DoHProxyServer:
    """
    Servidor proxy HTTP local con resolución DNS-over-HTTPS.
    Se inicia como daemon thread; no bloquea la aplicación.
    """

    def __init__(self, host: str = PROXY_HOST, port: int = PROXY_PORT):
        self.host = host
        self.port = port
        self._sock: Optional[socket.socket] = None
        self._thread: Optional[threading.Thread] = None

    def start(self) -> bool:
        """Inicia el servidor. Devuelve True si arrancó correctamente."""
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._sock.bind((self.host, self.port))
            self._sock.listen(200)
            self._sock.settimeout(1.0)
            self._thread = threading.Thread(target=self._run, daemon=True, name="doh-proxy")
            self._thread.start()
            logging.info("Proxy DoH activo en %s:%d", self.host, self.port)
            return True
        except Exception as exc:
            logging.warning("No se pudo iniciar el proxy DoH: %s", exc)
            return False

    def stop(self) -> None:
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass

    def _run(self) -> None:
        while True:
            try:
                client, _ = self._sock.accept()
                threading.Thread(
                    target=_handle, args=(client,), daemon=True
                ).start()
            except socket.timeout:
                continue
            except Exception:
                break
