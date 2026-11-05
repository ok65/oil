import pytest


def test_maturo_turntable_reads_and_moves_to_position(maturo_turntable_driver, monkeypatch):
    monkeypatch.setattr("oil.positioners.maturo.time.sleep", lambda _: None)
    driver, virtual, _ = maturo_turntable_driver

    assert driver.position == 0.0
    driver.move_to(45.5)

    assert abs(driver.position - 45.5) <= 0.5
    assert driver.busy is False
    assert "CW" in virtual.command_log
    assert "ST" in virtual.command_log
    assert "LD 45.5 DG NP GO" not in virtual.command_log
    assert virtual.read_memory("prologix.mode") == 1
    assert virtual.read_memory("prologix.gpib_address") == 7
    assert virtual.read_memory("prologix.auto_read") is False


def test_maturo_turntable_sets_speed_limits_and_stops(maturo_turntable_driver):
    driver, virtual, _ = maturo_turntable_driver

    driver.speed = 5
    driver.clockwise_limit = 350
    driver.counterclockwise_limit = -150
    driver.move_clockwise()
    driver.stop()

    assert driver.speed == 5
    assert driver.clockwise_limit == 350
    assert driver.counterclockwise_limit == -150
    assert virtual.read_memory("position.degrees") == 0
    assert virtual.read_memory("position.busy") is False
    assert "LD 5 SP" in virtual.command_log
    assert "CW" in virtual.command_log
    assert "ST" in virtual.command_log


def test_maturo_move_to_selects_counterclockwise_and_stops(maturo_turntable_driver, monkeypatch):
    monkeypatch.setattr("oil.positioners.maturo.time.sleep", lambda _: None)
    driver, virtual, _ = maturo_turntable_driver
    virtual.write_memory("position.degrees", 20.0)

    driver.move_to(-10)

    assert "CC" in virtual.command_log
    assert "ST" in virtual.command_log
    assert virtual.read_memory("position.degrees") < 20
    assert virtual.read_memory("position.degrees") > -11
    assert virtual.read_memory("position.busy") is False


def test_maturo_move_to_already_at_target_does_not_start_motion(maturo_turntable_driver):
    driver, virtual, _ = maturo_turntable_driver
    virtual.write_memory("position.degrees", 10.2)

    driver.move_to(10.0)

    assert "CW" not in virtual.command_log
    assert "CC" not in virtual.command_log
    assert "ST" in virtual.command_log


def test_maturo_move_to_uses_coarse_then_fine_speed(maturo_turntable_driver, monkeypatch):
    monkeypatch.setattr("oil.positioners.maturo.time.sleep", lambda _: None)
    driver, virtual, _ = maturo_turntable_driver
    virtual.write_memory("position.virtual_step.degrees", 1.0)

    driver.move_to(20, speed=5)

    speed_writes = [command for command in virtual.command_log if command.endswith(" SP")]
    assert speed_writes == ["LD 5 SP", "LD 1 SP"]
    assert virtual.command_log.count("CW") == 2
    assert virtual.command_log.count("ST") == 2
    assert abs(driver.position - 20) <= 0.5


def test_maturo_turntable_rejects_out_of_range_targets_without_moving(maturo_turntable_driver):
    driver, virtual, _ = maturo_turntable_driver
    driver.clockwise_limit = 300

    with pytest.raises(ValueError, match="outside configured turntable limits"):
        driver.move_to(350)
    with pytest.raises(ValueError, match=r"between -200 and \+400"):
        driver.move_to(-201)

    assert virtual.read_memory("position.degrees") == 0.0
    assert "LD -201.0 DG NP" not in virtual.command_log


def test_maturo_turntable_validates_speed_and_device_address(monkeypatch):
    from oil.positioners import MaturoTurntable

    with pytest.raises(ValueError, match="speed"):
        MaturoTurntable._validate_speed(9)
    with pytest.raises(ValueError, match="device_address"):
        MaturoTurntable._validate_device_address(6)
