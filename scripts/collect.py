import can
import time
import random
import datetime
import logging

# Configura o logging para salvar em um arquivo Ãºnico (append mode)
log_filename = "coleta.log"
logging.basicConfig(filename=log_filename, level=logging.INFO, format='%(message)s')

def createLogLine(msg):
    payload = " ".join(["{:02X}".format(byte) for byte in msg.data])
    logging.info(f'{msg.timestamp} {msg.channel} {hex(msg.arbitration_id)} {payload}')

# ConfiguraÃ§Ã£o da interface CAN (can0 = exemplo)
bus = can.interface.Bus(channel='can0', bustype='socketcan')

try:
    while True:
        for msg in bus:
            print(msg)
            createLogLine(msg)

except KeyboardInterrupt:
    pass

# Limpeza da interface CAN
bus.shutdown()