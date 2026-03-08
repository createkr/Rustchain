//! HTTP server for exposing Prometheus metrics

use crate::error::Result;
use crate::metrics::MetricsRegistry;
use hyper::service::{make_service_fn, service_fn};
use hyper::{Body, Method, Request, Response, Server, StatusCode};
use std::convert::Infallible;
use std::net::SocketAddr;
use std::sync::Arc;
use tokio::sync::RwLock;
use tracing::{error, info};

/// Metrics HTTP server
pub struct MetricsServer {
    port: u16,
    metrics: Arc<RwLock<MetricsRegistry>>,
}

impl MetricsServer {
    /// Create a new metrics server
    pub fn new(port: u16, metrics: Arc<RwLock<MetricsRegistry>>) -> Self {
        Self { port, metrics }
    }

    /// Handle incoming HTTP requests
    async fn handle_request(
        req: Request<Body>,
        metrics: Arc<RwLock<MetricsRegistry>>,
    ) -> std::result::Result<Response<Body>, Infallible> {
        let path = req.uri().path();
        let method = req.method();

        // Health check endpoint
        if path == "/health" && method == &Method::GET {
            return Ok(Response::new(Body::from("OK")));
        }

        // Metrics endpoint
        if path == "/metrics" && method == &Method::GET {
            let metrics_guard = metrics.read().await;

            match metrics_guard.encode() {
                Ok(body) => {
                    return Ok(Response::builder()
                        .status(StatusCode::OK)
                        .header("Content-Type", "text/plain; version=0.0.4")
                        .body(Body::from(body))
                        .unwrap());
                }
                Err(e) => {
                    error!("Failed to encode metrics: {}", e);
                    return Ok(Response::builder()
                        .status(StatusCode::INTERNAL_SERVER_ERROR)
                        .body(Body::from(format!("Error encoding metrics: {}", e)))
                        .unwrap());
                }
            }
        }

        // Root endpoint with info
        if path == "/" && method == &Method::GET {
            let info = r#"RustChain Prometheus Exporter

Endpoints:
  GET /metrics  - Prometheus metrics
  GET /health   - Health check
  GET /         - This info page

For more information, see the documentation.
"#;
            return Ok(Response::builder()
                .status(StatusCode::OK)
                .header("Content-Type", "text/plain")
                .body(Body::from(info))
                .unwrap());
        }

        // 404 for unknown paths
        Ok(Response::builder()
            .status(StatusCode::NOT_FOUND)
            .body(Body::from("Not Found"))
            .unwrap())
    }

    /// Run the HTTP server
    pub async fn run(&self) -> Result<()> {
        let addr: SocketAddr = ([0, 0, 0, 0], self.port).into();
        let metrics = self.metrics.clone();

        let make_svc = make_service_fn(move |_conn| {
            let metrics = metrics.clone();
            async move {
                Ok::<_, Infallible>(service_fn(move |req| {
                    let metrics = metrics.clone();
                    async {
                        Self::handle_request(req, metrics).await
                    }
                }))
            }
        });

        let server = Server::bind(&addr).serve(make_svc);

        info!("Metrics server listening on http://{}", addr);
        info!("Metrics endpoint: http://{}/metrics", addr);

        if let Err(e) = server.await {
            error!("Server error: {}", e);
            return Err(e.into());
        }

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use hyper::{Client, Uri};
    use std::time::Duration;

    #[tokio::test]
    async fn test_metrics_endpoint() {
        let metrics = Arc::new(RwLock::new(MetricsRegistry::new()));
        let server = MetricsServer::new(19100, metrics.clone());

        // Start server in background
        let server_handle = tokio::spawn(async move {
            let _ = server.run().await;
        });

        // Give server time to start
        tokio::time::sleep(Duration::from_millis(100)).await;

        // Test metrics endpoint
        let client = Client::new();
        let uri: Uri = "http://127.0.0.1:19100/metrics".parse().unwrap();
        let response = client.get(uri).await.unwrap();

        assert_eq!(response.status(), StatusCode::OK);
        assert_eq!(
            response.headers().get("Content-Type").unwrap(),
            "text/plain; version=0.0.4"
        );

        // Clean up
        server_handle.abort();
    }

    #[tokio::test]
    async fn test_health_endpoint() {
        let metrics = Arc::new(RwLock::new(MetricsRegistry::new()));
        let server = MetricsServer::new(19101, metrics.clone());

        let server_handle = tokio::spawn(async move {
            let _ = server.run().await;
        });

        tokio::time::sleep(Duration::from_millis(100)).await;

        let client = Client::new();
        let uri: Uri = "http://127.0.0.1:19101/health".parse().unwrap();
        let response = client.get(uri).await.unwrap();

        assert_eq!(response.status(), StatusCode::OK);

        server_handle.abort();
    }
}
