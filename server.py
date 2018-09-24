
# /usr/bin/python3
import socket
import sys
import re
import time
import math
import hashlib
import random
import threading

base9 = 1000000000

lock = threading.Lock()

# Recebe numero de sequencia e prob de erro e retorna o pacote ACK
def build_ack(seq):

    nano, sec = math.modf(time.time())

    bseq = seq.to_bytes(8, byteorder='big')
    bsec = int(sec).to_bytes(8, byteorder='big')
    bnano = int(nano*base9).to_bytes(4, byteorder='big')

    ack = bseq + bsec + bnano

    m = hashlib.md5()
    m.update(ack)

    if is_error():
        print('Erro no MD5')
        md5 = (random.getrandbits(128)).to_bytes(16, byteorder='big')
    else:
        md5 = bytes.fromhex(m.hexdigest())

    return add_checksum(bseq + bsec + bnano + md5)

def add_checksum(partial):

    m = hashlib.md5()
    m.update(partial)

    if is_error():
        bchecksum = (random.getrandbits(128)).to_bytes(16, byteorder='big')
    else:
        bchecksum = bytes.fromhex(m.hexdigest())

    return partial + bchecksum

# Geracao de erro na mensagem
def is_error():
    
    global PERROR
    
    rand = random.uniform(0, 1)

    return rand < PERROR

# Thread do usuario
def user_thread(udp, outputFile):

    global RWS

    janela = [None] * RWS
    lfa = RWS   # Maior quadro aceitavel
    nfe = 0     # Proximo quadro esperado  
    index = 0

    while True:
        global lock
        
        # Tamanho maximo do pacote = 8 + 8 + 4 + 2 + 2^14 + 16
        data, address = udp.recvfrom(16422)

        print('Origem: {}'.format(address))
        # Verificacao do md5
        if(check_md5(data)):
            
            seqnumber = 0
            seqnumber = seqnumber.from_bytes(
                data[:8], byteorder='big', signed=False)
            
            messageSize = 0
            messageSize = messageSize.from_bytes(data[20:22], byteorder='big', signed=False)
            
            message = (data[22:(22 + messageSize)]).decode('ascii')
            print(message)

            # TODO: Implementar a janela circular
            # TODO: e arrumar os indices
            
            # Quadro eh o proximo esperado
            if seqnumber == nfe:
                # Salva mensagem na janela

                janela[nfe] = message
                # Enviar ACK
                ack = build_ack(seqnumber)
                udp.sendto(ack, address)

                lock.acquire()
                # Salvar janela ate proximo None
                with open(outputFile, 'a') as file:
                    while janela[index] != None:
                        file.write(message)
                        file.write('\n')
                        index += 1               
                lock.release()
                nfe = index    
            
            # Quadro esta dentro da janela esperada
            elif seqnumber > nfe or seqnumber < lfa:
                janela[seqnumber] = message
                # Enviar ACK
                ack = build_ack(seqnumber)
                udp.sendto(ack, address)



# Retorna True se md5 estiver correto
def check_md5(data):

    bSeqNumber   = data[0:8]
    bSeconds     = data[8:16]
    bNanoSec     = data[16:20]
    bMessageSize = data[20:22]

    messageSize = 0
    messageSize = messageSize.from_bytes(
        data[20:22], byteorder='big', signed=False)

    bMessage = data[22:(22 + messageSize)]
    md5Recebido = (data[(22 + messageSize):(22 + messageSize + 16)]).hex()

    md5Calculado = hashlib.md5()
    md5Calculado.update(
        (bSeqNumber + bSeconds + bNanoSec + bMessageSize + bMessage))

    return md5Recebido == md5Calculado.hexdigest()

def main():
    global RWS, PERROR

    if (len(sys.argv) < 4):
        print("ERROR: Argumentos invalidos.")
        print("Tente: fileName port RWS Perror")
        sys.exit()

    FILE   = sys.argv[1]
    PORT   = int(sys.argv[2])
    RWS    = int(sys.argv[3])
    PERROR = float(sys.argv[4])

    server_address = ('localhost', PORT)

    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    udp.bind(server_address)

    try:
        user = threading.Thread(target=user_thread, args=(udp, FILE,))
        user.start()

    except (KeyboardInterrupt, SystemExit):
        user.join()
        exit()

if __name__ == '__main__':
    main()
