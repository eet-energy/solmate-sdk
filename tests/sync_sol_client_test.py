"""Unit tests for the sync API Client."""

import unittest
import sys
import os

sys.path.append(os.path.abspath('.'))

from solmate_sdk import SolMateAPIClient


class BasicUsageTest(unittest.TestCase):
    """Basic Test Case"""

    serial_num = "test1"
    default_user_pw = None

    def test_online(self):
        """Try connecting to a client and check online status."""
        print(f"Check online status of solmate {self.serial_num}")
        client = SolMateAPIClient(self.serial_num)
        client.connect()
        print(client.check_online())

    def test_get_online_values(self):
        """Try initialising a client and get live values."""
        print(f"Try get live values of solmate {self.serial_num}")
        client = SolMateAPIClient(self.serial_num)
        client.quickstart(self.default_user_pw)
        print(f"Current live values of your SolMate: {client.get_live_values()}")

if __name__ == '__main__':
    unittest.main()