"""
Sensor Layer - Foundation of the Smart Home Energy Management System
Implements Observer pattern for sensor notifications and multiple sensor types
"""

import math
import random
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime, timedelta


class SensorSubject:
    """
    Base class implementing the Observer pattern for sensors.
    Manages registration and notification of observers.
    """
    
    def __init__(self):
        self._observers: List['SensorObserver'] = []
    
    def register_observer(self, observer: 'SensorObserver') -> None:
        """Register an observer to be notified of sensor changes."""
        if observer not in self._observers:
            self._observers.append(observer)
    
    def unregister_observer(self, observer: 'SensorObserver') -> None:
        """Unregister an observer."""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def notify_observers(self, sensor_data: Dict[str, Any]) -> None:
        """Notify all registered observers of sensor data."""
        for observer in self._observers:
            observer.update(sensor_data)


class SensorObserver(ABC):
    """
    Abstract base class for sensor observers.
    Other modules (e.g., control logic, logging) will implement this.
    """
    
    @abstractmethod
    def update(self, sensor_data: Dict[str, Any]) -> None:
        """
        Called when a sensor reading is available.
        
        Args:
            sensor_data: Dictionary containing sensor readings and metadata
        """
        pass


class TemperatureSensor(SensorSubject):
    """
    Temperature sensor that generates readings based on time of day.
    Uses a sine wave that peaks around 2PM to simulate realistic daily temperature variation.
    Adds random noise (±0.5°C) for realism.
    Range: 15–45°C
    """
    
    def __init__(self, base_temp: float = 20.0, room_name: str = "Unknown"):
        """
        Initialize temperature sensor.
        
        Args:
            base_temp: Base temperature for the room (default 20°C)
            room_name: Name of the room this sensor is in
        """
        super().__init__()
        self.base_temp = base_temp
        self.room_name = room_name
        self.min_temp = 15.0
        self.max_temp = 45.0
    
    def read(self, simulated_hour: float) -> float:
        """
        Generate a temperature reading based on time of day.
        
        Args:
            simulated_hour: Hour of day (0-24) in simulated time
        
        Returns:
            Temperature in Celsius
        """
        # Sine wave peaks at 14 (2PM), minimum at 2 (2AM)
        # Formula: base_temp + amplitude * sin((hour - 14) * π / 12)
        amplitude = (self.max_temp - self.min_temp) / 2
        
        # Calculate sine component (peaks at 14:00)
        sine_component = amplitude * math.sin((simulated_hour - 14) * math.pi / 12)
        
        # Add base temperature offset
        temp = self.base_temp + sine_component
        
        # Add random noise (±0.5°C)
        noise = random.uniform(-0.5, 0.5)
        temp += noise
        
        # Clamp to valid range
        temp = max(self.min_temp, min(self.max_temp, temp))
        
        # Notify observers
        sensor_data = {
            'sensor_type': 'temperature',
            'room': self.room_name,
            'value': round(temp, 2),
            'unit': '°C',
            'hour': simulated_hour
        }
        self.notify_observers(sensor_data)
        
        return round(temp, 2)


class PIRSensor(SensorSubject):
    """
    Passive Infrared (motion) sensor that detects room occupancy.
    Returns 1 (occupied) or 0 (empty).
    Uses probability based on time of day:
    - Night (10PM-6AM): 10% occupied
    - Work hours (6AM-5PM): 20% occupied
    - Evening (5PM-10PM): 80% occupied
    
    Once a room becomes occupied, it stays occupied for a random number of readings
    before re-evaluating occupancy probability.
    """
    
    def __init__(self, room_name: str = "Unknown"):
        """
        Initialize PIR sensor.
        
        Args:
            room_name: Name of the room this sensor is in
        """
        super().__init__()
        self.room_name = room_name
        self.is_occupied = False
        self.readings_until_reevaluate = 0
    
    def _get_occupancy_probability(self, simulated_hour: float) -> float:
        """
        Get occupancy probability based on time of day.
        
        Args:
            simulated_hour: Hour of day (0-24)
        
        Returns:
            Probability of occupancy (0.0-1.0)
        """
        if 22 <= simulated_hour or simulated_hour < 6:  # 10PM-6AM
            return 0.10
        elif 6 <= simulated_hour < 17:  # 6AM-5PM (work hours)
            return 0.20
        else:  # 5PM-10PM (evening)
            return 0.80
    
    def read(self, simulated_hour: float) -> int:
        """
        Generate a motion sensor reading.
        
        Args:
            simulated_hour: Hour of day (0-24) in simulated time
        
        Returns:
            1 if occupied, 0 if empty
        """
        # If we need to re-evaluate occupancy
        if self.readings_until_reevaluate <= 0:
            probability = self._get_occupancy_probability(simulated_hour)
            self.is_occupied = random.random() < probability
            
            # If occupied, stay occupied for 2-8 readings (10-40 minutes)
            if self.is_occupied:
                self.readings_until_reevaluate = random.randint(2, 8)
            else:
                # If empty, re-evaluate next reading
                self.readings_until_reevaluate = 1
        else:
            self.readings_until_reevaluate -= 1
        
        occupancy = 1 if self.is_occupied else 0
        
        # Notify observers
        sensor_data = {
            'sensor_type': 'pir',
            'room': self.room_name,
            'value': occupancy,
            'occupied': self.is_occupied,
            'hour': simulated_hour
        }
        self.notify_observers(sensor_data)
        
        return occupancy


class LDRSensor(SensorSubject):
    """
    Light Dependent Resistor (LDR) sensor that measures ambient light.
    Returns 0 (dark) to 1023 (bright).
    Follows a daylight curve:
    - Dark before 6AM
    - Peaks at noon
    - Dark after 6PM
    Adds realistic noise.
    """
    
    def __init__(self, room_name: str = "Unknown"):
        """
        Initialize LDR sensor.
        
        Args:
            room_name: Name of the room this sensor is in
        """
        super().__init__()
        self.room_name = room_name
        self.min_brightness = 0
        self.max_brightness = 1023
    
    def read(self, simulated_hour: float) -> int:
        """
        Generate a light level reading based on time of day.
        
        Args:
            simulated_hour: Hour of day (0-24) in simulated time
        
        Returns:
            Light level (0-1023)
        """
        # Daylight curve: peaks at 12 (noon), dark before 6AM and after 6PM
        # Using cosine for smooth curve
        
        if simulated_hour < 6 or simulated_hour > 18:
            # Dark period (before 6AM or after 6PM)
            brightness = self.min_brightness + random.uniform(-10, 10)
        elif 6 <= simulated_hour <= 18:
            # Daylight period
            # Cosine peaks at 12, is 0 at 6 and 18
            cosine_component = math.cos((simulated_hour - 12) * math.pi / 6)
            # Map from [-1, 1] to [0, 1023]
            brightness = (cosine_component + 1) / 2 * self.max_brightness
            
            # Add noise
            noise = random.uniform(-30, 30)
            brightness += noise
        else:
            brightness = self.min_brightness
        
        # Clamp to valid range
        brightness = max(self.min_brightness, min(self.max_brightness, brightness))
        brightness = int(brightness)
        
        # Notify observers
        sensor_data = {
            'sensor_type': 'ldr',
            'room': self.room_name,
            'value': brightness,
            'unit': '0-1023',
            'hour': simulated_hour
        }
        self.notify_observers(sensor_data)
        
        return brightness


class RoomSensors:
    """
    Bundles all three sensors for a single room.
    Provides a unified interface to read all sensors at once.
    """
    
    def __init__(self, room_name: str, base_temp: float = 20.0):
        """
        Initialize all sensors for a room.
        
        Args:
            room_name: Name of the room
            base_temp: Base temperature for the room
        """
        self.room_name = room_name
        self.temperature_sensor = TemperatureSensor(base_temp, room_name)
        self.pir_sensor = PIRSensor(room_name)
        self.ldr_sensor = LDRSensor(room_name)
    
    def register_observer(self, observer: SensorObserver) -> None:
        """
        Register an observer to all sensors in this room.
        
        Args:
            observer: Observer to register
        """
        self.temperature_sensor.register_observer(observer)
        self.pir_sensor.register_observer(observer)
        self.ldr_sensor.register_observer(observer)
    
    def read_all(self, simulated_hour: float) -> Dict[str, Any]:
        """
        Read all sensors for this room.
        
        Args:
            simulated_hour: Hour of day (0-24) in simulated time
        
        Returns:
            Dictionary with all sensor readings
        """
        readings = {
            'room': self.room_name,
            'hour': simulated_hour,
            'temperature': self.temperature_sensor.read(simulated_hour),
            'occupancy': self.pir_sensor.read(simulated_hour),
            'light_level': self.ldr_sensor.read(simulated_hour)
        }
        return readings
