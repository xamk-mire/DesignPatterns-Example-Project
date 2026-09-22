# Device families — Abstract Factory

## Problem

A greenhouse site needs a matching **kit**: the same kinds of sensors and actuators, but with environment-specific labels and protocol hints (`simulation` vs stub `edge` hardware). Building those pieces with scattered constructors (or only Factory Method) makes it easy to mix a sim moisture sensor with an edge pump.

## Solution

**Abstract Factory:** `DeviceFamilyFactory.create_device_set()` returns a coherent list of domain `Device`s. `SimulationDeviceFactory` and `EdgeHardwareFactory` each produce two sensors and two actuators. Sensor *types* still come from Phase 2 Factory Method creators; the family factory tags them with `role`, `device_family`, and `protocol`.

## Versus Factory Method

| Pattern | Product |
|---------|---------|
| Factory Method | One sensor of a chosen type |
| Abstract Factory | A product **line** — sensors + actuators that belong together |

## Where to look

| Piece | Path |
|-------|------|
| `Device` | `backend/src/domain/devices/entity.py` |
| Family factories | `backend/src/domain/devices/family_factory.py` |
| Phase 2 creators (composed) | `backend/src/domain/sensors/creators.py` |
| DTO + mapper | `backend/src/application/devices/dto.py`, `mappers.py` |
| Service | `backend/src/application/devices/family_service.py` |
| HTTP | `backend/src/interfaces/api/devices.py` |
| UI | `frontend/src/components/devices/` |

`Device` is not an API DTO. The factory and repository never import Pydantic; the router maps with `devices_to_dtos`.

## Try this extension

Add a third family (for example `greenhouse-lab`) with its own `protocol` string and display-name prefix. Register it in `get_family_factory` — the provision endpoint should accept the new key without a new table.
