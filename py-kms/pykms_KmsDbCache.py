#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KMS database cache for faster lookups and better error handling.
Caches application and SKU names to avoid repeated database searches.
"""

from __future__ import annotations

import uuid
import logging
from typing import Dict, Optional, Tuple
from pykms_DB2Dict import kmsDB2Dict

loggersrv = logging.getLogger("logsrv")


class KmsDbCache:
    """Cache for KMS database lookups to improve performance and reliability."""

    def __init__(self):
        """Initialize the cache."""
        self._app_cache: Dict[str, str] = {}  # UUID -> AppName
        self._sku_cache: Dict[str, str] = {}  # UUID -> SkuName
        self._loaded = False
        self._load_cache()

    def _load_cache(self) -> None:
        """Load and cache all SKU and Application names from database."""
        try:
            kmsdb = kmsDB2Dict()
            appitems = kmsdb[2]

            for appitem in appitems:
                try:
                    app_id = appitem.get("Id")
                    app_name = appitem.get("DisplayName", str(app_id))
                    if app_id:
                        self._app_cache[str(app_id)] = app_name
                except (KeyError, TypeError):
                    continue

                # Also cache all SKUs under this app
                try:
                    kmsitems = appitem.get("KmsItems", [])
                    for kmsitem in kmsitems:
                        skuitems = kmsitem.get("SkuItems", [])
                        for skuitem in skuitems:
                            try:
                                sku_id = skuitem.get("Id")
                                sku_name = skuitem.get("DisplayName", str(sku_id))
                                if sku_id:
                                    self._sku_cache[str(sku_id)] = sku_name
                            except (KeyError, TypeError):
                                continue
                except (KeyError, TypeError):
                    continue

            self._loaded = True
            loggersrv.debug(f"KMS cache loaded: {len(self._app_cache)} apps, {len(self._sku_cache)} SKUs")

        except Exception as e:
            loggersrv.warning(f"Failed to load KMS database cache: {e}")
            self._loaded = False

    def get_app_name(self, app_id: uuid.UUID) -> str:
        """
        Get application name by UUID.

        Args:
            app_id: Application UUID

        Returns:
            str: Application name or UUID string if not found
        """
        try:
            app_id_str = str(app_id)
            if app_id_str in self._app_cache:
                return self._app_cache[app_id_str]

            # If not in cache, try to search database
            if not self._loaded:
                self._load_cache()
                if app_id_str in self._app_cache:
                    return self._app_cache[app_id_str]

            loggersrv.debug(f"Application ID not found in database: {app_id}")
            return app_id_str

        except Exception as e:
            loggersrv.warning(f"Error looking up application name: {e}")
            return str(app_id)

    def get_sku_name(self, sku_id: uuid.UUID) -> str:
        """
        Get SKU name by UUID.

        Args:
            sku_id: SKU UUID

        Returns:
            str: SKU name or UUID string if not found
        """
        try:
            sku_id_str = str(sku_id)
            if sku_id_str in self._sku_cache:
                return self._sku_cache[sku_id_str]

            # If not in cache, try to search database
            if not self._loaded:
                self._load_cache()
                if sku_id_str in self._sku_cache:
                    return self._sku_cache[sku_id_str]

            loggersrv.debug(f"SKU ID not found in database: {sku_id}")
            return sku_id_str

        except Exception as e:
            loggersrv.warning(f"Error looking up SKU name: {e}")
            return str(sku_id)

    def get_both(self, app_id: uuid.UUID, sku_id: uuid.UUID) -> Tuple[str, str]:
        """
        Get both application and SKU names in one call.

        Args:
            app_id: Application UUID
            sku_id: SKU UUID

        Returns:
            Tuple[str, str]: (app_name, sku_name)
        """
        return (self.get_app_name(app_id), self.get_sku_name(sku_id))

    def refresh(self) -> None:
        """Refresh the cache by reloading from database."""
        self._app_cache.clear()
        self._sku_cache.clear()
        self._load_cache()


# Global cache instance
_kms_db_cache: Optional[KmsDbCache] = None


def get_cache() -> KmsDbCache:
    """Get or create the global KMS database cache."""
    global _kms_db_cache
    if _kms_db_cache is None:
        _kms_db_cache = KmsDbCache()
    return _kms_db_cache
