
import asyncio
import logging
import socket
import re
import operator
from functools import reduce
from smb.SMBConnection import SMBConnection
from netifaces import interfaces, ifaddresses, AF_INET

file_log = logging.FileHandler('Log_gals.log')
console_out = logging.StreamHandler()

logging.basicConfig(handlers=(file_log, console_out),
                    format='[%(asc_time)s | %(level_name)s]: %(message)s',
                    datefmt='%d.%m.%Y %H:%M:%S',
                    level=logging.INFO)

logging.info('Start server!')

ip_address = []

for ifaceName in interfaces():
    addresses = [i['addr'] for i in ifaddresses(ifaceName).setdefault(AF_INET, [{'addr': 'No IP addr'}])]
    ip_address.append(addresses)
    logging.info(' '.join(addresses))


def checksum(sentence: str):
    nmea_data = sentence.strip('$*')
    calc_check_sum = reduce(operator.xor, (ord(s) for s in nmea_data), 0)
    return calc_check_sum


def smb_connection_to_request_gals():
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

        with open('gals.txt', 'wb') as fp:
            conn.retrieveFile('shared', '/ActiveGals.txt', fp)
            fp.close()
        conn.close()
    except:
        logging.info('SMB error!')


def get_track_from_log_file():
    fp = open('gals.txt', 'r')
    last_line = fp.readlines()[-1]
    logging.info('Last line from anchor log: {}'.format(last_line))
    fp.close()

    last_line = last_line.strip('\n')
    last_line = last_line.replace(';', '')
    s = last_line.split(',')

    first_line = '$XXRTE,1,1,c,{0},,*'.format(s[4])
    second_line = '$XXWPL,{0},{1},{2},{3},*'.format(str(s[0][:-1]).zfill(12), ''.join(re.findall('[A-Z]', str(s[0]))),
                                                    str(s[1][:-1]).zfill(13), ''.join(re.findall('[A-Z]', str(s[1]))))
    third_line = '$XXWPL,{0},{1},{2},{3},*'.format(str(s[2][:-1]).zfill(12), ''.join(re.findall('[A-Z]', str(s[2]))),
                                                   str(s[3][:-1]).zfill(13), ''.join(re.findall('[A-Z]', str(s[3]))))

    message = '{0}{1}\r\n' \
              '{2}{3}\r\n' \
              '{4}{5}\r\n'.format(first_line,
                                  str(hex(checksum(first_line)).split('x')[-1]).upper().zfill(2),
                                  second_line,
                                  str(hex(checksum(second_line)).split('x')[-1]).upper().zfill(2),
                                  third_line,
                                  str(hex(checksum(third_line)).split('x')[-1]).upper().zfill(2))

    return message


async def handle_connection(reader, writer):
    peername = writer.get_extra_info('peername')
    logging.info('Accepted connection from {}'.format(peername))
    while True:
        try:
            if writer.is_closing():
                logging.info('Connection from {} closed by remote client '.format(peername))
                break
            smb_connection_to_request_gals()
            message = get_track_from_log_file()
            writer.write(bytes(message, encoding='UTF-8'))
            logging.info('Message send to {} '.format(peername))
            logging.info('Message: {} '.format(message))
            await asyncio.sleep(5)
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
    server = await asyncio.start_server(handle_connection, host=host, port=2009)
    logging.info('Listening established on {0}'.format(server.sockets[0].getsockname()))
    try:
        async with server:
            await server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        async with server:
            await server.close()


asyncio.run(main())
