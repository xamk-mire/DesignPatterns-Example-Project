# Strategy — irrigation decisions

## Problem

A location needs one irrigation rule that can change without rewriting the evaluate path. The same moisture reading and the same zone thresholds should be able to wait under one rule and irrigate under another.

## Solution

`AutomationStrategy.decide` takes a `LocationAutomationContext` (location, zone, latest moisture, low, high) and returns a `Recommendation` (`irrigate` or `wait`, plus a reason). `get_strategy` returns `ConservativeMoistureStrategy` or `AggressiveMoistureStrategy`. Any other key raises before `decide`.

Conservative irrigates only when moisture is strictly below the zone low. Aggressive irrigates when moisture is below the midpoint `(low + high) / 2`. Missing moisture waits with the reason `no moisture sensor in this zone`.

`AutomationService.set_strategy` stores one key per location. `evaluate` loads that key, builds one context per zone from the newest `moisture_sensor` reading assigned to the zone, and calls `decide`. If any zone irrigates, the location action is `irrigate` and the reason names that zone. Otherwise the location waits. Strategies do not read the database.

## Where to look

| Piece | Path |
|-------|------|
| Context and recommendation | `backend/src/domain/automation/context.py` |
| Strategies | `backend/src/domain/automation/strategy.py` |
| Save and evaluate | `backend/src/application/automation/service.py` |
| HTTP | `PUT /api/locations/{location_id}/automation`, `POST /api/locations/{location_id}/automation/evaluate` |
| Panel | `frontend/src/components/automation/StrategyPanel.tsx` |

## Try this extension

Add a third key that irrigates only when moisture is below `low` and the zone schedule says watering is due. Register it in `get_strategy` and leave `evaluate` unchanged.
