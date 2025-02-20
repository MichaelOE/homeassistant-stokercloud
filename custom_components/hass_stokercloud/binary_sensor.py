"""Platform for binary_sensor integration."""

import logging

from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import IntegrationEntityDescription
from .const import ALARM, DOMAIN, MANUFACTURER, MODEL, RUNNING

# from .const import CLIMATE_CONTROL_STEERING_WHEEL_HEAT, DOMAIN, DOOR_LOCK, GEAR_IN_PARK

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    _LOGGER.debug("Setup sensors")

    my_data = hass.data[DOMAIN][entry.entry_id]

    entities: list[IntegrationSensor] = []

    # for sensor in SENSORS:
    entities: list[IntegrationSensor] = [
        IntegrationSensor(my_data._coordinator, sensor, my_data)
        for sensor in BINARY_SENSORS
    ]

    # Add entities to Home Assistant
    async_add_entities(entities)


class IntegrationSensor(CoordinatorEntity):
    """Sensor used by all entities, inherits from CoordinatorEntity."""

    def __init__(self, coordinator, sensor: IntegrationEntityDescription, client):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)
        self._data = client
        self._coordinator = coordinator
        self.entity_description = sensor
        self._attr_unique_id = f"{self.coordinator._alias}_{sensor.key}"
        self._attr_name = f"{self.coordinator._alias} {sensor.name}"

        _LOGGER.info(self._attr_unique_id)

        # if "climate_control_steering_wheel_heat" in self.entity_description.key:
        # self.options = LIST_CLIMATE_CONTROL_STEERING_WHEEL_HEAT
        # self.device_class = SensorDeviceClass.ENUM

    @property
    def device_info(self):
        """Return device information about this entity."""
        _LOGGER.debug("My Fisker: device_info")

        return {
            "identifiers": {(DOMAIN, self._coordinator._alias)},
            "manufacturer": MANUFACTURER,
            "model": MODEL,
            "name": self._coordinator._alias,
        }

    @property
    def icon(self):
        return self.entity_description.icon

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        if self.entity_description.key:
            val = self.coordinator.data[self.entity_description.key]

            self._attr_state = val

            if "alarm" in self.entity_description.key:
                self._attr_state = ALARM[val][0]
            elif "running" in self.entity_description.key:
                self._attr_state = RUNNING[val][0]

            data_available = True
            self._attr_available = data_available

        # Only call async_write_ha_state if the state has changed
        if data_available:
            self.async_write_ha_state()

    @property
    def should_poll(self):
        return False

    @property
    def state(self):
        try:
            state = self._attr_state
        except (KeyError, ValueError):
            return None
        return state


# Get an item by its key
def get_sensor_by_key(key):
    for sensor in BINARY_SENSORS:
        if sensor.key == key:
            return sensor
    return None


"""All binary_sensor entities."""

BINARY_SENSORS: tuple[SensorEntityDescription, ...] = (
    IntegrationEntityDescription(
        key="miscdata_running",
        name="Running",
        icon="mdi:radiator",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    IntegrationEntityDescription(
        key="miscdata_alarm",
        name="Alarm",
        icon="mdi:alarm-light-outline",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
)
