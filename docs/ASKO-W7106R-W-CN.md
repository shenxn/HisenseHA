# ASKO W7106R.W.CN — read-only China-cloud adapter

This personal fork retains the `hisense` domain, config entries, device identifiers,
and all existing entity unique IDs. It does not add washer controls.

## Verified scope

The adapter matches only the exact configured model `W7106R.W.CN` (case and
surrounding whitespace ignored). Similar models and overseas variants keep the
upstream parser. Existing entries obtain this model from their stored
`device_name`; a nickname is not treated as a model match.

Two real named-state cloud responses during an active wash on 2026-11-22 contained:

| Cloud field | Observation | HA mapping |
| --- | --- | --- |
| `remainWashTime` | 26, then 25 approximately one minute later | Existing remaining-time sensor, minutes |
| `runStatus` | 1004 during the reported active wash | Existing run-state sensor: `running` |
| `workMode` | 1032 | Existing program-code sensor, numeric code |
| `dehydrationSpeed` | 1600 | Existing configured-spin sensor, rpm |
| `onlineStatus` | 1 | Availability; never interpreted as power |
| `childLock`, `fault` | 0 | Existing child-lock and fault sensors |

The countdown behavior supports a minute interpretation; comparison with the
physical panel/App is still needed to establish whether it covers the whole
cycle or only the wash stage. The meaning of program 1032 and specific phase
represented by state 1004 are not established. Other state codes remain
`unknown_<code>`; zero remaining minutes alone never means cycle complete.

Power, door lock, actual motor speed, temperature, drying and wash phase stay
unknown until this model's semantics are verified. Missing values and cloud
placeholders clear previous values rather than displaying stale readings.
Offline responses make normal sensors unavailable. The legacy 00f byte-array
decoder is never applied to this ASKO model.

## Refresh behavior

The upstream on-demand refresh policy is retained. Use the existing Force refresh
button for a new cloud read. This release does **not** add periodic cloud polling
or a fabricated local countdown. Sensors include `last_read_time` and the raw
`run_state_code` to distinguish a stored snapshot from a new read. A reliable
completion notification needs separately verified completion codes and a tested
refresh strategy; it is not claimed by this release.

## Installation and validation

Back up the installed `custom_components/hisense` directory and registry/config
before changing the update source to `shenxn/HisenseHA`. The release zip contains
the contents of that component directory. Keep the existing integration entry;
do not delete and recreate the device. A Core restart is required after replacing
Python modules. Updating files alone is not runtime verification.

After restart, check the existing remaining-time, run-state and configured-spin
entities and their timestamps against a fresh cloud read and the appliance panel.
The standalone regression suite uses sanitized state fields, no household IDs or
credentials: `python -m unittest discover -s tests -v` (requires `cryptography`).
