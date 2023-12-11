"""Unit tests for the async API Client."""

import unittest
import sys
import os

sys.path.append(os.path.abspath('.'))

from solmate_sdk import AsyncSolMateAPIClient


class BasicUsageTest(unittest.IsolatedAsyncioTestCase):
    """Basic Test Case"""

    serial_num = "test1"
    default_user_pw = None

    async def test_online(self):
        """Try connecting to a client, check online status and close."""
        print(f"Check online status of solmate {self.serial_num}")
        client = AsyncSolMateAPIClient(self.serial_num)
        await client.connect()
        print(await client.check_online())
        await client.close()

    async def test_get_online_values(self):
        """Try initialising a client and get live values."""
        print(f"Try get live values of solmate {self.serial_num}")
        client = AsyncSolMateAPIClient(self.serial_num)
        await client.quickstart(self.default_user_pw)
        print(f"Current live values of your SolMate: {await client.get_live_values()}")

if __name__ == '__main__':
    unittest.main()