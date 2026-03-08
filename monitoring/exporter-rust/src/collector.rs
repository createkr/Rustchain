//! Metrics collector that fetches data from RustChain node APIs

use crate::config::Config;
use crate::error::{Error, Result};
use crate::metrics::MetricsRegistry;
use serde::Deserialize;
use std::collections::HashMap;
use std::sync::Arc;
use std::time::Instant;
use tokio::sync::RwLock;
use tokio::time::{sleep, Duration};
use tracing::{debug, error, info, warn};

/// Node health response
#[derive(Debug, Deserialize, Clone)]
pub struct HealthResponse {
    pub ok: bool,
    #[serde(default)]
    pub uptime_s: f64,
    #[serde(default)]
    pub db_rw: bool,
    #[serde(default)]
    pub version: String,
    #[serde(default)]
    pub build: String,
}

/// Epoch response
#[derive(Debug, Deserialize, Clone)]
pub struct EpochResponse {
    #[serde(default)]
    pub epoch: u64,
    #[serde(default)]
    pub slot: u64,
    #[serde(default)]
    pub epoch_pot: f64,
    #[serde(default)]
    pub enrolled_miners: u64,
    #[serde(default)]
    pub total_supply_rtc: f64,
    #[serde(default)]
    pub circulating_supply_rtc: f64,
}

/// Block response
#[derive(Debug, Deserialize, Clone)]
pub struct BlockResponse {
    #[serde(default)]
    pub height: u64,
    #[serde(default)]
    pub timestamp: i64,
    #[serde(default)]
    pub tx_count: u64,
}

/// Miner information
#[derive(Debug, Deserialize, Clone)]
pub struct MinerInfo {
    #[serde(default)]
    pub hardware_type: String,
    #[serde(default)]
    pub hardware_model: String,
    #[serde(default)]
    pub tier: String,
    #[serde(default)]
    pub hardware_tier: String,
    #[serde(default)]
    pub device_arch: String,
    #[serde(default)]
    pub architecture: String,
    #[serde(default)]
    pub vintage_class: String,
    #[serde(default)]
    pub cpu_vintage: String,
    #[serde(default)]
    pub antiquity_multiplier: f64,
    #[serde(default)]
    pub multiplier: f64,
    #[serde(default)]
    pub region: String,
    #[serde(default)]
    pub country: String,
}

/// Miners response (can be array or object with miners field)
#[derive(Debug, Deserialize, Clone)]
#[serde(untagged)]
pub enum MinersResponse {
    /// Direct array of miners
    List(Vec<MinerInfo>),
    /// Object with miners field
    Object {
        #[serde(default)]
        miners: Vec<MinerInfo>,
        #[serde(default)]
        active_miners: Vec<MinerInfo>,
    },
}

impl MinersResponse {
    /// Get the list of miners from the response
    pub fn into_miners(self) -> Vec<MinerInfo> {
        match self {
            MinersResponse::List(miners) => miners,
            MinersResponse::Object { miners, active_miners } => {
                if !miners.is_empty() {
                    miners
                } else {
                    active_miners
                }
            }
        }
    }
}

/// Metrics collector that periodically fetches data from the node
#[derive(Clone)]
pub struct MetricsCollector {
    node_url: String,
    metrics: Arc<RwLock<MetricsRegistry>>,
    client: reqwest::Client,
}

impl MetricsCollector {
    /// Create a new metrics collector
    pub fn new(node_url: String, metrics: Arc<RwLock<MetricsRegistry>>) -> Self {
        let client = reqwest::Client::builder()
            .timeout(Duration::from_secs(10))
            .build()
            .expect("Failed to create HTTP client");
        
        Self {
            node_url,
            metrics,
            client,
        }
    }

    /// Fetch JSON from a node endpoint
    async fn fetch_json<T: for<'de> Deserialize<'de>>(&self, endpoint: &str) -> Result<T> {
        let url = format!("{}{}", self.node_url.trim_end_matches('/'), endpoint);
        let start = Instant::now();
        
        let response = self.client
            .get(&url)
            .header("Accept", "application/json")
            .header("User-Agent", "RustChain-Prometheus-Exporter/0.1.0")
            .send()
            .await
            .map_err(|e| Error::Http(e))?;
        
        let status = response.status();
        let duration = start.elapsed();
        
        // Record API duration
        {
            let metrics = self.metrics.read().await;
            metrics
                .api_request_duration_seconds
                .with_label_values(&[endpoint])
                .observe(duration.as_secs_f64());
        }
        
        if !status.is_success() {
            let metrics = self.metrics.read().await;
            metrics
                .api_errors_total
                .with_label_values(&[endpoint, &status.as_u16().to_string()])
                .inc();
            return Err(Error::NodeApi(format!(
                "HTTP {}: {}",
                status,
                response.text().await.unwrap_or_default()
            )));
        }
        
        let data: T = response.json().await.map_err(|e| Error::Http(e))?;
        Ok(data)
    }

    /// Collect health metrics
    async fn collect_health(&self) {
        match self.fetch_json::<HealthResponse>("/health").await {
            Ok(health) => {
                let metrics = self.metrics.read().await;
                metrics.node_health.set(if health.ok { 1.0 } else { 0.0 });
                metrics.node_uptime_seconds.set(health.uptime_s);
                metrics.node_db_status.set(if health.db_rw { 1.0 } else { 0.0 });

                metrics.node_version.reset();
                metrics.node_version.with_label_values(&[
                    &health.version,
                    &self.node_url,
                ]).set(1.0);
            }
            Err(e) => {
                warn!("Failed to fetch health: {}", e);
                let metrics = self.metrics.read().await;
                metrics.node_health.set(0.0);
                metrics
                    .scrape_errors_total
                    .with_label_values(&["health_error"])
                    .inc();
            }
        }
    }

    /// Collect epoch metrics
    async fn collect_epoch(&self) {
        match self.fetch_json::<EpochResponse>("/epoch").await {
            Ok(epoch) => {
                let metrics = self.metrics.read().await;
                metrics.epoch_number.set(epoch.epoch as i64);
                metrics.epoch_slot.set(epoch.slot as i64);
                metrics.epoch_pot.set(epoch.epoch_pot);
                metrics.enrolled_miners_total.set(epoch.enrolled_miners as i64);
                metrics.total_supply_rtc.set(epoch.total_supply_rtc);
                metrics.circulating_supply_rtc.set(epoch.circulating_supply_rtc);
            }
            Err(e) => {
                warn!("Failed to fetch epoch: {}", e);
                let metrics = self.metrics.read().await;
                metrics
                    .scrape_errors_total
                    .with_label_values(&["epoch_error"])
                    .inc();
            }
        }
    }

    /// Collect block metrics
    async fn collect_blocks(&self) {
        // Try multiple endpoints
        let block = match self.fetch_json::<BlockResponse>("/blocks/latest").await {
            Ok(b) => Ok(b),
            Err(_) => self.fetch_json::<BlockResponse>("/api/blocks/latest").await,
        };

        if let Ok(block) = block {
            let metrics = self.metrics.read().await;
            metrics.block_height_latest.set(block.height as i64);
            metrics.block_timestamp_latest.set(block.timestamp);
            metrics.blocks_total.inc_by(block.tx_count);
            metrics.transactions_total.inc_by(block.tx_count);
        } else {
            let metrics = self.metrics.read().await;
            metrics
                .scrape_errors_total
                .with_label_values(&["block_error"])
                .inc();
        }

        // Transaction pool
        let tx_pool: Result<serde_json::Value> = match self.fetch_json("/tx/pool").await {
            Ok(p) => Ok(p),
            Err(_) => self.fetch_json("/api/tx/pool").await,
        };

        if let Ok(pool) = tx_pool {
            let size: usize = if pool.is_array() {
                pool.as_array().map(|a| a.len()).unwrap_or(0)
            } else if pool.is_object() {
                pool.get("size")
                    .or_else(|| pool.get("count"))
                    .and_then(|v| v.as_u64())
                    .map(|v| v as usize)
                    .unwrap_or(0)
            } else {
                0
            };

            let metrics = self.metrics.read().await;
            metrics.tx_pool_size.set(size as i64);
        }
    }

    /// Collect miner metrics
    async fn collect_miners(&self) {
        let miners_data: Result<MinersResponse> = match self.fetch_json("/api/miners").await {
            Ok(m) => Ok(m),
            Err(_) => match self.fetch_json("/miners").await {
                Ok(m) => Ok(m),
                Err(_) => self.fetch_json("/network/miners").await,
            },
        };

        let miners = match miners_data {
            Ok(m) => m.into_miners(),
            Err(e) => {
                warn!("Failed to fetch miners: {}", e);
                let metrics = self.metrics.read().await;
                metrics
                    .scrape_errors_total
                    .with_label_values(&["miners_error"])
                    .inc();
                return;
            }
        };

        let metrics = self.metrics.read().await;
        metrics.active_miners_total.set(miners.len() as i64);

        // Aggregate by hardware type and tier
        let mut hardware_counts: HashMap<(String, String), u64> = HashMap::new();
        let mut arch_counts: HashMap<(String, String), u64> = HashMap::new();
        let mut multipliers: Vec<f64> = Vec::new();

        for miner in &miners {
            let hw_type = if !miner.hardware_type.is_empty() {
                &miner.hardware_type
            } else {
                &miner.hardware_model
            };
            let tier = if !miner.tier.is_empty() {
                &miner.tier
            } else {
                &miner.hardware_tier
            };
            hardware_counts
                .entry((hw_type.to_string(), tier.to_string()))
                .or_insert(0)
                .saturating_add(1);

            let arch = if !miner.device_arch.is_empty() {
                &miner.device_arch
            } else {
                &miner.architecture
            };
            let vintage = if !miner.vintage_class.is_empty() {
                &miner.vintage_class
            } else {
                &miner.cpu_vintage
            };
            arch_counts
                .entry((arch.to_string(), vintage.to_string()))
                .or_insert(0)
                .saturating_add(1);

            let mult = if miner.antiquity_multiplier > 0.0 {
                miner.antiquity_multiplier
            } else {
                miner.multiplier.max(1.0)
            };
            multipliers.push(mult);
            metrics.antiquity_multiplier_histogram.observe(mult);
        }

        // Update hardware gauge
        metrics.miners_by_hardware.reset();
        for ((hw_type, tier), count) in &hardware_counts {
            metrics
                .miners_by_hardware
                .with_label_values(&[hw_type, tier])
                .set(*count as f64);
        }

        // Update architecture gauge
        metrics.miners_by_architecture.reset();
        for ((arch, vintage), count) in &arch_counts {
            metrics
                .miners_by_architecture
                .with_label_values(&[arch, vintage])
                .set(*count as f64);
        }

        // Average multiplier
        if !multipliers.is_empty() {
            let avg = multipliers.iter().sum::<f64>() / multipliers.len() as f64;
            metrics.antiquity_multiplier_average.set(avg);
        }
    }

    /// Perform a full metrics collection
    async fn collect_all(&self) {
        let start = Instant::now();
        
        debug!("Starting metrics collection");
        
        self.collect_health().await;
        self.collect_epoch().await;
        self.collect_blocks().await;
        self.collect_miners().await;
        
        let duration = start.elapsed();
        
        let metrics = self.metrics.read().await;
        metrics.scrape_duration_seconds.observe(duration.as_secs_f64());
        metrics
            .exporter_last_scrape_time
            .set(chrono::Utc::now().timestamp() as f64);
        
        info!("Metrics collected in {:.3}s", duration.as_secs_f64());
    }

    /// Run the continuous collection loop
    pub async fn run(&self, interval_secs: u64) {
        let interval = Duration::from_secs(interval_secs);
        
        info!("Starting metrics collection loop (interval: {}s)", interval_secs);
        
        // Initial collection
        self.collect_all().await;
        
        // Continuous collection
        loop {
            sleep(interval).await;
            self.collect_all().await;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_miners_response_list() {
        let json = r#"[{"hardware_type": "PowerPC G4", "antiquity_multiplier": 2.5}]"#;
        let response: MinersResponse = serde_json::from_str(json).unwrap();
        let miners = response.into_miners();
        assert_eq!(miners.len(), 1);
        assert_eq!(miners[0].hardware_type, "PowerPC G4");
    }

    #[test]
    fn test_miners_response_object() {
        let json = r#"{"miners": [{"hardware_type": "486", "antiquity_multiplier": 3.5}]}"#;
        let response: MinersResponse = serde_json::from_str(json).unwrap();
        let miners = response.into_miners();
        assert_eq!(miners.len(), 1);
        assert_eq!(miners[0].hardware_type, "486");
    }
}
