# TP1 rmtlog: Um Sistema de Log Remoto
DCC023: Redes de Computadores 2018/02\
Caio Augusto Ferreira Godoy e Lucas Furtini

## Introdução
Neste trabalho foi desenvolvido uma biblioteca para criação, transmissão e armazenamento de logs. A biblioteca permite que uma aplicação executando em um dispositivo d1 gere mensagens de log e as envie para um coletor executando no dispositivo d2. A biblioteca realiza a codificação e transmissão confiável de mensagens entre aplicações e um coletor de logs.


# Cliente

O cliente possui as seguintes funções:
- build_pack(seq, message): _Recebe o numero da linha (numero do pacote) e o conteudo da linha. Ela retorna um pacote parcial sem o checksum em bytes._
- check_ack(ack_package): _Verifica se o checksum recebido é valido_
- get_index(ack_package): _Pega o numero do pacote confirmado pelo servidor_
- is_error(): _Calcula a chance de dar erro na transação_
- add_checksum(partial): _Recebe um pacote parcial como parametro e gera um pacote final com checksum (usand a função is_error para calcular a chance de erro._
- send_thread(udp, server_address, contentArray): _Função de envio de mensagens que sera executada por um Thread. Ela fica enviando pacotes sem ACK dentro da janela de transmissão infinitamente._
- ack_thread(udp, contentSize): _Função responsável pelo recebimento dos acks  e pela manipulação da janela deslizante, que vai sendo modificada conforme os acks vao sendo confirmados._
- main(): _Função principal do programa, realiza a instanciação inicial_

# Servidor

O cliente possui as seguintes funções:
def build_pack(seq, message):


# Testing

Para testar usando multiplos clientes basta aumentar ou o tempo TOUT ou o TERROR dos clientes ou do servidor:

```
python3 server.py zoutput 5000 8 0.2
```

```
python3 client.py zinput localhost:5000 5 2 0.2
python3 client.py zinput2 localhost:5000 4 1 0.8
```
