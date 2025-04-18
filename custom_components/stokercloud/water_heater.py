from __future__ import annotations

import logging

from homeassistant.components.water_heater import (
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.const import CONF_USERNAME, STATE_OFF, STATE_ON, UnitOfTemperature

from .const import DOMAIN
from .mixins import StokerCloudControllerMixin
from .stokercloud_api import State

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config, async_add_entities):
    """Set up the sensor platform."""
    client = hass.data[DOMAIN][config.entry_id]
    serial = config.data[CONF_USERNAME]
    async_add_entities(
        [
            StokerCloudWaterHeater(client, serial, "Hot Water", ""),
        ]
    )


class StokerCloudWaterHeater(StokerCloudControllerMixin, WaterHeaterEntity):
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = (
        WaterHeaterEntityFeature.AWAY_MODE | WaterHeaterEntityFeature.OPERATION_MODE
    )

    @property
    def current_operation(self) -> str:
        if self.controller_data:
            if self.controller_data.state == State.HOT_WATER:
                return STATE_ON
            return STATE_OFF

    @property
    def current_temperature(self):
        if self.controller_data and self.controller_data.hotwater_temperature_current:
            return float(self.controller_data.hotwater_temperature_current.value)

    @property
    def target_temperature(self):
        if self.controller_data and self.controller_data.hotwater_temperature_requested:
            return float(self.controller_data.hotwater_temperature_requested.value)
