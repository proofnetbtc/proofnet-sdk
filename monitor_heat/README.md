# Windows System Heat Monitor

`monitor_heat.py` is a small Windows 11 diagnostic utility for spotting process
load, memory pressure, disk fullness, and available Windows temperature sensor
readings.

It is intended as a troubleshooting helper, not as a production telemetry agent.
Windows does not reliably expose CPU package or core temperature through the
standard WMI classes used here, so temperature lines include the sensor source
when one is available.

## Run

```powershell
python .\monitor_heat.py
```

Logs are written to timestamped files under:

```text
%USERPROFILE%\proofnet-monitor-logs\
```

Press `Ctrl+C` to stop the monitor.

## What It Records

- Overall CPU usage
- Memory usage
- `C:` disk fullness
- Available Windows temperature sensor reading and source
- Top CPU-consuming processes during the sample window

## Safety Notes

- PowerShell/WMI calls are bounded with timeouts so a stalled Windows query does
  not stop the monitor forever.
- The script uses only Python standard library modules.
- On non-Windows systems, Windows-specific probes return `N/A` instead of
  crashing.
