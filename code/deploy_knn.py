import can
import logging
import pickle
import pandas as pd
import numpy as np
from datetime import datetime

# === Carrega modelo e scaler ===
with open("kmeans_model_new.p", "rb") as f:
    kmeans_model = pickle.load(f)

with open("std_scaler.p", "rb") as f:
    std_scaler = pickle.load(f)

with open("train_cols.p", "rb") as f:
    train_cols = pickle.load(f)

# Threshold definido (de acordo com seu resultado)
BEST_VALIDATION_THRESHOLD = 0.6680124845466734

# Configura logging
logging.basicConfig(filename="freestate_attack.log", level=logging.INFO, format="%(message)s")

# === Função de pré-processamento ===
def preprocess_dataframe(df):
    # Converter timestamp para datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

    # Converter can_id para numérico
    df['can_id'] = df['can_id'].apply(
        lambda x: int(x, 16) if isinstance(x, str) and x.startswith('0x') else x
    ).astype(float)
    df['can_id'] = df['can_id'].fillna(0)

    # Calcular diferença de tempo por can_id
    df.sort_values(['can_id', 'timestamp'], inplace=True)
    df['timestamp_diff_ms'] = (
        df.groupby('can_id')['timestamp']
          .diff()
          .dt.total_seconds() * 1000
    ).fillna(0)
    df.sort_index(inplace=True)

    # Dropar timestamp original
    df.drop(columns=['timestamp'], inplace=True)

    # One-hot encode interface
    df = pd.get_dummies(df, columns=['interface'], drop_first=True)

    # Processar coluna data
    data_split = df['data'].str.split(' ', expand=True)
    for col in data_split.columns:
        data_split[col] = data_split[col].apply(
            lambda x: int(x, 16) if isinstance(x, str) else 0
        )
    data_split.columns = [f"data_{i}" for i in range(data_split.shape[1])]

    df = pd.concat([df.drop('data', axis=1), data_split], axis=1)

    # Reindex para colunas do treino
    df = df.reindex(columns=train_cols, fill_value=0)
    return df

# === Inicia leitura do barramento CAN ===
bus = can.interface.Bus(channel="can0", bustype="socketcan")

# Lista para armazenar histórico de mensagens
messages = []

try:
    while True:
        for msg in bus:
            ts_str = datetime.fromtimestamp(msg.timestamp).strftime("%Y-%m-%d %H:%M:%S")
            payload = " ".join(f"{b:02X}" for b in msg.data)
            log_line = f"{ts_str} {hex(msg.arbitration_id)} {payload}"
            logging.info(log_line)

            # Adiciona mensagem ao histórico
            messages.append({
                "timestamp": datetime.fromtimestamp(msg.timestamp),
                "interface": msg.channel,
                "can_id": hex(msg.arbitration_id),
                "data": payload
            })

            # Só processa se houver pelo menos 2 mensagens (para calcular diff)
            if len(messages) > 1:
                df = pd.DataFrame(messages)
                df_proc = preprocess_dataframe(df)
                X_scaled = std_scaler.transform(df_proc)

                # Calcula distância para cada centroide
                distances = kmeans_model.transform(X_scaled)
                anomaly_score = np.min(distances[-1])  # último registro

                # Classifica com base no threshold
                if anomaly_score > BEST_VALIDATION_THRESHOLD:
                    print(f"{ts_str} 🚨 Malicious (Anomaly) detected! Score: {anomaly_score:.4f} | {log_line}")
                else:
                    print(f"{ts_str} ✅ Benign | Score: {anomaly_score:.4f} | {log_line}")

except KeyboardInterrupt:
    pass

bus.shutdown()
