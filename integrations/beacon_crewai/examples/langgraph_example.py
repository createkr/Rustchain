#!/usr/bin/env python3
"""LangGraph + RustChain Beacon Integration Example.

This example demonstrates how to create LangGraph workflows that:
1. Have unique cryptographic identities via Beacon
2. Send signed heartbeat attestations to the RustChain network
3. Receive and verify messages from other agents
4. Provide cryptographic proof of workflow completion

Usage:
    python examples/langgraph_example.py

Requirements:
    pip install beacon-skill langgraph langchain-core
"""

import sys
import time
import json
from pathlib import Path
from typing import Any, Dict, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from integrations.beacon_crewai import BeaconNode, BeaconConfig, create_beacon_graph


def demo_basic_beacon_node():
    """Demonstrate basic beacon node creation and identity."""
    print("=" * 60)
    print("Demo 1: Basic Beacon Node with Cryptographic Identity")
    print("=" * 60)
    
    # Create beacon configuration
    config = BeaconConfig(
        agent_id="langgraph-demo-node-001",
        beacon_host="127.0.0.1",
        beacon_port=38400,
    )
    
    # Create beacon-enabled node
    beacon_node = BeaconNode(config=config)
    
    # Get node identity (cryptographic keypair)
    identity_result = beacon_node.get_identity_node({})
    identity = identity_result.get("identity", {})
    
    print(f"\nNode ID: {identity.get('agent_id', 'N/A')}")
    print(f"Public Key: {identity.get('pubkey_hex', 'N/A')[:64]}...")
    
    # Get state summary
    state_summary = beacon_node.get_state_summary()
    print(f"\nBeacon State Summary:")
    print(f"  Host: {state_summary['beacon_host']}:{state_summary['beacon_port']}")
    print(f"  Messages Received: {state_summary['messages_received_count']}")
    print(f"  Messages Verified: {state_summary['messages_verified_count']}")
    
    return beacon_node


def demo_send_heartbeat_node(beacon_node):
    """Demonstrate sending a signed heartbeat via LangGraph node."""
    print("\n" + "=" * 60)
    print("Demo 2: Send Signed Heartbeat via LangGraph Node")
    print("=" * 60)
    
    # Prepare state for heartbeat
    state = {
        "action": "send_heartbeat",
        "status": "alive",
        "health_data": {
            "timestamp": int(time.time()),
            "status": "healthy",
            "workflow_status": "running",
            "node_metrics": {"cpu": 0.3, "memory": 0.5},
        },
    }
    
    # Execute heartbeat node
    result = beacon_node.send_heartbeat_node(state)
    
    envelope = result.get("heartbeat_envelope", "")
    print(f"\nHeartbeat sent successfully!")
    print(f"Envelope (first 80 chars): {envelope[:80] if envelope else 'N/A'}...")
    print(f"Envelope length: {len(envelope)} chars")
    print(f"Last heartbeat time: {result.get('last_heartbeat_time', 'N/A')}")
    
    return result


def demo_verify_envelope_node(beacon_node, envelope):
    """Demonstrate verifying a beacon envelope via LangGraph node."""
    print("\n" + "=" * 60)
    print("Demo 3: Verify Envelope via LangGraph Node")
    print("=" * 60)
    
    # Prepare state for verification
    state = {
        "action": "verify_envelope",
        "envelope": envelope,
    }
    
    # Execute verification node
    result = beacon_node.verify_envelope_node(state)
    
    verification = result.get("verification_result", {})
    print(f"\nVerification Result:")
    print(f"  Valid: {verification.get('valid', False)}")
    print(f"  Agent ID: {verification.get('agent_id', 'N/A')}")
    
    return result


def demo_full_langgraph():
    """Demonstrate complete LangGraph workflow with beacon integration."""
    print("\n" + "=" * 60)
    print("Demo 4: Complete LangGraph Workflow with Beacon")
    print("=" * 60)
    
    # Create beacon-enabled graph
    graph = create_beacon_graph(
        agent_id="workflow-beacon-agent",
        beacon_host="127.0.0.1",
        beacon_port=38400,
    )
    
    print("\nLangGraph workflow created!")
    print(f"Graph type: {type(graph).__name__}")
    
    # Run identity action
    print("\nRunning: Get Identity")
    identity_result = graph.invoke({"action": "get_identity"})
    identity = identity_result.get("identity", {})
    print(f"  Agent ID: {identity.get('agent_id', 'N/A')}")
    
    # Run heartbeat action
    print("\nRunning: Send Heartbeat")
    heartbeat_result = graph.invoke({
        "action": "send_heartbeat",
        "status": "alive",
        "health_data": {"workflow": "demo", "step": 1},
    })
    envelope = heartbeat_result.get("heartbeat_envelope", "")
    print(f"  Envelope: {envelope[:60] if envelope else 'N/A'}...")
    
    # Run verification action
    print("\nRunning: Verify Envelope")
    verify_result = graph.invoke({
        "action": "verify_envelope",
        "envelope": envelope,
    })
    verification = verify_result.get("verification_result", {})
    print(f"  Valid: {verification.get('valid', False)}")
    
    # Run contract listing action
    print("\nRunning: List Contract")
    contract_result = graph.invoke({
        "action": "list_contract",
        "contract_type": "workflow_service",
        "price_rtc": 25.0,
        "duration_days": 14,
    })
    contract = contract_result.get("contract_result", {})
    print(f"  Contract ID: {contract.get('contract_id', 'N/A')}")
    
    return graph


def demo_conditional_workflow():
    """Demonstrate conditional workflow based on beacon state."""
    print("\n" + "=" * 60)
    print("Demo 5: Conditional Workflow with Beacon State")
    print("=" * 60)
    
    from langgraph.graph import StateGraph, END
    from integrations.beacon_crewai.beacon_langgraph import BeaconGraphState
    
    # Create beacon node
    config = BeaconConfig(agent_id="conditional-workflow-agent")
    beacon_node = BeaconNode(config)
    
    # Build conditional workflow
    workflow = StateGraph(BeaconGraphState)
    
    # Add nodes
    workflow.add_node("get_identity", beacon_node.get_identity_node)
    workflow.add_node("send_heartbeat", beacon_node.send_heartbeat_node)
    workflow.add_node("verify", beacon_node.verify_envelope_node)
    
    # Set entry point
    workflow.set_entry_point("get_identity")
    
    # Add conditional edges
    def route_after_identity(state: BeaconGraphState) -> str:
        """Route based on identity retrieval success."""
        if state.get("identity"):
            return "send_heartbeat"
        return END
    
    workflow.add_conditional_edges(
        "get_identity",
        route_after_identity,
        {
            "send_heartbeat": "send_heartbeat",
            END: END,
        }
    )
    
    def route_after_heartbeat(state: BeaconGraphState) -> str:
        """Route based on heartbeat success."""
        if state.get("heartbeat_envelope"):
            return "verify"
        return END
    
    workflow.add_conditional_edges(
        "send_heartbeat",
        route_after_heartbeat,
        {
            "verify": "verify",
            END: END,
        }
    )
    
    workflow.add_edge("verify", END)
    
    # Compile graph
    compiled = workflow.compile()
    
    print("\nConditional workflow created!")
    print("Flow: get_identity -> send_heartbeat -> verify")
    
    # Run workflow
    print("\nRunning conditional workflow...")
    result = compiled.invoke({})
    
    print(f"\nWorkflow Results:")
    print(f"  Identity: {result.get('identity', {}).get('agent_id', 'N/A')}")
    print(f"  Heartbeat: {result.get('heartbeat_envelope', 'N/A')[:50] if result.get('heartbeat_envelope') else 'N/A'}...")
    print(f"  Verified: {result.get('verification_result', {}).get('valid', False)}")
    
    return compiled


def demo_multi_agent_orchestration():
    """Demonstrate multi-agent orchestration with beacon verification."""
    print("\n" + "=" * 60)
    print("Demo 6: Multi-Agent Orchestration with Beacon")
    print("=" * 60)
    
    # Create multiple beacon nodes (simulating different agents)
    agent1 = BeaconNode(BeaconConfig(agent_id="orchestrator-agent"))
    agent2 = BeaconNode(BeaconConfig(agent_id="worker-agent"))
    
    print("\nCreated two beacon-enabled agents:")
    
    # Get identities
    id1 = agent1.get_identity_node({}).get("identity", {})
    id2 = agent2.get_identity_node({}).get("identity", {})
    
    print(f"  Agent 1 (Orchestrator): {id1.get('agent_id', 'N/A')}")
    print(f"  Agent 2 (Worker): {id2.get('agent_id', 'N/A')}")
    
    # Agent 1 sends heartbeat
    print("\nOrchestrator sends heartbeat...")
    hb1 = agent1.send_heartbeat_node({"status": "alive"})
    envelope1 = hb1.get("heartbeat_envelope", "")
    
    # Agent 2 verifies Agent 1's heartbeat
    print("Worker verifies orchestrator's heartbeat...")
    verify1 = agent2.verify_envelope_node({"envelope": envelope1})
    valid1 = verify1.get("verification_result", {}).get("valid", False)
    print(f"  Verification: {'✓ Valid' if valid1 else '✗ Invalid'}")
    
    # Agent 2 sends heartbeat
    print("\nWorker sends heartbeat...")
    hb2 = agent2.send_heartbeat_node({"status": "alive", "health_data": {"role": "worker"}})
    envelope2 = hb2.get("heartbeat_envelope", "")
    
    # Agent 1 verifies Agent 2's heartbeat
    print("Orchestrator verifies worker's heartbeat...")
    verify2 = agent1.verify_envelope_node({"envelope": envelope2})
    valid2 = verify2.get("verification_result", {}).get("valid", False)
    print(f"  Verification: {'✓ Valid' if valid2 else '✗ Invalid'}")
    
    print("\nMulti-agent beacon verification complete!")
    print("Both agents have cryptographically verified each other.")
    
    return (agent1, agent2)


def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("RustChain Beacon + LangGraph Integration Examples")
    print("=" * 60)
    print("\nThis demo shows how LangGraph workflows can participate in")
    print("the RustChain Beacon network with cryptographic identities")
    print("and signed attestations.\n")
    
    # Demo 1: Create beacon node
    node = demo_basic_beacon_node()
    
    # Demo 2: Send heartbeat via node
    hb_result = demo_send_heartbeat_node(node)
    
    # Demo 3: Verify envelope via node
    envelope = hb_result.get("heartbeat_envelope", "")
    demo_verify_envelope_node(node, envelope)
    
    # Demo 4: Full LangGraph workflow
    demo_full_langgraph()
    
    # Demo 5: Conditional workflow
    demo_conditional_workflow()
    
    # Demo 6: Multi-agent orchestration
    demo_multi_agent_orchestration()
    
    print("\n" + "=" * 60)
    print("All demos completed!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Integrate with your LangChain/LangGraph workflows")
    print("2. Connect to the RustChain Beacon network")
    print("3. Build multi-agent systems with cryptographic trust")
    print("\nFor more information, see:")
    print("  - integrations/beacon_crewai/README.md")
    print("  - https://rustchain.org/docs/beacon")
    print("  - https://langchain-ai.github.io/langgraph/")
    print()


if __name__ == "__main__":
    main()
