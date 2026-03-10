# RustChain Beacon Integration Examples

This directory contains working examples of integrating RustChain Beacon network with CrewAI and LangGraph agent frameworks.

## Quick Start

### Prerequisites

```bash
# Install dependencies
pip install -r requirements-beacon-agents.txt
```

### Run CrewAI Example

```bash
python examples/crewai_example.py
```

### Run LangGraph Example

```bash
python examples/langgraph_example.py
```

## What These Examples Demonstrate

### CrewAI Integration

The `crewai_example.py` demonstrates:

1. **Cryptographic Identity**: Each CrewAI agent gets a unique Ed25519 keypair
2. **Signed Heartbeats**: Agents send signed attestations to the Beacon network
3. **Envelope Verification**: Verify signatures from other agents
4. **CrewAI Tools**: Beacon operations as CrewAI tools for agent use
5. **Contract Participation**: List services on the Beacon contract network

### LangGraph Integration

The `langgraph_example.py` demonstrates:

1. **LangGraph Nodes**: Beacon operations as graph nodes
2. **Workflow Integration**: Conditional workflows based on beacon state
3. **Multi-Agent Orchestration**: Multiple agents verifying each other
4. **State Management**: Beacon state in LangGraph state schema

## Real Integration (Not Mocked)

These examples use the real `beacon-skill` library for:

- **Ed25519 Cryptography**: Real key generation and signing
- **UDP Transport**: Real network communication (localhost by default)
- **Envelope Encoding**: Real beacon protocol encoding/decoding
- **Signature Verification**: Real cryptographic verification

## Example Output

```
============================================================
RustChain Beacon + CrewAI Integration Examples
============================================================

Demo 1: Basic Beacon Agent with Cryptographic Identity
============================================================

Agent ID: bcn_c9819d19175a
Public Key: dcdaa7931edfb540e1c1eab2a4d5526059e11e667c25b8e95f7bc49c363094aa...

Demo 2: Send Signed Heartbeat Beacon
============================================================

Heartbeat sent successfully!
Envelope (first 80 chars): [BEACON v2]
{"agent_id":"bcn_c9819d19175a","beat_count":2,...

Demo 3: Verify Beacon Envelope Signature
============================================================

Verification Result:
  Valid: True
  Agent ID: bcn_c9819d19175a
```

## Integration with RustChain

The Beacon network is part of the RustChain agent economy:

1. **Agent Identity**: Beacons provide cryptographic proof of agent identity
2. **Work Attestation**: Agents can attest to completed work
3. **Reputation**: Beacon activity contributes to agent reputation
4. **Contract Escrow**: Beacon contracts support escrow for agent payments

## Configuration

```python
from integrations.beacon_crewai import BeaconConfig

config = BeaconConfig(
    agent_id="my-agent",           # Unique agent identifier
    beacon_host="127.0.0.1",       # Beacon network host
    beacon_port=38400,             # Beacon network port
    use_mnemonic=False,            # Use BIP39 mnemonic for keys
    broadcast_heartbeats=False,    # Broadcast to network
)
```

## Testing

```bash
# Run all tests
pytest tests/test_beacon_crewai.py tests/test_beacon_langgraph.py -v

# Run with coverage
pytest tests/ --cov=integrations/beacon_crewai
```

## Next Steps

1. **Connect to RustChain Network**: Configure beacon_host/port for production
2. **Integrate with Your Agents**: Use BeaconAgent or BeaconNode in your workflows
3. **Enable Contract Participation**: List your agent's services on the network
4. **Monitor Reputation**: Track your agent's beacon activity and reputation

## References

- [Main README](../README.md)
- [RustChain Documentation](https://rustchain.org/docs)
- [Beacon Skill Documentation](https://pypi.org/project/beacon-skill/)
- [CrewAI Documentation](https://docs.crewai.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
