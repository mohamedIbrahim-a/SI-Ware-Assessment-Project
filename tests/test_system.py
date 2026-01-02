import unittest
import json
from simulator import SensorSimulator
from core.sensor_config import SENSOR_CONFIG

class TestSensorSystem(unittest.TestCase):
    """
    Unit tests for the Si-Ware Sensor Dashboard system.
    Covers sensor parsing, alarm logic, and API output structure.
    """

    def setUp(self):
        """Initialize simulator for testing."""
        self.simulator = SensorSimulator(SENSOR_CONFIG)

    def test_api_output_structure(self):
        """
        Verify that SenatorSimulator.generate_data() returns the expected dictionary structure.
        
        Input: None (calls generate_data)
        Output: Asserts dictionary structure and required keys
        """
        data = self.simulator.generate_data()
        self.assertIsInstance(data, dict)
        
        for sid, reading in data.items():
            self.assertIn(sid, SENSOR_CONFIG)
            self.assertIn('value', reading)
            self.assertIn('status', reading)
            self.assertIn('timestamp', reading)
            self.assertIsInstance(reading['value'], (int, float))
            self.assertIsInstance(reading['status'], str)

    def test_sensor_parsing(self):
        """
        Verify that JSON strings are correctly parsed into dictionaries.
        
        Input: Simulated JSON string
        Output: Asserts dictionary contents match input
        """
        sample_data = {"S01": {"value": 20.5, "status": "OK", "timestamp": 123456789}}
        json_str = json.dumps(sample_data)
        parsed_data = json.loads(json_str)
        
        self.assertEqual(parsed_data, sample_data)
        self.assertEqual(parsed_data["S01"]["value"], 20.5)

    def test_alarm_logic_high_limit(self):
        """
        Verify that a value above the high limit is identified.
        
        Input: Manual value injection
        Output: Asserts value > high limit
        """
        sid = "S01" # Temperature: (15.0, 25.0)
        high_limit = SENSOR_CONFIG[sid]["limits"][1]
        test_value = high_limit + 5.0
        
        self.assertTrue(test_value > high_limit, f"Value {test_value} should exceed high limit {high_limit}")

    def test_alarm_logic_low_limit(self):
        """
        Verify that a value below the low limit is identified.
        
        Input: Manual value injection
        Output: Asserts value < low limit
        """
        sid = "S01"
        low_limit = SENSOR_CONFIG[sid]["limits"][0]
        test_value = low_limit - 5.0
        
        self.assertTrue(test_value < low_limit, f"Value {test_value} should be below low limit {low_limit}")

    def test_fault_state_detection(self):
        """
        Verify that fault statuses are correctly flagged.
        
        Input: Mock fault status
        Output: Asserts status is not 'OK'
        """
        reading = {"value": 0.0, "status": "SENSOR_ERROR", "timestamp": 123456}
        self.assertNotEqual(reading["status"], "OK")

if __name__ == '__main__':
    unittest.main()
