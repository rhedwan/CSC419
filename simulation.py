"""
Simulation Engine - Main simulation loop for 24-hour smart home energy management
Runs 288 steps (5-minute intervals) with 4 rooms, reading all sensors and logging data
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
from sensors import RoomSensors, SensorObserver


class SimulationLogger(SensorObserver):
    """
    Logs all sensor readings during simulation.
    Implements SensorObserver to receive notifications from sensors.
    """
    
    def __init__(self):
        self.readings: List[Dict[str, Any]] = []
    
    def update(self, sensor_data: Dict[str, Any]) -> None:
        """Log sensor data when notified."""
        self.readings.append(sensor_data)
    
    def get_readings(self) -> List[Dict[str, Any]]:
        """Get all logged readings."""
        return self.readings
    
    def get_readings_for_room(self, room_name: str) -> List[Dict[str, Any]]:
        """Get all readings for a specific room."""
        return [r for r in self.readings if r.get('room') == room_name]


class SmartHomeSimulation:
    """
    Main simulation engine for the smart home energy management system.
    Simulates 24 hours (288 steps at 5-minute intervals) with 4 rooms.
    """
    
    # Simulation parameters
    TOTAL_STEPS = 288  # 24 hours × 60 minutes / 5 minutes per step
    STEP_DURATION_MINUTES = 5
    TOTAL_HOURS = 24
    
    # Room configuration: (name, base_temperature)
    ROOMS = [
        ("Living Room", 22.0),
        ("Bedroom", 18.0),
        ("Kitchen", 21.0),
        ("Study", 20.0),
    ]
    
    def __init__(self):
        """Initialize the simulation with 4 rooms."""
        self.rooms: Dict[str, RoomSensors] = {}
        self.logger = SimulationLogger()
        self.simulation_data: Dict[str, Any] = {}
        
        # Initialize rooms
        for room_name, base_temp in self.ROOMS:
            room = RoomSensors(room_name, base_temp)
            room.register_observer(self.logger)
            self.rooms[room_name] = room
    
    def get_simulated_hour(self, step: int) -> float:
        """
        Convert step number to simulated hour of day.
        
        Args:
            step: Step number (0-287)
        
        Returns:
            Hour of day (0.0-24.0)
        """
        minutes_elapsed = step * self.STEP_DURATION_MINUTES
        hour = (minutes_elapsed / 60.0) % self.TOTAL_HOURS
        return hour
    
    def run_simulation(self, verbose: bool = False) -> Dict[str, Any]:
        """
        Run the full 24-hour simulation.
        
        Args:
            verbose: If True, print progress at each step
        
        Returns:
            Dictionary with simulation results and statistics
        """
        print("=" * 80)
        print("SMART HOME ENERGY MANAGEMENT SYSTEM - 24 HOUR SIMULATION")
        print("=" * 80)
        print(f"\nSimulation Parameters:")
        print(f"  Total Steps: {self.TOTAL_STEPS} (5-minute intervals)")
        print(f"  Total Duration: {self.TOTAL_HOURS} hours")
        print(f"  Rooms: {len(self.rooms)}")
        print(f"  Rooms: {', '.join([r[0] for r in self.ROOMS])}")
        print()
        
        # Run simulation loop
        print("Running simulation...")
        for step in range(self.TOTAL_STEPS):
            simulated_hour = self.get_simulated_hour(step)
            
            # Read all sensors for all rooms
            for room_name, room in self.rooms.items():
                room.read_all(simulated_hour)
            
            # Print progress every 24 steps (2 hours)
            if verbose and step % 24 == 0:
                print(f"  Step {step:3d} / {self.TOTAL_STEPS} (Hour {simulated_hour:5.1f})")
        
        print(f"✓ Simulation complete. Processed {self.TOTAL_STEPS} steps.\n")
        
        # Analyze results
        return self._analyze_results()
    
    def _analyze_results(self) -> Dict[str, Any]:
        """
        Analyze simulation results and generate statistics.
        
        Returns:
            Dictionary with analysis results
        """
        results = {
            'simulation_metadata': {
                'total_steps': self.TOTAL_STEPS,
                'step_duration_minutes': self.STEP_DURATION_MINUTES,
                'total_duration_hours': self.TOTAL_HOURS,
                'rooms': len(self.rooms),
                'total_readings': len(self.logger.readings)
            },
            'room_statistics': {}
        }
        
        # Analyze each room
        for room_name in self.rooms.keys():
            room_readings = self.logger.get_readings_for_room(room_name)
            stats = self._analyze_room(room_name, room_readings)
            results['room_statistics'][room_name] = stats
        
        return results
    
    def _analyze_room(self, room_name: str, readings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze sensor data for a single room.
        
        Args:
            room_name: Name of the room
            readings: List of sensor readings for this room
        
        Returns:
            Dictionary with room statistics
        """
        # Separate readings by sensor type
        temp_readings = [r for r in readings if r['sensor_type'] == 'temperature']
        pir_readings = [r for r in readings if r['sensor_type'] == 'pir']
        ldr_readings = [r for r in readings if r['sensor_type'] == 'ldr']
        
        stats = {
            'total_readings': len(readings),
            'temperature': self._analyze_temperature(temp_readings),
            'occupancy': self._analyze_occupancy(pir_readings),
            'light': self._analyze_light(ldr_readings)
        }
        
        return stats
    
    def _analyze_temperature(self, readings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze temperature readings."""
        if not readings:
            return {}
        
        values = [r['value'] for r in readings]
        return {
            'readings': len(values),
            'min': min(values),
            'max': max(values),
            'avg': round(sum(values) / len(values), 2),
            'range': round(max(values) - min(values), 2)
        }
    
    def _analyze_occupancy(self, readings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze occupancy readings."""
        if not readings:
            return {}
        
        values = [r['value'] for r in readings]
        occupied_count = sum(values)
        total_count = len(values)
        occupancy_rate = occupied_count / total_count if total_count > 0 else 0
        
        return {
            'readings': total_count,
            'occupied_count': occupied_count,
            'empty_count': total_count - occupied_count,
            'occupancy_rate': round(occupancy_rate, 3)
        }
    
    def _analyze_light(self, readings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze light level readings."""
        if not readings:
            return {}
        
        values = [r['value'] for r in readings]
        return {
            'readings': len(values),
            'min': min(values),
            'max': max(values),
            'avg': round(sum(values) / len(values), 1),
            'range': max(values) - min(values)
        }
    
    def print_summary(self, results: Dict[str, Any]) -> None:
        """
        Print a formatted summary of simulation results.
        
        Args:
            results: Results dictionary from run_simulation()
        """
        print("=" * 80)
        print("SIMULATION RESULTS SUMMARY")
        print("=" * 80)
        
        metadata = results['simulation_metadata']
        print(f"\nSimulation Metadata:")
        print(f"  Total Steps: {metadata['total_steps']}")
        print(f"  Total Duration: {metadata['total_duration_hours']} hours")
        print(f"  Rooms: {metadata['rooms']}")
        print(f"  Total Readings: {metadata['total_readings']}")
        
        print(f"\n{'Room':<20} {'Temp (°C)':<15} {'Occupancy':<15} {'Light (0-1023)':<15}")
        print("-" * 65)
        
        for room_name, stats in results['room_statistics'].items():
            temp_stat = stats['temperature']
            occ_stat = stats['occupancy']
            light_stat = stats['light']
            
            temp_str = f"{temp_stat['min']:.1f}-{temp_stat['max']:.1f} (avg {temp_stat['avg']})"
            occ_str = f"{occ_stat['occupancy_rate']:.1%}"
            light_str = f"{light_stat['min']}-{light_stat['max']} (avg {light_stat['avg']:.0f})"
            
            print(f"{room_name:<20} {temp_str:<15} {occ_str:<15} {light_str:<15}")
        
        print("\n" + "=" * 80)
        print("DETAILED ROOM STATISTICS")
        print("=" * 80)
        
        for room_name, stats in results['room_statistics'].items():
            print(f"\n{room_name}:")
            print(f"  Total Readings: {stats['total_readings']}")
            
            if stats['temperature']:
                temp = stats['temperature']
                print(f"  Temperature:")
                print(f"    Min: {temp['min']}°C")
                print(f"    Max: {temp['max']}°C")
                print(f"    Avg: {temp['avg']}°C")
                print(f"    Range: {temp['range']}°C")
            
            if stats['occupancy']:
                occ = stats['occupancy']
                print(f"  Occupancy:")
                print(f"    Occupied: {occ['occupied_count']} readings ({occ['occupancy_rate']:.1%})")
                print(f"    Empty: {occ['empty_count']} readings ({1-occ['occupancy_rate']:.1%})")
            
            if stats['light']:
                light = stats['light']
                print(f"  Light Level:")
                print(f"    Min: {light['min']}")
                print(f"    Max: {light['max']}")
                print(f"    Avg: {light['avg']:.0f}")
                print(f"    Range: {light['range']}")
    
    def export_raw_data(self, filename: str = "simulation_data.json") -> None:
        """
        Export all raw sensor readings to a JSON file.
        
        Args:
            filename: Output filename
        """
        data = {
            'metadata': {
                'total_steps': self.TOTAL_STEPS,
                'step_duration_minutes': self.STEP_DURATION_MINUTES,
                'total_duration_hours': self.TOTAL_HOURS,
                'rooms': list(self.rooms.keys()),
                'total_readings': len(self.logger.readings)
            },
            'readings': self.logger.readings
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✓ Raw data exported to {filename}")


def main():
    """Main entry point for the simulation."""
    # Create and run simulation
    sim = SmartHomeSimulation()
    results = sim.run_simulation(verbose=True)
    
    # Print summary
    sim.print_summary(results)
    
    # Export raw data
    sim.export_raw_data("simulation_data.json")
    
    return results


if __name__ == "__main__":
    main()
