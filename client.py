# /usr/bin/python3
import sys
import socket
import select
import random

def format_line(line):
    return line.rstrip().replace("\n", "")

def is_error(perror):
    rand = random.uniform(0, 1)
    if perror <= rand:
        return True
    return False


# verifica se a mensagem é valida
def is_ascii(s):
    return all(ord(c) < 128 for c in s)


def main():
    # pega argumentos do argv
    FILE = sys.argv[1]
    IP_PORT = sys.argv[2]
    # Tamanho da janela dae transmissao
    WTX = sys.argv[3]
    # Temporizador de retransmissão
    TOUT = int(sys.argv[4])
    # Chance de enviar erro
    PERROR = float(sys.argv[5])

    ip_port = IP_PORT.split(":")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = (ip_port[0], ip_port[1])

    
    seq_number = 0
    inp = open(FILE, 'r') 
    for line in inp:
        print(format_line(line))
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
