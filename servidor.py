
# /usr/bin/python3
import socket
import sys
import re
import time
import math
import hashlib
import random
import threading
from heapq import heappush, heappop, nsmallest

base9 = 1000000000

clients = {}

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
        # print('Erro no MD5')
        md5 = (random.getrandbits(128)).to_bytes(16, byteorder='big')
    else:
        md5 = bytes.fromhex(m.hexdigest())

    return add_md5(bseq + bsec + bnano + md5)

def add_md5(partial):

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

def new_client(address):
    
    global RWS, clients
    
    clients[address] = {}
    clients[address]['janela'] = {}
    clients[address]['lfa'] = RWS - 1
    clients[address]['nfe'] = 0
    
    for v in range(RWS):
        clients[address]['janela'][v] = None

# Thread do usuario
def user_thread(udp, outputFile):

    global RWS, lock, clients

    while True:
        # Tamanho maximo do pacote = 8 + 8 + 4 + 2 + 2^14 + 16
        data, addr = udp.recvfrom(16422)

        lock.acquire()
        if addr not in clients: new_client(addr)
        lock.release()
        # print(clients[addr]['janela'].keys())

        # Verificacao do md5
        if(check_md5(data)):

            lock.acquire()
            seqnumber = int.from_bytes(
                data[:8], byteorder='big', signed=False)
            
            messageSize = int.from_bytes(data[20:22], byteorder='big', signed=False)
            
            message = (data[22:(22 + messageSize)]).decode('ascii')

            # Pacote recebido eh o esperado
            if seqnumber == clients[addr]['nfe']:
                clients[addr]['janela'][seqnumber] = message
                ack = build_ack(seqnumber)
                udp.sendto(ack, addr)

                # Salvar janela ate proximo None
                with open(outputFile, 'a') as file:
                    #print('CLIENTE: {}'.format(clients[addr]))
                    #print('JANELA: {}'.format(clients[addr]['janela']))
                    #print('PACOTE: {}'.format(clients[addr]['janela'][seqnumber]))
                    
                    # Verifica o tamanho da janela para evitar iterar em janelas pequenas. 
                    if RWS == 1:
                        file.write(clients[addr]['janela'][seqnumber])
                        file.write('\n')
                        del clients[addr]['janela'][seqnumber]
                        seqnumber += 1
                    
                    elif RWS == 2:
                        
                        if clients[addr]['janela'][seqnumber] != None:
                            file.write(clients[addr]['janela'][seqnumber])
                            file.write('\n')
                            del clients[addr]['janela'][seqnumber]
                            seqnumber += 1

                    else:
                        while clients[addr]['janela'][seqnumber] != None:
                            file.write(clients[addr]['janela'][seqnumber])
                            file.write('\n')
                            del clients[addr]['janela'][seqnumber]
                            seqnumber += 1               
                
                # Atualizar janela
                clients[addr]['nfe'] = seqnumber
                clients[addr]['lfa'] = seqnumber + RWS - 1
                for v in range(seqnumber, clients[addr]['lfa']):
                    if v not in clients[addr]['janela'] and v > seqnumber: 
                        clients[addr]['janela'][v] = None
            
            # Pacote recebido não é o esperado mas está dentro da janela.
            elif seqnumber > clients[addr]['nfe'] and seqnumber < clients[addr]['lfa']:
                # Quadro esta dentro da janela esperada
                clients[addr]['janela'][seqnumber] = message
                ack = build_ack(seqnumber)
                udp.sendto(ack, addr)
            
            # Pacote recebido está abaixo da janela esperada
            elif seqnumber < clients[addr]['nfe']:
                # Caso receba abaixo da janela deve reenviar ack
                ack = build_ack(seqnumber)
                udp.sendto(ack, addr)

            lock.release()


# Retorna True se md5 estiver correto
def check_md5(data):

    bSeqNumber   = data[0:8]
    bSeconds     = data[8:16]
    bNanoSec     = data[16:20]
    bMessageSize = data[20:22]

    messageSize = int.from_bytes(
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
