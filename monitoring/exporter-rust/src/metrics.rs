//! Prometheus metrics definitions and registry

use prometheus::{
    CounterVec, Gauge, GaugeVec, Histogram, HistogramVec, IntCounter, IntGauge,
    Opts, Registry, TextEncoder,
};
use std::sync::Arc;

/// Metrics registry containing all Prometheus metrics
#[derive(Clone)]
pub struct MetricsRegistry {
    /// Prometheus registry
    pub registry: Registry,

    // Node Health Metrics
    pub node_health: Gauge,
    pub node_uptime_seconds: Gauge,
    pub node_db_status: Gauge,
    pub node_version: GaugeVec,

    // Network & Consensus Metrics
    pub epoch_number: IntGauge,
    pub epoch_slot: IntGauge,
    pub epoch_pot: Gauge,
    pub enrolled_miners_total: IntGauge,
    pub active_miners_total: IntGauge,
    pub total_supply_rtc: Gauge,
    pub circulating_supply_rtc: Gauge,

    // Block & Transaction Metrics
    pub block_height_latest: IntGauge,
    pub block_timestamp_latest: IntGauge,
    pub blocks_total: IntCounter,
    pub transactions_total: IntCounter,
    pub tx_pool_size: IntGauge,

    // Miner Analytics (with labels)
    pub miners_by_hardware: GaugeVec,
    pub miners_by_architecture: GaugeVec,
    pub miners_by_region: GaugeVec,
    pub antiquity_multiplier_average: Gauge,
    pub antiquity_multiplier_histogram: Histogram,

    // Performance Metrics
    pub scrape_duration_seconds: Histogram,
    pub api_request_duration_seconds: HistogramVec,
    pub scrape_errors_total: CounterVec,
    pub api_errors_total: CounterVec,

    // System Metrics
    pub exporter_start_time: Gauge,
    pub exporter_last_scrape_time: Gauge,
    pub exporter_info: GaugeVec,
}

impl MetricsRegistry {
    /// Create a new metrics registry with all metrics registered
    pub fn new() -> Self {
        let registry = Registry::new_custom(Some("rustchain".to_string()), None)
            .expect("Failed to create Prometheus registry");

        // Node Health Metrics
        let node_health = Gauge::with_opts(Opts::new(
            "rustchain_node_health",
            "Node health status (1=healthy, 0=unhealthy)"
        )).expect("Failed to create node_health metric");

        let node_uptime_seconds = Gauge::with_opts(Opts::new(
            "rustchain_node_uptime_seconds",
            "Node uptime in seconds"
        )).expect("Failed to create node_uptime_seconds metric");

        let node_db_status = Gauge::with_opts(Opts::new(
            "rustchain_node_db_status",
            "Database read/write status (1=ok, 0=error)"
        )).expect("Failed to create node_db_status metric");

        let node_version = GaugeVec::new(
            Opts::new("rustchain_node_version_info", "Node version information"),
            &["version", "node_url"]
        ).expect("Failed to create node_version metric");

        // Network & Consensus Metrics
        let epoch_number = IntGauge::with_opts(Opts::new(
            "rustchain_epoch_number",
            "Current epoch number"
        )).expect("Failed to create epoch_number metric");

        let epoch_slot = IntGauge::with_opts(Opts::new(
            "rustchain_epoch_slot",
            "Current slot within epoch"
        )).expect("Failed to create epoch_slot metric");

        let epoch_pot = Gauge::with_opts(Opts::new(
            "rustchain_epoch_pot",
            "Epoch reward pot size in RTC"
        )).expect("Failed to create epoch_pot metric");

        let enrolled_miners_total = IntGauge::with_opts(Opts::new(
            "rustchain_enrolled_miners_total",
            "Total number of enrolled miners"
        )).expect("Failed to create enrolled_miners_total metric");

        let active_miners_total = IntGauge::with_opts(Opts::new(
            "rustchain_active_miners_total",
            "Number of currently active miners"
        )).expect("Failed to create active_miners_total metric");

        let total_supply_rtc = Gauge::with_opts(Opts::new(
            "rustchain_total_supply_rtc",
            "Total RTC token supply"
        )).expect("Failed to create total_supply_rtc metric");

        let circulating_supply_rtc = Gauge::with_opts(Opts::new(
            "rustchain_circulating_supply_rtc",
            "Circulating RTC token supply"
        )).expect("Failed to create circulating_supply_rtc metric");

        // Block & Transaction Metrics
        let block_height_latest = IntGauge::with_opts(Opts::new(
            "rustchain_block_height_latest",
            "Latest block height"
        )).expect("Failed to create block_height_latest metric");

        let block_timestamp_latest = IntGauge::with_opts(Opts::new(
            "rustchain_block_timestamp_latest",
            "Latest block timestamp (Unix epoch)"
        )).expect("Failed to create block_timestamp_latest metric");

        let blocks_total = IntCounter::with_opts(Opts::new(
            "rustchain_blocks_total",
            "Total number of blocks produced"
        )).expect("Failed to create blocks_total metric");

        let transactions_total = IntCounter::with_opts(Opts::new(
            "rustchain_transactions_total",
            "Total number of transactions processed"
        )).expect("Failed to create transactions_total metric");

        let tx_pool_size = IntGauge::with_opts(Opts::new(
            "rustchain_tx_pool_size",
            "Current transaction pool size"
        )).expect("Failed to create tx_pool_size metric");

        // Miner Analytics
        let miners_by_hardware = GaugeVec::new(
            Opts::new("rustchain_miners_by_hardware", "Active miners grouped by hardware type"),
            &["hardware_type", "tier"]
        ).expect("Failed to create miners_by_hardware metric");

        let miners_by_architecture = GaugeVec::new(
            Opts::new("rustchain_miners_by_architecture", "Active miners grouped by CPU architecture"),
            &["architecture", "vintage_class"]
        ).expect("Failed to create miners_by_architecture metric");

        let miners_by_region = GaugeVec::new(
            Opts::new("rustchain_miners_by_region", "Active miners grouped by geographic region"),
            &["region", "country"]
        ).expect("Failed to create miners_by_region metric");

        let antiquity_multiplier_average = Gauge::with_opts(Opts::new(
            "rustchain_antiquity_multiplier_average",
            "Average antiquity multiplier across active miners"
        )).expect("Failed to create antiquity_multiplier_average metric");

        let antiquity_multiplier_histogram = Histogram::with_opts(
            prometheus::HistogramOpts::new(
                "rustchain_antiquity_multiplier",
                "Distribution of antiquity multipliers"
            )
            .buckets(vec![0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0])
        ).expect("Failed to create antiquity_multiplier_histogram metric");

        // Performance Metrics
        let scrape_duration_seconds = Histogram::with_opts(
            prometheus::HistogramOpts::new(
                "rustchain_scrape_duration_seconds",
                "Duration of metric collection scrapes"
            )
            .buckets(vec![0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0])
        ).expect("Failed to create scrape_duration_seconds metric");

        let api_request_duration_seconds = HistogramVec::new(
            prometheus::HistogramOpts::new(
                "rustchain_api_request_duration_seconds",
                "Duration of API requests to RustChain node"
            )
            .buckets(vec![0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]),
            &["endpoint"]
        ).expect("Failed to create api_request_duration_seconds metric");

        let scrape_errors_total = CounterVec::new(
            Opts::new("rustchain_scrape_errors_total", "Total number of scrape errors"),
            &["error_type"]
        ).expect("Failed to create scrape_errors_total metric");

        let api_errors_total = CounterVec::new(
            Opts::new("rustchain_api_errors_total", "Total number of API errors"),
            &["endpoint", "status_code"]
        ).expect("Failed to create api_errors_total metric");

        // System Metrics
        let exporter_start_time = Gauge::with_opts(Opts::new(
            "rustchain_exporter_start_time",
            "Exporter start time (Unix epoch)"
        )).expect("Failed to create exporter_start_time metric");

        let exporter_last_scrape_time = Gauge::with_opts(Opts::new(
            "rustchain_exporter_last_scrape_time",
            "Last successful scrape time (Unix epoch)"
        )).expect("Failed to create exporter_last_scrape_time metric");

        let exporter_info = GaugeVec::new(
            Opts::new("rustchain_exporter_info", "Exporter information"),
            &["version", "node_url", "scrape_interval"]
        ).expect("Failed to create exporter_info metric");

        // Register all metrics
        registry.register(Box::new(node_health.clone())).expect("Failed to register node_health");
        registry.register(Box::new(node_uptime_seconds.clone())).expect("Failed to register node_uptime_seconds");
        registry.register(Box::new(node_db_status.clone())).expect("Failed to register node_db_status");
        registry.register(Box::new(node_version.clone())).expect("Failed to register node_version");

        registry.register(Box::new(epoch_number.clone())).expect("Failed to register epoch_number");
        registry.register(Box::new(epoch_slot.clone())).expect("Failed to register epoch_slot");
        registry.register(Box::new(epoch_pot.clone())).expect("Failed to register epoch_pot");
        registry.register(Box::new(enrolled_miners_total.clone())).expect("Failed to register enrolled_miners_total");
        registry.register(Box::new(active_miners_total.clone())).expect("Failed to register active_miners_total");
        registry.register(Box::new(total_supply_rtc.clone())).expect("Failed to register total_supply_rtc");
        registry.register(Box::new(circulating_supply_rtc.clone())).expect("Failed to register circulating_supply_rtc");

        registry.register(Box::new(block_height_latest.clone())).expect("Failed to register block_height_latest");
        registry.register(Box::new(block_timestamp_latest.clone())).expect("Failed to register block_timestamp_latest");
        registry.register(Box::new(blocks_total.clone())).expect("Failed to register blocks_total");
        registry.register(Box::new(transactions_total.clone())).expect("Failed to register transactions_total");
        registry.register(Box::new(tx_pool_size.clone())).expect("Failed to register tx_pool_size");

        registry.register(Box::new(miners_by_hardware.clone())).expect("Failed to register miners_by_hardware");
        registry.register(Box::new(miners_by_architecture.clone())).expect("Failed to register miners_by_architecture");
        registry.register(Box::new(miners_by_region.clone())).expect("Failed to register miners_by_region");
        registry.register(Box::new(antiquity_multiplier_average.clone())).expect("Failed to register antiquity_multiplier_average");
        registry.register(Box::new(antiquity_multiplier_histogram.clone())).expect("Failed to register antiquity_multiplier_histogram");

        registry.register(Box::new(scrape_duration_seconds.clone())).expect("Failed to register scrape_duration_seconds");
        registry.register(Box::new(api_request_duration_seconds.clone())).expect("Failed to register api_request_duration_seconds");
        registry.register(Box::new(scrape_errors_total.clone())).expect("Failed to register scrape_errors_total");
        registry.register(Box::new(api_errors_total.clone())).expect("Failed to register api_errors_total");

        registry.register(Box::new(exporter_start_time.clone())).expect("Failed to register exporter_start_time");
        registry.register(Box::new(exporter_last_scrape_time.clone())).expect("Failed to register exporter_last_scrape_time");
        registry.register(Box::new(exporter_info.clone())).expect("Failed to register exporter_info");

        Self {
            registry,
            node_health,
            node_uptime_seconds,
            node_db_status,
            node_version,
            epoch_number,
            epoch_slot,
            epoch_pot,
            enrolled_miners_total,
            active_miners_total,
            total_supply_rtc,
            circulating_supply_rtc,
            block_height_latest,
            block_timestamp_latest,
            blocks_total,
            transactions_total,
            tx_pool_size,
            miners_by_hardware,
            miners_by_architecture,
            miners_by_region,
            antiquity_multiplier_average,
            antiquity_multiplier_histogram,
            scrape_duration_seconds,
            api_request_duration_seconds,
            scrape_errors_total,
            api_errors_total,
            exporter_start_time,
            exporter_last_scrape_time,
            exporter_info,
        }
    }

    /// Encode metrics in Prometheus text format
    pub fn encode(&self) -> Result<String, prometheus::Error> {
        let encoder = TextEncoder::new();
        let metric_families = self.registry.gather();
        let mut buffer = String::new();
        encoder.encode_utf8(&metric_families, &mut buffer)?;
        Ok(buffer)
    }

    /// Reset all counter metrics (useful for testing)
    pub fn reset_counters(&self) {
        self.blocks_total.reset();
        self.transactions_total.reset();
        self.scrape_errors_total.reset();
        self.api_errors_total.reset();
    }
}

impl Default for MetricsRegistry {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_registry_creation() {
        let registry = MetricsRegistry::new();
        assert!(registry.registry.gather().len() > 0);
    }

    #[test]
    fn test_metrics_encoding() {
        let registry = MetricsRegistry::new();
        let encoded = registry.encode().expect("Failed to encode metrics");
        assert!(encoded.contains("rustchain_node_health"));
        assert!(encoded.contains("rustchain_epoch_number"));
    }

    #[test]
    fn test_gauge_operations() {
        let registry = MetricsRegistry::new();
        registry.node_health.set(1.0);
        assert_eq!(registry.node_health.get(), 1.0);
    }

    #[test]
    fn test_counter_operations() {
        let registry = MetricsRegistry::new();
        let initial = registry.blocks_total.get();
        registry.blocks_total.inc();
        assert_eq!(registry.blocks_total.get(), initial + 1);
    }

    #[test]
    fn test_labeled_gauge_operations() {
        let registry = MetricsRegistry::new();
        registry
            .miners_by_hardware
            .with_label_values(&["PowerPC G4", "Vintage"])
            .set(5.0);
        assert_eq!(
            registry
                .miners_by_hardware
                .with_label_values(&["PowerPC G4", "Vintage"])
                .get(),
            5.0
        );
    }
}
