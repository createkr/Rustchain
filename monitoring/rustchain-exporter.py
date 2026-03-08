#!/usr/bin/env python3
"""
RustChain Prometheus Exporter - Enhanced Version
Exposes comprehensive RustChain node metrics in Prometheus format

Features:
- Node health and performance metrics
- Network and consensus metrics
- Miner analytics with hardware breakdown
- Transaction and block statistics
- Grafana-friendly label structure
- Real endpoint integration with /api/* endpoints
- Error tracking and scrape duration histograms

Author: RustChain Team
License: MIT
"""
import time
import os
import json
import requests
from prometheus_client import (
    start_http_server, 
    Gauge, Counter, Info, Histogram, Enum,
    generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry
)
from prometheus_client.core import REGISTRY
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('rustchain-exporter')

# =============================================================================
# Configuration
# =============================================================================
RUSTCHAIN_NODE = os.environ.get('RUSTCHAIN_NODE', 'https://rustchain.org')
EXPORTER_PORT = int(os.environ.get('EXPORTER_PORT', 9100))
SCRAPE_INTERVAL = int(os.environ.get('SCRAPE_INTERVAL', 30))
TLS_VERIFY = os.environ.get('TLS_VERIFY', 'true').lower() in ('true', '1', 'yes')
TLS_CA_BUNDLE = os.environ.get('TLS_CA_BUNDLE', None)
REQUEST_TIMEOUT = int(os.environ.get('REQUEST_TIMEOUT', 10))

# =============================================================================
# Prometheus Metrics Definitions
# =============================================================================

# --- Node Health Metrics ---
node_health = Enum(
    'rustchain_node_health',
    'Node health status',
    states=['healthy', 'unhealthy']
)
node_uptime_seconds = Gauge(
    'rustchain_node_uptime_seconds',
    'Node uptime in seconds'
)
node_db_status = Enum(
    'rustchain_node_db_status',
    'Database read/write status',
    states=['ok', 'error']
)
node_version_info = Info(
    'rustchain_node_version',
    'Node version information'
)
node_build_info = Info(
    'rustchain_build',
    'Build information'
)

# --- Network & Consensus Metrics ---
epoch_number = Gauge(
    'rustchain_epoch_number',
    'Current epoch number'
)
epoch_slot = Gauge(
    'rustchain_epoch_slot',
    'Current slot within epoch'
)
epoch_pot = Gauge(
    'rustchain_epoch_pot',
    'Epoch reward pot size in RTC'
)
enrolled_miners = Gauge(
    'rustchain_enrolled_miners_total',
    'Total number of enrolled miners'
)
active_miners = Gauge(
    'rustchain_active_miners_total',
    'Number of currently active miners'
)
total_supply = Gauge(
    'rustchain_total_supply_rtc',
    'Total RTC token supply'
)
circulating_supply = Gauge(
    'rustchain_circulating_supply_rtc',
    'Circulating RTC token supply'
)

# --- Block & Transaction Metrics ---
latest_block_height = Gauge(
    'rustchain_block_height_latest',
    'Latest block height'
)
latest_block_timestamp = Gauge(
    'rustchain_block_timestamp_latest',
    'Latest block timestamp (Unix epoch)'
)
blocks_total = Counter(
    'rustchain_blocks_total',
    'Total number of blocks produced'
)
transactions_total = Counter(
    'rustchain_transactions_total',
    'Total number of transactions processed'
)
tx_pool_size = Gauge(
    'rustchain_tx_pool_size',
    'Current transaction pool size'
)

# --- Miner Analytics (with labels) ---
miners_by_hardware = Gauge(
    'rustchain_miners_by_hardware',
    'Active miners grouped by hardware type',
    ['hardware_type', 'tier']
)
miners_by_arch = Gauge(
    'rustchain_miners_by_architecture',
    'Active miners grouped by CPU architecture',
    ['architecture', 'vintage_class']
)
miners_by_region = Gauge(
    'rustchain_miners_by_region',
    'Active miners grouped by geographic region',
    ['region', 'country']
)
avg_antiquity_multiplier = Gauge(
    'rustchain_antiquity_multiplier_average',
    'Average antiquity multiplier across active miners'
)
antiquity_multiplier_histogram = Histogram(
    'rustchain_antiquity_multiplier',
    'Distribution of antiquity multipliers',
    buckets=[0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0]
)

# --- Performance Metrics ---
scrape_duration_seconds = Histogram(
    'rustchain_scrape_duration_seconds',
    'Duration of metric collection scrapes',
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)
api_request_duration_seconds = Histogram(
    'rustchain_api_request_duration_seconds',
    'Duration of API requests to RustChain node',
    ['endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)
scrape_errors_total = Counter(
    'rustchain_scrape_errors_total',
    'Total number of scrape errors',
    ['error_type']
)
api_errors_total = Counter(
    'rustchain_api_errors_total',
    'Total number of API errors',
    ['endpoint', 'status_code']
)

# --- System Metrics ---
exporter_start_time = Gauge(
    'rustchain_exporter_start_time',
    'Exporter start time (Unix epoch)'
)
exporter_last_scrape_time = Gauge(
    'rustchain_exporter_last_scrape_time',
    'Last successful scrape time (Unix epoch)'
)
exporter_info = Info(
    'rustchain_exporter',
    'Exporter information'
)


# =============================================================================
# Data Classes
# =============================================================================
@dataclass
class NodeHealth:
    """Node health metrics"""
    ok: bool = False
    uptime_s: float = 0.0
    db_rw: bool = False
    version: str = "unknown"
    build: str = "unknown"


@dataclass
class EpochInfo:
    """Epoch and network metrics"""
    epoch: int = 0
    slot: int = 0
    epoch_pot: float = 0.0
    enrolled_miners: int = 0
    total_supply: float = 0.0
    circulating_supply: float = 0.0


@dataclass
class BlockInfo:
    """Block and transaction metrics"""
    height: int = 0
    timestamp: int = 0
    tx_count: int = 0


@dataclass
class MinerStats:
    """Miner statistics"""
    total_active: int = 0
    hardware_counts: Dict[str, Dict[str, int]] = field(default_factory=dict)
    arch_counts: Dict[str, Dict[str, int]] = field(default_factory=dict)
    multipliers: List[float] = field(default_factory=list)


# =============================================================================
# Exporter Class
# =============================================================================
class RustChainExporter:
    """
    RustChain Prometheus Exporter
    
    Collects metrics from RustChain node APIs and exposes them
    in Prometheus format for Grafana visualization.
    """
    
    def __init__(self, node_url: str, verify_tls: bool = True, ca_bundle: Optional[str] = None):
        self.node_url = node_url.rstrip('/')
        self.verify_tls = verify_tls
        self.ca_bundle = ca_bundle
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'RustChain-Prometheus-Exporter/1.0'
        })
        
        # Metrics state
        self.health = NodeHealth()
        self.epoch = EpochInfo()
        self.block = BlockInfo()
        self.miners = MinerStats()
        
        logger.info(f"Initialized exporter for node: {self.node_url}")
    
    def _get_verify_param(self) -> Any:
        """Get verify parameter for requests"""
        if self.ca_bundle:
            return self.ca_bundle
        return self.verify_tls
    
    def _fetch_json(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Fetch JSON data from a node endpoint"""
        url = f"{self.node_url}{endpoint}"
        start_time = time.time()
        
        try:
            response = self.session.get(
                url,
                verify=self._get_verify_param(),
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            # Record API duration
            duration = time.time() - start_time
            api_request_duration_seconds.labels(endpoint=endpoint).observe(duration)
            
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if hasattr(e, 'response') else 0
            api_errors_total.labels(endpoint=endpoint, status_code=str(status)).inc()
            scrape_errors_total.labels(error_type='http_error').inc()
            logger.error(f"HTTP error fetching {endpoint}: {e}")
            
        except requests.exceptions.Timeout:
            api_errors_total.labels(endpoint=endpoint, status_code='timeout').inc()
            scrape_errors_total.labels(error_type='timeout').inc()
            logger.error(f"Timeout fetching {endpoint}")
            
        except requests.exceptions.RequestException as e:
            api_errors_total.labels(endpoint=endpoint, status_code='network').inc()
            scrape_errors_total.labels(error_type='network_error').inc()
            logger.error(f"Network error fetching {endpoint}: {e}")
            
        except json.JSONDecodeError as e:
            scrape_errors_total.labels(error_type='parse_error').inc()
            logger.error(f"JSON parse error for {endpoint}: {e}")
            
        return None
    
    def _collect_health(self) -> None:
        """Collect node health metrics"""
        data = self._fetch_json('/health')
        if not data:
            node_health.state('unhealthy')
            return
        
        self.health.ok = data.get('ok', False)
        self.health.uptime_s = data.get('uptime_s', 0.0)
        self.health.db_rw = data.get('db_rw', False)
        self.health.version = data.get('version', 'unknown')
        self.health.build = data.get('build', 'unknown')
        
        # Update metrics
        node_health.state('healthy' if self.health.ok else 'unhealthy')
        node_uptime_seconds.set(self.health.uptime_s)
        node_db_status.state('ok' if self.health.db_rw else 'error')
        
        node_version_info.info({
            'version': self.health.version,
            'node_url': self.node_url
        })
        node_build_info.info({'build': self.health.build})
    
    def _collect_epoch(self) -> None:
        """Collect epoch and network metrics"""
        data = self._fetch_json('/epoch')
        if not data:
            return
        
        self.epoch.epoch = data.get('epoch', 0)
        self.epoch.slot = data.get('slot', 0)
        self.epoch.epoch_pot = data.get('epoch_pot', 0.0)
        self.epoch.enrolled_miners = data.get('enrolled_miners', 0)
        self.epoch.total_supply = data.get('total_supply_rtc', 0.0)
        self.epoch.circulating_supply = data.get('circulating_supply_rtc', 0.0)
        
        # Update metrics
        epoch_number.set(self.epoch.epoch)
        epoch_slot.set(self.epoch.slot)
        epoch_pot.set(self.epoch.epoch_pot)
        enrolled_miners.set(self.epoch.enrolled_miners)
        total_supply.set(self.epoch.total_supply)
        circulating_supply.set(self.epoch.circulating_supply)
    
    def _collect_blocks(self) -> None:
        """Collect block and transaction metrics"""
        # Try multiple endpoints for block data
        data = self._fetch_json('/blocks/latest') or self._fetch_json('/api/blocks/latest')
        
        if data:
            self.block.height = data.get('height', data.get('block_height', 0))
            self.block.timestamp = data.get('timestamp', data.get('block_timestamp', 0))
            self.block.tx_count = data.get('tx_count', data.get('transaction_count', 0))
            
            latest_block_height.set(self.block.height)
            latest_block_timestamp.set(self.block.timestamp)
        
        # Get transaction pool size
        tx_pool = self._fetch_json('/tx/pool') or self._fetch_json('/api/tx/pool')
        if tx_pool:
            if isinstance(tx_pool, list):
                tx_pool_size.set(len(tx_pool))
            elif isinstance(tx_pool, dict):
                tx_pool_size.set(tx_pool.get('size', tx_pool.get('count', 0)))
    
    def _collect_miners(self) -> None:
        """Collect miner analytics"""
        # Try multiple endpoints for miner data
        data = (
            self._fetch_json('/api/miners') or 
            self._fetch_json('/miners') or
            self._fetch_json('/network/miners')
        )
        
        if not data:
            return
        
        # Handle both list and dict responses
        miners_list = data if isinstance(data, list) else data.get('miners', data.get('active_miners', []))
        
        if not miners_list:
            return
        
        self.miners.total_active = len(miners_list)
        self.miners.hardware_counts = {}
        self.miners.arch_counts = {}
        self.miners.multipliers = []
        
        # Clear previous gauge values by collecting new label sets
        hardware_data = {}
        arch_data = {}
        
        for miner in miners_list:
            # Hardware type and tier
            hw_type = miner.get('hardware_type', miner.get('hardware_model', 'Unknown'))
            tier = miner.get('tier', miner.get('hardware_tier', 'Unknown'))
            hw_key = f"{hw_type}:{tier}"
            hardware_data[hw_key] = hardware_data.get(hw_key, 0) + 1
            
            # Architecture and vintage class
            arch = miner.get('device_arch', miner.get('architecture', 'Unknown'))
            vintage = miner.get('vintage_class', miner.get('cpu_vintage', 'Unknown'))
            arch_key = f"{arch}:{vintage}"
            arch_data[arch_key] = arch_data.get(arch_key, 0) + 1
            
            # Antiquity multiplier
            mult = float(miner.get('antiquity_multiplier', miner.get('multiplier', 1.0)))
            self.miners.multipliers.append(mult)
            antiquity_multiplier_histogram.observe(mult)
        
        # Update hardware gauge
        for key, count in hardware_data.items():
            hw_type, tier = key.rsplit(':', 1)
            miners_by_hardware.labels(hardware_type=hw_type, tier=tier).set(count)
        
        # Update architecture gauge
        for key, count in arch_data.items():
            arch, vintage = key.rsplit(':', 1)
            miners_by_arch.labels(architecture=arch, vintage_class=vintage).set(count)
        
        # Update average multiplier
        if self.miners.multipliers:
            avg_mult = sum(self.miners.multipliers) / len(self.miners.multipliers)
            avg_antiquity_multiplier.set(avg_mult)
        
        active_miners.set(self.miners.total_active)
    
    def collect(self) -> None:
        """Collect all metrics from the node"""
        start_time = time.time()
        
        try:
            self._collect_health()
            self._collect_epoch()
            self._collect_blocks()
            self._collect_miners()
            
            # Update scrape timing
            duration = time.time() - start_time
            scrape_duration_seconds.observe(duration)
            exporter_last_scrape_time.set(time.time())
            
            logger.info(f"Metrics collected successfully in {duration:.3f}s")
            
        except Exception as e:
            scrape_errors_total.labels(error_type='collection_error').inc()
            logger.error(f"Error collecting metrics: {e}")
            raise


# =============================================================================
# Custom Collector for REGISTRY
# =============================================================================
class RustChainCollector:
    """Prometheus collector that integrates with the exporter"""
    
    def __init__(self, exporter: RustChainExporter):
        self.exporter = exporter
    
    def collect(self):
        """Collect metrics for Prometheus"""
        self.exporter.collect()
        
        # Yield all metrics from the registry
        for metric in REGISTRY.collect():
            yield metric


# =============================================================================
# Metrics Handler for HTTP Server
# =============================================================================
def make_wsgi_app(exporter: RustChainExporter) -> callable:
    """Create WSGI app for serving metrics"""
    from prometheus_client import make_wsgi_app as _make_wsgi_app
    
    def custom_app(environ, start_response):
        # Collect fresh metrics before serving
        exporter.collect()
        return _make_wsgi_app()(environ, start_response)
    
    return custom_app


# =============================================================================
# Main Entry Point
# =============================================================================
def main():
    """Main exporter entry point"""
    logger.info("=" * 60)
    logger.info("RustChain Prometheus Exporter v1.0")
    logger.info("=" * 60)
    logger.info(f"Node URL: {RUSTCHAIN_NODE}")
    logger.info(f"Exporter Port: {EXPORTER_PORT}")
    logger.info(f"Scrape Interval: {SCRAPE_INTERVAL}s")
    logger.info(f"TLS Verify: {TLS_VERIFY}")
    logger.info("=" * 60)
    
    # Initialize exporter
    exporter = RustChainExporter(
        node_url=RUSTCHAIN_NODE,
        verify_tls=TLS_VERIFY,
        ca_bundle=TLS_CA_BUNDLE
    )
    
    # Set exporter info
    exporter_info.info({
        'version': '1.0.0',
        'node_url': RUSTCHAIN_NODE,
        'scrape_interval': str(SCRAPE_INTERVAL)
    })
    exporter_start_time.set(time.time())
    
    # Register custom collector
    collector = RustChainCollector(exporter)
    REGISTRY.register(collector)
    
    # Start HTTP server
    start_http_server(EXPORTER_PORT)
    logger.info(f"Exporter started on port {EXPORTER_PORT}")
    logger.info(f"Metrics endpoint: http://localhost:{EXPORTER_PORT}/metrics")
    logger.info("")
    logger.info("Waiting for Prometheus to scrape...")
    
    # Keep running
    try:
        while True:
            time.sleep(SCRAPE_INTERVAL)
    except KeyboardInterrupt:
        logger.info("Exporter shutting down...")


if __name__ == '__main__':
    main()
