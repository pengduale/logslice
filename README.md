# logslice

A lightweight log filtering and tailing utility with regex support and structured output.

---

## Installation

```bash
pip install logslice
```

Or install from source:

```bash
git clone https://github.com/youruser/logslice.git && cd logslice && pip install .
```

---

## Usage

**Filter logs by pattern:**

```bash
logslice filter app.log --pattern "ERROR|WARN"
```

**Tail a live log file with regex filtering:**

```bash
logslice tail /var/log/syslog --pattern "timeout" --lines 50
```

**Output structured JSON:**

```bash
logslice filter app.log --pattern "ERROR" --format json
```

**Filter between a date range:**

```bash
logslice filter app.log --pattern "ERROR" --since "2024-01-01" --until "2024-01-31"
```

**Python API:**

```python
from logslice import LogSlicer

slicer = LogSlicer("app.log")
for entry in slicer.filter(pattern=r"ERROR\s+\d+"):
    print(entry)
```

---

## Options

| Flag | Description |
|------|-------------|
| `--pattern` | Regex pattern to match against log lines |
| `--lines` | Number of lines to tail (default: 100) |
| `--format` | Output format: `plain` or `json` (default: `plain`) |
| `--ignore-case` | Case-insensitive matching |
| `--since` | Only show log entries on or after this date (e.g. `2024-01-01`) |
| `--until` | Only show log entries on or before this date (e.g. `2024-01-31`) |

---

## License

This project is licensed under the [MIT License](LICENSE).
