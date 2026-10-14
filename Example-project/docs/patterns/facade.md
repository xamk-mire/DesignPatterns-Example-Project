# Facade — location overview

## Problem

The dashboard needs one picture of a location: its zones, the devices assigned to those zones, each device’s newest reading, the saved irrigation key, and the recommendation that key would make now. Those facts already live in locations, devices, sensor readings, and automation rules. The overview route should not reach into each of those stores itself.

## Solution

`GET /api/locations/{location_id}/overview` calls only `LocationOverviewFacade.get_overview`. The handler does not import device, reading, or automation repositories.

The facade loads the location, assigned devices, and one newest reading per device, then asks `AutomationService.evaluate` for `last_recommendation` when a strategy key is saved. It does not reimplement `decide`. When no key is saved, `strategy_key` and `last_recommendation` are null and the request still succeeds. A missing location is 404.

Assigned devices are those with this `location_id` and a `zone_id`. Unassigned devices are omitted from counts, zone device lists, and readings.

No new table. Existing tables are enough; there is no overview SQL view.

## N+1

Assigned devices are one query. Newest readings are one `DISTINCT ON (device_id)` query. `evaluate` still looks up moisture once per zone, because that path belongs to the strategy service and locations have few zones.

## Where to look

| Piece | Path |
|-------|------|
| Read model | `backend/src/application/overview/dto.py` |
| Facade | `backend/src/application/overview/facade.py` |
| HTTP | `GET /api/locations/{location_id}/overview` |
| Panel | `frontend/src/components/overview/OverviewPanel.tsx` |

## Try this extension

Add family counts beside sensor and actuator counts inside the facade. Leave the route handler as a single call to `get_overview`.
