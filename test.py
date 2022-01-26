import asyncio
import os
import unittest

from iotfirmware import AbstractDeviceHandler


PWD = os.path.dirname(os.path.abspath(__file__))

SAMPLE_CONFIG = {
    'desired': {
        'firmwareVersion': '0.0.1',
        'checkout': [
            {
                'download': 'file://' + os.path.join(PWD, 'testfile1'),
                'filename': 'testfile1',
                'sha256sum': '15ef462c77eea7ecaca7d0498858b639'
                             '3797ed04af1240e591de0f6cf36e7768',
                'location': './updates',
            },
            {
                'download': 'file://' + os.path.join(PWD, 'testfile2'),
                'filename': 'testfile2',
                'sha256sum': '15ef462c77eea7ecaca7d0498858b639'
                             '3797ed04af1240e591de0f6cf36e7768',
                'location': './firmware',
            },
        ],
        'daemons': [
            ('python', 'mockdaemon.py',),
        ],
        'environ': {
            'param_1': 'value_1',
            'param_2': 'value_2',
        },
    },
    'reported': {
    },
}


class MockDeviceHandler(AbstractDeviceHandler):

    def __init__(self):
        super().__init__(self, sync_period=1)

        self.is_connected = False

    async def connect(self):
        self.is_connected = True

    async def disconnect(self):
        self.is_connected = False

    async def fetch_config_data(self):
        self.config = SAMPLE_CONFIG['desired']

    def get_config_data(self):
        return self.config

    def get_daemons(self):
        return self.config['daemons']

    def get_is_connected(self):
        return self.is_connected

    def get_update_info(self):
        return self.config['checkout']


class ClientTestCase(unittest.IsolatedAsyncioTestCase):

    def setUp(self) -> None:
        self.cl = MockDeviceHandler.get_instance()

    def tearDown(self) -> None:
        del self.cl

    async def test_InitAndShutdown(self):
        await self.cl.connect()

        self.assertTrue(self.cl.get_is_connected())

        await self.cl.disconnect()

        self.assertFalse(self.cl.get_is_connected())

    async def test_MainLoop_Stop(self):
        self.cl.restart = True
        await self.cl.sync_loop()


class ConfigTestCase(unittest.IsolatedAsyncioTestCase):

    def setUp(self) -> None:
        self.cl = MockDeviceHandler.get_instance()

    def tearDown(self) -> None:
        del self.cl

    async def test_DownloadConfig(self):
        await self.cl.connect()
        await self.cl.retrieve_config_data()

        self.assertEqual(self.cl.get_config_data(), SAMPLE_CONFIG['desired'])

        await self.cl.disconnect()

    async def test_EnvironConfigData(self):
        await self.cl.connect()
        await self.cl.retrieve_config_data()

        for param, val in SAMPLE_CONFIG['desired']['environ'].items():
            self.assertEqual(self.cl.get_environ()[param], val)

        await self.cl.disconnect()

    async def test_EnvironConfigEnvvar(self):
        await self.cl.connect()
        await self.cl.retrieve_config_data()

        for param, val in SAMPLE_CONFIG['desired']['environ'].items():
            self.assertEqual(os.environ.get(param), val)

        await self.cl.disconnect()


class UpdateTestCase(unittest.IsolatedAsyncioTestCase):

    def setUp(self) -> None:
        self.cl = MockDeviceHandler.get_instance()

        pwd = os.curdir

        with open(os.path.join(PWD, 'testfile1'), 'w') as f:
            f.write('TEST CONTENT')
        with open(os.path.join(PWD, 'testfile2'), 'w') as f:
            f.write('TEST CONTENT')

        for fdata in SAMPLE_CONFIG['desired']['checkout']:
            fpath = os.path.join(pwd, fdata['location'], fdata['filename'])

            if os.path.exists(fpath):
                os.remove(fpath)

    def tearDown(self) -> None:
        pwd = os.curdir

        os.remove(os.path.join(PWD, 'testfile1'))
        os.remove(os.path.join(PWD, 'testfile2'))

        for fdata in SAMPLE_CONFIG['desired']['checkout']:
            fpath = os.path.join(pwd, fdata['location'], fdata['filename'])

            if os.path.exists(fpath):
                os.remove(fpath)

        del self.cl

    async def test_DownloadUpdate_FilesPresent(self):
        await self.cl.connect()
        await self.cl.retrieve_config_data()

        self.cl.download_update()

        for fdata in SAMPLE_CONFIG['desired']['checkout']:
            file_path = os.path.join(os.curdir, fdata['location'])
            file_uri = os.path.join(file_path, fdata['filename'])

            self.assertTrue(os.path.exists(file_uri))

    async def test_DownloadUpdate_NotConnected_Error(self):
        with self.assertRaises(RuntimeError):
            await self.cl.download_update()

    async def test_GetUpdateInfo(self):
        await self.cl.retrieve_config_data()

        update_info = self.cl.get_update_info()

        self.assertEqual(update_info, SAMPLE_CONFIG['desired']['checkout'])


if __name__ == '__main__':
    unittest.main()
