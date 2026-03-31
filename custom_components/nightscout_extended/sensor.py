"""Sensor platform for Nightscout Extended."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NightscoutExtendedCoordinator


@dataclass(frozen=True)
class NightscoutSensorEntityDescription(SensorEntityDescription):
    """Extend the base description with a coordinator data key."""
    data_key: str = ""


SENSOR_DESCRIPTIONS: tuple[NightscoutSensorEntityDescription, ...] = (
    NightscoutSensorEntityDescription(
        key="cage",
        data_key="cage",
        name="Cannula Age",
        icon="mdi:needle",
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NightscoutSensorEntityDescription(
        key="sage",
        data_key="sage",
        name="Sensor Age",
        icon="mdi:diabetes",
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NightscoutSensorEntityDescription(
        key="pump_battery",
        data_key="pump_battery",
        name="Pump Battery",
        icon="mdi:battery",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NightscoutSensorEntityDescription(
        key="pump_reservoir",
        data_key="pump_reservoir",
        name="Pump Reservoir",
        icon="mdi:water",
        native_unit_of_measurement="U",  # insulin units
        state_class=SensorStateClass.MEASUREMENT,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Nightscout Extended sensors from a config entry."""
    coordinator: NightscoutExtendedCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        NightscoutExtendedSensor(coordinator, description, entry)
        for description in SENSOR_DESCRIPTIONS
    )


class NightscoutExtendedSensor(CoordinatorEntity[NightscoutExtendedCoordinator], SensorEntity):
    """A single Nightscout Extended sensor."""

    entity_description: NightscoutSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: NightscoutExtendedCoordinator,
        description: NightscoutSensorEntityDescription,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        # Unique ID ensures HA tracks this entity across restarts
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        # Group all sensors under one device representing the Nightscout instance
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Nightscout Extended",
            "manufacturer": "Nightscout",
            "model": "CGM Remote Monitor",
            "configuration_url": entry.data.get("url"),
        }

    @property
    def native_value(self):
        """Return the current sensor value from coordinator data."""
        return self.coordinator.data.get(self.entity_description.data_key)
