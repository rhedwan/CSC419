"""
Test suite for sensors.py
Verifies sensor behavior at different times of day and observer notifications
"""

from sensors import (
    SensorObserver, RoomSensors, TemperatureSensor, 
    PIRSensor, LDRSensor
)
from typing import Dict, Any


class TestObserver(SensorObserver):
    """Test observer that logs sensor readings."""
    
    def __init__(self, name: str = "TestObserver"):
        self.name = name
        self.readings = []
    
    def update(self, sensor_data: Dict[str, Any]) -> None:
        """Log sensor data when notified."""
        self.readings.append(sensor_data)
        print(f"  [{self.name}] {sensor_data['sensor_type'].upper()}: {sensor_data}")


def test_temperature_sensor():
    """Test temperature sensor at different times of day."""
    print("\n=== TEMPERATURE SENSOR TESTS ===")
    
    sensor = TemperatureSensor(base_temp=20.0, room_name="TestRoom")
    observer = TestObserver("TempObserver")
    sensor.register_observer(observer)
    
    test_hours = [0, 6, 12, 14, 18, 23]
    print("\nTesting temperature readings at different hours:")
    
    for hour in test_hours:
        temp = sensor.read(float(hour))
        print(f"Hour {hour:2d}: {temp}°C")
    
    # Verify readings are in valid range
    for reading in observer.readings:
        assert 15 <= reading['value'] <= 45, f"Temperature out of range: {reading['value']}"
    
    print(f"✓ All {len(observer.readings)} temperature readings in valid range (15-45°C)")


def test_pir_sensor():
    """Test PIR sensor at different times of day."""
    print("\n=== PIR SENSOR TESTS ===")
    
    sensor = PIRSensor(room_name="TestRoom")
    observer = TestObserver("PIRObserver")
    sensor.register_observer(observer)
    
    test_hours = [2, 6, 12, 18, 22]
    print("\nTesting occupancy at different hours (10 readings per hour):")
    
    occupancy_by_hour = {}
    for hour in test_hours:
        occupancy_by_hour[hour] = []
        for i in range(10):
            occupancy = sensor.read(float(hour))
            occupancy_by_hour[hour].append(occupancy)
        
        avg_occupancy = sum(occupancy_by_hour[hour]) / len(occupancy_by_hour[hour])
        print(f"Hour {hour:2d} (avg occupancy: {avg_occupancy:.1%}): {occupancy_by_hour[hour]}")
    
    # Verify readings are 0 or 1
    for reading in observer.readings:
        assert reading['value'] in [0, 1], f"Invalid occupancy value: {reading['value']}"
    
    print(f"✓ All {len(observer.readings)} PIR readings are valid (0 or 1)")


def test_ldr_sensor():
    """Test LDR sensor at different times of day."""
    print("\n=== LDR SENSOR TESTS ===")
    
    sensor = LDRSensor(room_name="TestRoom")
    observer = TestObserver("LDRObserver")
    sensor.register_observer(observer)
    
    test_hours = [0, 3, 6, 9, 12, 15, 18, 21, 23]
    print("\nTesting light levels at different hours:")
    
    for hour in test_hours:
        brightness = sensor.read(float(hour))
        day_phase = "NIGHT" if (hour < 6 or hour > 18) else "DAY"
        print(f"Hour {hour:2d} ({day_phase:5s}): {brightness:4d}")
    
    # Verify readings are in valid range
    for reading in observer.readings:
        assert 0 <= reading['value'] <= 1023, f"Light level out of range: {reading['value']}"
    
    # Verify night readings are low and day readings are higher
    night_readings = [r['value'] for r in observer.readings if r['hour'] < 6 or r['hour'] > 18]
    day_readings = [r['value'] for r in observer.readings if 6 <= r['hour'] <= 18]
    
    avg_night = sum(night_readings) / len(night_readings) if night_readings else 0
    avg_day = sum(day_readings) / len(day_readings) if day_readings else 0
    
    print(f"✓ All {len(observer.readings)} LDR readings in valid range (0-1023)")
    print(f"  Average night brightness: {avg_night:.0f}")
    print(f"  Average day brightness: {avg_day:.0f}")
    assert avg_day > avg_night, "Day brightness should be higher than night"


def test_room_sensors():
    """Test RoomSensors bundled class."""
    print("\n=== ROOM SENSORS TESTS ===")
    
    room = RoomSensors("Living Room", base_temp=22.0)
    observer = TestObserver("RoomObserver")
    room.register_observer(observer)
    
    print("\nReading all sensors for Living Room at different times:")
    
    test_hours = [0, 6, 12, 18, 23]
    for hour in test_hours:
        readings = room.read_all(float(hour))
        print(f"\nHour {hour:2d}:")
        print(f"  Temperature: {readings['temperature']}°C")
        print(f"  Occupancy: {readings['occupancy']} (occupied={readings['occupancy']==1})")
        print(f"  Light Level: {readings['light_level']}")
    
    print(f"\n✓ RoomSensors.read_all() returned {len(observer.readings)} total readings")
    print(f"  (3 readings per hour × {len(test_hours)} hours)")


def test_observer_notifications():
    """Test that observer notifications fire correctly."""
    print("\n=== OBSERVER NOTIFICATION TESTS ===")
    
    sensor = TemperatureSensor(base_temp=20.0, room_name="NotificationTest")
    observer1 = TestObserver("Observer1")
    observer2 = TestObserver("Observer2")
    
    sensor.register_observer(observer1)
    sensor.register_observer(observer2)
    
    print("\nRegistering 2 observers and reading sensor 3 times:")
    for i in range(3):
        sensor.read(float(i))
    
    assert len(observer1.readings) == 3, f"Observer1 should have 3 readings, got {len(observer1.readings)}"
    assert len(observer2.readings) == 3, f"Observer2 should have 3 readings, got {len(observer2.readings)}"
    
    print(f"✓ Observer1 received {len(observer1.readings)} notifications")
    print(f"✓ Observer2 received {len(observer2.readings)} notifications")
    
    # Test unregister
    sensor.unregister_observer(observer1)
    sensor.read(float(3))
    
    assert len(observer1.readings) == 3, "Observer1 should not receive new readings after unregister"
    assert len(observer2.readings) == 4, "Observer2 should receive new reading"
    
    print(f"✓ After unregistering Observer1:")
    print(f"  Observer1 still has {len(observer1.readings)} readings (no new ones)")
    print(f"  Observer2 now has {len(observer2.readings)} readings (got new one)")


def run_all_tests():
    """Run all sensor tests."""
    print("=" * 60)
    print("SENSOR LAYER TEST SUITE")
    print("=" * 60)
    
    try:
        test_temperature_sensor()
        test_pir_sensor()
        test_ldr_sensor()
        test_room_sensors()
        test_observer_notifications()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        return True
    
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
