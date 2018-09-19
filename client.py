# /usr/bin/python3
import sys
import socket
import random
import time
import math
import hashlib
from threading import Thread, Lock
from heapq import heappush, heappop, nsmallest

base9 = 1000000000

readlock = Lock()
total_sent = 0
total_errors = 0
sliding_window = {}

def build_pack(seq, message):
    # Get seconds and nanoseconds
    nano, sec = math.modf(time.time())

    bseq = seq.to_bytes(8, byteorder='big')
    bsec = int(sec).to_bytes(8, byteorder='big')
    bnano = int(nano*base9).to_bytes(4, byteorder='big')
    blen = len(message).to_bytes(2, byteorder='big')
    bmsg = message.encode('ascii')
    
    return add_checksum(bseq + bsec + bnano + blen + bmsg)


def check_ack(ack_package):
    # TODO
    # must check ack package
    return true

def get_index(ack_package):
    # TODO
    # must return ack index (seq_number acked)
    return 1

def is_error():
    global PERROR
    rand = random.uniform(0, 1)
    if rand < PERROR:
        return True
    return False


def add_checksum(partial):
    global total_errors
    m = hashlib.md5()
    m.update(partial)

    if is_error(PERROR):
        total_error += 1
        bchecksum = (random.getrandbits(128)).to_bytes(16, byteorder='big')
    else:
        bchecksum = bytes.fromhex(m.hexdigest())

    return partial + bchecksum


def send_thread(udp, server_address, contentArray):
    global readlock, sliding_window, total_sent
    while True:
        readlock.acquire()
        if sw_begin == len(contentArray):
            readlock.release()
            break
        try:
            for key, value in sliding_window.items():
                if value != -1:
                    package = build_pack(key, contentArray[key].rstrip().replace("\n", ""))
                    udp.sendto(package, server_address)
                    total_sent += 1
        finally:
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

        try:
            ack_pkg, addr = udp.recvfrom(36)
        except socket.timeout:
            continue

        # TODO implementar check_package ou similar
        if not check_package(ack_pkg):
            continue

        # TODO implementar get_index ou similar
        ack_index = get_index(ack_pkg)
        
        readlock.acquire()
        # Verifica se o pacote está dentro da janela
        if ack_index >= sw_begin and ack_index <= sw_end:
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
    for v in range(sw_end):
        sliding_window[v] = 0

    # Instancia socket UDP
    server_address = (IP, PORT)
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    udp.settimeout(TOUT)
    
    # Roubada basica carregando todo o arquivo na memoria, facilita MUITO a vida. 
    # Index vai ser o seq_number, e o valor a mensagem. (em nenhum lugar é cobrado otimização de memoria)
    f = open(FILE, 'r')
    contentArray = f.read().split("\n")
    f.close()

    # Cria e starta as threads
    send = Thread(target=send_thread, args=(udp, server_address, contentArray,))
    ack = Thread(target=ack_thread, args=(udp, len(contentArray),))
    send.start()
    ack.start()
    send.join()
    ack.join()

    # Imprime valores finais
    unique = set(contentArray)
    print("%d %d %d %.3fs" % ((len(unique)), total_sent,  total_errors,  (time.time() - start_time)))

if __name__ == '__main__':
    main()
