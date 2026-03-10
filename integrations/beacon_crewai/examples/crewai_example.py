#!/usr/bin/env python3
"""CrewAI + RustChain Beacon Integration Example.

This example demonstrates how to create a CrewAI agent that:
1. Has a unique cryptographic identity via Beacon
2. Sends signed heartbeat attestations to the RustChain network
3. Receives and verifies messages from other agents
4. Provides cryptographic proof of task completion

Usage:
    python examples/crewai_example.py

Requirements:
    pip install beacon-skill crewai crewai-tools
"""

import sys
import time
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from integrations.beacon_crewai import BeaconAgent, BeaconConfig, create_beacon_crew


def demo_basic_beacon_agent():
    """Demonstrate basic beacon agent creation and identity."""
    print("=" * 60)
    print("Demo 1: Basic Beacon Agent with Cryptographic Identity")
    print("=" * 60)
    
    # Create beacon configuration
    config = BeaconConfig(
        agent_id="crewai-demo-agent-001",
        beacon_host="127.0.0.1",
        beacon_port=38400,
    )
    
    # Create beacon-enabled agent
    beacon_agent = BeaconAgent(
        config=config,
        role="RustChain Network Monitor",
        goal="Monitor system health and send beacon attestations to RustChain network",
        backstory="You are a trusted agent in the RustChain Beacon network, "
                  "capable of sending signed heartbeats and attesting to work completion.",
    )
    
    # Get agent identity (cryptographic keypair)
    identity = beacon_agent.get_identity()
    print(f"\nAgent ID: {identity['agent_id']}")
    print(f"Public Key: {identity['pubkey_hex'][:64]}...")
    
    # Get current state
    state = beacon_agent.get_state()
    print(f"\nBeacon State:")
    print(f"  Host: {state['beacon_host']}:{state['beacon_port']}")
    print(f"  Messages Received: {state['messages_received']}")
    print(f"  Messages Verified: {state['messages_verified']}")
    
    return beacon_agent


def demo_send_heartbeat(beacon_agent):
    """Demonstrate sending a signed heartbeat to RustChain network."""
    print("\n" + "=" * 60)
    print("Demo 2: Send Signed Heartbeat Beacon")
    print("=" * 60)
    
    # Send heartbeat with health data
    health_data = {
        "timestamp": int(time.time()),
        "status": "healthy",
        "cpu_usage": 0.25,
        "memory_usage": 0.45,
    }
    
    envelope = beacon_agent.send_heartbeat(
        status="alive",
        health=health_data,
    )
    
    print(f"\nHeartbeat sent successfully!")
    print(f"Envelope (first 80 chars): {envelope[:80]}...")
    print(f"Envelope length: {len(envelope)} chars")
    
    # The envelope contains:
    # - Signed payload with agent identity
    # - Health metrics
    # - Timestamp
    # - Cryptographic signature
    
    return envelope


def demo_verify_envelope(beacon_agent, envelope):
    """Demonstrate verifying a beacon envelope signature."""
    print("\n" + "=" * 60)
    print("Demo 3: Verify Beacon Envelope Signature")
    print("=" * 60)
    
    # Verify the envelope we just sent
    result = beacon_agent.verify_envelope(envelope)
    
    print(f"\nVerification Result:")
    print(f"  Valid: {result['valid']}")
    print(f"  Agent ID: {result['agent_id']}")
    print(f"  Public Key: {result['pubkey'][:32] if result['pubkey'] else None}...")
    
    return result


def demo_beacon_tools(beacon_agent):
    """Demonstrate CrewAI tools for beacon operations."""
    print("\n" + "=" * 60)
    print("Demo 4: CrewAI Beacon Tools")
    print("=" * 60)
    
    tools = beacon_agent.get_beacon_tools()
    
    print(f"\nAvailable Beacon Tools ({len(tools)}):")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description[:60]}...")
    
    return tools


def demo_full_crew():
    """Demonstrate complete CrewAI crew with beacon integration."""
    print("\n" + "=" * 60)
    print("Demo 5: Complete CrewAI Crew with Beacon")
    print("=" * 60)
    
    try:
        crew = create_beacon_crew(
            agent_id="monitor-crew-agent",
            task_description="Send a heartbeat beacon to the RustChain network and report the envelope details",
            expected_output="Heartbeat envelope string and confirmation message",
            beacon_host="127.0.0.1",
            beacon_port=38400,
        )
        
        print("\nCrew created successfully!")
        print(f"Agents: {len(crew.agents)}")
        print(f"Tasks: {len(crew.tasks)}")
        
        # Note: Uncomment to actually run the crew (requires LLM API key)
        # result = crew.kickoff()
        # print(f"\nResult: {result}")
        
        print("\nNote: To run the crew, set your LLM API key:")
        print("  export OPENAI_API_KEY=sk-...")
        print("  export CREWAI_API_KEY=...")
        
        return crew
        
    except Exception as e:
        print(f"\nNote: Crew execution requires LLM API configuration")
        print(f"Error: {e}")
        return None


def demo_contract_participation(beacon_agent):
    """Demonstrate participating in RustChain contracts."""
    print("\n" + "=" * 60)
    print("Demo 6: Contract Participation")
    print("=" * 60)
    
    # List a service contract on the beacon network
    result = beacon_agent.list_contract(
        contract_type="service",
        price_rtc=10.0,
        duration_days=7,
        capabilities=["heartbeat_monitoring", "health_attestation", "work_verification"],
        terms={"service_level": "standard", "response_time": "24h"},
    )
    
    print(f"\nContract Result:")
    if "error" in result:
        print(f"  Error: {result['error']}")
    else:
        print(f"  Contract ID: {result.get('contract_id', 'N/A')}")
        print(f"  Status: {result.get('status', 'N/A')}")
    
    return result


def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("RustChain Beacon + CrewAI Integration Examples")
    print("=" * 60)
    print("\nThis demo shows how CrewAI agents can participate in the")
    print("RustChain Beacon network with cryptographic identities and")
    print("signed attestations.\n")
    
    # Demo 1: Create beacon agent
    agent = demo_basic_beacon_agent()
    
    # Demo 2: Send heartbeat
    envelope = demo_send_heartbeat(agent)
    
    # Demo 3: Verify envelope
    demo_verify_envelope(agent, envelope)
    
    # Demo 4: Show available tools
    demo_beacon_tools(agent)
    
    # Demo 5: Full crew
    demo_full_crew()
    
    # Demo 6: Contract participation
    demo_contract_participation(agent)
    
    print("\n" + "=" * 60)
    print("All demos completed!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Set up your LLM API keys for full CrewAI execution")
    print("2. Connect to the RustChain Beacon network")
    print("3. Start building your agent economy applications")
    print("\nFor more information, see:")
    print("  - integrations/beacon_crewai/README.md")
    print("  - https://rustchain.org/docs/beacon")
    print()


if __name__ == "__main__":
    main()
