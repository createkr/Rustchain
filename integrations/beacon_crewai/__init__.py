"""Beacon integration for CrewAI and LangGraph agent frameworks.

This package provides integration between the RustChain Beacon network
and popular AI agent frameworks, enabling:

- Cryptographic identity for AI agents
- Signed heartbeat attestations
- Message verification from other agents
- Contract participation with escrow
- Work completion attestations

Modules:
    beacon_crewai: CrewAI agent integration
    beacon_langgraph: LangGraph node integration
    beacon_config: Shared configuration
"""

from .beacon_config import BeaconConfig
from .beacon_crewai import BeaconAgent, create_beacon_crew, BEACON_SKILL_AVAILABLE, CREWAI_AVAILABLE
from .beacon_langgraph import (
    BeaconNode,
    BeaconConfig as LangGraphBeaconConfig,
    BeaconGraphState,
    create_beacon_graph,
    create_beacon_tools,
    BEACON_SKILL_AVAILABLE as LANGGRAPH_BEACON_SKILL_AVAILABLE,
    LANGGRAPH_AVAILABLE,
    LANGCHAIN_AVAILABLE,
)

__version__ = "0.1.0"
__all__ = [
    # Config
    "BeaconConfig",
    # CrewAI
    "BeaconAgent",
    "create_beacon_crew",
    "BEACON_SKILL_AVAILABLE",
    "CREWAI_AVAILABLE",
    # LangGraph
    "BeaconNode",
    "LangGraphBeaconConfig",
    "BeaconGraphState",
    "create_beacon_graph",
    "create_beacon_tools",
    "LANGGRAPH_BEACON_SKILL_AVAILABLE",
    "LANGGRAPH_AVAILABLE",
    "LANGCHAIN_AVAILABLE",
]
