"""Exercise real HA entities with a cloud-free coordinator snapshot."""

import asyncio
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from homeassistant.const import __version__
from homeassistant.core import HomeAssistant
from custom_components.hisense.pyhisenseapi import HiSenseWasher
from custom_components.hisense.sensor import HisenseWasherSensor, WASHER_SENSOR_DESCRIPTIONS


async def main():
    with tempfile.TemporaryDirectory() as config_dir:
        hass = HomeAssistant(config_dir)
        client = HiSenseWasher(
            wifi_id="test", device_id="test-device", refresh_token="", session=None,
            device_name="W7106R.W.CN", device_model="W7106R.W.CN",
        )
        client._update_from_states({
            "onlineStatus": "1", "remainWashTime": "25", "runStatus": "1004",
            "workMode": "1032", "dehydrationSpeed": "1600",
        })
        coordinator = SimpleNamespace(
            hass=hass, client=client, device_type="洗衣机", data=client.get_status(),
            last_update_success=True, last_success_time=datetime.now(timezone.utc),
        )
        description = next(d for d in WASHER_SENSOR_DESCRIPTIONS if d.key == "remaining_minutes")
        sensor = HisenseWasherSensor(coordinator, description)
        assert sensor.native_value == 25
        assert sensor.available
        assert sensor.unique_id == "remaining_minutes_test_device"
        assert sensor.device_info["identifiers"] == {("hisense", "test-device")}
        assert sensor.extra_state_attributes["run_state_code"] == 1004
        assert sensor.extra_state_attributes["last_read_time"]
        coordinator.data["online"] = False
        assert not sensor.available
        coordinator.data["online"] = True
        coordinator.last_update_success = False
        assert not sensor.available
        print(f"HA {__version__}: real entity values, identity, timestamps and availability passed")


asyncio.run(main())
