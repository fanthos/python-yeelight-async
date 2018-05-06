import asyncio
import json
import async_timeout

from . import net

PROPS = ["power", "bright", "ct", "rgb", "hue", "sat", "color_mode", "flowing", "delayoff", "music_on", "name", "nl_br"]

class Protocol():
    def __init__(self, remoteip, callback):
        self._callback = callback
        self._buffer = ''
        self._decoder = json.JSONDecoder()
        self._socket = None
        self._msgid = 0
        self._event = asyncio.Event()
        self._lock = asyncio.Lock()
        self._remoteip = remoteip
        self._lastmicros = 0
        self._resp = None
        self._props = {}
        # asyncio.ensure_future(self._connect())

    async def connect(self):
        if self._socket is not None:
            return
        self._socket = await net.light_connect(
            self._remoteip,
            lambda msg, state=None: self._callback_socket(msg, state))

    def _callback_socket(self, msg, state=None):
        if msg is None:
            if state == 'disconnect':
                self._socket = None
                asyncio.ensure_future(self.connect())
        self._buffer += msg
        while len(self._buffer):
            try:
                result, index = self._decoder.raw_decode(self._buffer)
                self._callback_msg(result)
                self._buffer = self._buffer[index:].lstrip()
            except ValueError:
                # Not enough data to decode, read more
                break

    def _callback_msg(self, msg):
        print(json.dumps(msg))
        msgid = msg.get('id')
        if msgid == self._msgid:
            self._resp = msg
            self._event.set()
        elif msgid is None:
            props = msg.get('params')
            self._props.update(props)
            asyncio.ensure_future(self._callback(self._props))
        else:
            pass

    async def _send(self, msg):
        if self._socket is None:
            return False
        self._socket.write((msg + '\r\n').encode())
        return True

    async def command(self, method, params):
        try:
            await self._lock.acquire()
            msgid = self._msgid + 1
            if msgid >= 60000:
                msgid = 1
            self._msgid = msgid
            msgobj = {
                'id': msgid,
                'method': method,
                'params': params
            }
            ret = await self._send(json.dumps(msgobj))
            if not ret:
                return False
            async with async_timeout.timeout(2) as tm:
                self._event.clear()
                await self._event.wait()
            if tm.expired:
                return False

            ret = self._resp.get('result')
            self._resp = None

            if ret is not None:
                return ret
            else:
                return False
        except:
            return False
        finally:
            self._lock.release()
