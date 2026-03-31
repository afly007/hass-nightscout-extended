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

from .const import (
    DOMAIN,
    KEY_CAGE,
    KEY_CAGE_STALE,
    KEY_PUMP_BATTERY,
    KEY_PUMP_RESERVOIR,
    KEY_SAGE,
    KEY_SAGE_STALE,
)
from .coordinator import NightscoutExtendedCoordinator


@dataclass(frozen=True)
class NightscoutSensorEntityDescription(SensorEntityDescription):
    """Extend the base description with coordinator data keys."""

    data_key: str = ""
    # When set, the coordinator stores a boolean at this key indicating whether
    # the value is stale (no record found within the lookback window).
    stale_key: str | None = None


SENSOR_DESCRIPTIONS: tuple[NightscoutSensorEntityDescription, ...] = (
    NightscoutSensorEntityDescription(
        key=KEY_CAGE,
        data_key=KEY_CAGE,
        stale_key=KEY_CAGE_STALE,
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
        name="Sensor Age",
        icon="mdi:diabetes",
        native_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    NightscoutSensorEntityDescription(
        key=KEY_PUMP_BATTERY,
        data_key=KEY_PUMP_BATTERY,
        name="Pump Battery",
        icon="mdi:battery",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    NightscoutSensorEntityDescription(
        key=KEY_PUMP_RESERVOIR,
        data_key=KEY_PUMP_RESERVOIR,
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
    def native_value(self) -> float | None:
        """Return the sensor value from coordinator data."""
        return self.coordinator.data.get(self.entity_description.data_key)

    @property
    def extra_state_attributes(self) -> dict[str, bool] | None:
        """Expose a ``data_available`` attribute for CAGE and SAGE sensors.

        Returns ``None`` for sensors that have no staleness concept (battery,
        reservoir). For CAGE and SAGE, ``data_available: false`` means no
        treatment record was found within the lookback window — either the entry
        is missing from Nightscout or the consumable is genuinely overdue.

        Useful in automations::

            state_attr('sensor.cannula_age', 'data_available') == false
        """
        stale_key = self.entity_description.stale_key
        if stale_key is None:
            return None
        return {"data_available": not self.coordinator.data.get(stale_key, True)}
