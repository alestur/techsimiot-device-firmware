import asyncio
import json
import os

from datetime import datetime

from azure.iot.device.aio import IoTHubDeviceClient

from . import AbstractDeviceHandler


CONNECTION_STRING = os.environ.get('AZURE_CONNECTION_STRING')


class AzureDeviceHandler(AbstractDeviceHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.cl = IoTHubDeviceClient. \
            create_from_connection_string(CONNECTION_STRING)
        self.cl.on_message_received = self.__class__.message_handler

    @staticmethod
    def message_handler(msg):
        if msg.custom_properties.get('RESTART'):
            print('Received a restart signal...')
            AzureDeviceHandler.get_instance().restart = True

    async def connect(self):
        print('Connecting to Azure IoT...')
        await self.cl.connect()

    async def disconnect(self):
        print('Disconnecting from Azure IoT...')
        await self.cl.shutdown()

    def get_is_connected(self):
        return self.cl.connected

    def get_update_info(self):
        return self.config.get('checkout')

    async def fetch_config_data(self):
        self.config = self.config or {}

        data = await self.cl.get_twin()
        conf = dict(self.config)

        self.config.update(data.get('desired'))

        if conf != self.config:
            self.is_config_updated = True

    async def push_config_data(self, data):
        data = json.loads(json.dumps(data))
        await self.cl.patch_twin_reported_properties(data)
