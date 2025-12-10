from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberMode,
    callback,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfMass
from homeassistant.core import _LOGGER, HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import IntegrationNumberEntityDescription
from .const import DOMAIN, MANUFACTURER, MODEL


async def async_setup_entry(
    hass: HomeAssistant, config: ConfigEntry, async_add_entities
):
    """Set up the sensor platform."""
    stoker = hass.data[DOMAIN][config.entry_id]

    # Fetch initial data so we have data when entities subscribe
    # await CustomIntegration._coordinator.async_config_entry_first_refresh()

    entities: list[IntegrationNumber] = [
        IntegrationNumber(stoker, number) for number in NUMBER_SENSORS
    ]

    async_add_entities(entities)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    # Code for setting up your platform inside of the event loop
    _LOGGER.debug("async_setup_platform")

    @property
    def native_value(self):
        return self._attr_native_value

    async def async_set_native_value(self, value: float):
        self._attr_native_value = value
        # send value to device / API here
        self.async_write_ha_state()


class IntegrationNumber(CoordinatorEntity, NumberEntity):
    def __init__(
        self,
        client,
        number: IntegrationNumberEntityDescription,
    ):
        """Initialize the number."""
        super().__init__(client._coordinator)
        self._data = client
        self.coordinator = client._coordinator
        self.entity_description: IntegrationNumberEntityDescription = number
        self._attr_unique_id = f"{self.coordinator._alias}_{number.key}"
        self._attr_name = f"{self.coordinator._alias} {number.name}"

        self._attr_native_value = None
        # self._attr_min_value = None
        # self._attr_max_value = None
        # self._attr_step = number.step

    @property
    def device_info(self):
        """Return device information about this entity."""
        _LOGGER.debug("StokerCloudNumber: device_info")

        return {
            "identifiers": {(DOMAIN, self.coordinator._alias)},
            "manufacturer": MANUFACTURER,
            "model": MODEL,
            "name": self.coordinator._alias,
        }

    @property
    def should_poll(self):
        return False

    @property
    def friendly_name(self):
        return self.entity_description.name

    @property
    def native_value(self):
        return self._attr_native_value

    async def async_set_native_value(self, value: float):
        # send value to device / API here

        retval = await self.coordinator._api.update_controller_value(
            self.entity_description.updateParams[0],
            self.entity_description.updateParams[1],
            value,
        )

        self._attr_native_value = retval.value
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        data_available = False

        # if self.entity_description.key:
        if self.entity_description.key in self.coordinator.data:
            val = self.coordinator.data[self.entity_description.key]

            self._attr_native_value = val

            data_available = True
            self._attr_available = data_available
        else:
            _LOGGER.warning(
                f"The item {self.entity_description.key} is not returned from the 'cloud'"
            )

        # Only call async_write_ha_state if the state has changed
        if data_available:
            self.async_write_ha_state()


NUMBER_SENSORS: tuple[IntegrationNumberEntityDescription, ...] = (
    IntegrationNumberEntityDescription(
        key="frontdata_0_value",
        name="Hopper content",
        icon="mdi:information",
        native_min_value=0,
        native_max_value=250,
        native_step=1,
        mode=NumberMode.BOX,
        device_class=NumberDeviceClass.VOLUME,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        value=lambda data, key: data[key],
        updateParams=["hopper.content", "hopper.content"],
    ),
)
