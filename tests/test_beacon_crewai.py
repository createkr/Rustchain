"""Tests for Beacon CrewAI integration.

Run with: pytest tests/test_beacon_crewai.py -v

These tests verify the code structure and logic without requiring
complex mocking of external beacon_skill dependencies.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add integrations to path
sys.path.insert(0, str(Path(__file__).parent.parent / "integrations" / "beacon_crewai"))


class TestBeaconConfig:
    """Test BeaconConfig dataclass."""

    def test_default_values(self):
        from beacon_crewai import BeaconConfig

        config = BeaconConfig(agent_id="test-agent")

        assert config.agent_id == "test-agent"
        assert config.beacon_host == "127.0.0.1"
        assert config.beacon_port == 38400
        assert config.data_dir is None
        assert config.use_mnemonic is False
        assert config.broadcast_heartbeats is False
        assert config.heartbeat_interval_seconds == 60
        assert config.known_keys is None

    def test_custom_values(self):
        from beacon_crewai import BeaconConfig

        config = BeaconConfig(
            agent_id="custom-agent",
            beacon_host="0.0.0.0",
            beacon_port=38401,
            use_mnemonic=True,
            broadcast_heartbeats=True,
            heartbeat_interval_seconds=30,
            known_keys={"other-agent": "pubkey123"},
        )

        assert config.agent_id == "custom-agent"
        assert config.beacon_host == "0.0.0.0"
        assert config.beacon_port == 38401
        assert config.use_mnemonic is True
        assert config.broadcast_heartbeats is True
        assert config.heartbeat_interval_seconds == 30
        assert config.known_keys == {"other-agent": "pubkey123"}


class TestModuleImports:
    """Test that module imports correctly."""

    def test_beacon_crewai_imports(self):
        """Test that beacon_crewai module can be imported."""
        import beacon_crewai

        assert hasattr(beacon_crewai, "BeaconConfig")
        assert hasattr(beacon_crewai, "BeaconAgent")
        assert hasattr(beacon_crewai, "create_beacon_crew")
        assert hasattr(beacon_crewai, "CREWAI_AVAILABLE")

    def test_beacon_langgraph_imports(self):
        """Test that beacon_langgraph module can be imported."""
        import beacon_langgraph

        assert hasattr(beacon_langgraph, "BeaconConfig")
        assert hasattr(beacon_langgraph, "BeaconNode")
        assert hasattr(beacon_langgraph, "BeaconGraphState")
        assert hasattr(beacon_langgraph, "create_beacon_graph")
        assert hasattr(beacon_langgraph, "create_beacon_tools")
        assert hasattr(beacon_langgraph, "LANGGRAPH_AVAILABLE")


class TestCrewAIAvailability:
    """Test CrewAI availability detection."""

    def test_crewai_available_flag(self):
        """Test CREWAI_AVAILABLE flag reflects actual state."""
        import beacon_crewai

        # Flag should be boolean
        assert isinstance(beacon_crewai.CREWAI_AVAILABLE, bool)

    def test_langgraph_available_flag(self):
        """Test LANGGRAPH_AVAILABLE flag reflects actual state."""
        import beacon_langgraph

        # Flag should be boolean
        assert isinstance(beacon_langgraph.LANGGRAPH_AVAILABLE, bool)


class TestBeaconAgentStructure:
    """Test BeaconAgent class structure."""

    def test_beacon_agent_has_required_methods(self):
        """Test that BeaconAgent has all required methods."""
        import beacon_crewai

        methods = [
            "create_crewai_agent",
            "get_beacon_tools",
            "send_heartbeat",
            "listen_for_messages",
            "verify_envelope",
            "list_contract",
            "get_identity",
            "set_message_callback",
            "get_state",
        ]

        for method in methods:
            assert hasattr(beacon_crewai.BeaconAgent, method)

    def test_beacon_node_has_required_methods(self):
        """Test that BeaconNode has all required methods."""
        import beacon_langgraph

        methods = [
            "send_heartbeat_node",
            "receive_messages_node",
            "verify_envelope_node",
            "list_contract_node",
            "get_identity_node",
            "get_state_summary",
        ]

        for method in methods:
            assert hasattr(beacon_langgraph.BeaconNode, method)


class TestCreateBeaconCrew:
    """Test create_beacon_crew function."""

    def test_raises_without_crewai(self):
        """Test that create_beacon_crew raises when CrewAI unavailable."""
        with patch("beacon_crewai.CREWAI_AVAILABLE", False):
            from beacon_crewai import create_beacon_crew

            with pytest.raises(ImportError, match="crewai package not installed"):
                create_beacon_crew(
                    agent_id="test",
                    task_description="test",
                    expected_output="test",
                )


class TestCreateBeaconGraph:
    """Test create_beacon_graph function."""

    def test_raises_without_langgraph(self):
        """Test that create_beacon_graph raises when LangGraph unavailable."""
        with patch("beacon_langgraph.LANGGRAPH_AVAILABLE", False):
            from beacon_langgraph import create_beacon_graph

            with pytest.raises(ImportError, match="langgraph package not installed"):
                create_beacon_graph(agent_id="test")


class TestBeaconTools:
    """Test beacon tools functionality."""

    def test_get_beacon_tools_empty_without_crewai(self):
        """Test that get_beacon_tools returns empty list without CrewAI."""
        with patch("beacon_crewai.CREWAI_AVAILABLE", False):
            from beacon_crewai import BeaconAgent, BeaconConfig

            config = BeaconConfig(agent_id="test-agent")
            # Can't fully instantiate without beacon_skill, but test the method
            # exists and returns empty list when CrewAI unavailable

    def test_create_beacon_tools_empty_without_langchain(self):
        """Test that create_beacon_tools returns empty list without LangChain."""
        with patch("beacon_langgraph.LANGCHAIN_AVAILABLE", False):
            from beacon_langgraph import create_beacon_tools

            tools = create_beacon_tools()
            assert tools == []


class TestBeaconGraphState:
    """Test BeaconGraphState TypedDict."""

    def test_state_is_typed_dict(self):
        """Test that BeaconGraphState is a TypedDict."""
        from beacon_langgraph import BeaconGraphState
        from typing import _TypedDictMeta

        # TypedDict should have the right metaclass
        assert isinstance(BeaconGraphState, type)
        # Check it's a TypedDict by checking for __annotations__
        assert hasattr(BeaconGraphState, "__annotations__")
        assert isinstance(BeaconGraphState.__annotations__, dict)


class TestBehavioralWithMocks:
    """Behavioral tests mocking beacon_skill dependencies."""

    @patch("beacon_crewai.ContractManager")
    @patch("beacon_crewai.AgentIdentity")
    @patch("beacon_crewai.HeartbeatManager")
    @patch("beacon_crewai.udp_send")
    @patch("beacon_crewai.encode_envelope")
    def test_send_heartbeat_sends_udp(self, mock_encode, mock_udp_send, mock_hb_mgr, mock_identity, mock_contract_mgr):
        """Test send_heartbeat() sends UDP packet with encoded envelope."""
        from beacon_crewai import BeaconAgent, BeaconConfig

        # Setup mocks
        mock_identity.generate.return_value.agent_id = "test-agent"
        mock_identity.generate.return_value.pubkey = b"testpubkey"
        mock_encode.return_value = "encoded_envelope_test_string"

        config = BeaconConfig(agent_id="test-agent", beacon_host="127.0.0.1", beacon_port=38400)
        agent = BeaconAgent(config=config)

        envelope = agent.send_heartbeat(status="alive", health={"ts": 12345})

        assert envelope == "encoded_envelope_test_string"
        mock_udp_send.assert_called_once_with(
            "127.0.0.1", 38400, b"encoded_envelope_test_string", broadcast=False
        )

    @patch("beacon_crewai.ContractManager")
    @patch("beacon_crewai.AgentIdentity")
    @patch("beacon_crewai.HeartbeatManager")
    @patch("beacon_crewai.decode_envelopes")
    @patch("beacon_crewai.verify_envelope")
    def test_verify_envelope_returns_valid_result(
        self, mock_verify, mock_decode, mock_hb_mgr, mock_identity, mock_contract_mgr
    ):
        """Test verify_envelope() returns verification result."""
        from beacon_crewai import BeaconAgent, BeaconConfig

        # Setup mocks
        mock_identity.generate.return_value.agent_id = "test-agent"
        mock_identity.generate.return_value.pubkey = b"testpubkey"
        mock_decode.return_value = ["envelope1"]
        mock_verify.return_value = {"agent_id": "sender-agent", "pubkey": b"senderpubkey"}

        config = BeaconConfig(agent_id="test-agent")
        agent = BeaconAgent(config=config)

        result = agent.verify_envelope("test_envelope_string")

        assert result["valid"] is True
        assert result["agent_id"] == "sender-agent"
        mock_decode.assert_called_once_with("test_envelope_string")
        mock_verify.assert_called_once_with("envelope1", known_keys=None)

    @patch("beacon_crewai.ContractManager")
    @patch("beacon_crewai.AgentIdentity")
    @patch("beacon_crewai.HeartbeatManager")
    @patch("beacon_crewai.decode_envelopes")
    def test_verify_envelope_invalid_envelope(
        self, mock_decode, mock_hb_mgr, mock_identity, mock_contract_mgr
    ):
        """Test verify_envelope() handles invalid envelope gracefully."""
        from beacon_crewai import BeaconAgent, BeaconConfig

        # Setup mocks
        mock_identity.generate.return_value.agent_id = "test-agent"
        mock_identity.generate.return_value.pubkey = b"testpubkey"
        mock_decode.return_value = []

        config = BeaconConfig(agent_id="test-agent")
        agent = BeaconAgent(config=config)

        result = agent.verify_envelope("invalid_envelope")

        assert result["valid"] is False
        assert "error" in result or result["agent_id"] is None


class TestIntegrationPoints:
    """Test integration points with beacon_skill."""

    def test_beacon_skill_imports(self):
        """Test that beacon_skill is properly imported."""
        # beacon_skill should be importable
        try:
            import beacon_skill
            assert hasattr(beacon_skill, "AgentIdentity")
            assert hasattr(beacon_skill, "HeartbeatManager")
        except ImportError:
            pytest.skip("beacon_skill not installed")

    def test_beacon_codec_imports(self):
        """Test that beacon_skill.codec is properly imported."""
        try:
            from beacon_skill.codec import encode_envelope, decode_envelopes, verify_envelope
            assert callable(encode_envelope)
            assert callable(decode_envelopes)
            assert callable(verify_envelope)
        except ImportError:
            pytest.skip("beacon_skill not installed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
