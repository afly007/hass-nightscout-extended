"""Sensor platform for Nightscout Extended."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

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

from .const import (
    DOMAIN,
    KEY_CAGE,
    KEY_CAGE_STALE,
    KEY_CAGE_TIMESTAMP,
    KEY_LAST_READING,
    KEY_PUMP_BATTERY,
    KEY_PUMP_RESERVOIR,
    KEY_PUMP_TIMESTAMP,
    KEY_SAGE,
    KEY_SAGE_STALE,
    KEY_SAGE_TIMESTAMP,
)
from .coordinator import NightscoutExtendedCoordinator


@dataclass(frozen=True)
class NightscoutSensorEntityDescription(SensorEntityDescription):
    """Extend the base description with coordinator data keys."""

    data_key: str = ""
    # When set, the coordinator stores a boolean at this key that indicates
    # whether a record was found within the lookback window.
    stale_key: str | None = None
    # When set, the coordinator stores a datetime at this key that is exposed
    # as a ``last_reported`` attribute on the sensor.
    timestamp_key: str | None = None


SENSOR_DESCRIPTIONS: tuple[NightscoutSensorEntityDescription, ...] = (
    NightscoutSensorEntityDescription(
        key=KEY_CAGE,
        data_key=KEY_CAGE,
        stale_key=KEY_CAGE_STALE,
        timestamp_key=KEY_CAGE_TIMESTAMP,
        name="Cannula Age",
        icon="mdi:needle",
        native_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    NightscoutSensorEntityDescription(
        key=KEY_SAGE,
        data_key=KEY_SAGE,
        stale_key=KEY_SAGE_STALE,
        timestamp_key=KEY_SAGE_TIMESTAMP,
        name="Sensor Age",
        icon="mdi:diabetes",
        native_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    NightscoutSensorEntityDescription(
        key=KEY_LAST_READING,
        data_key=KEY_LAST_READING,
        name="CGM Last Reading",
        icon="mdi:clock-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    NightscoutSensorEntityDescription(
        key=KEY_PUMP_BATTERY,
        data_key=KEY_PUMP_BATTERY,
        timestamp_key=KEY_PUMP_TIMESTAMP,
        name="Pump Battery",
        icon="mdi:battery",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NightscoutSensorEntityDescription(
        key=KEY_PUMP_RESERVOIR,
        data_key=KEY_PUMP_RESERVOIR,
        timestamp_key=KEY_PUMP_TIMESTAMP,
        name="Pump Reservoir",
        icon="mdi:water",
        native_unit_of_measurement="U",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
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


class NightscoutExtendedSensor(
    CoordinatorEntity[NightscoutExtendedCoordinator], SensorEntity
):
    """A single Nightscout Extended sensor entity."""

    entity_description: NightscoutSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: NightscoutExtendedCoordinator,
        description: NightscoutSensorEntityDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialise the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Nightscout Extended",
            "manufacturer": "Nightscout",
            "model": "CGM Remote Monitor",
            "configuration_url": entry.data.get("url"),
        }

    @property
    def native_value(self) -> float | datetime | None:
        """Return the sensor value from coordinator data."""
        return self.coordinator.data.get(self.entity_description.data_key)

    @property
    def extra_state_attributes(self) -> dict | None:
        """Return additional attributes for this sensor.

        ``data_available`` (CAGE and SAGE only) — False when no treatment record
        was found within the lookback window, meaning the data is missing or the
        consumable is overdue.

        ``last_reported`` — the datetime when this value was last recorded in
        Nightscout. Useful for detecting connectivity or uploader issues:

            state_attr('sensor.cannula_age', 'last_reported')
        """
        attrs: dict = {}

        stale_key = self.entity_description.stale_key
        if stale_key is not None:
            attrs["data_available"] = not self.coordinator.data.get(stale_key, True)

        timestamp_key = self.entity_description.timestamp_key
        if timestamp_key is not None:
            attrs["last_reported"] = self.coordinator.data.get(timestamp_key)

        return attrs if attrs else None
