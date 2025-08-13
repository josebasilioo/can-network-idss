#!/usr/bin/env python3

import csv
import datetime
from pathlib import Path
from typing import List, Optional


def convert_line_to_row(line: str) -> Optional[List[str]]:
    line = line.strip()
    if not line:
        return None

    parts = line.split()
    try:
        epoch_seconds = float(parts[0])
    except Exception:
        return None

    interface = parts[1] if len(parts) > 1 else ""
    can_identifier = parts[2] if len(parts) > 2 else ""
    payload_hex = " ".join(parts[3:]) if len(parts) > 3 else ""

    local_dt = datetime.datetime.fromtimestamp(epoch_seconds)
    ts_str = local_dt.strftime("%Y-%m-%d %H:%M:%S")

    return [ts_str, interface, can_identifier, payload_hex]


def convert_log_to_csv(input_path: Path, output_path: Path) -> None:
    with input_path.open("r", encoding="utf-8", errors="replace") as infile, output_path.open(
        "w", newline="", encoding="utf-8"
    ) as outfile:
        writer = csv.writer(outfile)
        writer.writerow(["timestamp", "interface", "can_id", "data"])

        for line in infile:
            row = convert_line_to_row(line)
            if row is not None:
                writer.writerow(row)


if __name__ == "__main__":
    project_dir = Path(__file__).resolve().parent
    input_file = project_dir / "coleta.log"
    output_file = project_dir / "coleta.csv"

    convert_log_to_csv(input_file, output_file)
    print(f"CSV gerado em: {output_file}")
