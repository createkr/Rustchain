//! Error types for the RustChain Prometheus exporter

use thiserror::Error;

/// Result type alias for exporter operations
pub type Result<T> = std::result::Result<T, Error>;

/// Exporter error types
#[derive(Error, Debug)]
pub enum Error {
    /// HTTP client error
    #[error("HTTP error: {0}")]
    Http(#[from] reqwest::Error),

    /// Prometheus metrics error
    #[error("Prometheus error: {0}")]
    Prometheus(#[from] prometheus::Error),

    /// JSON serialization/deserialization error
    #[error("JSON error: {0}")]
    JsonSerde(#[from] serde_json::Error),

    /// Tokio runtime error
    #[error("Tokio error: {0}")]
    Tokio(#[from] tokio::task::JoinError),

    /// Hyper server error
    #[error("HTTP server error: {0}")]
    Hyper(#[from] hyper::Error),

    /// Configuration error
    #[error("Configuration error: {0}")]
    Config(String),

    /// Node API error
    #[error("Node API error: {0}")]
    NodeApi(String),

    /// Metrics collection error
    #[error("Metrics collection error: {0}")]
    Collection(String),
}

impl Error {
    /// Check if this is a retryable error
    pub fn is_retryable(&self) -> bool {
        match self {
            Error::Http(e) => e.is_timeout() || e.is_connect(),
            Error::NodeApi(_) => true,
            Error::Collection(_) => true,
            _ => false,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_error_display() {
        let err = Error::Config("test error".to_string());
        assert_eq!(format!("{}", err), "Configuration error: test error");
    }

    #[test]
    fn test_retryable_errors() {
        let config_err = Error::Config("test".to_string());
        assert!(!config_err.is_retryable());

        let node_err = Error::NodeApi("timeout".to_string());
        assert!(node_err.is_retryable());
    }
}
