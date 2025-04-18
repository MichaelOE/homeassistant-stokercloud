import decimal
from enum import Enum
import json
import logging
import time
from urllib import request
from urllib.parse import urljoin

import aiohttp

from .const import BASE_URL

#
# Based on code from https://github.com/KristianOellegaard/stokercloud-client
#

logger = logging.getLogger(__name__)


class TokenInvalid(Exception):
    pass


class Client:

    def __init__(self, name: str, password: str = None, cache_time_seconds: int = 10):
        self.name = name
        self.password = password
        self.token = None
        self.state = None
        self.last_fetch = None
        self.cache_time_seconds = cache_time_seconds

    async def refresh_token(self):
        async with aiohttp.ClientSession() as session:
            url = urljoin(BASE_URL, "v2/dataout2/login.php?user=" + self.name)
            async with session.get(url) as response:
                data = await response.json()
                self.token = data["token"]  # actual token
                self.state = data["credentials"]  # readonly

    async def make_request(self, url, *args, **kwargs):
        try:
            if self.token is None:
                raise TokenInvalid()
            absolute_url = urljoin(BASE_URL, "%s?token=%s" % (url, self.token))
            logger.debug(absolute_url)
            async with aiohttp.ClientSession() as session:
                async with session.get(absolute_url) as response:
                    return await response.json()
        except TokenInvalid:
            await self.refresh_token()
            return await self.make_request(url, *args, **kwargs)

    async def update_controller_data(self):
        self.cached_data = await self.make_request("v2/dataout2/controllerdata2.php")
        self.last_fetch = time.time()

    async def controller_data(self):
        if (
            not self.last_fetch
            or (time.time() - self.last_fetch) > self.cache_time_seconds
        ):
            await self.update_controller_data()
        return ControllerData(self.cached_data)

    async def controller_data_json(self):
        if (
            not self.last_fetch
            or (time.time() - self.last_fetch) > self.cache_time_seconds
        ):
            await self.update_controller_data()
        return self.flatten_json(self.cached_data)

    def flatten_json(self, jsonIn):
        out = {}

        def flatten(x, name=""):
            if type(x) is dict:
                for a in x:
                    flatten(x[a], name + a + "_")
            elif type(x) is list:
                i = 0
                for a in x:
                    flatten(a, name + str(i) + "_")
                    i += 1
            else:
                out[name[:-1]] = x

        flatten(jsonIn)
        return out


class NotConnectedException(Exception):
    pass


class PowerState(Enum):
    ON = 1
    OFF = 0


class Unit(Enum):
    KWH = "kwh"
    PERCENT = "pct"
    DEGREE = "deg"
    KILO_GRAM = "kg"
    GRAM = "g"


class State(Enum):
    POWER = "state_5"
    HOT_WATER = "state_7"
    IGNITION_1 = "state_2"
    IGNITION_2 = "state_4"
    FAULT_IGNITION = "state_13"
    OFF = "state_14"


STATE_BY_VALUE = {key.value: key for key in State}


class Value:
    def __init__(self, value, unit):
        self.value = decimal.Decimal(value)
        self.unit = unit

    def __eq__(self, other):
        if not isinstance(other, Value):
            # don't attempt to compare against unrelated types
            return NotImplemented

        return self.value == other.value and self.unit == other.unit

    def __repr__(self):
        return "%s %s" % (self.value, self.unit)

    # def get_from_list_by_key(lst, key, value):
    #     for itm in lst:
    #         if itm.get(key) == value:
    #             return itm


class ControllerData:
    def __init__(self, data):
        if data["notconnected"] != 0:
            raise NotConnectedException("Furnace/boiler not connected to StokerCloud")
        self.data = data

    def get_sub_item(self, submenu, _id):
        return get_from_list_by_key(self.data[submenu], "id", _id)

    @property
    def alarm(self):
        return {0: PowerState.OFF, 1: PowerState.ON}.get(
            self.data["miscdata"].get("alarm")
        )

    @property
    def running(self):
        return {0: PowerState.OFF, 1: PowerState.ON}.get(
            self.data["miscdata"].get("running")
        )

    @property
    def serial_number(self):
        return self.data["serial"]

    @property
    def boiler_temperature_current(self):
        return Value(self.get_sub_item("frontdata", "boilertemp")["value"], Unit.DEGREE)

    @property
    def boiler_temperature_requested(self):
        return Value(
            self.get_sub_item("frontdata", "-wantedboilertemp")["value"], Unit.DEGREE
        )

    @property
    def boiler_kwh(self):
        return Value(self.get_sub_item("boilerdata", "5")["value"], Unit.KWH)

    @property
    def state(self):
        return STATE_BY_VALUE.get(self.data["miscdata"]["state"]["value"])

    @property
    def hotwater_temperature_current(self):
        return Value(self.get_sub_item("frontdata", "dhw")["value"], Unit.DEGREE)

    @property
    def hotwater_temperature_requested(self):
        return Value(self.get_sub_item("frontdata", "dhwwanted")["value"], Unit.DEGREE)

    @property
    def consumption_total(self):
        return Value(self.get_sub_item("hopperdata", "4")["value"], Unit.KILO_GRAM)

    @property
    def consumption_day(self):
        return Value(self.get_sub_item("hopperdata", "3")["value"], Unit.KILO_GRAM)
