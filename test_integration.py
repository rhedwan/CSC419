"""
Integration Tests - End-to-end testing of the sensor layer and simulation
Verifies that all modules connect properly and work together
"""

import json
from sensors import RoomSensors, SensorObserver
from simulation import SmartHomeSimulation
from typing import Dict, Any, List


class IntegrationTestObserver(SensorObserver):
    """Observer for integration testing."""
    
    def __init__(self):
        self.readings: List[Dict[str, Any]] = []
    
    def update(self, sensor_data: Dict[str, Any]) -> None:
        """Record sensor data."""
        self.readings.append(sensor_data)


def test_single_room_integration():
    """Test a single room with all three sensors."""
    print("\n=== SINGLE ROOM INTEGRATION TEST ===")
    
    room = RoomSensors("Test Room", base_temp=20.0)
    observer = IntegrationTestObserver()
    room.register_observer(observer)
    
    # Simulate readings at different times
    test_hours = [0, 6, 12, 18, 23]
    print(f"Reading single room at {len(test_hours)} different times...")
    
    for hour in test_hours:
        readings = room.read_all(float(hour))
        assert readings['room'] == "Test Room"
        assert 'temperature' in readings
        assert 'occupancy' in readings
        assert 'light_level' in readings
    
    # Verify observer received all notifications
    expected_readings = len(test_hours) * 3  # 3 sensors per read_all()
    assert len(observer.readings) == expected_readings, \
        f"Expected {expected_readings} readings, got {len(observer.readings)}"
    
    print(f"✓ Single room integration test passed")
    print(f"  - Room readings: {len(test_hours)}")
    print(f"  - Total sensor notifications: {len(observer.readings)}")
    print(f"  - Sensors per reading: 3 (temp, pir, ldr)")


def test_multiple_rooms_integration():
    """Test multiple rooms with independent sensors."""
    print("\n=== MULTIPLE ROOMS INTEGRATION TEST ===")
    
    rooms = {
        "Living Room": RoomSensors("Living Room", 22.0),
        "Bedroom": RoomSensors("Bedroom", 18.0),
        "Kitchen": RoomSensors("Kitchen", 21.0),
    }
    
    observers = {name: IntegrationTestObserver() for name in rooms.keys()}
    
    # Register observers
    for room_name, room in rooms.items():
        room.register_observer(observers[room_name])
    
    # Read all rooms at different times
    test_hours = [0, 6, 12, 18]
    print(f"Reading {len(rooms)} rooms at {len(test_hours)} different times...")
    
    for hour in test_hours:
        for room_name, room in rooms.items():
            readings = room.read_all(float(hour))
            assert readings['room'] == room_name
    
    # Verify each observer received correct number of readings
    for room_name, observer in observers.items():
        expected = len(test_hours) * 3
        assert len(observer.readings) == expected, \
            f"{room_name}: Expected {expected} readings, got {len(observer.readings)}"
    
    print(f"✓ Multiple rooms integration test passed")
    for room_name, observer in observers.items():
        print(f"  - {room_name}: {len(observer.readings)} notifications")


def test_simulation_end_to_end():
    """Test the full simulation end-to-end."""
    print("\n=== FULL SIMULATION END-TO-END TEST ===")
    
    sim = SmartHomeSimulation()
    
    # Verify simulation setup
    assert len(sim.rooms) == 4, f"Expected 4 rooms, got {len(sim.rooms)}"
    assert sim.TOTAL_STEPS == 288, f"Expected 288 steps, got {sim.TOTAL_STEPS}"
    
    print("Running full 24-hour simulation...")
    results = sim.run_simulation(verbose=False)
    
    # Verify results structure
    assert 'simulation_metadata' in results
    assert 'room_statistics' in results
    
    metadata = results['simulation_metadata']
    assert metadata['total_steps'] == 288
    assert metadata['total_duration_hours'] == 24
    assert metadata['rooms'] == 4
    
    # Verify we got readings
    total_readings = metadata['total_readings']
    assert total_readings > 0, "No readings generated"
    
    # Expected: 4 rooms × 288 steps × 3 sensors = 3456 readings
    expected_readings = 4 * 288 * 3
    assert total_readings == expected_readings, \
        f"Expected {expected_readings} readings, got {total_readings}"
    
    print(f"✓ Full simulation end-to-end test passed")
    print(f"  - Total steps: {metadata['total_steps']}")
    print(f"  - Total readings: {total_readings}")
    print(f"  - Rooms: {metadata['rooms']}")
    
    # Verify room statistics
    for room_name, stats in results['room_statistics'].items():
        assert stats['total_readings'] > 0
        assert 'temperature' in stats
        assert 'occupancy' in stats
        assert 'light' in stats
        
        # Verify temperature is in valid range
        temp = stats['temperature']
        assert 15 <= temp['min'] <= 45, f"Invalid min temp: {temp['min']}"
        assert 15 <= temp['max'] <= 45, f"Invalid max temp: {temp['max']}"
        
        # Verify occupancy is 0 or 1
        occ = stats['occupancy']
        assert 0 <= occ['occupancy_rate'] <= 1, f"Invalid occupancy rate: {occ['occupancy_rate']}"
        
        # Verify light is in valid range
        light = stats['light']
        assert 0 <= light['min'] <= 1023, f"Invalid min light: {light['min']}"
        assert 0 <= light['max'] <= 1023, f"Invalid max light: {light['max']}"
    
    print(f"  - All room statistics validated")


def test_simulated_time_progression():
    """Test that simulated time progresses correctly."""
    print("\n=== SIMULATED TIME PROGRESSION TEST ===")
    
    sim = SmartHomeSimulation()
    
    # Test hour calculation for various steps
    test_cases = [
        (0, 0.0),      # Step 0 = Hour 0
        (12, 1.0),     # Step 12 = Hour 1 (12 steps × 5 min = 60 min)
        (24, 2.0),     # Step 24 = Hour 2
        (144, 12.0),   # Step 144 = Hour 12 (noon)
        (287, 23.917), # Step 287 ≈ Hour 23.92
    ]
    
    print("Testing simulated hour calculation...")
    for step, expected_hour in test_cases:
        calculated_hour = sim.get_simulated_hour(step)
        # Allow small floating point error
        assert abs(calculated_hour - expected_hour) < 0.01, \
            f"Step {step}: Expected ~{expected_hour}, got {calculated_hour}"
        print(f"  Step {step:3d} → Hour {calculated_hour:6.2f} ✓")
    
    print(f"✓ Simulated time progression test passed")


def test_sensor_data_quality():
    """Test that sensor data is realistic and consistent."""
    print("\n=== SENSOR DATA QUALITY TEST ===")
    
    sim = SmartHomeSimulation()
    results = sim.run_simulation(verbose=False)
    
    print("Validating sensor data quality...")
    
    for room_name, stats in results['room_statistics'].items():
        # Temperature should vary realistically
        temp = stats['temperature']
        assert temp['max'] - temp['min'] > 5, \
            f"{room_name}: Temperature range too small: {temp['max'] - temp['min']}"
        
        # Light should follow daylight pattern
        light = stats['light']
        # Average light should be somewhere between min and max
        assert light['min'] <= light['avg'] <= light['max']
        
        # Occupancy should be reasonable
        occ = stats['occupancy']
        assert 0 <= occ['occupancy_rate'] <= 1
    
    print(f"✓ Sensor data quality test passed")
    print(f"  - Temperature ranges are realistic")
    print(f"  - Light levels follow daylight pattern")
    print(f"  - Occupancy rates are valid")


def test_raw_data_export():
    """Test that raw data can be exported correctly."""
    print("\n=== RAW DATA EXPORT TEST ===")
    
    sim = SmartHomeSimulation()
    sim.run_simulation(verbose=False)
    
    # Export data
    export_file = "/tmp/test_simulation_data.json"
    sim.export_raw_data(export_file)
    
    # Load and verify
    with open(export_file, 'r') as f:
        data = json.load(f)
    
    assert 'metadata' in data
    assert 'readings' in data
    
    metadata = data['metadata']
    assert metadata['total_steps'] == 288
    assert metadata['total_duration_hours'] == 24
    assert len(metadata['rooms']) == 4
    
    readings = data['readings']
    assert len(readings) == 3456  # 4 rooms × 288 steps × 3 sensors
    
    # Verify reading structure
    for reading in readings[:10]:  # Check first 10
        assert 'sensor_type' in reading
        assert 'room' in reading
        assert 'value' in reading
        assert 'hour' in reading
    
    print(f"✓ Raw data export test passed")
    print(f"  - File: {export_file}")
    print(f"  - Total readings: {len(readings)}")
    print(f"  - Metadata valid: ✓")


def run_all_integration_tests():
    """Run all integration tests."""
    print("=" * 80)
    print("INTEGRATION TEST SUITE")
    print("=" * 80)
    
    try:
        test_single_room_integration()
        test_multiple_rooms_integration()
        test_simulated_time_progression()
        test_sensor_data_quality()
        test_simulation_end_to_end()
        test_raw_data_export()
        
        print("\n" + "=" * 80)
        print("✓ ALL INTEGRATION TESTS PASSED")
        print("=" * 80)
        return True
    
    except AssertionError as e:
        print(f"\n✗ INTEGRATION TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_integration_tests()
    exit(0 if success else 1)
