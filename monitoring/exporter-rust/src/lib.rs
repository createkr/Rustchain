//! RustChain Prometheus Exporter
//! 
//! A native Rust implementation of the Prometheus metrics exporter for RustChain nodes.
//! Provides comprehensive metrics collection with Grafana-friendly label structures.
//!
//! # Features
//!
//! - Node health and performance metrics
//! - Network and consensus state
//! - Miner analytics with hardware breakdown
//! - Block and transaction statistics
//! - Histogram distributions for latency analysis
//!
//! # Example
//!
//! ```no_run
//! use rustchain_exporter::{Exporter, Config};
//!
//! #[tokio::main]
//! async fn main() -> anyhow::Result<()> {
//!     let config = Config::from_env();
//!     let exporter = Exporter::new(config);
//!     exporter.run().await?;
//!     Ok(())
//! }
//! ```

#![warn(missing_docs)]
#![warn(rust_2018_idioms)]

pub mod collector;
pub mod config;
pub mod error;
pub mod metrics;
pub mod server;

pub use collector::MetricsCollector;
pub use config::Config;
pub use error::{Error, Result};
pub use metrics::MetricsRegistry;
pub use server::MetricsServer;

use std::sync::Arc;
use tokio::sync::RwLock;
use tracing::{info, error};

/// Main exporter instance that coordinates all components
pub struct Exporter {
    config: Config,
    metrics: Arc<RwLock<MetricsRegistry>>,
    collector: MetricsCollector,
}

impl Exporter {
    /// Create a new exporter with the given configuration
    pub fn new(config: Config) -> Self {
        let metrics = Arc::new(RwLock::new(MetricsRegistry::new()));
        let collector = MetricsCollector::new(config.node_url.clone(), metrics.clone());
        
        Self {
            config,
            metrics,
            collector,
        }
    }

    /// Run the exporter, starting both the collection loop and HTTP server
    pub async fn run(&self) -> Result<()> {
        info!("Starting RustChain Prometheus Exporter v{}", env!("CARGO_PKG_VERSION"));
        info!("Node URL: {}", self.config.node_url);
        info!("Exporter port: {}", self.config.exporter_port);
        info!("Scrape interval: {}s", self.config.scrape_interval);

        // Clone Arc for the server
        let metrics = self.metrics.clone();
        
        // Start HTTP server
        let server = MetricsServer::new(self.config.exporter_port, metrics);
        let server_handle = tokio::spawn(async move {
            if let Err(e) = server.run().await {
                error!("HTTP server error: {}", e);
            }
        });

        // Start metrics collection loop
        let collector = self.collector.clone();
        let interval = self.config.scrape_interval;
        let collection_handle = tokio::spawn(async move {
            collector.run(interval).await;
        });

        // Wait for both tasks
        tokio::try_join!(server_handle, collection_handle)?;

        Ok(())
    }

    /// Get current metrics snapshot
    pub async fn get_metrics(&self) -> prometheus::Registry {
        self.metrics.read().await.registry.clone()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_exporter_creation() {
        let config = Config::default();
        let exporter = Exporter::new(config);
        assert_eq!(exporter.config.exporter_port, 9100);
    }

    #[tokio::test]
    async fn test_metrics_registry() {
        let config = Config::default();
        let exporter = Exporter::new(config);
        let registry = exporter.get_metrics().await;
        assert!(registry.gather().len() > 0);
    }
}
