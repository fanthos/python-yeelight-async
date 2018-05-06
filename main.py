#!/usr/bin/python3

import asyncio
from yeelight_async import Bulb

async def callback(msg, ):
    print(msg)

async def main():
    b = Bulb('192.168.201.65', callback)
    await b.connect()
    print(await b.get_prop())
    while True:
        await asyncio.sleep(10)
        await b.cron_get()

loop = asyncio.get_event_loop()
asyncio.ensure_future(main())
loop.run_forever()
