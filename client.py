# /usr/bin/python3
import sys
import socket
import random
import time
import math
import hashlib
import threading
from heapq import heappush, heappop, nsmallest

base9 = 1000000000

readlock = threading.Lock()
total_sent = 0
total_errors = 0
sliding_window = {}

def build_pack(seq, message):

    # Get seconds and nanoseconds
    nano, sec = math.modf(time.time())

    bseq = seq.to_bytes(8, byteorder='big', signed=False)
    bsec = int(sec).to_bytes(8, byteorder='big', signed=False)
    bnano = int(nano*base9).to_bytes(4, byteorder='big', signed=False)
    blen = len(message).to_bytes(2, byteorder='big', signed=False)
    bmsg = message.encode('ascii')

    return add_md5(bseq + bsec + bnano + blen + bmsg)

def add_md5(partial):

    global total_errors

    m = hashlib.md5()
    m.update(partial)

    if is_error():
        # print("Checksum error")
        total_errors += 1
        bchecksum = (random.getrandbits(128)).to_bytes(16, byteorder='big')
    else:
        bchecksum = bytes.fromhex(m.hexdigest())

    return partial + bchecksum


def is_error():
    global PERROR
    rand = random.uniform(0, 1)

    return rand < PERROR

def check_md5(data):
    bSeqNumber   = data[0:8]
    bSeconds     = data[8:16]
    bNanoSec     = data[16:20]
    md5recvd     = data[20:36]

    md5Calculado = hashlib.md5()
    md5Calculado.update((bSeqNumber + bSeconds + bNanoSec))
    return md5recvd.hex() == md5Calculado.hexdigest()

def get_index(data):
    return int.from_bytes(data[0:8], byteorder='big', signed=False)

def send_thread(udp, server_address, contentList):

    global readlock, sliding_window, total_sent, TOUT

    while True:
        readlock.acquire()
        if sw_begin == len(contentList):
            readlock.release()
            break

        for key, value in sliding_window.items():
            if key >= len(contentList): break
            if value == -1: continue
            if value == 0 or value < time.time():
                sliding_window[key] = time.time() + TOUT
                # print("SEND %d" % key)
                package = build_pack(key, contentList[key])
                udp.sendto(package, server_address)
                total_sent += 1
        readlock.release()

def ack_thread(udp, contentSize):

    global readlock, sliding_window, total_sent, sw_begin, sw_end

    acked = []

    while True:
        readlock.acquire()
        if sw_begin == contentSize:
            readlock.release()
            break
        readlock.release()
        time.sleep(0.005)
        try:
            ack_pkg, addr = udp.recvfrom(36)
            seqnumber = 0
            seqnumber = seqnumber.from_bytes(
                ack_pkg[:8], byteorder='big', signed=False)
        except socket.timeout:
            continue
    
        if not check_md5(ack_pkg):
            continue
        ack_index = get_index(ack_pkg)
        
        readlock.acquire()
        if ack_index >= sw_begin and ack_index <= sw_end:
            # print('ACK #: {}'.format(ack_index))
            heappush(acked, ack_index)

            # Colocando -1 nos vetor de sliding_window para não reenviar o mesmo pacote
            if sw_begin != nsmallest(1, acked)[0]:
                sliding_window[ack_index] = -1

            # Atualiza o limite da janela
            while len(acked) > 0 and sw_begin == nsmallest(1, acked)[0]:
                heappop(acked)
                del sliding_window[sw_begin]
                sw_begin += 1

            # Colocando 0 nos novos pacotes a serem enviados
            while True:
                if not sw_end in sliding_window:
                    sliding_window[sw_end] = 0
                if sw_end == contentSize - 1:
                    break
                if sw_end >= sw_begin + WTX-1:
                    break
                sw_end += 1
        readlock.release()

def main():
    global WTX, TOUT, PERROR, sliding_window, sw_begin, sw_end

    # Leitura de argumentos
    start_time = time.time()
    if (len(sys.argv) < 5):
        print("ERROR: Argumentos invalidos.")
        print("Tente: fileName IP:port Wtx Tout Perror")
        sys.exit()

    FILE = sys.argv[1]
    IP, PORT = sys.argv[2].split(":")
    WTX = int(sys.argv[3])
    TOUT = int(sys.argv[4])
    PERROR = float(sys.argv[5])

    # Instancia variaveis da Janela Deslizante
    sw_begin = 0
    sw_end = WTX-1
    for v in range(WTX):
        sliding_window[v] = 0

    # Instancia socket UDP
    server_address = (IP, int(PORT))
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    udp.settimeout(TOUT)

    # Lista contendo as mensagens lidas do arquivo de LOG
    contentList = []
    with open(FILE, 'r') as file:
        for line in file:
            line = line.strip('\n')
            contentList.append(line)

    # Cria e starta as threads
    try:
        send = threading.Thread(target=send_thread, args=(
            udp, server_address, contentList,))
        ack = threading.Thread(
            target=ack_thread, args=(udp, len(contentList),))
        send.start()
        ack.start()
        send.join()
        ack.join()

    except (KeyboardInterrupt, SystemExit):
        exit()

    # Imprime valores finais
    unique = set(contentList)
    print("%d %d %d %.3fs" % ((len(unique)), total_sent,
                              total_errors,  (time.time() - start_time)))


if __name__ == '__main__':
    main()
