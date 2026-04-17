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

## Log Fields

- `Timestamp`: local time when the log entry was started.
- `CPU Usage`: overall CPU utilization percentage sampled from Windows counters.
- `Memory`: physical memory utilization percentage plus used and total memory.
- `Disk`: percentage of the `C:` drive currently in use.
- `Temperature`: available Windows sensor reading and the sensor source, when
  Windows exposes one.
- `Top CPU-consuming processes`: process names ranked by CPU time consumed
  during the sample window, with working-set memory shown for each process.

## Safety Notes

- PowerShell/WMI calls are bounded with timeouts so a stalled Windows query does
  not stop the monitor forever.
- The script uses only Python standard library modules.
- On non-Windows systems, Windows-specific probes return `N/A` instead of
  crashing.
