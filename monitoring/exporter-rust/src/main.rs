//! RustChain Prometheus Exporter - Main Entry Point
//!
//! A native Rust implementation of the Prometheus metrics exporter for RustChain nodes.
//!
//! # Usage
//!
//! ```bash
//! # Run with defaults
//! cargo run --release
//!
//! # Run with custom configuration
//! RUSTCHAIN_NODE=http://localhost:8099 EXPORTER_PORT=9100 cargo run --release
//!
//! # Or use a config file
//! rustchain-exporter --config config.toml
//! ```

use anyhow::Result;
use rustchain_exporter::{Config, Exporter};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize logging
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "rustchain_exporter=info,tower_http=warn".into()),
        )
        .with(tracing_subscriber::fmt::layer())
        .init();

    // Load configuration
    let config = Config::from_env();
    
    // Validate configuration
    if let Err(e) = config.validate() {
        tracing::error!("Invalid configuration: {}", e);
        std::process::exit(1);
    }

    // Create and run exporter
    let exporter = Exporter::new(config);
    
    tracing::info!("Starting RustChain Prometheus Exporter");
    
    if let Err(e) = exporter.run().await {
        tracing::error!("Exporter failed: {}", e);
        std::process::exit(1);
    }

    Ok(())
}
