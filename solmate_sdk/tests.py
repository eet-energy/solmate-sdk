"""Unit tests for the API Client."""

import unittest

from .apiclient import SolMateAPIClient


class BasicUsageTest(unittest.TestCase):
    """Basic Test Case"""

    def test_simplest_case(self):
        """Try initialising a client and get live values."""
        client = SolMateAPIClient("test1")
        client.connect("token")
        print(f"Current live values of your SolMate: {client.get_live_values()}")
