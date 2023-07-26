#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import logging
import socket
import operator
from functools import reduce
from smb.SMBConnection import SMBConnection
from netifaces import interfaces, ifaddresses, AF_INET
import argparse


file_log = logging.FileHandler('Log.log')
console_out = logging.StreamHandler()

logging.basicConfig(handlers=(file_log, console_out),
                    format='[%(asctime)s | %(levelname)s]: %(message)s',
                    datefmt='%d.%m.%Y %H:%M:%S',
                    level=logging.INFO)

parser = argparse.ArgumentParser(description='Anchor Sender!')

parser.add_argument("-z", "--zone", help="WGS84 zones.", type=int, default=43)

args = parser.parse_args()

logging.info('Start server!')

logging.info('Anchor sender with {0}!'.format(str(args.zone)))

ip_address = []

for ifaceName in interfaces():
    addresses = [i['addr'] for i in ifaddresses(ifaceName).setdefault(AF_INET, [{'addr':'No IP addr'}] )]
    ip_address.append(addresses)
    logging.info(' '.join(addresses))

anchors = []


def checksum(sentence: str):
    nmea_data = sentence.strip('$*')
    calc_check_sum = reduce(operator.xor, (ord(s) for s in nmea_data), 0)
    return calc_check_sum


def smb_connection_to_request_anchor():
    conn = SMBConnection('user',
                         'Sa123456',
                         'Just_User',
                         'Desktop-c88b89k',
                         use_ntlm_v2=True)
    try:
        assert conn.connect('10.10.202.98', 139)
        if conn:
            logging.info('Successful connection: {}'.format(conn))
        else:
            logging.error('Connection failed')

        with open('anchor.txt', 'wb') as fp:
            conn.retrieveFile('shared', '/bridgeLOG.txt', fp)
            fp.close()
        conn.close()
    except:
        logging.info('SMB error!')


def get_anchor_from_log_file():
    fp = open('anchor.txt', 'r')
    last_line = fp.readlines()[-1]
    logging.info('Last line from anchor log: {}'.format(last_line))
    fp.close()

    last_line = last_line.strip('\n')
    s = last_line.split(',')
    for i in range(1, 9):
        anchors.append('$PNVEANC,' + str(i) + ',' + str(args.zone) + 'N' + ',' + str(s[(i * 2) + 1]) + ',' +
                       str(s[i + 17]) + ',' + ',' + '*')

    for i in range(8):
        calc_checksum = checksum(anchors[i])
        anchors[i] = anchors[i] + str(hex(calc_checksum).split('x')[-1]).upper().zfill(2) + '\r\n'


async def handle_connection(reader, writer):
    peername = writer.get_extra_info('peername')
    logging.info('Accepted connection from {}'.format(peername))
    while True:
        try:
            if writer.is_closing():
                logging.info('Connection from {} closed by remote client '.format(peername))
                break
            smb_connection_to_request_anchor()
            get_anchor_from_log_file()
            for i in range(len(anchors)):
                writer.write(bytes(anchors[i], encoding='UTF-8'))
                logging.info('Message send to {} '.format(peername))
                logging.info('Message: {} '.format(anchors[i]))
            # os.remove('anchor.txt')
            # logging.info('Local log file successful deleted!')
            anchors.clear()
            await asyncio.sleep(50)
        except asyncio.TimeoutError:
            logging.info('Connection from {} closed by timeout'.format(peername))
            break
    writer.close()


async def main():
    host = socket.gethostbyname(socket.gethostname())
    #logging.info(host)
    for i in range(len(ip_address)):
        if (str(ip_address[i]).find('10.10.202')) != -1:
            host = ip_address[i]
            logging.info(host)
    ip_address.clear()
    logging.basicConfig(level=logging.INFO)
    server = await asyncio.start_server(handle_connection, host=host, port=2007)
    logging.info('Listening established on {0}'.format(server.sockets[0].getsockname()))
    try:
        async with server:
            await server.serve_forever()
    except KeyboardInterrupt:
        server.close()
        await server.wait_closed()
    finally:
        server.close()
        await server.wait_closed()


asyncio.run(main())
