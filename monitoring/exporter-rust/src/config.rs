//! Configuration module for the RustChain Prometheus exporter

use serde::{Deserialize, Serialize};
use std::env;

/// Exporter configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    /// RustChain node URL to scrape metrics from
    pub node_url: String,
    /// Port to expose the Prometheus metrics endpoint
    pub exporter_port: u16,
    /// Interval between metric collections in seconds
    pub scrape_interval: u64,
    /// Whether to verify TLS certificates
    pub tls_verify: bool,
    /// Request timeout in seconds
    pub request_timeout: u64,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            node_url: "https://rustchain.org".to_string(),
            exporter_port: 9100,
            scrape_interval: 30,
            tls_verify: true,
            request_timeout: 10,
        }
    }
}

impl Config {
    /// Load configuration from environment variables
    ///
    /// # Environment Variables
    ///
    /// - `RUSTCHAIN_NODE`: Node URL (default: https://rustchain.org)
    /// - `EXPORTER_PORT`: Metrics port (default: 9100)
    /// - `SCRAPE_INTERVAL`: Collection interval in seconds (default: 30)
    /// - `TLS_VERIFY`: Verify TLS certificates (default: true)
    /// - `REQUEST_TIMEOUT`: Request timeout in seconds (default: 10)
    pub fn from_env() -> Self {
        let _ = dotenvy::dotenv(); // .env file is optional

        Self {
            node_url: env::var("RUSTCHAIN_NODE")
                .unwrap_or_else(|_| "https://rustchain.org".to_string()),
            exporter_port: env::var("EXPORTER_PORT")
                .unwrap_or_else(|_| "9100".to_string())
                .parse()
                .unwrap_or(9100),
            scrape_interval: env::var("SCRAPE_INTERVAL")
                .unwrap_or_else(|_| "30".to_string())
                .parse()
                .unwrap_or(30),
            tls_verify: env::var("TLS_VERIFY")
                .unwrap_or_else(|_| "true".to_string())
                .parse()
                .unwrap_or(true),
            request_timeout: env::var("REQUEST_TIMEOUT")
                .unwrap_or_else(|_| "10".to_string())
                .parse()
                .unwrap_or(10),
        }
    }

    /// Create configuration from a JSON string
    pub fn from_json(json: &str) -> Result<Self, serde_json::Error> {
        serde_json::from_str(json)
    }

    /// Validate configuration
    pub fn validate(&self) -> Result<(), String> {
        if self.node_url.is_empty() {
            return Err("node_url cannot be empty".to_string());
        }
        if self.exporter_port == 0 {
            return Err("exporter_port cannot be 0".to_string());
        }
        if self.scrape_interval == 0 {
            return Err("scrape_interval cannot be 0".to_string());
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_default_config() {
        let config = Config::default();
        assert_eq!(config.node_url, "https://rustchain.org");
        assert_eq!(config.exporter_port, 9100);
        assert_eq!(config.scrape_interval, 30);
        assert!(config.tls_verify);
        assert_eq!(config.request_timeout, 10);
    }

    #[test]
    fn test_config_validation() {
        let valid_config = Config::default();
        assert!(valid_config.validate().is_ok());

        let invalid_config = Config {
            node_url: String::new(),
            ..Default::default()
        };
        assert!(invalid_config.validate().is_err());
    }
}
