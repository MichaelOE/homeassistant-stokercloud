"""NBE Stoker Cloud"""

import asyncio
from dataclasses import dataclass
from datetime import timedelta
import logging

from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .stokercloud_api import Client as StokerCloudClient

_LOGGER = logging.getLogger(__name__)

# PLATFORMS: list[Platform] = [Platform.SENSOR]
PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.SENSOR]


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the component."""
    hass.data[DOMAIN] = {}
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    nbe_user = entry.data[CONF_USERNAME]
    stokerCloud = StokerCloudClient(nbe_user)

    # Fetch initial data so we have data when entities subscribe
    coordinator = IntegrationCoordinator(hass, stokerCloud, nbe_user, 60)

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = HassIntegration(coordinator, nbe_user)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class HassIntegration:
    def __init__(self, coordinator: DataUpdateCoordinator, nbe_user: str):
        self._nbe_user = nbe_user
        _LOGGER.debug("StokerCloud __init__" + self._nbe_user)

        # create an instance of StokerCloud
        self._coordinator = coordinator

    def get_name(self):
        return f"stoker_cloud_{self._nbe_user}"

    def get_unique_id(self):
        return f"stoker_cloud_{self._nbe_user}"


class IntegrationCoordinator(DataUpdateCoordinator):
    """StokerCloud coordinator."""

    def __init__(
        self, hass, stokerClient: StokerCloudClient, alias: str, pollinterval: int
    ):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name=f"StokerCloud coordinator for '{alias}'",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=15),
        )
        self._api = stokerClient
        self._alias = alias

    async def _async_update_data(self):
        # Fetch data from API endpoint. This is the place to pre-process the data to lookup tables so entities can quickly look up their data.

        try:
            # controller_data = await self._api.controller_data()
            controller_data = await self._api.controller_data_json()
            return controller_data

        except:
            _LOGGER.error("StecaGridCoordinator _async_update_data failed")
        # except ApiAuthError as err:
        #     # Raising ConfigEntryAuthFailed will cancel future updates
        #     # and start a config flow with SOURCE_REAUTH (async_step_reauth)
        #     raise ConfigEntryAuthFailed from err
        # except ApiError as err:
        #     raise UpdateFailed(f"Error communicating with API: {err}")


@dataclass
class IntegrationEntityDescription(SensorEntityDescription):
    """Describes Stecagrid sensor entity."""

    def __init__(
        self,
        key,
        name,
        icon,
        device_class,
        native_unit_of_measurement,
        value,
        format=None,
    ):
        super().__init__(key)
        self.key = key
        self.name = name
        self.icon = icon
        if device_class is not None:
            self.device_class = device_class
        self.native_unit_of_measurement = native_unit_of_measurement
        self.value = value
        self.format = format
