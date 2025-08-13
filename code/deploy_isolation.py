import can
import logging
import pickle
import pandas as pd
import numpy as np
from datetime import datetime

# === Carrega modelo e scaler ===
with open("isolation_forest_model.p", "rb") as f:
    isolation_forest_model = pickle.load(f)

with open("std_scaler.p", "rb") as f:
    std_scaler = pickle.load(f)

with open("train_cols.p", "rb") as f:
    train_cols = pickle.load(f)

# Threshold definido (ajuste de acordo com seu modelo)
BEST_VALIDATION_THRESHOLD = -0.15  # exemplo, ajuste conforme necessário

# Configura logging
logging.basicConfig(filename="freestate_attack.log", level=logging.INFO, format="%(message)s")

# === Função de pré-processamento ===
def preprocess_dataframe(df):
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

    df['can_id'] = df['can_id'].apply(
        lambda x: int(x, 16) if isinstance(x, str) and x.startswith('0x') else x
    ).astype(float)
    df['can_id'] = df['can_id'].fillna(0)

    df.sort_values(['can_id', 'timestamp'], inplace=True)
    df['timestamp_diff_ms'] = (
        df.groupby('can_id')['timestamp']
          .diff()
          .dt.total_seconds() * 1000
    ).fillna(0)
    df.sort_index(inplace=True)

    df.drop(columns=['timestamp'], inplace=True)

    df = pd.get_dummies(df, columns=['interface'], drop_first=True)

    data_split = df['data'].str.split(' ', expand=True)
    for col in data_split.columns:
        data_split[col] = data_split[col].apply(
            lambda x: int(x, 16) if isinstance(x, str) else 0
        )
    data_split.columns = [f"data_{i}" for i in range(data_split.shape[1])]

    df = pd.concat([df.drop('data', axis=1), data_split], axis=1)

    df = df.reindex(columns=train_cols, fill_value=0)
    return df

# === Inicia leitura do barramento CAN ===
bus = can.interface.Bus(channel="can0", bustype="socketcan")

messages = []

try:
    while True:
        for msg in bus:
            ts_str = datetime.fromtimestamp(msg.timestamp).strftime("%Y-%m-%d %H:%M:%S")
            payload = " ".join(f"{b:02X}" for b in msg.data)
            log_line = f"{ts_str} {hex(msg.arbitration_id)} {payload}"
            logging.info(log_line)

            messages.append({
                "timestamp": datetime.fromtimestamp(msg.timestamp),
                "interface": msg.channel,
                "can_id": hex(msg.arbitration_id),
                "data": payload
            })

            if len(messages) > 1:
                df = pd.DataFrame(messages)
                df_proc = preprocess_dataframe(df)
                X_scaled = std_scaler.transform(df_proc)

                # Isolation Forest - decision_function retorna score
                scores = isolation_forest_model.decision_function(X_scaled)
                anomaly_score = scores[-1]  # último registro

                if anomaly_score < BEST_VALIDATION_THRESHOLD:
                    print(f"{ts_str} 🚨 Malicious (Anomaly) detected! Score: {anomaly_score:.4f} | {log_line}")
                else:
                    print(f"{ts_str} ✅ Benign | Score: {anomaly_score:.4f} | {log_line}")

except KeyboardInterrupt:
    pass

bus.shutdown()
