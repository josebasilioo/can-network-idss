#!/usr/bin/env python3

import argparse
import csv
import random
from pathlib import Path
from typing import List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Gera um CSV de ataque stealth a partir de um CSV benigno existente "
            "(ex.: coleta.csv), preservando o padrão de mensagens para enganar detectores."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path(__file__).resolve().parent / "coleta.csv",
        help="Caminho do CSV de entrada (benigno).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent / "stealth_attack.csv",
        help="Caminho do CSV de saída (ataque stealth).",
    )
    parser.add_argument(
        "--num-rows",
        type=int,
        default=5000,
        help="Número de linhas a copiar do CSV benigno (preserva ordem).",
    )
    parser.add_argument(
        "--start-offset",
        type=int,
        default=0,
        help=(
            "Offset inicial a partir do fim do arquivo para a janela selecionada. "
            "0 usa as últimas linhas; 100 ignora as 100 últimas, etc."
        ),
    )
    parser.add_argument(
        "--perturb",
        type=float,
        default=0.0,
        help=(
            "Taxa (0.0-1.0) de pequenas perturbações no payload para mimetizar drift. "
            "Padrão 0.0 (cópia perfeita)."
        ),
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Semente para reprodutibilidade quando usar --perturb > 0.",
    )
    return parser.parse_args()


def should_perturb(probability: float) -> bool:
    return probability > 0 and random.random() < probability


def hex_byte_to_int(byte_str: str) -> int:
    return int(byte_str, 16)


def int_to_hex_byte(value: int) -> str:
    return f"{value & 0xFF:02X}"


def slight_perturbation(can_id: str, data_field: str) -> str:
    """
    Introduz uma perturbação mínima, dependente do ID, mantendo proximidade semântica.
    Mantém comprimento original do payload.
    """
    if not data_field:
        return data_field

    bytes_list: List[str] = [b for b in data_field.split() if b]
    if not bytes_list:
        return data_field

    # Estratégias leves por ID comum; fallback = variar 1 byte em ±1
    try:
        if can_id.lower() in {"0x36"} and len(bytes_list) >= 2:
            # Toca 2º byte ±1, mantendo faixa próxima
            idx = 1
        elif can_id.lower() in {"0x26"} and len(bytes_list) >= 2:
            idx = 1
        else:
            # Escolhe um índice aleatório válido
            idx = random.randrange(len(bytes_list))

        val = hex_byte_to_int(bytes_list[idx])
        delta = random.choice([-1, 1])
        bytes_list[idx] = int_to_hex_byte(val + delta)
        return " ".join(bytes_list)
    except Exception:
        return data_field


def main() -> None:
    args = parse_args()

    if args.perturb > 0:
        random.seed(args.seed)

    if not args.input.exists():
        raise FileNotFoundError(f"CSV de entrada não encontrado: {args.input}")

    with args.input.open("r", encoding="utf-8", errors="replace") as fin:
        reader = csv.reader(fin)
        header = next(reader, None)
        if header is None:
            raise ValueError("CSV de entrada vazio.")

        # Verifica/normaliza cabeçalho esperado
        expected_header = ["timestamp", "interface", "can_id", "data", "label"]
        if [h.strip() for h in header] != expected_header:
            raise ValueError(
                f"Cabeçalho inesperado em {args.input.name}: {header}. Esperado: {expected_header}"
            )

        rows = list(reader)

    total = len(rows)
    if total == 0:
        raise ValueError(
            "Nenhuma linha de dados encontrada no CSV de entrada.")

    # Seleciona janela no fim (mais recente), aplicando start_offset
    end_idx = max(0, total - args.start_offset)
    start_idx = max(0, end_idx - args.num_rows)
    selected = rows[start_idx:end_idx]

    if not selected:
        raise ValueError(
            f"Janela vazia. Tamanho total={total}, start_idx={start_idx}, end_idx={end_idx}, num_rows={args.num_rows}."
        )

    with args.output.open("w", newline="", encoding="utf-8") as fout:
        writer = csv.writer(fout)
        writer.writerow(["timestamp", "interface", "can_id", "data", "label"])

        for ts, iface, can_id, data_field, _label in selected:
            new_data = (
                slight_perturbation(can_id, data_field) if should_perturb(
                    args.perturb) else data_field
            )
            writer.writerow([ts, iface or "can0", can_id, new_data, "stealth"])

    print(
        f"Gerado {len(selected)} linhas em {args.output.name} usando base {args.input.name}. Perturbação={args.perturb}."
    )


if __name__ == "__main__":
    main()
