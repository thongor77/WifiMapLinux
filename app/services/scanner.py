import re
import subprocess
from dataclasses import dataclass


@dataclass
class WifiNetwork:
    ssid: str
    bssid: str
    signal_dbm: int
    channel: int
    frequency_mhz: int


def scan_wifi() -> list[WifiNetwork]:
    """Scan with nmcli first, fall back to iw."""
    result = _scan_nmcli()
    if result is None:
        result = _scan_iw()
    return result or []


def _pct_to_dbm(pct: int) -> int:
    """Convert nmcli SIGNAL quality (0-100 %) to approximate dBm."""
    return int(pct / 2) - 100


def _scan_nmcli() -> list[WifiNetwork] | None:
    try:
        out = subprocess.check_output(
            ["nmcli", "-t", "-f", "SSID,BSSID,SIGNAL,CHAN,FREQ", "dev", "wifi"],
            timeout=15, text=True, stderr=subprocess.DEVNULL,
        )
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None

    networks = []
    for line in out.strip().splitlines():
        # nmcli -t escapes field separators inside values with backslash
        parts = re.split(r"(?<!\\):", line)
        if len(parts) < 5:
            continue
        ssid = parts[0].replace("\\:", ":")
        bssid = parts[1].replace("\\:", ":")
        try:
            signal_pct = int(parts[2])
            channel = int(parts[3])
            freq = int(re.sub(r"[^\d]", "", parts[4]))
        except ValueError:
            continue
        networks.append(WifiNetwork(ssid=ssid, bssid=bssid,
                                    signal_dbm=_pct_to_dbm(signal_pct),
                                    channel=channel, frequency_mhz=freq))
    return networks or None


def _get_wifi_iface() -> str | None:
    try:
        out = subprocess.check_output(["iw", "dev"], text=True, stderr=subprocess.DEVNULL)
        for line in out.splitlines():
            if line.strip().startswith("Interface"):
                return line.strip().split()[1]
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass
    return None


def _scan_iw() -> list[WifiNetwork] | None:
    iface = _get_wifi_iface()
    if not iface:
        return None
    try:
        out = subprocess.check_output(
            ["iw", "dev", iface, "scan"],
            timeout=15, text=True, stderr=subprocess.DEVNULL,
        )
    except (FileNotFoundError, subprocess.CalledProcessError,
            subprocess.TimeoutExpired, PermissionError):
        return None

    networks: list[WifiNetwork] = []
    cur: dict = {}

    for line in out.splitlines():
        line = line.strip()
        if line.startswith("BSS "):
            if cur:
                n = _bss_to_network(cur)
                if n:
                    networks.append(n)
            cur = {"bssid": line.split()[1].split("(")[0]}
        elif "SSID:" in line:
            cur["ssid"] = line.split("SSID:", 1)[1].strip()
        elif "signal:" in line:
            try:
                cur["signal"] = int(float(line.split("signal:")[1].split("dBm")[0]))
            except ValueError:
                pass
        elif "DS Parameter set: channel" in line:
            try:
                cur["channel"] = int(line.rsplit("channel", 1)[1].strip())
            except (ValueError, IndexError):
                pass
        elif line.startswith("freq:"):
            try:
                cur["freq"] = int(line.split(":")[1].strip())
            except ValueError:
                pass

    if cur:
        n = _bss_to_network(cur)
        if n:
            networks.append(n)

    return networks or None


def _bss_to_network(d: dict) -> WifiNetwork | None:
    try:
        return WifiNetwork(
            ssid=d.get("ssid", "<caché>"),
            bssid=d.get("bssid", ""),
            signal_dbm=d.get("signal", -100),
            channel=d.get("channel", 0),
            frequency_mhz=d.get("freq", 0),
        )
    except Exception:
        return None
