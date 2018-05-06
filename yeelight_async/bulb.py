import asyncio

from .protocol import Protocol, PROPS
from .utils import intrange

SMOOTH_DURATION = 300

FUNCTIONS_DICT = {
    'set_ct_abx': (intrange(1700, 6500), 'smooth', SMOOTH_DURATION),
    'set_rgb': (intrange(0, 0x00ffffff), 'smooth', SMOOTH_DURATION),
    'set_hsv': (intrange(0, 359), intrange(0, 100), 'smooth', SMOOTH_DURATION),
    'set_bright': (intrange(1, 100), 'smooth', SMOOTH_DURATION),
    'set_power': (str, 'smooth', SMOOTH_DURATION),
    'toggle': (),
    'set_default': (),
    # 'start_cf: (intrange(0), int, str),
    # 'stop_cf': (,),
    # 'set_scene': (str, int, int, int),
    'cron_add': (intrange(0, 0), intrange(0)),
    'cron_get': (0,),
    'cron_del': (0,),
    'set_adjust': (str, str),
    # 'set_music': (),
    'set_name': (str,),
}

class Bulb(Protocol):
    def __getattr__(self, name):
        if name in FUNCTIONS_DICT:
            me = self
            async def _func(*args):
                return await me._call(name, *args)
                # if len(args) != len(argslist):
                #     raise AttributeError
            return _func
        raise AttributeError

    async def call(self, name, *args):
        args_new = []
        argslist = FUNCTIONS_DICT.get(name)
        for i in range(len(argslist)):
            f = argslist[i]
            if callable(f):
                args_new.append(f(args[i]))
            else:
                args_new.append(f)
        return await self.command(name, args_new)

    def _callback_socket(self, msg, state=None):
        if msg is None and state == 'connect':
            asyncio.ensure_future(self.get_prop())
        else:
            super()._callback_socket(msg, state)

    async def get_prop(self):
        ret = await self.command('get_prop', PROPS)
        if ret:
            props = {
                k: v for k, v in zip(PROPS, ret) if v != ''
            }
            dict(zip(PROPS, ret))
            if props:
                self._props.update(props)
            return self._props
        return ret
