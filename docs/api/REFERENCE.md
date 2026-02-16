# RustChain API Reference

**Base URL:** `https://<rustchain-host>`  
**Authentication:** Read-only endpoints are public. Writes require Ed25519 signatures or an Admin Key.  
**Endpoint discovery:** Host/IP can change; confirm the current public endpoint from maintainers before production integration.  
**Certificate Note:** Prefer normal TLS verification in production. Use `-k` only as a temporary local-dev fallback when you knowingly target a self-signed endpoint.

---

## 🟢 Public Endpoints

### 1. Node Health
Check the status of the node, database, and sync state.

- **Endpoint:** `GET /health`
- **Response:**
  ```json
  {
    "ok": true,
    "version": "2.2.1-rip200",
    "uptime_s": 97300,
    "db_rw": true,
    "tip_age_slots": 0,
    "backup_age_hours": 16.58
  }
  ```

---

### 2. Epoch Information
Get details about the current mining epoch, slot progress, and rewards.

- **Endpoint:** `GET /epoch`
- **Response:**
  ```json
  {
    "epoch": 75,
    "slot": 10800,
    "blocks_per_epoch": 144,
    "epoch_pot": 1.5,
    "enrolled_miners": 10
  }
  ```

---

### 3. Active Miners
List all miners currently participating in the network with their hardware details.

- **Endpoint:** `GET /api/miners`
- **Response (Array):**
  ```json
  [
    {
      "miner": "wallet_id_string",
      "device_arch": "G4",
      "device_family": "PowerPC",
      "hardware_type": "PowerPC G4 (Vintage)",
      "antiquity_multiplier": 2.5,
      "last_attest": 1771187406
    }
  ]
  ```

---

### 4. Wallet Balance
Query the RTC balance for any valid miner ID.

- **Endpoint:** `GET /wallet/balance?miner_id={NAME}`
- **Example (strict TLS):** `curl --fail --silent --show-error 'https://<rustchain-host>/wallet/balance?miner_id=scott'`
- **Dev fallback (self-signed only):** `curl -k --fail --silent --show-error 'https://<rustchain-host>/wallet/balance?miner_id=scott'`
- **Response:**
  ```json
  {
    "ok": true,
    "miner_id": "scott",
    "amount_rtc": 42.5,
    "amount_i64": 42500000
  }
  ```

---

## 🔵 Signed Transactions (Public Write)

### Submit Signed Transfer
Transfer RTC between wallets without requiring an admin key.

- **Endpoint:** `POST /wallet/transfer/signed`
- **Payload:**
  ```json
  {
    "from_address": "RTC...",
    "to_address": "RTC...",
    "amount_rtc": 1.5,
    "nonce": 1771187406,
    "signature": "hex_encoded_signature",
    "public_key": "hex_encoded_pubkey"
  }
  ```
- **Process:** 
  1. Construct JSON payload using API field names: `from_address`, `to_address`, `amount_rtc`, `nonce`.
  2. Build signing message as canonical JSON object with keys: `from`, `to`, `amount`, `nonce` (exactly as server verification expects).
  3. Sign that message with the Ed25519 private key.
  4. Submit request with `signature` and `public_key` as hex strings.

---

## 🔴 Authenticated Endpoints (Admin Only)

**Required Header:** `X-Admin-Key: {YOUR_ADMIN_KEY}`

### 1. Internal Admin Transfer
Move funds between any two wallets (requires admin authority).

- **Endpoint:** `POST /wallet/transfer`
- **Payload:** `{"from_miner": "A", "to_miner": "B", "amount_rtc": 10.0}`

### 2. Manual Settlement
Manually trigger the epoch settlement process.

- **Endpoint:** `POST /rewards/settle`

---

## ⚠️ Implementation Notes & Common Mistakes

### Field Name Precision
The RustChain API is strict about field names. Common errors include:
- ❌ `miner_id` instead of **`miner`** (in miner object)
- ❌ `current_slot` instead of **`slot`** (in epoch info)
- ❌ `total_miners` instead of **`enrolled_miners`**
- ❌ `from` / `to` in request body for `/wallet/transfer/signed` (must send **`from_address`** / **`to_address`**)

### Wallet Formats
Wallets are **simple UTF-8 strings** (1-256 chars).  
- ✅ `my-wallet-name`
- ❌ `0x...` (Ethereum addresses are not native RTC wallets)
- ❌ `4TR...` (Solana addresses must be bridged via BoTTube)

### Certificate Errors
Keep TLS verification enabled by default. If a temporary self-signed lab node is unavoidable, use `-k` only for that specific test endpoint and remove it once proper certs are available.

---
*Last Updated: February 2026*
