"""Pytest configuration: add py-kms package dir to path so tests can import pykms_* modules."""
import os
import sys

# tests/ may live at repo_root/tests (then py-kms is repo_root/py-kms) or inside py-kms/tests
_tests_dir = os.path.dirname(os.path.abspath(__file__))
_parent = os.path.dirname(_tests_dir)
_pykms = os.path.join(_parent, "py-kms") if os.path.isdir(os.path.join(_parent, "py-kms")) else _parent
if _pykms not in sys.path:
    sys.path.insert(0, _pykms)
