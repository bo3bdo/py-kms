"""Tests for JSON config serialization (daemon config)."""
import json

import pykms_Server as srv


def test_config_to_json_serializable_excludes_operation():
    """Operation key is omitted from serialized config."""
    config = {"operation": "start", "ip": "0.0.0.0", "port": 1688}
    out = srv._config_to_json_serializable(config)
    assert "operation" not in out
    assert out.get("ip") == "0.0.0.0"
    assert out.get("port") == 1688


def test_config_to_json_serializable_bytes_to_hex():
    """Bytes (e.g. hwid) are serialized as hex string."""
    config = {"hwid": b"\x36\x4F\x46\x3A\x88\x63\xD3\x5F", "ip": "0.0.0.0"}
    out = srv._config_to_json_serializable(config)
    assert isinstance(out["hwid"], str)
    assert out["hwid"] == "364f463a8863d35f" or out["hwid"] == "364F463A8863D35F"
    assert json.dumps(out)  # must be JSON-serializable
