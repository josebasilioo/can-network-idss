#!/usr/bin/env python3

import csv
import datetime as dt
import re
from pathlib import Path
from typing import Optional, Tuple

# Patterns:
# A) epoch + interface + id + data (e.g., coleta.log)
PATTERN_A = re.compile(
    r"^(?P<epoch>\d+\.\d+)\s+(?P<iface>\S+)\s+(?P<canid>0x[0-9A-Fa-f]+)\s*(?P<data>(?:[0-9A-Fa-f]{2}(?:\s+|$))*)$"
)

# B) human ts + ID= + optional DATA= (e.g., spoofing, fuzzy, impersonation, freestate)
PATTERN_B = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+ID=(?P<id>\S+)(?:\s+DATA=(?P<data>(?:[0-9A-Fa-f]{2}(?:\s+|$))*))?$"
)

# C) human ts + epoch + CH= + ID= + DATA= (e.g., variant with both ts and epoch)
PATTERN_C = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+(?P<epoch>\d+\.\d+)\s+CH=(?P<iface>\S+)\s+ID=(?P<id>\S+)\s+DATA=(?P<data>(?:[0-9A-Fa-f]{2}(?:\s+|$))*)$"
)

# D) human ts + 'Created a socket' or similar lines to ignore
PATTERN_D = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+Created a socket$"
)


def format_ts_from_epoch(epoch_str: str) -> str:
    epoch = float(epoch_str)
    # Use local time per user's earlier expectation
    return dt.datetime.fromtimestamp(epoch).strftime("%Y-%m-%d %H:%M:%S")


def normalize_data_bytes(data: Optional[str]) -> str:
    if not data:
        return ""
    # Collapse whitespace and uppercase pairs
    parts = re.findall(r"[0-9A-Fa-f]{2}", data)
    return " ".join(p.upper() for p in parts)


def parse_line(line: str) -> Optional[Tuple[str, str, str, str]]:
    s = line.strip()
    if not s:
        return None

    # Ignore obvious non-data lines
    if s == "Created a socket" or s.endswith("Created a socket"):
        return None

    m = PATTERN_C.match(s)
    if m:
        ts = m.group("ts")
        iface = m.group("iface")
        canid = m.group("id")
        data = normalize_data_bytes(m.group("data"))
        return ts, iface, canid, data

    m = PATTERN_B.match(s)
    if m:
        ts = m.group("ts")
        canid = m.group("id")
        # Skip lines like ID=Created a socket
        if not canid.lower().startswith("0x"):
            return None
        data = normalize_data_bytes(m.group("data"))
        return ts, "", canid, data

    m = PATTERN_A.match(s)
    if m:
        ts = format_ts_from_epoch(m.group("epoch"))
        iface = m.group("iface")
        canid = m.group("canid")
        data = normalize_data_bytes(m.group("data"))
        return ts, iface, canid, data

    # Not recognized
    return None


def infer_label(file_name: str) -> str:
    if file_name == "coleta.log":
        return "Benign"
    stem = file_name
    if "." in stem:
        stem = stem.rsplit(".", 1)[0]
    # take prefix before first underscore
    label = stem.split("_", 1)[0]
    return label


def convert_file(log_path: Path, csv_path: Path) -> int:
    rows = 0
    label = infer_label(log_path.name)
    with log_path.open("r", encoding="utf-8", errors="replace") as fin, csv_path.open(
        "w", newline="", encoding="utf-8"
    ) as fout:
        writer = csv.writer(fout)
        writer.writerow(["timestamp", "interface", "can_id", "data", "label"])
        for line in fin:
            parsed = parse_line(line)
            if parsed is None:
                continue
            ts, iface, canid, data = parsed
            iface = iface or "can0"
            writer.writerow([ts, iface, canid, data, label])
            rows += 1
    return rows


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    log_files = sorted(base_dir.glob("*.log"))
    if not log_files:
        print("Nenhum arquivo .log encontrado.")
        return

    total_rows = 0
    for logf in log_files:
        csvf = logf.with_suffix(".csv")
        rows = convert_file(logf, csvf)
        total_rows += rows
        print(f"Convertido: {logf.name} -> {csvf.name} ({rows} linhas)")

    print(f"Conversão concluída. Linhas totais: {total_rows}")


if __name__ == "__main__":
    main()
