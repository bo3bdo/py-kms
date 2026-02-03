#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Input validation and security checks for py-kms."""

from __future__ import annotations

import os
import re
import binascii
from typing import Any


class ValidationError(ValueError):
    """Custom exception for validation failures."""

    pass


class InputValidator:
    """Validates various input types for py-kms."""

    @staticmethod
    def validate_hwid(hwid: str) -> bytes:
        """
        Validate HWID format.

        Args:
            hwid: HWID string (16 hex chars or "RANDOM")

        Returns:
            bytes: Validated HWID as bytes

        Raises:
            ValidationError: If HWID is invalid
        """
        if hwid == "RANDOM":
            import uuid

            randomhwid = uuid.uuid4().hex
            hwid = randomhwid[:16]

        # Strip 0x prefix if present
        if hwid.startswith("0x"):
            hwid = hwid[2:]

        # Validate hex characters only
        if not re.match(r"^[0-9a-fA-F]*$", hwid):
            invalid_chars = set(hwid) - set("0123456789abcdefABCDEF")
            raise ValidationError(f"HWID contains invalid hex characters: {invalid_chars}")

        # Validate length
        if len(hwid) % 2 != 0:
            raise ValidationError(f"HWID hex string has odd length: {len(hwid)}")
        if len(hwid) < 16:
            raise ValidationError(f"HWID hex string too short: {len(hwid)} < 16")
        if len(hwid) > 16:
            raise ValidationError(f"HWID hex string too long: {len(hwid)} > 16")

        try:
            return binascii.a2b_hex(hwid)
        except (binascii.Error, ValueError) as e:
            raise ValidationError(f"Failed to convert HWID to bytes: {e}") from e

    @staticmethod
    def validate_ip_address(ip: str) -> str:
        """
        Validate IPv4 or IPv6 address.

        Args:
            ip: IP address string

        Returns:
            str: Validated IP address

        Raises:
            ValidationError: If IP is invalid
        """
        import socket

        try:
            socket.inet_pton(socket.AF_INET, ip)
            return ip
        except (OSError, socket.error):
            try:
                socket.inet_pton(socket.AF_INET6, ip)
                return ip
            except (OSError, socket.error) as e:
                raise ValidationError(f"Invalid IP address: {ip}") from e

    @staticmethod
    def validate_port(port: int) -> int:
        """
        Validate port number.

        Args:
            port: Port number

        Returns:
            int: Validated port

        Raises:
            ValidationError: If port is invalid
        """
        if not isinstance(port, int):
            try:
                port = int(port)
            except (ValueError, TypeError) as e:
                raise ValidationError(f"Port must be integer: {port}") from e

        if port < 1 or port > 65535:
            raise ValidationError(f"Port out of range (1-65535): {port}")

        return port

    @staticmethod
    def validate_database_path(path: str) -> str:
        """
        Validate database file path (security check).

        Args:
            path: Path to database file

        Returns:
            str: Validated path

        Raises:
            ValidationError: If path is invalid/unsafe
        """
        # Prevent directory traversal
        if ".." in path:
            raise ValidationError(f"Path traversal attempt detected: {path}")

        # Get absolute path
        abs_path = os.path.abspath(path)

        # Check if path is trying to access outside safe directory
        if path.startswith("/") and not abs_path.startswith("/tmp") and not abs_path.startswith("/var/lib"):
            # Allow some common locations but warn about absolute paths
            if not os.path.exists(os.path.dirname(abs_path)):
                raise ValidationError(f"Database directory does not exist: {os.path.dirname(abs_path)}")

        return abs_path

    @staticmethod
    def validate_lcid(lcid: int) -> int:
        """
        Validate LCID (Locale ID).

        Args:
            lcid: LCID value

        Returns:
            int: Validated LCID

        Raises:
            ValidationError: If LCID is invalid
        """
        if not isinstance(lcid, int):
            try:
                lcid = int(lcid)
            except (ValueError, TypeError) as e:
                raise ValidationError(f"LCID must be integer: {lcid}") from e

        # Basic LCID validation (0x0000 to 0xFFFF)
        if lcid < 0 or lcid > 0xFFFF:
            raise ValidationError(f"LCID out of range (0-65535): {lcid}")

        return lcid

    @staticmethod
    def validate_client_count(count: int | None) -> int | None:
        """
        Validate client count.

        Args:
            count: Client count value

        Returns:
            int | None: Validated count

        Raises:
            ValidationError: If count is invalid
        """
        if count is None:
            return None

        if not isinstance(count, int):
            try:
                count = int(count)
            except (ValueError, TypeError) as e:
                raise ValidationError(f"Client count must be integer: {count}") from e

        if count < 0:
            raise ValidationError(f"Client count cannot be negative: {count}")

        return count

    @staticmethod
    def validate_interval(value: int, min_val: int = 1, max_val: int = 1000000) -> int:
        """
        Validate interval (activation, renewal, timeout).

        Args:
            value: Interval value in seconds/minutes
            min_val: Minimum allowed value
            max_val: Maximum allowed value

        Returns:
            int: Validated interval

        Raises:
            ValidationError: If interval is invalid
        """
        if not isinstance(value, int):
            try:
                value = int(value)
            except (ValueError, TypeError) as e:
                raise ValidationError(f"Interval must be integer: {value}") from e

        if value < min_val or value > max_val:
            raise ValidationError(f"Interval out of range ({min_val}-{max_val}): {value}")

        return value

    @staticmethod
    def validate_rpc_packet(data: bytes, min_size: int = 20) -> bytes:
        """
        Validate RPC packet structure.

        Args:
            data: RPC packet bytes
            min_size: Minimum expected packet size

        Returns:
            bytes: Validated packet data

        Raises:
            ValidationError: If packet is invalid
        """
        if not isinstance(data, bytes):
            raise ValidationError(f"RPC packet must be bytes, got {type(data)}")

        if len(data) < min_size:
            raise ValidationError(f"RPC packet too short: {len(data)} < {min_size}")

        # Check RPC header (first byte should be 0x05 for RPC)
        if data[0] != 0x05:
            raise ValidationError(f"Invalid RPC packet signature: {hex(data[0])}")

        return data
