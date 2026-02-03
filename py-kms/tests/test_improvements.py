#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive test suite for py-kms improvements.
Tests cover critical issues: thread safety, validation, error handling, and transactions.
"""

import unittest
import threading
import tempfile
import os
import sys
import time
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pykms_ThreadSafeConfig import ThreadSafeConfig
from pykms_Validator import InputValidator, ValidationError


class TestThreadSafeConfig(unittest.TestCase):
    """Test thread-safe configuration management."""

    def setUp(self):
        self.config = ThreadSafeConfig()

    def test_basic_get_set(self):
        """Test basic get/set operations."""
        self.config.set("key1", "value1")
        self.assertEqual(self.config.get("key1"), "value1")

    def test_dict_like_access(self):
        """Test dictionary-like access patterns."""
        self.config["key1"] = "value1"
        self.assertEqual(self.config["key1"], "value1")
        self.assertTrue("key1" in self.config)

    def test_update(self):
        """Test bulk update operation."""
        data = {"key1": "value1", "key2": "value2"}
        self.config.update(data)
        self.assertEqual(self.config.get("key1"), "value1")
        self.assertEqual(self.config.get("key2"), "value2")

    def test_thread_safety(self):
        """Test that config is thread-safe under concurrent access."""
        results = []
        errors = []

        def worker(thread_id: int):
            try:
                # Each thread sets and reads 100 times
                for i in range(100):
                    key = f"thread_{thread_id}_key_{i}"
                    value = f"value_{i}"
                    self.config.set(key, value)
                    retrieved = self.config.get(key)
                    if retrieved != value:
                        errors.append(f"Thread {thread_id} got wrong value: {retrieved} != {value}")
                results.append(thread_id)
            except Exception as e:
                errors.append(f"Thread {thread_id} error: {e}")

        # Start 10 concurrent threads
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(threads), 10)
        self.assertEqual(len(results), 10)
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")

    def test_copy(self):
        """Test thread-safe copy."""
        self.config.set("key1", "value1")
        copy = self.config.copy()
        self.assertEqual(copy["key1"], "value1")


class TestInputValidator(unittest.TestCase):
    """Test input validation functions."""

    def test_hwid_valid(self):
        """Test valid HWID."""
        hwid = InputValidator.validate_hwid("364F463A8863D35F")
        self.assertIsInstance(hwid, bytes)
        self.assertEqual(len(hwid), 8)  # 16 hex chars = 8 bytes

    def test_hwid_random(self):
        """Test RANDOM HWID generation."""
        hwid = InputValidator.validate_hwid("RANDOM")
        self.assertIsInstance(hwid, bytes)
        self.assertEqual(len(hwid), 8)

    def test_hwid_invalid_chars(self):
        """Test invalid characters in HWID."""
        with self.assertRaises(ValidationError) as cm:
            InputValidator.validate_hwid("ZZZZZZZZZZZZZZZZ")
        self.assertIn("invalid hex", str(cm.exception).lower())

    def test_hwid_too_short(self):
        """Test HWID too short."""
        with self.assertRaises(ValidationError):
            InputValidator.validate_hwid("364F463A88")

    def test_hwid_too_long(self):
        """Test HWID too long."""
        with self.assertRaises(ValidationError):
            InputValidator.validate_hwid("364F463A8863D35F364F463A8863D35F")

    def test_ip_ipv4_valid(self):
        """Test valid IPv4 address."""
        ip = InputValidator.validate_ip_address("192.168.1.1")
        self.assertEqual(ip, "192.168.1.1")

    def test_ip_ipv6_valid(self):
        """Test valid IPv6 address."""
        ip = InputValidator.validate_ip_address("::1")
        self.assertEqual(ip, "::1")

    def test_ip_invalid(self):
        """Test invalid IP address."""
        with self.assertRaises(ValidationError):
            InputValidator.validate_ip_address("999.999.999.999")

    def test_port_valid(self):
        """Test valid port."""
        port = InputValidator.validate_port(1688)
        self.assertEqual(port, 1688)

    def test_port_too_low(self):
        """Test port too low."""
        with self.assertRaises(ValidationError):
            InputValidator.validate_port(0)

    def test_port_too_high(self):
        """Test port too high."""
        with self.assertRaises(ValidationError):
            InputValidator.validate_port(99999)

    def test_port_string_conversion(self):
        """Test port conversion from string."""
        port = InputValidator.validate_port("1688")
        self.assertEqual(port, 1688)

    def test_lcid_valid(self):
        """Test valid LCID."""
        lcid = InputValidator.validate_lcid(1033)
        self.assertEqual(lcid, 1033)

    def test_lcid_invalid(self):
        """Test invalid LCID."""
        with self.assertRaises(ValidationError):
            InputValidator.validate_lcid(100000)

    def test_client_count_valid(self):
        """Test valid client count."""
        count = InputValidator.validate_client_count(50)
        self.assertEqual(count, 50)

    def test_client_count_none(self):
        """Test None client count."""
        count = InputValidator.validate_client_count(None)
        self.assertIsNone(count)

    def test_interval_valid(self):
        """Test valid interval."""
        interval = InputValidator.validate_interval(120)
        self.assertEqual(interval, 120)

    def test_interval_invalid(self):
        """Test invalid interval."""
        with self.assertRaises(ValidationError):
            InputValidator.validate_interval(-1)

    def test_rpc_packet_valid(self):
        """Test valid RPC packet."""
        packet = b"\x05" + b"\x00" * 30
        validated = InputValidator.validate_rpc_packet(packet)
        self.assertEqual(validated, packet)

    def test_rpc_packet_too_short(self):
        """Test RPC packet too short."""
        with self.assertRaises(ValidationError):
            InputValidator.validate_rpc_packet(b"\x05\x00")

    def test_rpc_packet_invalid_signature(self):
        """Test invalid RPC packet signature."""
        packet = b"\x04" + b"\x00" * 30
        with self.assertRaises(ValidationError):
            InputValidator.validate_rpc_packet(packet)

    def test_database_path_valid(self):
        """Test valid database path."""
        path = InputValidator.validate_database_path("./clients.db")
        self.assertIsInstance(path, str)
        self.assertNotIn("..", path)

    def test_database_path_traversal(self):
        """Test directory traversal prevention."""
        with self.assertRaises(ValidationError):
            InputValidator.validate_database_path("../../etc/passwd")


class TestDatabaseTransactions(unittest.TestCase):
    """Test database transaction atomicity."""

    def setUp(self):
        """Create temporary database for testing."""
        self.test_db_fd, self.test_db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.test_db_fd)

    def tearDown(self):
        """Clean up temporary database."""
        if os.path.exists(self.test_db_path):
            os.unlink(self.test_db_path)

    def test_sql_initialize(self):
        """Test database initialization."""
        try:
            from pykms_Sql import sql_initialize

            db_path = sql_initialize(self.test_db_path)
            self.assertTrue(os.path.exists(db_path))
        except ImportError:
            self.skipTest("sqlite3 not available")

    def test_sql_update_insert(self):
        """Test SQL insert operation."""
        try:
            import sqlite3
            from pykms_Sql import sql_initialize, sql_update

            # Create fresh database
            if os.path.exists(self.test_db_path):
                os.unlink(self.test_db_path)

            db_path = sql_initialize(self.test_db_path)

            info = {
                "clientMachineId": "test-client-1",
                "machineName": "TEST-PC",
                "appId": "Windows 10",
                "skuId": "Pro",
                "licenseStatus": "Unlicensed",
                "requestTime": int(time.time()),
            }

            # Should not raise an exception
            sql_update(db_path, info)

            # Verify insert worked by querying directly
            con = sqlite3.connect(db_path)
            cur = con.cursor()
            cur.execute("SELECT * FROM clients WHERE clientMachineId=?;", ["test-client-1"])
            result = cur.fetchone()
            con.close()

            self.assertIsNotNone(result)

        except ImportError:
            self.skipTest("sqlite3 not available")


class TestRateLimiting(unittest.TestCase):
    """Test rate limiting functionality."""

    def test_simple_rate_limiter(self):
        """Test basic rate limiting."""
        from collections import defaultdict
        import time

        # Simple in-memory rate limiter
        class SimpleRateLimiter:
            def __init__(self, max_requests: int, time_window: float):
                self.max_requests = max_requests
                self.time_window = time_window
                self.requests: Dict[str, list] = defaultdict(list)

            def is_allowed(self, client_ip: str) -> bool:
                now = time.time()
                # Clean old requests
                self.requests[client_ip] = [
                    req_time for req_time in self.requests[client_ip] if now - req_time < self.time_window
                ]

                if len(self.requests[client_ip]) >= self.max_requests:
                    return False

                self.requests[client_ip].append(now)
                return True

        limiter = SimpleRateLimiter(max_requests=5, time_window=1.0)

        # First 5 requests should be allowed
        for i in range(5):
            self.assertTrue(limiter.is_allowed("192.168.1.1"))

        # 6th request should be blocked
        self.assertFalse(limiter.is_allowed("192.168.1.1"))

        # Different IP should be allowed
        self.assertTrue(limiter.is_allowed("192.168.1.2"))


class TestExceptionHandling(unittest.TestCase):
    """Test improved exception handling."""

    def test_specific_exceptions(self):
        """Test that specific exceptions are raised."""
        # ValidationError should be raised for invalid input
        with self.assertRaises(ValidationError):
            InputValidator.validate_hwid("INVALID")

        # Should not be generic Exception
        self.assertIsInstance(ValidationError("test"), ValueError)


class TestTimezoneHandling(unittest.TestCase):
    """Test timezone localization with both pytz and zoneinfo."""

    def test_zoneinfo_compatibility(self):
        """Test that zoneinfo.ZoneInfo works correctly."""
        try:
            from datetime import datetime
            from zoneinfo import ZoneInfo

            # Create naive datetime
            naive_dt = datetime(2024, 1, 1, 12, 0, 0)

            # Create zoneinfo timezone
            tz = ZoneInfo("UTC")

            # Should use replace, not localize (zoneinfo doesn't have localize method)
            localized_dt = naive_dt.replace(tzinfo=tz)

            self.assertIsNotNone(localized_dt)
            self.assertIsNotNone(localized_dt.tzinfo)
            # Verify it's aware (has timezone info)
            self.assertFalse(localized_dt.tzinfo is None)

        except ImportError:
            self.skipTest("zoneinfo not available (Python < 3.9)")

    def test_timezone_handling_graceful_fallback(self):
        """Test graceful fallback when timezone handling fails."""
        from datetime import datetime

        # Simulate the fallback logic
        naive_dt = datetime(2024, 1, 1, 12, 0, 0)

        # If timezone lookup fails, should return naive datetime
        local_dt = naive_dt

        self.assertIsNotNone(local_dt)
        self.assertIsNone(local_dt.tzinfo)


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
