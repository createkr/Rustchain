# RustChain Monitoring Runbook

This runbook provides troubleshooting steps for common alerts in the RustChain monitoring system.

## Table of Contents

- [Node Down](#node-down)
- [Miner Drop](#miner-drop)
- [Slow Scrape](#slow-scrape)
- [High Transaction Pool](#high-transaction-pool)
- [Epoch Stalled](#epoch-stalled)

---

## Node Down

**Alert**: `RustChainNodeDown`  
**Severity**: Critical  
**Condition**: `rustchain_node_health == 0` for 2 minutes

### Symptoms
- Grafana shows node health as 0 (red)
- No new blocks being produced
- API endpoints not responding

### Troubleshooting Steps

1. **Check node process**
   ```bash
   systemctl status rustchain-node
   docker ps | grep rustchain
   ```

2. **Check node logs**
   ```bash
   journalctl -u rustchain-node -n 100
   docker logs rustchain-node --tail 100
   ```

3. **Check disk space**
   ```bash
   df -h
   ```

4. **Check memory**
   ```bash
   free -h
   top -p $(pgrep rustchain)
   ```

5. **Test API endpoint**
   ```bash
   curl -v http://localhost:8099/health
   ```

6. **Restart node if needed**
   ```bash
   systemctl restart rustchain-node
   # or
   docker restart rustchain-node
   ```

### Resolution
- If disk full: Clean up old logs, expand storage
- If OOM: Increase memory limit, check for memory leaks
- If crash: Review logs, report bug with stack trace

---

## Miner Drop

**Alert**: `RustChainMinerDrop`  
**Severity**: Warning  
**Condition**: Miner count decreases by >20% in 5 minutes

### Symptoms
- Sudden drop in active miner count
- Multiple miners disconnecting

### Troubleshooting Steps

1. **Check miner connectivity**
   ```bash
   curl http://localhost:8099/api/miners | jq length
   ```

2. **Review miner logs**
   ```bash
   journalctl -u rustchain-miner -n 50
   ```

3. **Check network connectivity**
   ```bash
   ping -c 4 rustchain.org
   traceroute rustchain.org
   ```

4. **Check for network issues**
   ```bash
   netstat -tlnp | grep 8099
   ss -tlnp | grep 8099
   ```

5. **Verify epoch transition**
   ```bash
   curl http://localhost:8099/epoch | jq
   ```

### Resolution
- If network issue: Wait for network recovery
- If epoch transition: Normal behavior, miners re-enrolling
- If persistent: Check miner software compatibility

---

## Slow Scrape

**Alert**: `RustChainSlowScrape`  
**Severity**: Warning  
**Condition**: Scrape duration > 5 seconds for 5 minutes

### Symptoms
- Prometheus showing slow scrape times
- Gaps in metrics data

### Troubleshooting Steps

1. **Check exporter CPU usage**
   ```bash
   top -p $(pgrep -f rustchain-exporter)
   ```

2. **Check exporter memory**
   ```bash
   ps aux | grep rustchain-exporter
   ```

3. **Test node API latency**
   ```bash
   time curl http://localhost:8099/health
   time curl http://localhost:8099/epoch
   time curl http://localhost:8099/api/miners
   ```

4. **Check network latency**
   ```bash
   ping -c 10 <node-host>
   ```

5. **Review exporter logs**
   ```bash
   docker logs rustchain-exporter --tail 50
   journalctl -u rustchain-exporter -n 50
   ```

### Resolution
- If node slow: Investigate node performance
- If network latency: Check network path, consider co-locating exporter
- If exporter overloaded: Increase scrape interval

---

## High Transaction Pool

**Alert**: `RustChainHighTXPool` / `RustChainTXPoolCritical`  
**Severity**: Warning/Critical  
**Condition**: TX pool size > 500 (warning) or > 1000 (critical)

### Symptoms
- Growing transaction backlog
- Slow transaction confirmation

### Troubleshooting Steps

1. **Check current pool size**
   ```bash
   curl http://localhost:8099/tx/pool | jq '.size'
   ```

2. **Check block production rate**
   ```bash
   curl http://localhost:8099/blocks/latest | jq '.height'
   ```

3. **Review transaction throughput**
   ```promql
   rate(rustchain_transactions_total[5m])
   ```

4. **Check for spam transactions**
   ```bash
   curl http://localhost:8099/tx/pool | jq '.[] | select(.fee < 0.001)'
   ```

### Resolution
- If legitimate load: Wait for blocks to process
- If spam: Consider implementing rate limiting
- If block production issue: Check miner activity

---

## Epoch Stalled

**Alert**: `RustChainEpochStalled`  
**Severity**: Warning  
**Condition**: Epoch number unchanged for 15 minutes

### Symptoms
- Epoch not advancing
- No new blocks in current epoch

### Troubleshooting Steps

1. **Check current epoch**
   ```bash
   curl http://localhost:8099/epoch | jq '.'
   ```

2. **Check enrolled miners**
   ```bash
   curl http://localhost:8099/epoch | jq '.enrolled_miners'
   ```

3. **Check block height progression**
   ```promql
   delta(rustchain_block_height_latest[15m])
   ```

4. **Review consensus logs**
   ```bash
   journalctl -u rustchain-node -n 100 | grep -i epoch
   ```

### Resolution
- If no miners: Wait for miners to enroll
- If consensus issue: Check node synchronization
- If network partition: Verify peer connectivity

---

## Exporter Issues

### Exporter Not Responding

1. **Check exporter status**
   ```bash
   systemctl status rustchain-exporter
   docker ps | grep exporter
   ```

2. **Test metrics endpoint**
   ```bash
   curl http://localhost:9100/metrics
   ```

3. **Restart exporter**
   ```bash
   systemctl restart rustchain-exporter
   docker restart rustchain-exporter
   ```

### High Scrape Errors

1. **Check error types**
   ```promql
   rustchain_scrape_errors_total
   ```

2. **Review exporter logs**
   ```bash
   docker logs rustchain-exporter --tail 100
   ```

3. **Check node availability**
   ```bash
   curl -v http://localhost:8099/health
   ```

---

## Contact

- **GitHub Issues**: https://github.com/Scottcjn/Rustchain/issues
- **Documentation**: https://github.com/Scottcjn/Rustchain/tree/main/monitoring
