# Location configuration — Builder

## Problem

A site is not one field. It is a location name plus one or more zones, and each zone needs moisture limits and a schedule that fit together. Saving a location row before those pieces are valid leaves a half-built site in PostgreSQL.

## Solution

**Builder:** `LocationConfigBuilder` collects the name and zones one call at a time. `build()` checks the whole configuration and returns a frozen `LocationConfig`, or raises `ConfigurationError`. The repository writes the location and its zones in one transaction only after `build()` succeeds.

## Versus the earlier factories

| Pattern | What it produces |
|---------|------------------|
| Factory Method | One sensor of a chosen type, ready immediately |
| Abstract Factory | A fixed device kit for one family |
| Builder | A location configuration assembled step by step, then validated |

## Where to look

| Piece | Path |
|-------|------|
| `Location`, `Zone`, `LocationConfig` | `backend/src/domain/locations/entity.py` |
| Builder | `backend/src/domain/locations/config_builder.py` |
| `ConfigurationError` | `backend/src/domain/locations/errors.py` |
| DTO + mapper | `backend/src/application/locations/dto.py`, `mappers.py` |
| Service | `backend/src/application/locations/config_service.py` |
| Assignment | `backend/src/application/locations/zone_assignment_service.py` |
| Persistence | `backend/src/infrastructure/persistence/location_repository.py` |
| HTTP | `backend/src/interfaces/api/locations.py` |
| UI | `frontend/src/components/config/LocationConfigWizard.tsx` |

Validation lives in `build()`, not in the router. The API only turns `ConfigurationError` into HTTP 400. `LocationConfig` is not the response DTO; `location_config_to_dto` adds `location_id` on each zone from the saved location.

Zones reference their location with **`location_id`**. That is the site key for later phases. There is no `greenhouse_id` column.

## Why assignment is not a builder method

Devices already exist from earlier phases, and a zone has no id until the configuration is saved. `LocationConfigBuilder` therefore stops at `build()`. Listing locations, deleting one, and adding, editing, or deleting a zone on a saved location are later updates. They reuse the same zone checks, but they do not call `build()`.

`ZoneAssignmentService` runs after a zone row exists: `PATCH /api/devices/{id}/zone` sends only `zone_id`, and the service copies `devices.location_id` from that zone in the same write. A null `zone_id` clears both columns. An unassigned device is left out of every zone list. Deleting a zone clears both columns on devices that were in it before the row is removed.

A zone name is unique inside one location and may be reused in another. The device picker lists every saved location and labels each option as the location name and the zone name.

## Try this extension

Add an optional light-hours window on each zone (`light_on`, `light_off`) and reject a window where the end is not after the start. Callers keep using `add_zone`; only `build()` grows a new check.
