import pytest

from domain.locations.config_builder import LocationConfigBuilder
from domain.locations.errors import ConfigurationError


def test_build_success() -> None:
    config = (
        LocationConfigBuilder()
        .with_location_name("  Lab Site A  ")
        .add_zone("Bench 1", 0.2, 0.45, {"watering": "08:00"})
        .add_zone("Bench 2", 0.0, 1.0)
        .build()
    )
    assert config.location.name == "Lab Site A"
    assert config.location.id is None
    assert len(config.location.zones) == 2
    assert config.location.zones[0].schedule == {"watering": "08:00"}
    assert config.location.zones[1].schedule == {}


def test_build_requires_name() -> None:
    builder = LocationConfigBuilder().add_zone("Bench 1", 0.2, 0.45)
    with pytest.raises(ConfigurationError, match="Location name is required"):
        builder.build()
    with pytest.raises(ConfigurationError, match="Location name is required"):
        LocationConfigBuilder().with_location_name("   ").add_zone("Bench 1", 0.2, 0.45).build()


def test_build_requires_zones() -> None:
    with pytest.raises(ConfigurationError, match="At least one zone is required"):
        LocationConfigBuilder().with_location_name("Lab Site A").build()


def test_build_rejects_duplicate_zone_names() -> None:
    with pytest.raises(ConfigurationError, match="unique within the location"):
        (
            LocationConfigBuilder()
            .with_location_name("Lab")
            .add_zone("Bench 1", 0.2, 0.4)
            .add_zone("  Bench 1  ", 0.3, 0.5)
            .build()
        )


def test_build_rejects_invalid_thresholds() -> None:
    with pytest.raises(ConfigurationError, match="strictly less than high"):
        LocationConfigBuilder().with_location_name("Lab").add_zone("Bench", 0.6, 0.2).build()
    with pytest.raises(ConfigurationError, match="strictly less than high"):
        LocationConfigBuilder().with_location_name("Lab").add_zone("Bench", 0.4, 0.4).build()
    with pytest.raises(ConfigurationError, match="between 0 and 1"):
        LocationConfigBuilder().with_location_name("Lab").add_zone("Bench", -0.1, 0.4).build()
    with pytest.raises(ConfigurationError, match="between 0 and 1"):
        LocationConfigBuilder().with_location_name("Lab").add_zone("Bench", 0.2, 1.2).build()
