import asyncio
import socket
import sys
import json


BROADCAST_PORT = 1982
BROADCAST_ADDR = "239.255.255.250"

class socket_wrapper(socket.socket):
    def getsockname(self):
        return None

class DiscoveryProtocol:
    def __init__(self, loop, addr, callback):
        self.loop = loop
        self.addr = addr
        self.callback = callback

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        message = data.decode()
        print('Received %r from %s' % (message, addr))
        print('Send %r to %s' % (message, addr))
        asyncio.ensure_future(self.callback(message, addr))


msg = 'M-SEARCH * HTTP/1.1\r\n' \
        'ST:wifi_bulb\r\n' \
        'MAN:"ssdp:discover"\r\n'


async def discovery_listen(callback):
    loop = asyncio.get_event_loop()
    sock = socket_wrapper(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    transport, _ = await loop.create_datagram_endpoint(
        lambda: DiscoveryProtocol(loop, BROADCAST_ADDR, callback),
        sock=sock,
    )
    return transport

async def discovery_send(transport):
    transport.sendto(msg.encode(), ('239.255.255.250', 1900))


class ControlProtocol:
    def __init__(self, loop, callback):
        self._loop = loop
        self._callback = callback

    def connection_made(self, transport):
        self._transport = transport
        self._callback(None, 'connect')

    def data_received(self, data):
        message = data.decode()
        self._callback(message)

    def connection_lost(self, exc):
        self._callback(None, 'disconnect')


async def light_connect(remoteip, callback):
    loop = asyncio.get_event_loop()
    transport, _ = await loop.create_connection(
        lambda: ControlProtocol(loop, callback),
        remoteip, 55443
    )
    return transport

async def light_send(transport, payload):
    data = payload.encode()
    transport.write(data)
