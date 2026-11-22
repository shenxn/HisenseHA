"""Read-only mappings for individually verified washer models."""

ASKO_W7106R_CN = "W7106R.W.CN"


def supports_asko_washer(model: str) -> bool:
    """Do not infer a protocol from a brand, display name or similar model."""
    return model.strip().upper() == ASKO_W7106R_CN


def _integer(value):
    """Cloud values are integer strings; placeholders must remain unknown."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            pass
    return None


def _flag(value):
    value = _integer(value)
    return bool(value) if value in (0, 1) else None


def parse_asko_w7106r(states: dict) -> dict:
    """Parse a full named-state snapshot, clearing absent/unsupported values.

    1004 was observed during a user-confirmed active wash with a decreasing
    remainWashTime. No specific wash phase or other state code is inferred.
    Online status is connectivity, never a substitute for power or door lock.
    """
    run_state = _integer(states.get("runStatus"))
    remaining = _integer(states.get("remainWashTime"))
    spin = _integer(states.get("dehydrationSpeed"))
    online = _flag(states.get("onlineStatus"))
    return {
        "model_profile": ASKO_W7106R_CN,
        "online": online,
        "machine_state": (
            None if run_state is None or online is False
            else "running" if run_state == 1004
            else f"unknown_{run_state}"
        ),
        "run_state": run_state,
        "remaining_minutes": remaining if remaining is not None and remaining >= 0 else None,
        "program": _integer(states.get("workMode")),
        "configured_spin": spin if spin is not None and spin >= 0 else None,
        "fault": _integer(states.get("fault")),
        "child_lock": _flag(states.get("childLock")),
        # These fields have not been validated on this model. In particular,
        # startStop is not assumed to mean power, pause or a physical door lock.
        "power_on": None,
        "gate_locked": None,
        "phase": None,
        "phase_label": None,
        "motor_speed": None,
        "temperature_raw": None,
        "configured_temperature": None,
        "dry_setting": None,
    }
