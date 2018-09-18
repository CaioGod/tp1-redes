# /usr/bin/python3
import socket, sys, re, time, math, hashlib
import random

base9 = 1000000000

# Recebe numero de sequencia e prob de erro e retorna o pacote ACK
def build_ack(seq, perror):

    nano, sec = math.modf(time.time())

    bseq  = seq.to_bytes(8, byteoerder='big')
    bsec  = int(sec).to_bytes(8, byteoerder='big')
    bnano = int(nano*base9).to_bytes(4, byteoerder='big')
    
    ack = bseq + bsec + bnano

    m = hashlib.md5()
    m.update(ack)

    if is_error(perror):
        print('Erro no MD5')
        md5 = (random.getrandbits(128)).to_bytes(16, byteorder='big')
    else:
        md5 = bytes.fromhex(m.hexdigest())

    return bseq + bsec + bnano + md5

# Geracao de erro na mensagem
def is_error(perror):
    rand = random.uniform(0, 1)
    if perror <= rand:
        return True
    return False

def main():

    if (len(sys.argv) < 4):
        print("ERROR: Argumentos invalidos.")
        print("Tente: fileName port Wtx Perror")
        sys.exit()

    FILE   = sys.argv[1]
    PORT   = int(sys.argv[2])
    WTX    = int(sys.argv[3])
    PERROR = float(sys.argv[4])

    server_address = ('localhost', PORT)

if __name__ == '__main__':
    main()

# REFERENCIA: TP3

# # dic global que armazena relaçao tag:client
# subscriptions = {}

# # verifica se a tag é alphanumérica
# def isValid(tag):
#     return tag.isalnum()

# # verifica se a string é uma tag
# def isTag(s):
#     return (s == '+' or s == '-' or s == '#')

# # cria uma lista vazia em subscriptions[tag] caso não exista
# # insere o address dentro dela
# def insert(address, tag):
#     if isValid(tag):
#         if not tag in subscriptions:
#             subscriptions[tag] = []
#         if not address in subscriptions[tag]:
#             subscriptions[tag].append(address)

# # remove endereço do subscriptions[tag] nao faz nada caso não exista
# def remove(address, tag):
#     if isValid(tag):
#         if tag in subscriptions:
#             if address in subscriptions[tag]: 
#                 subscriptions[tag].remove(address)

# # verifica quem está escutando a tag, e envia mensgaem para todos
# def publish(sock, message, tag):
#     if isValid(tag):
#         if tag in subscriptions:
#             for address in subscriptions[tag]:
#                 sock.sendto(message, address)

# def main():
#     PORT = int(sys.argv[1])
#     # Create a UDP socket
#     sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#     # Bind the socket to the port
#     server_address = ('localhost', PORT)
#     print('starting up on {} port {}'.format(*server_address))
#     sock.bind(server_address)

#     while True:
#         data, address = sock.recvfrom(4096)
#         message = data.decode("utf-8")

#         # aqui eu crio uma lista dando split nos espaços e nas tags, mas mantento as tags.
#         # a mensagem "neymar #ney +bruna" gera tokens = ['neymar', ' ', '#', 'ney', ' ', '+', 'bruna']
#         tokens = list(filter(None, re.split('(\+|\-|\#| )', message)))

#         # itero os tokens, fazendo as actions na ordem que elas vieram no texto 
#         # no exemplo acima # vai ser feito antes do +
#         action = ''
#         for token in tokens:
#             if isTag(token):
#                 action = token
#             elif action == '+':
#                 insert(address, token)
#                 action = ''
#             elif action == '-':
#                 remove(address, token)
#                 action = ''
#             elif action == '#':
#                 publish(sock, data, token)
#                 action = ''
        
#         print(subscriptions)

# main()
