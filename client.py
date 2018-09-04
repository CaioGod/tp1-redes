# /usr/bin/python3
import sys
import socket
import random
import time
import math
import hashlib

base9 = 1000000000


# Recebe sequence_number, message e change de erro retorna o pacote (errado ou não)
def build_pack(seq, message, perror):
    # Get seconds and nanoseconds
    nano, sec = math.modf(time.time())

    bseq = seq.to_bytes(8, byteorder='big')
    bsec = int(sec).to_bytes(8, byteorder='big')
    bnano = int(nano*base9).to_bytes(4, byteorder='big')
    blen = len(message).to_bytes(2, byteorder='big')
    bmsg = message.encode('ascii')

    # Calculando md5 (usando dados transformados em bytes, pode estar errado)
    m = hashlib.md5()
    m.update(bseq + bsec + bnano + blen + bmsg)
    if is_error(perror):
        print('Erro no checksum')
        bchecksum = (random.getrandbits(128)).to_bytes(16, byteorder='big')
    else:
        bchecksum = bytes.fromhex(m.hexdigest())

    # print(seq, int(sec), int(nano*base9), len(message), message, m.hexdigest())
    # print(bseq, bsec, bnano, blen, bmsg, bchecksum)
    # print(bseq + bsec + bnano + blen + bmsg + bchecksum)
    
    return bseq + bsec + bnano + blen + bmsg + bchecksum


def is_error(perror):
    rand = random.uniform(0, 1)
    if perror <= rand:
        return True
    return False


def is_ascii(s):
    return all(ord(c) < 128 for c in s)


def main():
    FILE = sys.argv[1]
    IP_PORT = sys.argv[2]
    WTX = sys.argv[3]
    TOUT = int(sys.argv[4])
    PERROR = float(sys.argv[5])

    ip_port = IP_PORT.split(":")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = (ip_port[0], ip_port[1])

    seq_number = 0
    inp = open(FILE, 'r')
    for line in inp:
        pack = build_pack(seq_number, line.rstrip().replace("\n", ""), PERROR)
        print(pack)
        seq_number += 1

    inp.close()

    # # define a lista de readers
    # while True:
    #     # cria select apenas com readers
    #     inc, out, err = select.select(socketList, [], [])

    #     # loop que itera sobre os readers e define o comportamento de cada um
    #     for i in inc:
    #         if i == sock:
    #             data, server = sock.recvfrom(4096)
    #             if len(data) != 0:
    #                 message = data.decode("utf-8")
    #                 print (message)
    #         else:
    #             message = sys.stdin.readline().strip()
    #             if(is_ascii(message)):
    #                 message = message.encode('utf-8')
    #                 sock.sendto(message, server_address)
    #             else:
    #                 print('Mensagem invalida pois nao pertence a tabela ASCII')


main()
