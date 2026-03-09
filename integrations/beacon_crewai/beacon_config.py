"""Shared Beacon configuration.

This module provides a single source of truth for BeaconConfig,
used by both CrewAI and LangGraph integrations.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional


@dataclass
class BeaconConfig:
    """Configuration for Beacon integration."""
    agent_id: str
    beacon_host: str = "127.0.0.1"
    beacon_port: int = 38400
    data_dir: Optional[Path] = None
    use_mnemonic: bool = False
    broadcast_heartbeats: bool = False
    heartbeat_interval_seconds: int = 60
    known_keys: Optional[Dict[str, str]] = None  # agent_id -> pubkey mapping
