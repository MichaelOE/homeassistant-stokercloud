import voluptuous as vol

from homeassistant.const import CONF_USERNAME
import homeassistant.helpers.config_validation as cv

DOMAIN = "stokercloud"
DATA_SCHEMA = vol.Schema({vol.Required(CONF_USERNAME): cv.string})

MANUFACTURER = "NBE"
MODEL = "Stoker cloud boiler"

ALARM = {
    False: ["OK", "mdi:aalarm-light-outline"],
    True: ["ALARM", "mdi:alarm-light-outline"],
}

RUNNING = {
    False: ["IDLE", "mdi:radiator"],
    True: ["RUNNING", "mdi:radiator"],
}

STATE_STATE = {
    "state_2": ["IGNITION_1", "mdi:information"],
    "state_4": ["IGNITION_2", "mdi:information"],
    "state_5": ["POWER", "mdi:information"],
    "state_7": ["HOT_WATER", "mdi:information"],
    "state_13": ["FAULT_IGNITION", "mdi:information"],
    "state_14": ["OFF", "mdi:information"],
}

INFOMESSAGE = {
    "0": ["No info message", "mdi:information"],
    "13": ["Ash tray full", "mdi:information"],
    "24": ["Hopper content low", "mdi:information"],
}
