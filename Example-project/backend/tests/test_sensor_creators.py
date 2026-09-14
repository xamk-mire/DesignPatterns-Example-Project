from domain.sensors.creators import LightSensorCreator, MoistureSensorCreator, get_creator


def test_moisture_creator_defaults() -> None:
    sensor = MoistureSensorCreator().create_sensor()
    assert sensor.device_type == "moisture_sensor"
    assert "moisture_threshold" in sensor.default_config
    assert sensor.default_config["unit"] == "vwc"


def test_light_creator_defaults() -> None:
    sensor = LightSensorCreator().create_sensor()
    assert sensor.device_type == "light_sensor"
    assert sensor.default_config["unit"] == "lux"
    moisture = MoistureSensorCreator().create_sensor()
    assert sensor.default_config["unit"] != moisture.default_config["unit"]


def test_unknown_type_raises() -> None:
    try:
        get_creator("temperature")
    except ValueError as exc:
        assert "Unknown sensor type" in str(exc)
    else:
        raise AssertionError("expected ValueError")
