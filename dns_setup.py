"""
Utilidades para configurar DNS usando Cloudflare 1.1.1.1.

El navegador usa DNS sobre HTTPS (DoH) por defecto vía flags de Chromium,
configurados en main.py antes de iniciar QApplication.

Este módulo provee además la opción de configurar el DNS del sistema
en Windows para mayor cobertura.
"""
import os
import sys
import subprocess
import ctypes


def is_admin() -> bool:
    """Comprueba si el proceso tiene privilegios de administrador (Windows)."""
    if sys.platform != "win32":
        return False
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def set_windows_dns_elevated(parent=None):
    """
    Configura el DNS del sistema Windows a Cloudflare 1.1.1.1 / 1.0.0.1.
    Solicita elevación de privilegios via UAC si es necesario.
    Muestra diálogos de confirmación y resultado al usuario.
    """
    from PyQt5.QtWidgets import QMessageBox

    reply = QMessageBox.question(
        parent,
        "Configurar DNS del sistema",
        "¿Deseas configurar el DNS de todas las interfaces de red a Cloudflare 1.1.1.1?\n\n"
        "• DNS primario:   1.1.1.1  (Cloudflare – rápido y privado)\n"
        "• DNS secundario: 1.0.0.1  (Cloudflare – respaldo)\n\n"
        "Esto puede ayudar a evitar bloqueos de red basados en DNS.\n"
        "Se requieren permisos de administrador.",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.Yes,
    )

    if reply != QMessageBox.Yes:
        return

    # Script PowerShell para configurar DNS en todas las interfaces activas
    ps_script = r"""
$ErrorActionPreference = 'Stop'
$dns = @('1.1.1.1', '1.0.0.1')
$changed = 0
Get-NetAdapter | Where-Object { $_.Status -eq 'Up' } | ForEach-Object {
    try {
        Set-DnsClientServerAddress -InterfaceIndex $_.ifIndex -ServerAddresses $dns
        $changed++
        Write-Output "OK: $($_.Name)"
    } catch {
        Write-Output "ERROR: $($_.Name) - $_"
    }
}
Write-Output "Interfaces configuradas: $changed"
"""

    try:
        # Guardar script en carpeta temporal
        tmp = os.environ.get("TEMP", "C:\\Windows\\Temp")
        script_path = os.path.join(tmp, "cloudbrowser_set_dns.ps1")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(ps_script)

        if is_admin():
            # Ya somos admin, ejecutar directamente
            result = subprocess.run(
                ["powershell.exe", "-ExecutionPolicy", "Bypass",
                 "-File", script_path],
                capture_output=True, text=True, timeout=15,
            )
            output = result.stdout.strip()
        else:
            # Solicitar elevación via UAC (ShellExecuteW con "runas")
            ret = ctypes.windll.shell32.ShellExecuteW(
                None, "runas",
                "powershell.exe",
                f'-ExecutionPolicy Bypass -File "{script_path}"',
                None, 1,
            )
            output = f"Proceso iniciado (código: {ret})"
            if ret <= 32:
                raise RuntimeError(f"ShellExecute falló con código {ret}")

        QMessageBox.information(
            parent, "DNS configurado",
            "DNS del sistema configurado correctamente.\n\n"
            f"• Primario:   1.1.1.1\n"
            f"• Secundario: 1.0.0.1\n\n"
            f"Detalle:\n{output}",
        )

    except subprocess.TimeoutExpired:
        QMessageBox.warning(parent, "Tiempo agotado",
                            "La operación tardó demasiado. Inténtalo manualmente.")
    except Exception as exc:
        QMessageBox.critical(
            parent, "Error al configurar DNS",
            f"No se pudo configurar el DNS del sistema.\n\nError: {exc}\n\n"
            "Puedes configurarlo manualmente en:\n"
            "Panel de control > Redes > Propiedades del adaptador > IPv4\n"
            "DNS preferido: 1.1.1.1\nDNS alternativo: 1.0.0.1",
        )


def restore_windows_dns(parent=None):
    """Restaura el DNS del sistema a DHCP automático."""
    from PyQt5.QtWidgets import QMessageBox

    reply = QMessageBox.question(
        parent,
        "Restaurar DNS",
        "¿Restaurar el DNS del sistema a obtención automática (DHCP)?",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No,
    )
    if reply != QMessageBox.Yes:
        return

    ps_script = r"""
Get-NetAdapter | Where-Object { $_.Status -eq 'Up' } | ForEach-Object {
    Set-DnsClientServerAddress -InterfaceIndex $_.ifIndex -ResetServerAddresses
    Write-Output "Restaurado: $($_.Name)"
}
"""
    try:
        tmp = os.environ.get("TEMP", "C:\\Windows\\Temp")
        script_path = os.path.join(tmp, "cloudbrowser_restore_dns.ps1")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(ps_script)

        if is_admin():
            subprocess.run(
                ["powershell.exe", "-ExecutionPolicy", "Bypass",
                 "-File", script_path],
                timeout=15,
            )
        else:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", "powershell.exe",
                f'-ExecutionPolicy Bypass -File "{script_path}"',
                None, 1,
            )

        QMessageBox.information(parent, "DNS restaurado",
                                "DNS del sistema restaurado a obtención automática.")
    except Exception as exc:
        QMessageBox.warning(parent, "Error", f"No se pudo restaurar el DNS: {exc}")
