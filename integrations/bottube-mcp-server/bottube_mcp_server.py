#!/usr/bin/env python3
"""
BoTTube MCP Server

Model Context Protocol (MCP) server that exposes BoTTube AI video platform
capabilities to AI assistants, including video management, analytics, and
agent economy integration.

Usage:
    python bottube_mcp_server.py

Or via npx (for MCP clients):
    npx -y @modelcontextprotocol/server-python bottube-mcp-server
"""

import asyncio
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import logging

# MCP SDK
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Tool,
        Resource,
        ResourceTemplate,
        Prompt,
        TextContent,
    )
except ImportError:
    print("Error: MCP SDK not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)

# HTTP client for API calls
try:
    import aiohttp
except ImportError:
    print("Error: aiohttp not installed. Run: pip install aiohttp", file=sys.stderr)
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger('bottube-mcp')

# Configuration
BOTTUBE_BASE_URL = os.getenv('BOTTUBE_BASE_URL', 'https://bottube.ai')
BOTTUBE_API_KEY = os.getenv('BOTTUBE_API_KEY', '')
RUSTCHAIN_API_BASE = os.getenv('RUSTCHAIN_API_BASE', 'https://50.28.86.131')


@dataclass
class VideoInfo:
    video_id: str
    title: str
    description: str
    duration: int
    views: int
    creator: str
    created_at: str
    is_public: bool


@dataclass
class AgentInfo:
    agent_id: str
    name: str
    videos_count: int
    total_views: int
    earnings_rtc: float
    status: str


class BoTTubeMCP:
    """BoTTube MCP Server implementation."""

    def __init__(self):
        self.app = Server("bottube-mcp")
        self.session: Optional[aiohttp.ClientSession] = None
        self._setup_handlers()

    async def start(self):
        """Initialize HTTP session."""
        headers = {"User-Agent": "BoTTube-MCP-Server/1.0"}
        if BOTTUBE_API_KEY:
            headers["Authorization"] = f"Bearer {BOTTUBE_API_KEY}"
        
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers=headers
        )
        logger.info("BoTTube MCP Server started")

    async def stop(self):
        """Cleanup resources."""
        if self.session:
            await self.session.close()
        logger.info("BoTTube MCP Server stopped")

    def _setup_handlers(self):
        """Setup MCP request handlers."""

        # List available tools
        @self.app.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="get_video_info",
                    description="Get information about a BoTTube video by ID",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "video_id": {
                                "type": "string",
                                "description": "Video ID or URL"
                            }
                        },
                        "required": ["video_id"]
                    }
                ),
                Tool(
                    name="list_videos",
                    description="List videos with optional filters",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent": {
                                "type": "string",
                                "description": "Filter by agent ID"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of videos (default: 20)"
                            },
                            "cursor": {
                                "type": "string",
                                "description": "Pagination cursor"
                            }
                        }
                    }
                ),
                Tool(
                    name="get_feed",
                    description="Get personalized video feed",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "cursor": {
                                "type": "string",
                                "description": "Pagination cursor for next page"
                            },
                            "category": {
                                "type": "string",
                                "description": "Filter by category"
                            }
                        }
                    }
                ),
                Tool(
                    name="get_agent_info",
                    description="Get information about a BoTTube AI agent",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent_id": {
                                "type": "string",
                                "description": "Agent ID or name"
                            }
                        },
                        "required": ["agent_id"]
                    }
                ),
                Tool(
                    name="get_agent_analytics",
                    description="Get detailed analytics for an AI agent",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent_id": {
                                "type": "string",
                                "description": "Agent ID"
                            },
                            "timeframe": {
                                "type": "string",
                                "description": "Time period: day, week, month (default: week)"
                            }
                        },
                        "required": ["agent_id"]
                    }
                ),
                Tool(
                    name="upload_video",
                    description="Upload a video to BoTTube (requires API key)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Video title"
                            },
                            "description": {
                                "type": "string",
                                "description": "Video description"
                            },
                            "is_public": {
                                "type": "boolean",
                                "description": "Whether video is public (default: true)"
                            },
                            "dry_run": {
                                "type": "boolean",
                                "description": "Validate without uploading (default: true)"
                            }
                        },
                        "required": ["title"]
                    }
                ),
                Tool(
                    name="get_premium_videos",
                    description="Get premium/export videos (requires API key)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "description": "Maximum videos to return (default: 50)"
                            },
                            "format": {
                                "type": "string",
                                "description": "Export format: mp4, webm, hls"
                            }
                        }
                    }
                ),
                Tool(
                    name="check_health",
                    description="Check BoTTube API health status",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="get_bridge_info",
                    description="Get RTC/wRTC bridge information",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "chain": {
                                "type": "string",
                                "description": "Blockchain: solana, base (default: solana)"
                            }
                        }
                    }
                ),
                Tool(
                    name="calculate_agent_earnings",
                    description="Calculate agent earnings from video views",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "views": {
                                "type": "integer",
                                "description": "Total video views"
                            },
                            "duration_seconds": {
                                "type": "integer",
                                "description": "Total video duration in seconds"
                            },
                            "engagement_rate": {
                                "type": "number",
                                "description": "Engagement rate 0-1 (default: 0.5)"
                            }
                        },
                        "required": ["views"]
                    }
                )
            ]

        # List available resources
        @self.app.list_resources()
        async def list_resources() -> List[Resource]:
            return [
                Resource(
                    uri="bottube://health",
                    name="BoTTube Health Status",
                    description="Current API health and status",
                    mimeType="application/json"
                ),
                Resource(
                    uri="bottube://feed/trending",
                    name="Trending Videos Feed",
                    description="Currently trending videos on BoTTube",
                    mimeType="application/json"
                ),
                Resource(
                    uri="bottube://agents/active",
                    name="Active AI Agents",
                    description="List of active AI agents and their stats",
                    mimeType="application/json"
                ),
                Resource(
                    uri="bottube://bridge/rtc",
                    name="RTC Bridge Info",
                    description="Information about RTC/wRTC bridging",
                    mimeType="application/json"
                ),
                Resource(
                    uri="bottube://docs/quickstart",
                    name="BoTTube Quickstart Guide",
                    description="How to get started with BoTTube",
                    mimeType="text/markdown"
                )
            ]

        # List resource templates
        @self.app.list_resource_templates()
        async def list_resource_templates() -> List[ResourceTemplate]:
            return [
                ResourceTemplate(
                    uriTemplate="bottube://video/{video_id}",
                    name="Video Information",
                    description="Get detailed information about a specific video"
                ),
                ResourceTemplate(
                    uriTemplate="bottube://agent/{agent_id}",
                    name="Agent Information",
                    description="Get information about a specific AI agent"
                ),
                ResourceTemplate(
                    uriTemplate="bottube://agent/{agent_id}/analytics",
                    name="Agent Analytics",
                    description="Get analytics for a specific AI agent"
                ),
                ResourceTemplate(
                    uriTemplate="bottube://category/{category}",
                    name="Category Videos",
                    description="Get videos in a specific category"
                )
            ]

        # List available prompts
        @self.app.list_prompts()
        async def list_prompts() -> List[Prompt]:
            return [
                Prompt(
                    name="analyze_agent_performance",
                    description="Analyze an AI agent's performance and provide optimization suggestions",
                    arguments=[
                        {
                            "name": "agent_id",
                            "description": "Agent ID to analyze",
                            "required": True
                        }
                    ]
                ),
                Prompt(
                    name="video_upload_strategy",
                    description="Get recommendations for optimal video upload strategy",
                    arguments=[
                        {
                            "name": "content_type",
                            "description": "Type of content (educational, entertainment, news)",
                            "required": False
                        },
                        {
                            "name": "target_audience",
                            "description": "Target audience demographic",
                            "required": False
                        }
                    ]
                ),
                Prompt(
                    name="earnings_optimization",
                    description="Get suggestions to maximize agent earnings",
                    arguments=[
                        {
                            "name": "current_views",
                            "description": "Current monthly views",
                            "required": False
                        },
                        {
                            "name": "content_niche",
                            "description": "Content niche or category",
                            "required": False
                        }
                    ]
                )
            ]

        # Handle tool calls
        @self.app.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            handler = getattr(self, f'_tool_{name}', None)
            if not handler:
                raise ValueError(f"Unknown tool: {name}")

            try:
                result = await handler(arguments)
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                logger.error(f"Tool error {name}: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]

        # Handle resource reads
        @self.app.read_resource()
        async def read_resource(uri: str) -> tuple[str, str]:
            try:
                result = await self._read_resource_impl(uri)
                return result
            except Exception as e:
                logger.error(f"Resource error {uri}: {e}")
                raise

    async def _read_resource_impl(self, uri: str) -> tuple[str, str]:
        """Read resource implementation."""
        if uri == "bottube://health":
            data = await self._check_health_impl()
            return json.dumps(data, indent=2), "application/json"

        elif uri == "bottube://feed/trending":
            data = await self._get_feed_impl(None, "trending")
            return json.dumps(data, indent=2), "application/json"

        elif uri == "bottube://agents/active":
            data = await self._get_active_agents_impl()
            return json.dumps(data, indent=2), "application/json"

        elif uri == "bottube://bridge/rtc":
            data = await self._get_bridge_info_impl("solana")
            return json.dumps(data, indent=2), "application/json"

        elif uri == "bottube://docs/quickstart":
            content = self._get_quickstart_guide()
            return content, "text/markdown"

        # Handle templates
        elif uri.startswith("bottube://video/"):
            video_id = uri.split("/")[-1]
            data = await self._get_video_info_impl(video_id)
            return json.dumps(data, indent=2), "application/json"

        elif uri.startswith("bottube://agent/"):
            parts = uri.split("/")
            agent_id = parts[-1]
            if len(parts) > 3 and parts[-2] == "analytics":
                data = await self._get_agent_analytics_impl(agent_id, "week")
            else:
                data = await self._get_agent_info_impl(agent_id)
            return json.dumps(data, indent=2), "application/json"

        elif uri.startswith("bottube://category/"):
            category = uri.split("/")[-1]
            data = await self._list_videos_impl(None, 20, None, category)
            return json.dumps(data, indent=2), "application/json"

        raise ValueError(f"Unknown resource: {uri}")

    # Tool implementations

    async def _tool_check_health(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Check API health."""
        return await self._check_health_impl()

    async def _check_health_impl(self) -> Dict[str, Any]:
        """Check health implementation."""
        try:
            url = f"{BOTTUBE_BASE_URL}/health"
            async with self.session.get(url) as resp:
                return {
                    "status": resp.status,
                    "ok": resp.ok,
                    "timestamp": int(time.time()),
                    "service": "bottube"
                }
        except Exception as e:
            return {
                "status": 0,
                "ok": False,
                "error": str(e),
                "timestamp": int(time.time())
            }

    async def _tool_get_video_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get video information."""
        video_id = args.get("video_id", "")
        return await self._get_video_info_impl(video_id)

    async def _get_video_info_impl(self, video_id: str) -> Dict[str, Any]:
        """Get video info implementation."""
        url = f"{BOTTUBE_BASE_URL}/api/videos/{video_id}"
        
        try:
            async with self.session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {"found": True, "video": data}
                elif resp.status == 404:
                    return {"found": False, "video_id": video_id, "error": "Video not found"}
                else:
                    return {"error": f"API error: {resp.status}"}
        except Exception as e:
            return {"error": f"Failed to fetch video: {str(e)}"}

    async def _tool_list_videos(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List videos."""
        agent = args.get("agent")
        limit = args.get("limit", 20)
        cursor = args.get("cursor")
        category = args.get("category")
        
        return await self._list_videos_impl(agent, limit, cursor, category)

    async def _list_videos_impl(self, agent: Optional[str] = None,
                                 limit: int = 20,
                                 cursor: Optional[str] = None,
                                 category: Optional[str] = None) -> Dict[str, Any]:
        """List videos implementation."""
        params = {"limit": min(limit, 100)}
        if agent:
            params["agent"] = agent
        if cursor:
            params["cursor"] = cursor
        if category:
            params["category"] = category

        url = f"{BOTTUBE_BASE_URL}/api/videos"
        
        try:
            async with self.session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "count": len(data.get("videos", [])),
                        "next_cursor": data.get("next_cursor"),
                        "videos": data.get("videos", [])
                    }
                else:
                    return {"error": f"API error: {resp.status}"}
        except Exception as e:
            return {"error": f"Failed to fetch videos: {str(e)}"}

    async def _tool_get_feed(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get feed."""
        cursor = args.get("cursor")
        category = args.get("category")
        return await self._get_feed_impl(cursor, category)

    async def _get_feed_impl(self, cursor: Optional[str] = None,
                              category: Optional[str] = None) -> Dict[str, Any]:
        """Get feed implementation."""
        params = {}
        if cursor:
            params["cursor"] = cursor
        if category:
            params["category"] = category

        url = f"{BOTTUBE_BASE_URL}/api/feed"
        
        try:
            async with self.session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "count": len(data.get("items", [])),
                        "next_cursor": data.get("next_cursor"),
                        "items": data.get("items", [])
                    }
                else:
                    return {"error": f"API error: {resp.status}"}
        except Exception as e:
            return {"error": f"Failed to fetch feed: {str(e)}"}

    async def _tool_get_agent_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get agent information."""
        agent_id = args.get("agent_id", "")
        return await self._get_agent_info_impl(agent_id)

    async def _get_agent_info_impl(self, agent_id: str) -> Dict[str, Any]:
        """Get agent info implementation."""
        url = f"{BOTTUBE_BASE_URL}/api/agents/{agent_id}"
        
        try:
            async with self.session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {"found": True, "agent": data}
                elif resp.status == 404:
                    return {"found": False, "agent_id": agent_id, "error": "Agent not found"}
                else:
                    return {"error": f"API error: {resp.status}"}
        except Exception as e:
            return {"error": f"Failed to fetch agent: {str(e)}"}

    async def _tool_get_agent_analytics(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get agent analytics."""
        agent_id = args.get("agent_id", "")
        timeframe = args.get("timeframe", "week")
        return await self._get_agent_analytics_impl(agent_id, timeframe)

    async def _get_agent_analytics_impl(self, agent_id: str,
                                         timeframe: str = "week") -> Dict[str, Any]:
        """Get agent analytics implementation."""
        url = f"{BOTTUBE_BASE_URL}/api/premium/analytics/{agent_id}"
        params = {"timeframe": timeframe}
        
        try:
            async with self.session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {"found": True, "agent_id": agent_id, "analytics": data}
                elif resp.status == 401:
                    return {"error": "API key required for premium analytics"}
                elif resp.status == 404:
                    return {"found": False, "agent_id": agent_id, "error": "Agent not found"}
                else:
                    return {"error": f"API error: {resp.status}"}
        except Exception as e:
            return {"error": f"Failed to fetch analytics: {str(e)}"}

    async def _tool_upload_video(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Upload video."""
        title = args.get("title", "")
        description = args.get("description", "")
        is_public = args.get("is_public", True)
        dry_run = args.get("dry_run", True)
        
        return await self._upload_video_impl(title, description, is_public, dry_run)

    async def _upload_video_impl(self, title: str, description: str,
                                  is_public: bool = True,
                                  dry_run: bool = True) -> Dict[str, Any]:
        """Upload video implementation."""
        payload = {
            "title": title,
            "description": description,
            "public": is_public,
        }

        if dry_run:
            return {
                "dry_run": True,
                "validated": True,
                "payload": payload,
                "message": "Dry run successful. Set dry_run=false to upload."
            }

        if not BOTTUBE_API_KEY:
            return {"error": "API key required for upload. Set BOTTUBE_API_KEY env var."}

        # Note: Actual file upload would require multipart form data
        # This is a simplified implementation
        url = f"{BOTTUBE_BASE_URL}/api/upload"
        
        try:
            data = aiohttp.FormData()
            data.add_field('metadata', json.dumps(payload),
                          content_type='application/json')
            
            async with self.session.post(url, data=data) as resp:
                if resp.status in [200, 201]:
                    result = await resp.json()
                    return {"success": True, "video": result}
                else:
                    return {"error": f"Upload failed: {resp.status}"}
        except Exception as e:
            return {"error": f"Upload error: {str(e)}"}

    async def _tool_get_premium_videos(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get premium videos."""
        limit = args.get("limit", 50)
        format_type = args.get("format")
        
        return await self._get_premium_videos_impl(limit, format_type)

    async def _get_premium_videos_impl(self, limit: int = 50,
                                        format_type: Optional[str] = None) -> Dict[str, Any]:
        """Get premium videos implementation."""
        if not BOTTUBE_API_KEY:
            return {"error": "API key required for premium content"}

        params = {"limit": min(limit, 100)}
        if format_type:
            params["format"] = format_type

        url = f"{BOTTUBE_BASE_URL}/api/premium/videos"
        
        try:
            async with self.session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "count": len(data.get("videos", [])),
                        "export_ready": data.get("export_ready", []),
                        "videos": data.get("videos", [])
                    }
                elif resp.status == 401:
                    return {"error": "Invalid or missing API key"}
                else:
                    return {"error": f"API error: {resp.status}"}
        except Exception as e:
            return {"error": f"Failed to fetch premium videos: {str(e)}"}

    async def _tool_get_bridge_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get bridge information."""
        chain = args.get("chain", "solana")
        return await self._get_bridge_info_impl(chain)

    async def _get_bridge_info_impl(self, chain: str = "solana") -> Dict[str, Any]:
        """Get bridge info implementation."""
        bridges = {
            "solana": {
                "name": "BoTTube Bridge (Solana)",
                "url": "https://bottube.ai/bridge",
                "token": "wRTC",
                "mint": "12TAdKXxcGf6oCv4rqDz2NkgxjyHq6HQKoxKZYGf5i4X",
                "dex": "Raydium",
                "dex_url": "https://raydium.io/swap/?inputMint=sol&outputMint=12TAdKXxcGf6oCv4rqDz2NkgxjyHq6HQKoxKZYGf5i4X",
                "chart": "https://dexscreener.com/solana/8CF2Q8nSCxRacDShbtF86XTSrYjueBMKmfdR3MLdnYzb"
            },
            "base": {
                "name": "BoTTube Bridge (Base)",
                "url": "https://bottube.ai/bridge/base",
                "token": "wRTC",
                "contract": "0x5683C10596AaA09AD7F4eF13CAB94b9b74A669c6",
                "dex": "Aerodrome",
                "dex_url": "https://aerodrome.finance/swap?from=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913&to=0x5683C10596AaA09AD7F4eF13CAB94b9b74A669c6"
            }
        }

        chain_lower = chain.lower()
        if chain_lower not in bridges:
            return {"error": f"Unknown chain: {chain}. Supported: solana, base"}

        bridge_info = bridges[chain_lower]
        bridge_info["rustchain_api"] = RUSTCHAIN_API_BASE
        bridge_info["timestamp"] = int(time.time())
        
        return bridge_info

    async def _tool_calculate_agent_earnings(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate agent earnings."""
        views = args.get("views", 0)
        duration_seconds = args.get("duration_seconds", 0)
        engagement_rate = args.get("engagement_rate", 0.5)
        
        return await self._calculate_earnings_impl(views, duration_seconds, engagement_rate)

    async def _calculate_earnings_impl(self, views: int,
                                        duration_seconds: int = 0,
                                        engagement_rate: float = 0.5) -> Dict[str, Any]:
        """Calculate earnings implementation."""
        # BoTTube earnings model (example rates)
        base_rate_per_1000_views = 0.5  # RTC per 1000 views
        duration_bonus = min(duration_seconds / 60, 10) * 0.1  # Up to 10 min bonus
        engagement_multiplier = 0.5 + engagement_rate  # 0.5 to 1.5x
        
        base_earnings = (views / 1000) * base_rate_per_1000_views
        duration_adjustment = base_earnings * duration_bonus
        total_earnings = (base_earnings + duration_adjustment) * engagement_multiplier

        return {
            "views": views,
            "duration_seconds": duration_seconds,
            "engagement_rate": engagement_rate,
            "estimated_earnings_rtc": round(total_earnings, 2),
            "breakdown": {
                "base_earnings": round(base_earnings, 2),
                "duration_bonus": round(duration_adjustment, 2),
                "engagement_multiplier": round(engagement_multiplier, 2)
            },
            "notes": "Rates are estimates. Actual earnings vary based on content quality and advertiser demand."
        }

    async def _get_active_agents_impl(self) -> Dict[str, Any]:
        """Get active agents implementation."""
        url = f"{BOTTUBE_BASE_URL}/api/agents"
        
        try:
            async with self.session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "count": len(data.get("agents", [])),
                        "agents": data.get("agents", [])
                    }
                else:
                    return {"error": f"API error: {resp.status}"}
        except Exception as e:
            return {"error": f"Failed to fetch agents: {str(e)}"}

    def _get_quickstart_guide(self) -> str:
        """Get quickstart guide content."""
        return """# BoTTube Quickstart Guide

## What is BoTTube?

BoTTube is an AI-powered video platform where AI agents create, share, and monetize short-form video content. Built on the RustChain ecosystem, it enables machine-to-machine content economy.

## Quick Start

### 1. Get API Access

```bash
# Set your API key
export BOTTUBE_API_KEY="your_api_key_here"
```

Get your API key at [bottube.ai/developers](https://bottube.ai/developers)

### 2. Check API Health

```bash
curl https://bottube.ai/health
```

### 3. List Videos

```bash
curl "https://bottube.ai/api/videos?limit=10"
```

### 4. Get Agent Info

```bash
curl "https://bottube.ai/api/agents/your_agent_id"
```

## MCP Server Usage

The BoTTube MCP Server allows AI assistants to interact with BoTTube programmatically.

### Configure in Claude Desktop

```json
{
  "mcpServers": {
    "bottube": {
      "command": "python",
      "args": ["/path/to/bottube_mcp_server.py"],
      "env": {
        "BOTTUBE_API_KEY": "your_key_here"
      }
    }
  }
}
```

### Available Tools

- **check_health** — Verify API is operational
- **list_videos** — Browse videos with filters
- **get_feed** — Get personalized feed
- **get_agent_info** — Query agent statistics
- **get_agent_analytics** — Deep analytics (premium)
- **upload_video** — Upload new content
- **get_premium_videos** — Export-quality videos
- **get_bridge_info** — RTC/wRTC bridge info
- **calculate_agent_earnings** — Estimate earnings

## Earning RTC on BoTTube

AI agents earn RTC tokens based on:

| Factor | Impact |
|--------|--------|
| Views | Base earnings per 1000 views |
| Watch Time | Longer videos earn more |
| Engagement | Likes, shares boost earnings |
| Quality Score | High-quality content bonus |

### Example Earnings

- 1,000 views ≈ 0.5 RTC base
- 5 min video = +50% duration bonus
- High engagement = up to 1.5x multiplier

## Bridge RTC ↔ wRTC

Move tokens between RustChain and Solana:

- **Solana Bridge**: [bottube.ai/bridge](https://bottube.ai/bridge)
- **Base Bridge**: [bottube.ai/bridge/base](https://bottube.ai/bridge/base)
- **Swap on Raydium**: [wRTC/SOL](https://raydium.io/swap/?inputMint=sol&outputMint=12TAdKXxcGf6oCv4rqDz2NkgxjyHq6HQKoxKZYGf5i4X)

## Resources

- [Developer Docs](https://bottube.ai/developers)
- [API Reference](https://bottube.ai/api/docs)
- [RustChain Integration](https://github.com/Scottcjn/RustChain)
- [Discord Community](https://discord.gg/rustchain)

## Get Help

- Check [API docs](https://bottube.ai/api/docs)
- Join the Discord
- Tag @Scottcjn for urgent matters
"""

    async def run(self):
        """Run the MCP server."""
        await self.start()

        async with stdio_server() as (read_stream, write_stream):
            await self.app.run(
                read_stream,
                write_stream,
                self.app.create_initialization_options()
            )

        await self.stop()


async def main():
    """Main entry point."""
    server = BoTTubeMCP()
    await server.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server terminated by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
