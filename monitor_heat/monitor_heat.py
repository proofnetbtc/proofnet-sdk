#!/usr/bin/env python3
"""
Windows 11 System Heat Monitor v2
Logs CPU, memory, disk, temperature, and top processes.
Zero external dependencies — uses only stdlib + WMI/PowerShell queries.
"""

import ctypes
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path

LOG_FILE = Path.home() / "system_monitor.log"

# Processes to exclude from "top consumers" (noise, not real load)
EXCLUDED_PROCS = {"system idle process", "system", "idle", "memory compression"}


def get_cpu_percent(interval=1):
    """Get overall CPU usage % by sampling twice with a delay (no psutil)."""
    def _read_idle_and_total():
        # Use PowerShell to read Win32_PerfRawData_PerfOS_Processor (_Total)
        cmd = (
            'powershell -NoProfile -Command "'
            'Get-CimInstance Win32_PerfRawData_PerfOS_Processor '
            "-Filter \\\"Name='_Total'\\\" | "
            'Select-Object -Property PercentIdleTime,TimeStamp_Sys100NS | '
            'ForEach-Object { $_.PercentIdleTime; $_.TimeStamp_Sys100NS }"'
        )
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        lines = [l.strip() for l in result.stdout.strip().split('\n') if l.strip()]
        if len(lines) >= 2:
            return int(lines[0]), int(lines[1])
        return None, None

    idle1, ts1 = _read_idle_and_total()
    if idle1 is None:
        return None
    time.sleep(interval)
    idle2, ts2 = _read_idle_and_total()
    if idle2 is None or ts2 == ts1:
        return None

    idle_delta = idle2 - idle1
    total_delta = ts2 - ts1
    usage = (1.0 - idle_delta / total_delta) * 100.0
    return round(max(0.0, min(100.0, usage)), 1)


def get_memory():
    """Get memory usage via kernel32 GlobalMemoryStatusEx (no psutil)."""
    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    mem = MEMORYSTATUSEX()
    mem.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem))

    total_gb = mem.ullTotalPhys / (1024 ** 3)
    used_gb = (mem.ullTotalPhys - mem.ullAvailPhys) / (1024 ** 3)
    percent = mem.dwMemoryLoad
    return percent, round(used_gb, 1), round(total_gb, 1)


def get_disk(drive="C:"):
    """Get disk usage via os.statvfs / shutil fallback (no psutil)."""
    try:
        total, used, free = 0, 0, 0
        # Windows: use ctypes GetDiskFreeSpaceExW
        free_bytes = ctypes.c_ulonglong(0)
        total_bytes = ctypes.c_ulonglong(0)
        free_avail = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(
            drive + "\\",
            ctypes.byref(free_avail),
            ctypes.byref(total_bytes),
            ctypes.byref(free_bytes),
        )
        total = total_bytes.value
        free = free_avail.value
        used = total - free
        if total > 0:
            return round(used / total * 100, 1)
    except Exception:
        pass
    return None


def get_cpu_temp():
    """Get CPU temperature using multiple WMI methods."""
    # Method 1: MSAcpi_ThermalZoneTemperature (requires admin)
    try:
        cmd = (
            'powershell -NoProfile -Command "'
            "Get-CimInstance -Namespace root/WMI "
            "-ClassName MSAcpi_ThermalZoneTemperature "
            '-ErrorAction Stop | Select-Object -First 1 -ExpandProperty CurrentTemperature"'
        )
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        val = result.stdout.strip()
        if val and result.returncode == 0:
            temp_celsius = (float(val) - 2732) / 10
            if 0 < temp_celsius < 150:
                return round(temp_celsius, 1)
    except Exception:
        pass

    # Method 2: Win32_TemperatureProbe
    try:
        cmd = (
            'powershell -NoProfile -Command "'
            "Get-CimInstance Win32_TemperatureProbe "
            '-ErrorAction Stop | Select-Object -First 1 -ExpandProperty CurrentReading"'
        )
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        val = result.stdout.strip()
        if val and result.returncode == 0:
            temp = float(val)
            if 0 < temp < 150:
                return round(temp, 1)
    except Exception:
        pass

    return None


def get_top_processes(n=5):
    """Get top N processes by CPU time delta (two samples, no psutil).

    Samples process CPU times twice with a short gap, then ranks by
    which processes consumed the most CPU in that window.
    """
    def _snapshot():
        cmd = (
            'powershell -NoProfile -Command "'
            "Get-Process | Where-Object { $_.ProcessName -ne 'Idle' } | "
            "Select-Object Id,ProcessName,"
            "@{N='CPU_ms';E={[long]$_.TotalProcessorTime.TotalMilliseconds}},"
            "@{N='Mem_MB';E={[math]::Round($_.WorkingSet64/1MB,1)}} | "
            'ConvertTo-Csv -NoTypeInformation"'
        )
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        procs = {}
        for line in result.stdout.strip().split('\n')[1:]:  # skip header
            line = line.strip().strip('"')
            if not line:
                continue
            parts = [p.strip('"') for p in line.split('","')]
            if len(parts) >= 4:
                try:
                    pid = int(parts[0])
                    name = parts[1]
                    cpu_ms = float(parts[2]) if parts[2] else 0
                    mem_mb = float(parts[3]) if parts[3] else 0
                    if name.lower() not in EXCLUDED_PROCS:
                        procs[pid] = {"name": name, "cpu_ms": cpu_ms, "mem_mb": mem_mb}
                except (ValueError, IndexError):
                    continue
        return procs

    snap1 = _snapshot()
    time.sleep(1)
    snap2 = _snapshot()

    # Get total physical memory for percentage calculation
    _, _, total_gb = get_memory()
    total_mb = total_gb * 1024

    deltas = []
    for pid, info2 in snap2.items():
        if pid in snap1:
            cpu_delta = info2["cpu_ms"] - snap1[pid]["cpu_ms"]
            if cpu_delta > 0:
                deltas.append({
                    "name": info2["name"],
                    "cpu_delta_ms": cpu_delta,
                    "mem_mb": info2["mem_mb"],
                    "mem_pct": round(info2["mem_mb"] / total_mb * 100, 1) if total_mb > 0 else 0,
                })

    deltas.sort(key=lambda x: x["cpu_delta_ms"], reverse=True)
    return deltas[:n]


def log_system_state():
    """Log current system state."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cpu_pct = get_cpu_percent(interval=1)
    mem_pct, mem_used, mem_total = get_memory()
    disk_pct = get_disk("C:")
    temp = get_cpu_temp()

    log_entry = f"\n{'='*70}\n"
    log_entry += f"Timestamp: {timestamp}\n"
    log_entry += f"CPU Usage: {cpu_pct}%\n" if cpu_pct is not None else "CPU Usage: N/A\n"
    log_entry += f"Memory: {mem_pct}% ({mem_used}GB / {mem_total}GB)\n"
    if disk_pct is not None:
        log_entry += f"Disk: {disk_pct}% full\n"
    if temp is not None:
        log_entry += f"CPU Temperature: {temp}C\n"
    else:
        log_entry += "CPU Temperature: N/A (run as admin for WMI access)\n"

    log_entry += f"\nTop 5 CPU-consuming processes:\n"
    log_entry += f"{'-'*70}\n"

    top_procs = get_top_processes(5)
    if top_procs:
        for proc in top_procs:
            log_entry += (
                f"  {proc['name']:30} | "
                f"CPU: {proc['cpu_delta_ms']:7.0f}ms | "
                f"RAM: {proc['mem_mb']:8.1f}MB ({proc['mem_pct']}%)\n"
            )
    else:
        log_entry += "  (No processes using significant CPU)\n"

    print(log_entry)

    with open(LOG_FILE, 'a') as f:
        f.write(log_entry)


def main():
    print(f"System Heat Monitor v2 (no external dependencies)")
    print(f"Logging to: {LOG_FILE}")
    print("Press Ctrl+C to stop.\n")

    if LOG_FILE.exists():
        with open(LOG_FILE, 'w') as f:
            f.write(f"System Monitor Log - Started {datetime.now()}\n")

    interval = 5  # seconds between samples

    try:
        while True:
            log_system_state()
            time.sleep(interval)
    except KeyboardInterrupt:
        print(f"\n\nMonitoring stopped. Log saved to: {LOG_FILE}")


if __name__ == "__main__":
    main()
