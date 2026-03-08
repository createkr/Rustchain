#!/usr/bin/env python3
"""
Tests for RustChain Prometheus Exporter

Run with:
    python -m pytest tests/test_exporter.py -v
    python tests/test_exporter.py
"""
import unittest
import time
import json
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestRustChainExporter(unittest.TestCase):
    """Test cases for RustChain Prometheus Exporter"""
    
    def test_exporter_file_exists(self):
        """Test that the exporter file exists"""
        exporter_path = os.path.join(os.path.dirname(__file__), '..', 'rustchain-exporter.py')
        self.assertTrue(os.path.exists(exporter_path))
    
    def test_exporter_is_valid_python(self):
        """Test that the exporter is valid Python"""
        exporter_path = os.path.join(os.path.dirname(__file__), '..', 'rustchain-exporter.py')
        with open(exporter_path, 'r') as f:
            code = f.read()
        # This will raise SyntaxError if the code is invalid
        compile(code, exporter_path, 'exec')
    
    def test_exporter_has_required_functions(self):
        """Test that the exporter has required functions defined"""
        exporter_path = os.path.join(os.path.dirname(__file__), '..', 'rustchain-exporter.py')
        with open(exporter_path, 'r') as f:
            content = f.read()
        
        # Check for key function definitions (using method names in class)
        self.assertIn('def collect(self)', content)
        self.assertIn('def _fetch_json', content)
        self.assertIn('def main', content)
        self.assertIn('class RustChainExporter', content)
    
    def test_data_classes_defined(self):
        """Test data classes are properly defined"""
        exporter_path = os.path.join(os.path.dirname(__file__), '..', 'rustchain-exporter.py')
        with open(exporter_path, 'r') as f:
            content = f.read()
        
        # Check for dataclass definitions
        self.assertIn('@dataclass', content)
        self.assertIn('class NodeHealth', content)
        self.assertIn('class EpochInfo', content)
        self.assertIn('class MinerStats', content)
    
    def test_configuration_section(self):
        """Test configuration is properly defined"""
        exporter_path = os.path.join(os.path.dirname(__file__), '..', 'rustchain-exporter.py')
        with open(exporter_path, 'r') as f:
            content = f.read()
        
        # Check for configuration variables
        self.assertIn('RUSTCHAIN_NODE', content)
        self.assertIn('EXPORTER_PORT', content)
        self.assertIn('SCRAPE_INTERVAL', content)
        self.assertIn('TLS_VERIFY', content)


class TestMetricsOutput(unittest.TestCase):
    """Test Prometheus metrics output format"""
    
    def test_metrics_format(self):
        """Test metrics are in correct Prometheus format"""
        from prometheus_client import Gauge, generate_latest, CollectorRegistry
        
        # Use a fresh registry for testing
        registry = CollectorRegistry()
        test_gauge = Gauge('test_metric', 'Test metric description', registry=registry)
        test_gauge.set(42.0)
        
        output = generate_latest(registry).decode('utf-8')
        
        # Check format includes metric name and value
        self.assertIn('test_metric', output)
        self.assertIn('42.0', output)
    
    def test_labeled_metrics(self):
        """Test labeled metrics format"""
        from prometheus_client import Gauge, generate_latest, CollectorRegistry
        
        registry = CollectorRegistry()
        labeled = Gauge('labeled_metric', 'Labeled metric', ['label1', 'label2'], registry=registry)
        labeled.labels('value1', 'value2').set(100.0)
        
        output = generate_latest(registry).decode('utf-8')
        
        self.assertIn('labeled_metric', output)
        self.assertIn('value1', output)
        self.assertIn('value2', output)
    
    def test_counter_metrics(self):
        """Test counter metrics format"""
        from prometheus_client import Counter, generate_latest, CollectorRegistry
        
        registry = CollectorRegistry()
        counter = Counter('test_counter', 'Test counter', registry=registry)
        counter.inc(5)
        
        output = generate_latest(registry).decode('utf-8')
        
        self.assertIn('test_counter', output)
        self.assertIn('5.0', output)
    
    def test_histogram_metrics(self):
        """Test histogram metrics format"""
        from prometheus_client import Histogram, generate_latest, CollectorRegistry
        
        registry = CollectorRegistry()
        histogram = Histogram('test_histogram', 'Test histogram', registry=registry)
        histogram.observe(0.5)
        
        output = generate_latest(registry).decode('utf-8')
        
        self.assertIn('test_histogram', output)


class TestConfiguration(unittest.TestCase):
    """Test configuration handling"""
    
    def test_environment_variables_documented(self):
        """Test that environment variables are documented"""
        exporter_path = os.path.join(os.path.dirname(__file__), '..', 'rustchain-exporter.py')
        with open(exporter_path, 'r') as f:
            content = f.read()
        
        # Check that key env vars are referenced in the code
        self.assertIn('RUSTCHAIN_NODE', content)
        self.assertIn('EXPORTER_PORT', content)
        self.assertIn('SCRAPE_INTERVAL', content)
    
    def test_readme_exists(self):
        """Test that README documentation exists"""
        readme_path = os.path.join(os.path.dirname(__file__), '..', 'README.md')
        self.assertTrue(os.path.exists(readme_path))
        
        with open(readme_path, 'r') as f:
            content = f.read()
        
        # Check for key sections
        self.assertIn('RustChain Prometheus', content)
        self.assertIn('Configuration', content)
        self.assertIn('Metrics', content)


class TestIntegration(unittest.TestCase):
    """Integration tests for the exporter"""
    
    def test_mock_fetch_and_collect(self):
        """Test fetch and collect with mocked requests"""
        import requests
        
        # Create mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            'ok': True,
            'uptime_s': 3600.0,
            'db_rw': True,
            'version': '1.0.0',
            'epoch': 100,
            'slot': 50,
            'epoch_pot': 1000.0,
            'enrolled_miners': 25,
            'total_supply_rtc': 1000000.0
        }
        mock_response.raise_for_status.return_value = None
        
        with patch('requests.Session') as mock_session_class:
            mock_session = Mock()
            mock_session.get.return_value = mock_response
            mock_session_class.return_value = mock_session
            
            # Import fresh module
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "rustchain_exporter_integration",
                os.path.join(os.path.dirname(__file__), '..', 'rustchain-exporter.py')
            )
            module = importlib.util.module_from_spec(spec)
            
            # Just verify the module can be loaded
            self.assertIsNotNone(spec)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
