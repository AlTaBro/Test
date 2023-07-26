#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import logging


# class SenderServer(object):
#
#     def __init__(self, host, port, loop=None):
#         self._loop = loop or asyncio.get_event_loop()
#         self._host = host
#         self._port = port
#
#     async def start(self, and_loop=True):
#         self._server = await asyncio.start_server(self.handle_connection, host=self._host, port=self._port)
#         self._server = self._loop.run_until_complete(self._server)
#         logging.info('Listening established on {0}'.format(self._server.sockets[0].getsockname()))
#         if and_loop:
#             self._loop.run_forever()
#
#     async def stop(self, and_loop=True):
#         self._server.close()
#         if and_loop:
#             self._loop.close()
#
#     async def handle_connection(self, reader, writer):
#         peername = writer.get_extra_info('peer name')
#         logging.info('Accepted connection from {}'.format(peername))
#         while not reader.at_eof():
#             try:
#                 data = await asyncio.wait_for(reader.readline(), timeout=10.0)
#                 writer.write(data)
#             except asyncio.TimeoutError:
#                 break
#             writer.close()
#
#
# async def main():
#
#     server = SenderServer('127.0.0.1', 8888)
#     try:
#         await server.start()
#     except KeyboardInterrupt:
#         pass
#     finally:
#         await server.stop()
#
# asyncio.run(main())

async def handle_connection(reader, writer):
    peername = writer.get_extra_info('peername')
    logging.info('Accepted connection from {}'.format(peername))
    while True:
        try:
            data = await asyncio.wait_for(reader.readline(), timeout=10.0)
            message = data.decode()
            logging.info(f"Received {message!r}")
            # print(f"Received {message!r}")
            writer.write(data)
            if writer.is_closing():
                logging.info('Connection from {} closed by peer'.format(peername))
                break
        except asyncio.TimeoutError:
            logging.info('Connection from {} closed by timeout'.format(peername))
            break
    writer.close()


async def main():
    logging.basicConfig(level=logging.INFO)
    server = await asyncio.start_server(handle_connection, host= 'localhost', port=2007)
    logging.info('Listening established on {0}'.format(server.sockets[0].getsockname()))
    try:
        async with server:
            await server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        async with server:
            await server.close()


# if __name__ == '__main__':

asyncio.run(main())
