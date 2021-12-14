import asyncio
import os

from datetime import datetime

from iotfirmware.azureiot import AzureDeviceHandler


cl = None
is_ongoing = True
proc = None


async def run_proc(cl):
    daemons = []

    for i in cl.get_daemons():
        daemons.append(await asyncio.create_subprocess_exec(
            *i,
            env=os.environ.update(cl.get_environ()),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        ))
        print(*i, 'as', daemons[-1])

    while not cl.restart and len(daemons) > 0:
        for i in daemons:
            bline = await i.stdout.readline()
            sline = bline.decode('utf-8').strip()

            print('{} {}: {}'.format(datetime.now(), i, sline))

            if i.returncode is not None:
                cl.restart = True

        await asyncio.sleep(1)

    print('Processes terminate...')

    for i in daemons:
        if i.returncode is None:
            i.terminate()


async def sync_loop(cl):
    await cl.sync_loop()


async def iothub_client_init():
    """Create an IoT client"""
    device = AzureDeviceHandler()

    # connect the client.
    await device.connect()
    await device.retrieve_config_data()

    device.download_update()

    return device


async def iothub_client_destroy(cl):
    """Shut IoT client down"""
    await cl.disconnect()


async def main():
    cl = await iothub_client_init()
    print('Done.')

    await asyncio.gather(
        run_proc(cl),
        sync_loop(cl),
    )

    await iothub_client_destroy(cl)
    print('Done.')


if __name__ == "__main__":
    asyncio.run(main())
