"""Model dispatch and parsing tests, using sanitized real cloud fields."""

import asyncio
import importlib
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import AsyncMock

# Import the real API module without executing the HA setup module. No API or
# parser is stubbed; only the package loader is supplied for standalone tests.
ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "hisense_test_package"
package = types.ModuleType(PACKAGE)
package.__path__ = [str(ROOT / "custom_components" / "hisense")]
sys.modules[PACKAGE] = package
api = importlib.import_module(f"{PACKAGE}.pyhisenseapi")

# Device/account identifiers and household names intentionally excluded.
RUNNING = {
    "onlineStatus": "1", "remainWashTime": "26", "workMode": "1032",
    "runStatus": "1004", "startStop": "1", "dehydrationSpeed": "1600",
    "fault": "0", "childLock": "0",
}


def washer(model="W7106R.W.CN"):
    return api.HiSenseWasher(
        wifi_id="test-wifi", device_id="test-device", refresh_token="",
        session=None, access_token="test-token", device_model=model,
    )


class AskoWasherTest(unittest.TestCase):
    def test_real_running_snapshot_and_countdown(self):
        client = washer()
        for minutes in (26, 25):
            client._update_from_states({**RUNNING, "remainWashTime": str(minutes)})
            status = client.get_status()
            self.assertEqual(status["remaining_minutes"], minutes)
            self.assertEqual(status["machine_state"], "running")
            self.assertEqual(status["program"], 1032)
            self.assertEqual(status["configured_spin"], 1600)
            self.assertFalse(status["child_lock"])
            self.assertEqual(status["fault"], 0)
            for key in ("power_on", "gate_locked", "phase_label", "motor_speed"):
                self.assertIsNone(status[key])

    def test_missing_fields_clear_previous_snapshot(self):
        client = washer()
        client._update_from_states(RUNNING)
        client._update_from_states({"onlineStatus": "1"})
        for key in ("remaining_minutes", "machine_state", "program", "configured_spin", "fault", "child_lock"):
            self.assertIsNone(client.status[key], key)

    def test_invalid_minutes_and_flags_stay_unknown(self):
        for value in ("--", "", "NaN", "3.5", -1, None, True):
            client = washer()
            client._update_from_states({**RUNNING, "remainWashTime": value})
            self.assertIsNone(client.status["remaining_minutes"])
        client._update_from_states({**RUNNING, "childLock": "2"})
        self.assertIsNone(client.status["child_lock"])

    def test_zero_remaining_does_not_mean_complete(self):
        client = washer()
        client._update_from_states({**RUNNING, "remainWashTime": "0", "runStatus": "1999"})
        self.assertEqual(client.status["remaining_minutes"], 0)
        self.assertEqual(client.status["machine_state"], "unknown_1999")

    def test_offline_does_not_claim_running_or_power_off(self):
        client = washer()
        client._update_from_states({**RUNNING, "onlineStatus": "0"})
        self.assertFalse(client.status["online"])
        self.assertIsNone(client.status["machine_state"])
        self.assertIsNone(client.status["power_on"])

    def test_exact_model_only(self):
        for model in ("", "W7106R.W", "W7106R.W.UK", "Other_W7106R.W.CN"):
            client = washer(model)
            client._update_from_states(RUNNING)
            self.assertNotIn("model_profile", client.status)
            self.assertNotIn("remaining_minutes", client.status)
        client = washer(" w7106r.w.cn ")
        client._update_from_states(RUNNING)
        self.assertEqual(client.status["remaining_minutes"], 26)

    def test_existing_named_hisense_washer_is_unchanged(self):
        client = washer("WF100E5Q")
        client._update_from_states({
            "powerStatus": "1", "runStatus": "1", "startPauseStatus": "0",
            "remainRunTime": "42", "washTemperature": "40", "doorLockStatus": "1",
        })
        self.assertEqual(client.status["remaining_minutes"], 42)
        self.assertEqual(client.status["machine_state"], "running")
        self.assertTrue(client.status["gate_locked"])
        self.assertEqual(client.status["configured_temperature"], "temperature_40_c")

    def test_legacy_array_not_applied_to_asko(self):
        values = [0] * 110
        values[9], values[8], values[11], values[29] = 1, 1, 4, 35
        result = {"payload": {"deviceStatus": values}}
        self.assertFalse(washer()._update_status_from_result(result))
        legacy = washer("WF100E5Q")
        self.assertTrue(legacy._update_status_from_result(result))
        self.assertEqual(legacy.status["remaining_minutes"], 35)
        self.assertEqual(legacy.status["phase_label"], "main_wash")

    def test_real_check_status_dispatch(self):
        async def run():
            client = washer()
            client._post = AsyncMock(return_value={"payload": {"device": {"states": RUNNING}}})
            result = await client.check_status()
            self.assertEqual(result["remaining_minutes"], 26)
            self.assertEqual(client._post.await_args.args[3], "/4.0/iot/devices/detail")
        asyncio.run(run())

    def test_control_paths_never_send(self):
        async def run():
            client = washer()
            client._post = AsyncMock()
            self.assertFalse(await client._send_aihome_action("start", {}))
            self.assertFalse(await client._send_aihome_label("power", 1))
            client._post.assert_not_called()
        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
