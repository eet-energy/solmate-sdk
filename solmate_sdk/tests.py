"""Unit tests for the API Client."""

import unittest
from .apiclient import SolMateAPIClient


class BasicUsageTest(unittest.TestCase):
    """Basic Test Case"""

    serial_num = "test1"

    def test_online(self):
        """Try connecting to a client and check online status."""
        print(f"Checking online status of SolMate {self.serial_num}")
        client = SolMateAPIClient(self.serial_num)
        client.connect()
        print(client.check_online())

    def test_get_online_values(self):
        """Try initialising a client and get live values."""
        print(f"Getting live values of SolMate {self.serial_num}")
        client = SolMateAPIClient(self.serial_num)
        client.quickstart()
        print(f"Live values: {client.get_live_values()}")
