"""
BoTTube MCP Server

Model Context Protocol server for BoTTube AI video platform.
"""

__version__ = "1.0.0"
__author__ = "RustChain Contributors"
__email__ = "scott@rustchain.org"

from .bottube_mcp_server import BoTTubeMCP, main

__all__ = ["BoTTubeMCP", "main"]
