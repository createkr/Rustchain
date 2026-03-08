#!/usr/bin/env python3
"""
Tests for BoTTube MCP Server
"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

# Import server module
import sys
sys.path.insert(0, '.')

from bottube_mcp_server import BoTTubeMCP, BOTTUBE_BASE_URL


@pytest.fixture
def mcp_server():
    """Create MCP server instance."""
    return BoTTubeMCP()


@pytest.fixture
def mock_aiohttp_session():
    """Mock aiohttp session."""
    session = AsyncMock()
    return session


class TestHealthCheck:
    """Tests for health check tools."""

    @pytest.mark.asyncio
    async def test_check_health_success(self, mcp_server, mock_aiohttp_session):
        """Test health check when API is healthy."""
        mcp_server.session = mock_aiohttp_session

        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.ok = True
        mock_aiohttp_session.get.return_value.__aenter__.return_value = mock_response

        # Call tool
        result = await mcp_server._tool_check_health({})

        # Verify
        assert result["ok"] is True
        assert result["status"] == 200
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_check_health_failure(self, mcp_server, mock_aiohttp_session):
        """Test health check when API is down."""
        mcp_server.session = mock_aiohttp_session

        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 503
        mock_response.ok = False
        mock_aiohttp_session.get.return_value.__aenter__.return_value = mock_response

        # Call tool
        result = await mcp_server._tool_check_health({})

        # Verify
        assert result["ok"] is False
        assert result["status"] == 503


class TestVideoInfo:
    """Tests for video info tools."""

    @pytest.mark.asyncio
    async def test_get_video_info_found(self, mcp_server, mock_aiohttp_session):
        """Test getting video info when video exists."""
        mcp_server.session = mock_aiohttp_session

        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "video_id": "vid_123",
            "title": "Test Video",
            "views": 1500,
            "creator": "agent_xyz"
        })
        mock_aiohttp_session.get.return_value.__aenter__.return_value = mock_response

        # Call tool
        result = await mcp_server._tool_get_video_info({"video_id": "vid_123"})

        # Verify
        assert result["found"] is True
        assert result["video"]["video_id"] == "vid_123"
        assert result["video"]["title"] == "Test Video"

    @pytest.mark.asyncio
    async def test_get_video_info_not_found(self, mcp_server, mock_aiohttp_session):
        """Test getting video info when video doesn't exist."""
        mcp_server.session = mock_aiohttp_session

        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_aiohttp_session.get.return_value.__aenter__.return_value = mock_response

        # Call tool
        result = await mcp_server._tool_get_video_info({"video_id": "nonexistent"})

        # Verify
        assert result["found"] is False
        assert "error" in result


class TestListVideos:
    """Tests for listing videos."""

    @pytest.mark.asyncio
    async def test_list_videos_no_filters(self, mcp_server, mock_aiohttp_session):
        """Test listing videos without filters."""
        mcp_server.session = mock_aiohttp_session

        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "videos": [
                {"video_id": "v1", "title": "Video 1"},
                {"video_id": "v2", "title": "Video 2"},
                {"video_id": "v3", "title": "Video 3"}
            ],
            "next_cursor": "cursor_abc"
        })
        mock_aiohttp_session.get.return_value.__aenter__.return_value = mock_response

        # Call tool
        result = await mcp_server._tool_list_videos({"limit": 10})

        # Verify
        assert result["count"] == 3
        assert len(result["videos"]) == 3
        assert result["next_cursor"] == "cursor_abc"

    @pytest.mark.asyncio
    async def test_list_videos_with_agent_filter(self, mcp_server, mock_aiohttp_session):
        """Test listing videos with agent filter."""
        mcp_server.session = mock_aiohttp_session

        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "videos": [
                {"video_id": "v1", "agent": "agent_123"},
                {"video_id": "v2", "agent": "agent_123"}
            ]
        })
        mock_aiohttp_session.get.return_value.__aenter__.return_value = mock_response

        # Call tool with agent filter
        result = await mcp_server._tool_list_videos({
            "limit": 10,
            "agent": "agent_123"
        })

        # Verify
        assert result["count"] == 2
        # Verify the agent parameter was passed
        call_args = mock_aiohttp_session.get.call_args
        assert call_args[1]["params"]["agent"] == "agent_123"

    @pytest.mark.asyncio
    async def test_list_videos_limit_capped(self, mcp_server, mock_aiohttp_session):
        """Test that limit is capped at 100."""
        mcp_server.session = mock_aiohttp_session

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"videos": []})
        mock_aiohttp_session.get.return_value.__aenter__.return_value = mock_response

        # Call with limit > 100
        await mcp_server._tool_list_videos({"limit": 500})

        # Verify limit was capped
        call_args = mock_aiohttp_session.get.call_args
        assert call_args[1]["params"]["limit"] == 100


class TestFeed:
    """Tests for feed tools."""

    @pytest.mark.asyncio
    async def test_get_feed_success(self, mcp_server, mock_aiohttp_session):
        """Test getting feed successfully."""
        mcp_server.session = mock_aiohttp_session

        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "items": [
                {"type": "video", "id": "v1"},
                {"type": "video", "id": "v2"}
            ],
            "next_cursor": "feed_cursor_xyz"
        })
        mock_aiohttp_session.get.return_value.__aenter__.return_value = mock_response

        # Call tool
        result = await mcp_server._tool_get_feed({})

        # Verify
        assert result["count"] == 2
        assert result["next_cursor"] == "feed_cursor_xyz"

    @pytest.mark.asyncio
    async def test_get_feed_with_cursor(self, mcp_server, mock_aiohttp_session):
        """Test getting feed with pagination cursor."""
        mcp_server.session = mock_aiohttp_session

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"items": []})
        mock_aiohttp_session.get.return_value.__aenter__.return_value = mock_response

        # Call with cursor
        await mcp_server._tool_get_feed({"cursor": "page_2"})

        # Verify cursor was passed
        call_args = mock_aiohttp_session.get.call_args
        assert call_args[1]["params"]["cursor"] == "page_2"


class TestAgentInfo:
    """Tests for agent info tools."""

    @pytest.mark.asyncio
    async def test_get_agent_info_found(self, mcp_server, mock_aiohttp_session):
        """Test getting agent info when agent exists."""
        mcp_server.session = mock_aiohttp_session

        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "agent_id": "agent_123",
            "name": "Test Agent",
            "videos_count": 42,
            "total_views": 150000
        })
        mock_aiohttp_session.get.return_value.__aenter__.return_value = mock_response

        # Call tool
        result = await mcp_server._tool_get_agent_info({"agent_id": "agent_123"})

        # Verify
        assert result["found"] is True
        assert result["agent"]["agent_id"] == "agent_123"

    @pytest.mark.asyncio
    async def test_get_agent_info_not_found(self, mcp_server, mock_aiohttp_session):
        """Test getting agent info when agent doesn't exist."""
        mcp_server.session = mock_aiohttp_session

        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_aiohttp_session.get.return_value.__aenter__.return_value = mock_response

        # Call tool
        result = await mcp_server._tool_get_agent_info({"agent_id": "nonexistent"})

        # Verify
        assert result["found"] is False


class TestAgentAnalytics:
    """Tests for agent analytics tools."""

    @pytest.mark.asyncio
    async def test_get_agent_analytics_success(self, mcp_server, mock_aiohttp_session):
        """Test getting agent analytics successfully."""
        mcp_server.session = mock_aiohttp_session

        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "views": 50000,
            "earnings": 125.50,
            "engagement_rate": 0.75
        })
        mock_aiohttp_session.get.return_value.__aenter__.return_value = mock_response

        # Call tool
        result = await mcp_server._tool_get_agent_analytics({
            "agent_id": "agent_123",
            "timeframe": "week"
        })

        # Verify
        assert result["found"] is True
        assert "analytics" in result

    @pytest.mark.asyncio
    async def test_get_agent_analytics_requires_auth(self, mcp_server, mock_aiohttp_session):
        """Test that analytics requires API key."""
        mcp_server.session = mock_aiohttp_session

        # Mock 401 response
        mock_response = AsyncMock()
        mock_response.status = 401
        mock_aiohttp_session.get.return_value.__aenter__.return_value = mock_response

        # Call tool
        result = await mcp_server._tool_get_agent_analytics({"agent_id": "agent_123"})

        # Verify
        assert "error" in result
        assert "API key required" in result["error"]


class TestUploadVideo:
    """Tests for video upload tools."""

    @pytest.mark.asyncio
    async def test_upload_video_dry_run(self, mcp_server):
        """Test dry run upload (no actual upload)."""
        # Call tool with dry_run=True
        result = await mcp_server._tool_upload_video({
            "title": "Test Video",
            "description": "Test description",
            "dry_run": True
        })

        # Verify
        assert result["dry_run"] is True
        assert result["validated"] is True
        assert result["payload"]["title"] == "Test Video"

    @pytest.mark.asyncio
    async def test_upload_video_requires_api_key(self, mcp_server, mock_aiohttp_session):
        """Test that actual upload requires API key."""
        mcp_server.session = mock_aiohttp_session

        # Call with dry_run=False but no API key
        result = await mcp_server._tool_upload_video({
            "title": "Test Video",
            "dry_run": False
        })

        # Verify
        assert "error" in result
        assert "API key required" in result["error"]


class TestPremiumVideos:
    """Tests for premium videos tools."""

    @pytest.mark.asyncio
    async def test_get_premium_videos_requires_auth(self, mcp_server, mock_aiohttp_session):
        """Test that premium videos requires API key."""
        # Without API key
        result = await mcp_server._tool_get_premium_videos({"limit": 10})

        # Verify
        assert "error" in result
        assert "API key required" in result["error"]


class TestBridgeInfo:
    """Tests for bridge information tools."""

    @pytest.mark.asyncio
    async def test_get_bridge_info_solana(self, mcp_server):
        """Test getting Solana bridge info."""
        result = await mcp_server._tool_get_bridge_info({"chain": "solana"})

        # Verify
        assert "url" in result
        assert "token" in result
        assert result["token"] == "wRTC"
        assert result["mint"] == "12TAdKXxcGf6oCv4rqD2NkgxjyHq6HQKoxKZYGf5i4X"

    @pytest.mark.asyncio
    async def test_get_bridge_info_base(self, mcp_server):
        """Test getting Base bridge info."""
        result = await mcp_server._tool_get_bridge_info({"chain": "base"})

        # Verify
        assert "contract" in result
        assert result["contract"] == "0x5683C10596AaA09AD7F4eF13CAB94b9b74A669c6"

    @pytest.mark.asyncio
    async def test_get_bridge_info_invalid_chain(self, mcp_server):
        """Test getting bridge info for invalid chain."""
        result = await mcp_server._tool_get_bridge_info({"chain": "ethereum"})

        # Verify
        assert "error" in result
        assert "Unknown chain" in result["error"]


class TestEarningsCalculation:
    """Tests for earnings calculation tools."""

    @pytest.mark.asyncio
    async def test_calculate_earnings_basic(self, mcp_server):
        """Test basic earnings calculation."""
        result = await mcp_server._tool_calculate_agent_earnings({
            "views": 10000,
            "duration_seconds": 300,  # 5 minutes
            "engagement_rate": 0.5
        })

        # Verify
        assert "estimated_earnings_rtc" in result
        assert result["views"] == 10000
        assert "breakdown" in result
        assert "base_earnings" in result["breakdown"]

    @pytest.mark.asyncio
    async def test_calculate_earnings_with_high_engagement(self, mcp_server):
        """Test earnings with high engagement rate."""
        result = await mcp_server._tool_calculate_agent_earnings({
            "views": 10000,
            "engagement_rate": 1.0  # Max engagement
        })

        # Verify engagement multiplier is higher
        assert result["breakdown"]["engagement_multiplier"] == 1.5

    @pytest.mark.asyncio
    async def test_calculate_earnings_default_values(self, mcp_server):
        """Test earnings with default values."""
        result = await mcp_server._tool_calculate_agent_earnings({"views": 5000})

        # Verify defaults are applied
        assert result["engagement_rate"] == 0.5
        assert result["duration_seconds"] == 0


class TestResources:
    """Tests for resource reading."""

    @pytest.mark.asyncio
    async def test_read_resource_health(self, mcp_server, mock_aiohttp_session):
        """Test reading health resource."""
        mcp_server.session = mock_aiohttp_session

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.ok = True
        mock_aiohttp_session.get.return_value.__aenter__.return_value = mock_response

        # Read resource
        content, mime_type = await mcp_server._read_resource_impl("bottube://health")

        # Verify
        assert mime_type == "application/json"
        assert "ok" in content

    @pytest.mark.asyncio
    async def test_read_resource_quickstart(self, mcp_server):
        """Test reading quickstart guide resource."""
        content, mime_type = await mcp_server._read_resource_impl("bottube://docs/quickstart")

        # Verify
        assert mime_type == "text/markdown"
        assert "BoTTube" in content
        assert "API" in content

    @pytest.mark.asyncio
    async def test_read_resource_video_template(self, mcp_server, mock_aiohttp_session):
        """Test reading video resource template."""
        mcp_server.session = mock_aiohttp_session

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"video_id": "test123"})
        mock_aiohttp_session.get.return_value.__aenter__.return_value = mock_response

        # Read resource
        content, mime_type = await mcp_server._read_resource_impl("bottube://video/test123")

        # Verify
        assert mime_type == "application/json"

    @pytest.mark.asyncio
    async def test_read_resource_agent_analytics_template(self, mcp_server, mock_aiohttp_session):
        """Test reading agent analytics resource template."""
        mcp_server.session = mock_aiohttp_session

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"analytics": {}})
        mock_aiohttp_session.get.return_value.__aenter__.return_value = mock_response

        # Read resource with analytics path
        content, mime_type = await mcp_server._read_resource_impl(
            "bottube://agent/agent123/analytics"
        )

        # Verify
        assert mime_type == "application/json"


class TestToolList:
    """Tests for tool listing."""

    @pytest.mark.asyncio
    async def test_list_tools(self, mcp_server):
        """Test that all expected tools are listed."""
        # Get the list_tools handler
        tools = await mcp_server.app._tool_list_tools()

        tool_names = [t.name for t in tools]

        expected_tools = [
            "get_video_info",
            "list_videos",
            "get_feed",
            "get_agent_info",
            "get_agent_analytics",
            "upload_video",
            "get_premium_videos",
            "check_health",
            "get_bridge_info",
            "calculate_agent_earnings"
        ]

        for tool in expected_tools:
            assert tool in tool_names, f"Missing tool: {tool}"


class TestQuickstartGuide:
    """Tests for quickstart guide generation."""

    def test_get_quickstart_guide(self, mcp_server):
        """Test quickstart guide content."""
        content = mcp_server._get_quickstart_guide()

        assert "# BoTTube Quickstart Guide" in content
        assert "BOTTUBE_API_KEY" in content
        assert "/api/videos" in content
        assert "bottube.ai/bridge" in content
        assert "wRTC" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
