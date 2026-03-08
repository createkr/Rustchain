# RustChain Prometheus Metrics Exporter

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Rust](https://img.shields.io/badge/Rust-1.70+-orange.svg)](https://www.rust-lang.org)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org)

Complete Prometheus metrics exporter for RustChain nodes with Grafana integration, comprehensive monitoring, and alerting capabilities.

## Overview

The RustChain Prometheus Exporter provides real-time visibility into your RustChain node's health, performance, and network activity. It supports both Python and Rust implementations, offering flexibility for different deployment scenarios.

## Features

- **Node Health Monitoring**: Real-time health status, uptime, database status
- **Network Metrics**: Epoch, slot, enrolled miners, token supply
- **Miner Analytics**: Hardware breakdown, architecture distribution, antiquity multipliers
- **Block Statistics**: Latest block height, transaction counts, pool size
- **Performance Metrics**: Scrape duration, API latency histograms
- **Grafana Integration**: Pre-built dashboards and alerting rules
- **Dual Implementation**: Python for quick deployment, Rust for production performance

## Quick Start

### Python Exporter (Recommended for Development)

```bash
cd monitoring

# Install dependencies
pip install -r requirements.txt

# Run with defaults (scrapes https://rustchain.org)
python rustchain-exporter.py

# Run with custom node
RUSTCHAIN_NODE=http://localhost:8099 python rustchain-exporter.py
```

### Rust Exporter (Recommended for Production)

```bash
cd monitoring/exporter-rust

# Build
cargo build --release

# Run with defaults
./target/release/rustchain-exporter

# Run with environment variables
RUSTCHAIN_NODE=http://localhost:8099 EXPORTER_PORT=9100 ./target/release/rustchain-exporter
```

### Docker Deployment

```bash
cd monitoring
docker-compose up -d
```

Access Grafana at: http://localhost:3000 (admin/rustchain)

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RUSTCHAIN_NODE` | `https://rustchain.org` | RustChain node URL to scrape |
| `EXPORTER_PORT` | `9100` | Port to expose metrics endpoint |
| `SCRAPE_INTERVAL` | `30` | Seconds between metric collections |
| `TLS_VERIFY` | `true` | Verify TLS certificates |
| `TLS_CA_BUNDLE` | `None` | Path to CA bundle (Python only) |
| `REQUEST_TIMEOUT` | `10` | HTTP request timeout in seconds |

### Example `.env` File

```bash
# monitoring/.env
RUSTCHAIN_NODE=http://localhost:8099
EXPORTER_PORT=9100
SCRAPE_INTERVAL=30
TLS_VERIFY=true
REQUEST_TIMEOUT=10
```

## Metrics Reference

### Node Health Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `rustchain_node_health` | Enum | Node health status (healthy/unhealthy) |
| `rustchain_node_uptime_seconds` | Gauge | Node uptime in seconds |
| `rustchain_node_db_status` | Enum | Database status (ok/error) |
| `rustchain_node_version_info` | Info | Node version information |

### Network & Consensus Metrics

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `rustchain_epoch_number` | Gauge | Current epoch number | - |
| `rustchain_epoch_slot` | Gauge | Current slot within epoch | - |
| `rustchain_epoch_pot` | Gauge | Epoch reward pot (RTC) | - |
| `rustchain_enrolled_miners_total` | Gauge | Total enrolled miners | - |
| `rustchain_active_miners_total` | Gauge | Currently active miners | - |
| `rustchain_total_supply_rtc` | Gauge | Total RTC supply | - |
| `rustchain_circulating_supply_rtc` | Gauge | Circulating RTC supply | - |

### Block & Transaction Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `rustchain_block_height_latest` | Gauge | Latest block height |
| `rustchain_block_timestamp_latest` | Gauge | Latest block timestamp |
| `rustchain_blocks_total` | Counter | Total blocks produced |
| `rustchain_transactions_total` | Counter | Total transactions processed |
| `rustchain_tx_pool_size` | Gauge | Current transaction pool size |

### Miner Analytics (with Labels)

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `rustchain_miners_by_hardware` | Gauge | Miners by hardware type | `hardware_type`, `tier` |
| `rustchain_miners_by_architecture` | Gauge | Miners by architecture | `architecture`, `vintage_class` |
| `rustchain_miners_by_region` | Gauge | Miners by region | `region`, `country` |
| `rustchain_antiquity_multiplier_average` | Gauge | Average antiquity multiplier | - |
| `rustchain_antiquity_multiplier` | Histogram | Multiplier distribution | - |

### Performance Metrics

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `rustchain_scrape_duration_seconds` | Histogram | Collection duration | - |
| `rustchain_api_request_duration_seconds` | Histogram | API request latency | `endpoint` |
| `rustchain_scrape_errors_total` | Counter | Total scrape errors | `error_type` |
| `rustchain_api_errors_total` | Counter | Total API errors | `endpoint`, `status_code` |

## Grafana Dashboard

The included Grafana dashboard provides comprehensive visualization:

### Panels

1. **Node Health** - Real-time health indicator with color coding
2. **Active Miners** - Current miner count with trend
3. **Current Epoch** - Blockchain epoch number
4. **Epoch Pot** - Reward pool size
5. **Active Miners (24h)** - Time series graph
6. **RTC Total Supply** - Supply over time
7. **Miners by Hardware Type** - Pie chart distribution
8. **Miners by Architecture** - Architecture breakdown
9. **Average Antiquity Multiplier** - Gauge with thresholds
10. **Node Uptime** - Uptime graph
11. **Scrape Duration** - Performance with alert

### Import Dashboard

1. Open Grafana (http://localhost:3000)
2. Go to Dashboards → Import
3. Upload `grafana-dashboard.json`
4. Select Prometheus data source
5. Click Import

## Alerting Rules

Pre-configured alerts in `prometheus.yml`:

```yaml
groups:
  - name: rustchain_alerts
    rules:
      # Node Down Alert
      - alert: RustChainNodeDown
        expr: rustchain_node_health == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "RustChain node is down"
          description: "Node {{ $labels.instance }} has been unhealthy for 2 minutes"

      # Miner Drop Alert
      - alert: RustChainMinerDrop
        expr: rate(rustchain_active_miners_total[5m]) < -0.2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Significant miner drop detected"
          description: "Active miners decreased by >20% in 5 minutes"

      # Slow Scrape Alert
      - alert: RustChainSlowScrape
        expr: rustchain_scrape_duration_seconds > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Slow metric collection"
          description: "Scrape duration exceeds 5 seconds"
```

## API Endpoints

The exporter expects these endpoints from the RustChain node:

| Endpoint | Method | Response |
|----------|--------|----------|
| `/health` | GET | `{"ok": true, "uptime_s": 3600, "db_rw": true, "version": "1.0.0"}` |
| `/epoch` | GET | `{"epoch": 100, "slot": 50, "epoch_pot": 1000, "enrolled_miners": 25}` |
| `/blocks/latest` | GET | `{"height": 1000, "timestamp": 1234567890, "tx_count": 10}` |
| `/api/miners` | GET | `[{"hardware_type": "PowerPC G4", "antiquity_multiplier": 2.5}]` |
| `/tx/pool` | GET | `{"size": 5}` or `[{...}]` |

## Testing

### Python Tests

```bash
cd monitoring
pip install -r requirements.txt
python -m pytest tests/ -v --cov=rustchain-exporter
```

### Rust Tests

```bash
cd monitoring/exporter-rust
cargo test --all
```

### Integration Test

```bash
# Start exporter
python rustchain-exporter.py &

# Scrape metrics
curl http://localhost:9100/metrics

# Verify output
curl http://localhost:9100/metrics | grep rustchain
```

## Troubleshooting

### Exporter Not Starting

```bash
# Check Python dependencies
pip install -r requirements.txt

# Check Rust build
cargo build --release

# Verify node is accessible
curl https://rustchain.org/health
```

### No Metrics Data

1. **Check Prometheus targets**: http://localhost:9090/targets
2. **Verify exporter endpoint**: `curl http://localhost:9100/metrics`
3. **Check exporter logs**: `docker logs rustchain-exporter`
4. **Test node connectivity**: `curl https://rustchain.org/health`

### Grafana Shows No Data

1. **Verify data source**: Grafana → Configuration → Data Sources → Test
2. **Check time range**: Ensure you're viewing the correct time period
3. **Verify metric names**: Use Explore to query `rustchain_*`
4. **Check scrape interval**: Match exporter and Prometheus intervals

### High Scrape Duration

1. **Increase timeout**: `REQUEST_TIMEOUT=30`
2. **Reduce scrape frequency**: `SCRAPE_INTERVAL=60`
3. **Check node performance**: Node might be overloaded
4. **Network latency**: Deploy exporter closer to node

## Production Deployment

### Systemd Service (Python)

```ini
# /etc/systemd/system/rustchain-exporter.service
[Unit]
Description=RustChain Prometheus Exporter
After=network.target

[Service]
Type=simple
User=rustchain
WorkingDirectory=/opt/rustchain/monitoring
Environment=PATH=/opt/rustchain/venv/bin
Environment=RUSTCHAIN_NODE=http://localhost:8099
ExecStart=/opt/rustchain/venv/bin/python rustchain-exporter.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Systemd Service (Rust)

```ini
# /etc/systemd/system/rustchain-exporter.service
[Unit]
Description=RustChain Prometheus Exporter (Rust)
After=network.target

[Service]
Type=simple
User=rustchain
WorkingDirectory=/opt/rustchain/monitoring/exporter-rust
ExecStart=/opt/rustchain/monitoring/exporter-rust/target/release/rustchain-exporter
Restart=always
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
```

### Docker Compose

```yaml
version: '3.8'
services:
  exporter:
    build:
      context: ./exporter-rust
      dockerfile: ../Dockerfile.exporter-rust
    environment:
      - RUSTCHAIN_NODE=http://node:8099
      - EXPORTER_PORT=9100
    ports:
      - "9100:9100"
    restart: unless-stopped
    networks:
      - monitoring

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
    ports:
      - "9090:9090"
    depends_on:
      - exporter
    networks:
      - monitoring

  grafana:
    image: grafana/grafana:latest
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana-dashboard.json:/etc/grafana/provisioning/dashboards/dashboard.json
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=rustchain
      - GF_USERS_ALLOW_SIGN_UP=false
    ports:
      - "3000:3000"
    depends_on:
      - prometheus
    networks:
      - monitoring

volumes:
  prometheus_data:
  grafana_data:

networks:
  monitoring:
```

## Development

### Adding New Metrics

1. **Define metric** in `metrics.rs` (Rust) or at module top (Python)
2. **Register metric** with Prometheus registry
3. **Update collector** to populate metric
4. **Add tests** for new metric
5. **Update documentation**

### Code Style

**Python**:
```bash
black rustchain-exporter.py
flake8 rustchain-exporter.py
mypy rustchain-exporter.py
```

**Rust**:
```bash
cargo fmt
cargo clippy
```

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  RustChain Node │────▶│  Metrics         │────▶│  Prometheus     │
│  (port 8099)    │     │  Exporter        │     │  (port 9090)    │
│                 │     │  (port 9100)     │     │                 │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                                                          │ Scrape
                                                          ▼
                                                   ┌─────────────────┐
                                                   │  Grafana        │
                                                   │  (port 3000)    │
                                                   └─────────────────┘
```

## License

MIT License - See LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `cargo test && pytest`
5. Submit a pull request

## Support

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Documentation**: See `docs/` directory

## Changelog

### v1.0.0 (2025)
- Initial release
- Python exporter with comprehensive metrics
- Rust exporter for production use
- Grafana dashboard and alerting
- Docker deployment support
- Full test coverage
