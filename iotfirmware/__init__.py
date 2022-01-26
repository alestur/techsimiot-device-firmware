import asyncio
import hashlib
import os
import urllib.request


class AbstractDeviceHandler:
    __instance = None

    def __init__(self, *args, **kwargs):
        if self.__class__.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            self.__class__.__instance = self

        self.cl = None
        self.config = {}
        self.is_config_updated = False
        self.restart = False

        try:
            self.sync_period = int(kwargs.get('sync_period')) or 30
        except (ValueError, TypeError,):
            self.sync_period = 10

    @staticmethod
    def message_handler(msg):
        print('Received a restart signal...')

        if msg == 'RESTART':
            AbstractDeviceHandler.get_instance().restart = True

    @classmethod
    def get_instance(cls):
        if not cls.__instance:
            cls()

        return cls.__instance

    async def connect(self):
        raise NotImplementedError

    async def disconnect(self):
        pass

    def collect_config_data_to_push(self):
        data = {}
        data.update(os.environ)

        return data

    def download_update(self):
        if not self.get_is_connected():
            raise RuntimeError('Client not connected.')

        for fdata in self.get_update_info() or []:
            downdata = None
            filename = fdata.get('filename')
            location = fdata.get('location') or './'
            url = fdata.get('download')
            fullpath = os.path.abspath(os.path.join(location, filename))

            if fullpath and os.path.exists(fullpath):
                with open(fullpath, 'rb') as f:
                    content = f.read()

                    if type(content) == str:
                        b = content.encode('utf-8')
                    else:
                        b = content

                hexdigest = hashlib.sha256(b).hexdigest().lower()
            else:
                hexdigest = None

            if fdata.get('sha256sum').lower() != hexdigest:
                print('Downloading {}...'.format(url))
                try:
                    downdata = urllib.request.urlopen(url)
                except FileNotFoundError:
                    downdata = None
            else:
                print('Skipping {} (SHA256 sum match)...'.format(url))

            if downdata:
                content = downdata.read()

                if type(content) == str:
                    b = content.encode('utf-8')
                else:
                    b = content

                hexdigest = hashlib.sha256(b).hexdigest().lower()

                if hexdigest == fdata.get('sha256sum').lower():
                    mode = 'w' if type(content) == str else 'wb'

                    with open(fullpath, mode) as f:
                        f.write(content)

    async def fetch_config_data(self):
        raise NotImplementedError

    def get_config_data(self):
        return self.config

    def get_daemons(self):
        if type(self.config) == dict:
            return self.config.get('daemons') or []
        else:
            return []

    def get_environ(self):
        return self.config.get('environ') or {}

    def get_is_connected(self):
        raise NotImplementedError

    def get_update_info(self):
        raise NotImplementedError

    async def push_config_data(self, data):
        raise NotImplementedError

    async def retrieve_config_data(self):
        await self.fetch_config_data()

        if type(self.config.get('environ')) == dict:
            for param, val in self.get_environ().items():
                os.environ[param] = val

    async def sync_config_data(self):
        data = self.collect_config_data_to_push()
        await self.push_config_data(data)

    async def sync_loop(self):
        while not self.restart:
            await self.retrieve_config_data()

            if not self.config:
                self.restart = True
            elif self.is_config_updated:
                await self.sync_config_data()
                self.is_config_updated = False

            await asyncio.sleep(self.sync_period)
