"""
Hyperliquid Client for Engine V0
Read-only integration with Hyperliquid API
"""
import traceback
import threading
import time
from typing import Optional, Dict, Any, List
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from eth_account import Account

from config import (
    HYPERLIQUID_WALLET_ADDRESS,
    HYPERLIQUID_PRIVATE_KEY,
    HYPERLIQUID_NETWORK,
    MAX_API_CONCURRENCY,
    API_TIMEOUT_SECONDS
)


def quantize_to_tick(price: float, tick_size: float, mode: str = "nearest") -> float:
    """
    Quantize price to valid tick size multiple.
    
    Args:
        price: Raw price value
        tick_size: Exchange tick size (e.g., 0.1, 1.0, 0.01)
        mode: "nearest" (round to nearest), "down" (floor), "up" (ceil)
    
    Returns:
        Price quantized to exact tick size multiple
    """
    from decimal import Decimal, ROUND_HALF_UP, ROUND_DOWN, ROUND_UP
    
    if tick_size <= 0:
        return price
    
    price_d = Decimal(str(price))
    tick_d = Decimal(str(tick_size))
    
    # Calculate number of ticks
    ticks = price_d / tick_d
    
    if mode == "nearest":
        quantized_ticks = ticks.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    elif mode == "down":
        quantized_ticks = ticks.quantize(Decimal('1'), rounding=ROUND_DOWN)
    elif mode == "up":
        quantized_ticks = ticks.quantize(Decimal('1'), rounding=ROUND_UP)
    else:
        quantized_ticks = ticks.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    
    result = float(quantized_ticks * tick_d)
    
    print(f"[TICK] raw={price:.6f} tick={tick_size} quantized={result:.6f} mode={mode}")
    
    return result


class HLClient:
    """Hyperliquid client for read-only operations"""
    
    def __init__(self):
        """Initialize Hyperliquid clients"""
        self.wallet_address = HYPERLIQUID_WALLET_ADDRESS
        self.private_key = HYPERLIQUID_PRIVATE_KEY
        self.network = HYPERLIQUID_NETWORK
        
        # Determine API URL based on network
        if self.network == "mainnet":
            self.api_url = "https://api.hyperliquid.xyz"
        else:
            self.api_url = "https://api.hyperliquid-testnet.xyz"
        
        self.info_client: Optional[Info] = None
        self.exchange_client: Optional[Exchange] = None
        
        # Throttling Semaphore (Limit parallel API calls)
        self._api_semaphore = threading.Semaphore(MAX_API_CONCURRENCY)
        self._last_429_time = 0
        self._last_request_time = 0
        self._min_request_gap = 0.2  # 200ms gap between requests
        
        # Meta cache for symbol constraints
        self._meta_cache = None
        self._meta_cache_time = 0
        self._meta_cache_ttl = 300  # 5 minutes
        
        # ========== INTELLIGENT CACHING SYSTEM (Rate Limit Mitigation) ==========
        # Candles cache: {(symbol, interval): (data, timestamp)}
        self._candles_cache = {}
        
        # Timeframe-specific TTLs (in seconds)
        self._candle_ttl = {
            "1w": 300,   # 5 min - weekly data changes slowly
            "1d": 300,   # 5 min - daily data changes slowly  
            "4h": 300,   # 5 min - very stable
            "1h": 180,   # 3 min - hourly stable
            "15m": 120,  # 2 min - was 30s, still fresh
            "5m": 60,    # 1 min - was 30s, good balance
            "1m": 30     # 30 sec - was 10s, reduces API calls 3x
        }
        
        # Orderbook cache: {symbol: (data, timestamp)}
        self._orderbook_cache = {}
        self._orderbook_ttl = 15  # 15 sec - orderbooks change fast but not every tick
        
        # Funding cache: {symbol: (data, timestamp)}
        self._funding_cache = {}
        self._funding_ttl = 60  # 1 min - funding rates stable
        
        # Initialize clients
        self._init_clients()
    
    def _init_clients(self):
        """Initialize Hyperliquid SDK clients with retry for rate limits"""
        import time
        
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                print(f"[HL] Initializing clients for {self.network}...")
                print(f"[HL] API URL: {self.api_url}")
                print(f"[HL] Wallet: ***{self.wallet_address[-6:] if self.wallet_address else 'NOT_SET'}")
                
                # Info client for reading market data and account info
                self.info_client = Info(self.api_url, skip_ws=True)
                
                # Exchange client for trading operations (needed for some account queries)
                if self.private_key and self.wallet_address:
                    wallet = Account.from_key(self.private_key)
                    self.exchange_client = Exchange(
                    wallet=wallet,
                    base_url=self.api_url,
                    account_address=self.wallet_address
                    )
                
                print("[HL] Clients initialized successfully")
                return  # Success, exit retry loop
                
            except Exception as e:
                error_str = str(e)
                
                # Check if rate limited
                if "429" in error_str or "rate limit" in error_str.lower():
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (2 ** attempt)
                        print(f"[HL][WARN] Rate limited, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"[HL][ERROR] Rate limited after {max_retries} attempts")
                
                print(f"[HL][ERROR] Failed to initialize clients: {e}")
                traceback.print_exc()
                return
    def _wait_for_rate_limit(self):
        """Enforce strict rate limiting between requests"""
        try:
            current_time = time.time()
            time_since_last = current_time - self._last_request_time
            
            # If 429 received recently, wait longer
            if current_time - self._last_429_time < 10:
                time.sleep(1.0)
            
            # Enforce minimum gap
            elif time_since_last < self._min_request_gap:
                sleep_time = self._min_request_gap - time_since_last
                time.sleep(sleep_time)
            
            self._last_request_time = time.time()
            
        except Exception:
            pass  # Ensure throttling never crashes the bot

    def get_account_summary(self) -> Dict[str, Any]:
        """
        Get account summary with equity, margin, and positions count
        
        Returns:
            dict: {equity, available, margin, positions_count}
        """
        try:
            if not self.info_client or not self.wallet_address:
                return {
                    "equity": 0.0,
                    "available": 0.0,
                    "margin": 0.0,
                    "positions_count": 0
                }
            
            # Backoff if we recently had a 429
            if time.time() - self._last_429_time < 5:
                time.sleep(1)

            with self._api_semaphore:
                self._wait_for_rate_limit()
                # Get user state from Hyperliquid
                user_state = self.info_client.user_state(self.wallet_address)
            
            if not user_state:
                return {
                    "equity": 0.0,
                    "available": 0.0,
                    "margin": 0.0,
                    "positions_count": 0
                }
            
            # Extract margin summary
            margin_summary = user_state.get("marginSummary", {})
            account_value = float(margin_summary.get("accountValue", 0))
            total_margin_used = float(margin_summary.get("totalMarginUsed", 0))
            
            # Extract positions
            asset_positions = user_state.get("assetPositions", [])
            positions_count = len([p for p in asset_positions if p.get("position", {}).get("szi") != "0"])
            
            # Calculate available (withdrawable)
            withdrawable = float(user_state.get("withdrawable", 0))
            
            return {
                "equity": account_value,
                "available": withdrawable,
                "margin": total_margin_used,
                "positions_count": positions_count
            }
            
        except Exception as e:
            print(f"[HL][ERROR] get_account_summary failed: {e}")
            traceback.print_exc()
            return {
                "equity": 0.0,
                "available": 0.0,
                "margin": 0.0,
                "positions_count": 0
            }
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get simplified list of open positions
        
        Returns:
            list: [{coin, size, entry_price, unrealized_pnl}, ...]
        """
        try:
            if not self.info_client or not self.wallet_address:
                return []
            
            with self._api_semaphore:
                self._wait_for_rate_limit()
                user_state = self.info_client.user_state(self.wallet_address)
            
            if not user_state:
                return []
            
            asset_positions = user_state.get("assetPositions", [])
            positions = []
            
            for asset_pos in asset_positions:
                position = asset_pos.get("position", {})
                coin = position.get("coin", "")
                size = float(position.get("szi", 0))
                
                # Skip if no position
                if size == 0:
                    continue
                
                entry_price = float(position.get("entryPx", 0))
                unrealized_pnl = float(position.get("unrealizedPnl", 0))
                leverage = int(position.get("leverage", {}).get("value", 1))  # Extract leverage
                
                positions.append({
                    "coin": coin,
                    "size": size,
                    "entry_price": entry_price,
                    "unrealized_pnl": unrealized_pnl,
                    "leverage": leverage  # Add to output
                })
            
            return positions
            
        except Exception as e:
            print(f"[HL][ERROR] get_positions failed: {e}")
            traceback.print_exc()
            return []
    
    def get_last_price(self, symbol: str) -> Optional[float]:
        """
        Get last/mid price for a symbol
        
        Args:
            symbol: Trading symbol (e.g., "BTC", "ETH")
        
        Returns:
            float: Current price or None if failed
        """
        try:
            if not self.info_client:
                return None
            
            # Backoff if recently limited
            if time.time() - self._last_429_time < 5:
                time.sleep(0.5)

            with self._api_semaphore:
                self._wait_for_rate_limit()
                # Get all mid prices
                all_mids = self.info_client.all_mids()
            
            if not all_mids:
                return None
            
            # Return price for the symbol
            price = all_mids.get(symbol)
            
            if price is not None:
                return float(price)
            
            return None
            
        except Exception as e:
            if "429" in str(e):
                self._last_429_time = time.time()
            print(f"[HL][ERROR] get_last_price({symbol}) failed: {e}")
            traceback.print_exc()
            return None
    
    def get_prices(self, symbols: list[str]) -> dict[str, float]:
        """
        Get prices for multiple symbols
        
        Args:
            symbols: List of trading symbols
        
        Returns:
            dict: {symbol: price} for successful fetches
        """
        prices = {}
        try:
            if not self.info_client:
                return prices
            
            # Get all mid prices at once (more efficient)
            all_mids = self.info_client.all_mids()
            
            if not all_mids:
                return prices
            
            # Extract requested symbols
            for symbol in symbols:
                if symbol in all_mids:
                    prices[symbol] = float(all_mids[symbol])
            
            return prices
            
        except Exception as e:
            print(f"[HL][ERROR] get_prices failed: {e}")
            traceback.print_exc()
            return prices
    
    def get_positions_by_symbol(self) -> dict[str, dict]:
        """
        Get positions mapped by symbol
        
        Returns:
            dict: {symbol: {size, side, entry_price, unrealized_pnl, ...}}
        """
        positions_map = {}
        try:
            positions = self.get_positions()
            
            for pos in positions:
                symbol = pos["coin"]
                size = pos["size"]
                
                positions_map[symbol] = {
                    "size": abs(size),
                    "side": "LONG" if size > 0 else "SHORT",
                    "entry_price": pos["entry_price"],
                    "unrealized_pnl": pos["unrealized_pnl"],
                    "leverage": pos.get("leverage", 1)  # Include leverage
                }
            
            return positions_map
            
        except Exception as e:
            print(f"[HL][ERROR] get_positions_by_symbol failed: {e}")
            traceback.print_exc()
            return positions_map
    
    def get_meta_cached(self, ttl_seconds: int = 300) -> Optional[dict]:
        """
        Get meta (universe) with caching
        
        Args:
            ttl_seconds: Cache TTL in seconds
        
        Returns:
            dict: Meta data with universe info
        """
        import time
        current_time = time.time()
        
        # Check cache
        if self._meta_cache and (current_time - self._meta_cache_time) < ttl_seconds:
            return self._meta_cache
        
        # Fetch fresh meta
        try:
            if not self.info_client:
                return None
            
            meta = self.info_client.meta()
            
            if meta:
                self._meta_cache = meta
                self._meta_cache_time = current_time
            
            return meta
            
        except Exception as e:
            print(f"[HL][ERROR] get_meta_cached failed: {e}")
            traceback.print_exc()
            return None
    
    def get_symbol_constraints(self, symbol: str) -> dict:
        """
        Get trading constraints for a symbol
        
        Args:
            symbol: Trading symbol
        
        Returns:
            dict: {szDecimals, maxLeverage, onlyIsolated, tickSz, pxDecimals}
        """
        try:
            meta = self.get_meta_cached()
            
            if not meta or "universe" not in meta:
                return {
                    "szDecimals": 3,
                    "maxLeverage": 50,
                    "onlyIsolated": False,
                    "tickSz": 0.01,
                    "pxDecimals": 2
                }
            
            # Find symbol in universe
            for asset in meta["universe"]:
                if asset.get("name") == symbol:
                    # Get tick size - this is critical for price normalization
                    tick_sz = float(asset.get("tickSz", "0.01"))
                    
                    # Calculate price decimals from tick size
                    # tickSz=0.01 -> 2 decimals, tickSz=0.1 -> 1 decimal, etc
                    import math
                    px_decimals = max(0, -int(math.floor(math.log10(tick_sz)))) if tick_sz > 0 else 2
                    
                    return {
                        "szDecimals": asset.get("szDecimals", 3),
                        "maxLeverage": asset.get("maxLeverage", 50),
                        "onlyIsolated": asset.get("onlyIsolated", False),
                        "tickSz": tick_sz,
                        "pxDecimals": px_decimals
                    }
            
            # Default if not found
            return {
                "szDecimals": 3,
                "maxLeverage": 50,
                "onlyIsolated": False,
                "tickSz": 0.01,
                "pxDecimals": 2
            }
            
        except Exception as e:
            print(f"[HL][ERROR] get_symbol_constraints({symbol}) failed: {e}")
            return {
                "szDecimals": 3,
                "maxLeverage": 50,
                "onlyIsolated": False,
                "tickSz": 0.01,
                "pxDecimals": 2
            }
    
    def get_recent_fills(self, limit: int = 10) -> list:
        """
        Get recent fills for verification
        
        Args:
            limit: Number of recent fills
        
        Returns:
            list: Recent fills
        """
        try:
            if not self.info_client or not self.wallet_address:
                return []
            
            self._wait_for_rate_limit()
            user_fills = self.info_client.user_fills(self.wallet_address)
            
            if not user_fills:
                return []
            
            # Return most recent fills
            return user_fills[:limit]
            
        except Exception as e:
            print(f"[HL][ERROR] get_recent_fills failed: {e}")
            traceback.print_exc()
            return []
    
    def get_portfolio_pnl(self) -> Dict[str, Any]:
        """
        Fetch PnL windows from Hyperliquid Portfolio API.
        Uses POST /info with type "portfolio".
        
        Returns:
            dict with keys: day, week, month, allTime, and history arrays for extended windows
        """
        import time
        try:
            if not self.wallet_address:
                return {"error": "No wallet address"}
            
            import httpx
            self._wait_for_rate_limit()
            with httpx.Client(timeout=API_TIMEOUT_SECONDS) as client:
                resp = client.post(
                    f"{self.api_url}/info",
                    json={"type": "portfolio", "user": self.wallet_address}
                )
                
                if resp.status_code != 200:
                    print(f"[PNL][ERROR] Portfolio API returned {resp.status_code}")
                    return {"error": f"HTTP {resp.status_code}"}
                
                data = resp.json()
                
                # Parse the portfolio response
                # Format: [["day", {...}], ["week", {...}], ["month", {...}], ["allTime", {...}]]
                # Each period has pnlHistory array with last element being current PnL
                if not data or not isinstance(data, list) or len(data) == 0:
                    print(f"[PNL][WARN] Empty portfolio response")
                    return {"error": "Empty response"}
                
                result = {
                    "day": 0.0,
                    "week": 0.0,
                    "month": 0.0,
                    "allTime": 0.0,
                    "raw": data
                }
                
                for item in data:
                    if isinstance(item, list) and len(item) >= 2:
                        period_name = item[0]  # "day", "week", "month", "allTime"
                        period_data = item[1]
                        
                        # Get PnL from last entry in pnlHistory
                        pnl_hist = period_data.get("pnlHistory", [])
                        current_pnl = 0.0
                        if pnl_hist and len(pnl_hist) > 0:
                            current_pnl = float(pnl_hist[-1][1])
                        
                        if period_name == "day":
                            result["day"] = current_pnl
                        elif period_name == "week":
                            result["week"] = current_pnl
                        elif period_name == "month":
                            result["month"] = current_pnl
                        elif period_name == "allTime":
                            result["allTime"] = current_pnl
                
                print(f"[PNL] Portfolio fetched: day=${result['day']:.2f} week=${result['week']:.2f} month=${result['month']:.2f} allTime=${result['allTime']:.2f}")
                return result
                
        except Exception as e:
            print(f"[PNL][ERROR] get_portfolio_pnl failed: {e}")
            return {"error": str(e)}
    
    def get_open_orders(self) -> list:
        """
        Get open orders (MCP-first: using info_client.open_orders)
        
        Returns:
            list: Open orders with details
        """
        try:
            if not self.info_client or not self.wallet_address:
                return []
            
            # Use MCP info_client.open_orders
            self._wait_for_rate_limit()
            open_orders_response = self.info_client.open_orders(self.wallet_address)
            
            if not open_orders_response:
                return []
            
            return open_orders_response
            
        except Exception as e:
            print(f"[HL][ERROR] get_open_orders failed: {e}")
            traceback.print_exc()
            return []
    
    def get_candles(self, symbol: str, interval: str, limit: int = 100) -> list:
        """
        Get historical candles with intelligent caching
        Cache TTL varies by timeframe: 1w/1d=5min, 4h/1h=2min, 15m/5m=30s, 1m=10s
        
        Args:
            symbol: Trading symbol
            interval: Candle interval (1m, 5m, 15m, 1h, 4h, 1d, 1w)
            limit: Number of candles (max 5000)
        
        Returns:
            list: Candles with OHLCV data
        """
        try:
            if not self.info_client:
                return []
            
            import time
            current_time = time.time()
            
            # Check cache first
            cache_key = (symbol, interval)
            if cache_key in self._candles_cache:
                cached_data, cached_time = self._candles_cache[cache_key]
                ttl = self._candle_ttl.get(interval, 60)  # Default 1 min
                
                if (current_time - cached_time) < ttl:
                    # Cache hit!
                    return cached_data
            
            # Cache miss or expired - fetch fresh data
            # Detect signature once
            if not hasattr(self, '_candles_sig_detected'):
                import inspect
                sig = inspect.signature(self.info_client.candles_snapshot)
                self._candles_params = list(sig.parameters.keys())
                self._candles_sig_detected = True
                print(f"[HL] candles_signature={self._candles_params}")
            
            # Calculate time range
            now_ms = int(current_time * 1000)
            
            interval_ms = {
                "1m": 60 * 1000,
                "5m": 5 * 60 * 1000,
                "15m": 15 * 60 * 1000,
                "1h": 60 * 60 * 1000,
                "4h": 4 * 60 * 60 * 1000,
                "1d": 24 * 60 * 60 * 1000,
                "1w": 7 * 24 * 60 * 60 * 1000
            }.get(interval, 60 * 1000)
            
            start_ms = now_ms - (limit * interval_ms)
            
            # Try positional args first (most common)
            try:
                with self._api_semaphore:
                    self._wait_for_rate_limit()
                    candles = self.info_client.candles_snapshot(symbol, interval, start_ms, now_ms)
                if candles:
                    # Cache the result
                    self._candles_cache[cache_key] = (candles, current_time)
                    print(f"[HL][CACHE] Stored {symbol} {interval} ({len(candles)} candles, TTL={self._candle_ttl.get(interval, 60)}s)")
                    return candles
            except TypeError:
                pass  # Try fallback
            except Exception as e:
                if "429" in str(e):
                    self._last_429_time = time.time()
                raise e
            
            # Fallback: try with named params
            try:
                self._wait_for_rate_limit()
                candles = self.info_client.candles_snapshot(
                    coin=symbol, 
                    interval=interval, 
                    startTime=start_ms, 
                    endTime=now_ms
                )
                if candles:
                    # Cache the result
                    self._candles_cache[cache_key] = (candles, current_time)
                    print(f"[HL][CACHE] Stored {symbol} {interval} ({len(candles)} candles, TTL={self._candle_ttl.get(interval, 60)}s)")
                    return candles
            except Exception as e2:
                print(f"[HL][WARN] candles unavailable {symbol} {interval}: {e2}")
            
            return []
            
        except Exception as e:
            print(f"[HL][ERROR] get_candles({symbol}, {interval}) failed: {e}")
            return []

    
    def get_orderbook(self, symbol: str, depth: int = 10) -> dict:
        """
        Get L2 orderbook snapshot with 15s caching
        Reduces API spam while keeping data reasonably fresh
        
        Args:
            symbol: Trading symbol
            depth: Number of levels per side
        
        Returns:
            dict: Orderbook with bids, asks, spread, imbalance
        """
        try:
            if not self.info_client:
                return {}
            
            import time
            current_time = time.time()
            
            # Check cache
            if symbol in self._orderbook_cache:
                cached_data, cached_time = self._orderbook_cache[symbol]
                if (current_time - cached_time) < self._orderbook_ttl:
                    return cached_data
            
            # Use MCP info_client.l2_snapshot
            with self._api_semaphore:
                self._wait_for_rate_limit()
                snapshot = self.info_client.l2_snapshot(symbol)
            
            if not snapshot:
                return {}
            
            # Robust parsing - handle multiple formats
            bids = []
            asks = []
            
            # Format 1: {"levels": [[bids], [asks]]}
            if "levels" in snapshot and isinstance(snapshot["levels"], list):
                if len(snapshot["levels"]) > 0:
                    bids = snapshot["levels"][0][:depth] if isinstance(snapshot["levels"][0], list) else []
                if len(snapshot["levels"]) > 1:
                    asks = snapshot["levels"][1][:depth] if isinstance(snapshot["levels"][1], list) else []
            
            # Format 2: {"bids": [...], "asks": [...]}
            elif "bids" in snapshot and "asks" in snapshot:
                bids = snapshot["bids"][:depth] if isinstance(snapshot["bids"], list) else []
                asks = snapshot["asks"][:depth] if isinstance(snapshot["asks"], list) else []
            
            else:
                print(f"[HL][WARN] get_orderbook({symbol}) - unknown format: {list(snapshot.keys())}")
                return {}
            
            # Normalize to consistent format
            try:
                bids_normalized = []
                for b in bids:
                    if isinstance(b, (list, tuple)) and len(b) >= 2:
                        bids_normalized.append([float(b[0]), float(b[1])])
                    elif isinstance(b, dict) and "px" in b and "sz" in b:
                        bids_normalized.append([float(b["px"]), float(b["sz"])])
                
                asks_normalized = []
                for a in asks:
                    if isinstance(a, (list, tuple)) and len(a) >= 2:
                        asks_normalized.append([float(a[0]), float(a[1])])
                    elif isinstance(a, dict) and "px" in a and "sz" in a:
                        asks_normalized.append([float(a["px"]), float(a["sz"])])
                
                # Calculate spread and imbalance
                best_bid = bids_normalized[0][0] if bids_normalized else 0
                best_ask = asks_normalized[0][0] if asks_normalized else 0
                spread = best_ask - best_bid if best_bid and best_ask else 0
                
                bid_volume = sum(b[1] for b in bids_normalized)
                ask_volume = sum(a[1] for a in asks_normalized)
                imbalance = bid_volume / ask_volume if ask_volume > 0 else 1.0
                
                result = {
                    "bids": bids_normalized,
                    "asks": asks_normalized,
                    "spread": spread,
                    "imbalance": imbalance
                }
                
                # Cache the result
                self._orderbook_cache[symbol] = (result, current_time)
                
                return result
                
            except Exception as parse_error:
                print(f"[HL][ERROR] get_orderbook({symbol}) parse failed: {parse_error}")
                return {}
            
        except Exception as e:
            if "429" in str(e):
                self._last_429_time = time.time()
            print(f"[HL][ERROR] get_orderbook({symbol}) failed: {e}")
            traceback.print_exc()
            return {}
    
    def get_funding_info(self, symbol: str) -> dict:
        """
        Get funding rate and market info with 60s caching
        Funding rates change slowly, safe to cache
        
        Args:
            symbol: Trading symbol
        
        Returns:
            dict: Funding rate, next funding time, mark price, etc
        """
        try:
            if not self.info_client:
                return {}
            
            import time
            current_time = time.time()
            
            # Check cache
            if symbol in self._funding_cache:
                cached_data, cached_time = self._funding_cache[symbol]
                if (current_time - cached_time) < self._funding_ttl:
                    return cached_data
            
            # Fetch fresh data
            self._wait_for_rate_limit()
            meta_and_ctxs = self.info_client.meta_and_asset_ctxs()
            
            if not meta_and_ctxs:
                return {}
            
            # Find symbol in contexts
            for ctx in meta_and_ctxs[1]:  # Asset contexts
                if ctx.get("coin") == symbol:
                    funding_rate = float(ctx.get("funding", 0)) * 100  # Convert to %
                    mark_price = float(ctx.get("markPx", 0))
                    
                    result = {
                        "funding_rate": funding_rate,
                        "mark_price": mark_price
                    }
                    
                    # Add next funding time if available
                    if "nextFundingTime" in ctx:
                        result["next_funding_time"] = ctx["nextFundingTime"]
                    
                    # Add open interest if available
                    if "openInterest" in ctx:
                        result["open_interest"] = float(ctx["openInterest"])
                    
                    # Cache the result
                    self._funding_cache[symbol] = (result, current_time)
                    
                    return result
            
            return {}
            
        except Exception as e:
            print(f"[HL][ERROR] get_funding_info({symbol}) failed: {e}")
            traceback.print_exc()
            return {}

    def get_account_state(self) -> Dict[str, Any]:
        """
        Get full account state (wrapper for user_state)
        Fixes AttributeError: 'HLClient' object has no attribute 'get_account_state'
        """
        try:
            if not self.info_client or not self.wallet_address:
                return {}
            
            return self.info_client.user_state(self.wallet_address)
        except Exception as e:
            print(f"[HL][ERROR] get_account_state failed: {e}")
            return {}

    def close_position(self, symbol: str, size: float) -> Dict[str, Any]:
        """
        Close position for a symbol (Market Order reduce-only)
        Fixes AttributeError: 'HLClient' object has no attribute 'close_position'
        """
        try:
            # Determine side to close
            positions = self.get_positions_by_symbol()
            if symbol not in positions:
                return {"status": "error", "response": "No position found"}
            
            pos = positions[symbol]
            is_buy = (pos["side"] == "SHORT") # Close SHORT by BUYing
            
            print(f"[HL] Closing {symbol} {pos['side']} size={size} (is_buy={is_buy})")
            
            return self.place_market_order(
                symbol=symbol,
                is_buy=is_buy,
                size=size,
                reduce_only=True
            )
            
        except Exception as e:
            print(f"[HL][ERROR] close_position({symbol}) failed: {e}")
            return {"status": "error", "response": str(e)}

    def place_market_order(self, symbol: str, is_buy: bool, size: float, reduce_only: bool = False, slippage: float = None) -> dict:
        """
        Place market order using SDK market_open
        
        Args:
            symbol: Trading symbol
            is_buy: True for BUY, False for SELL
            size: Order size
            reduce_only: If True, can only reduce position
            slippage: Slippage tolerance (default from config)
        
        Returns:
            dict: Exchange response
        """
        try:
            if not self.exchange_client:
                return {"status": "error", "response": "exchange_client not initialized"}
            
            # Use config slippage if not provided
            if slippage is None:
                from config import ORDER_SLIPPAGE
                slippage = ORDER_SLIPPAGE
            
            # Use market_open for opening positions (SDK handles tick size)
            # Signature: market_open(name, is_buy, sz, px=None, slippage=0.05, cloid, builder)
            response = self.exchange_client.market_open(
                name=symbol,
                is_buy=is_buy,
                sz=size,
                px=None,  # Let SDK calculate market price
                slippage=slippage
            )
            
            return response
            
        except Exception as e:
            print(f"[HL][ERROR] place_market_order failed: {e}")
            traceback.print_exc()
            return {"status": "error", "response": str(e)}
    
    def close_position_market(self, symbol: str, size: float = None, slippage: float = None) -> dict:
        """
        Close position using SDK market_close
        
        Args:
            symbol: Trading symbol
            size: Size to close (None = close all)
            slippage: Slippage tolerance
        
        Returns:
            dict: Exchange response
        """
        try:
            if not self.exchange_client:
                return {"status": "error", "response": "exchange_client not initialized"}
            
            if slippage is None:
                from config import ORDER_SLIPPAGE
                slippage = ORDER_SLIPPAGE
            
            # Signature: market_close(coin, sz=None, px=None, slippage=0.05, cloid, builder)
            response = self.exchange_client.market_close(
                coin=symbol,
                sz=size,
                px=None,
                slippage=slippage
            )
            
            return response
            
        except Exception as e:
            print(f"[HL][ERROR] close_position_market failed: {e}")
            traceback.print_exc()
            return {"status": "error", "response": str(e)}
    
    def update_leverage(self, symbol: str, leverage: int, is_cross: bool = False) -> dict:
        """
        Update leverage for symbol (wraps MCP exchange_client)
        
        Args:
            symbol: Trading symbol
            leverage: Leverage value
            is_cross: True for cross margin, False for isolated
        
        Returns:
            dict: Exchange response
        """
        try:
            if not self.exchange_client:
                return {"status": "error", "response": "exchange_client not initialized"}
            
            # Signature: update_leverage(leverage, name, is_cross)
            response = self.exchange_client.update_leverage(
                leverage=leverage,
                name=symbol,  # Correct parameter name
                is_cross=is_cross
            )
            
            return response
            
        except Exception as e:
            print(f"[HL][ERROR] update_leverage failed: {e}")
            traceback.print_exc()
            return {"status": "error", "response": str(e)}
    
    def place_trigger_order(self, symbol: str, is_buy: bool, trigger_price: float, size: float, 
                           is_stop_loss: bool = True, reduce_only: bool = True) -> dict:
        """
        Place trigger order (stop loss or take profit)
        
        Args:
            symbol: Trading symbol
            is_buy: True for BUY trigger, False for SELL trigger
            trigger_price: Price that triggers the order
            size: Order size
            is_stop_loss: True for stop loss (sl), False for take profit (tp)
            reduce_only: If True, can only reduce position
        
        Returns:
            dict: Exchange response
        """
        try:
            if not self.exchange_client:
                return {"status": "error", "response": "exchange_client not initialized"}
            
            # Helper to ensure float type (SDK requires float, not str)
            def _to_float(x, name="value"):
                """Convert to float, handling str with $ and ,"""
                if x is None:
                    raise ValueError(f"{name} is None")
                if isinstance(x, (int, float)):
                    return float(x)
                if isinstance(x, str):
                    s = x.strip().replace("$", "").replace(",", "")
                    return float(s)
                raise TypeError(f"{name} must be number or str, got {type(x)}")
            
            # Convert all numeric values to float (CRITICAL for SDK)
            trigger_px_f = _to_float(trigger_price, "trigger_price")
            size_f = _to_float(size, "size")
            
            # Normalize trigger price with tick size
            constraints = self.get_symbol_constraints(symbol)
            tick_sz = constraints.get("tickSz", 0.01)
            
            # CRITICAL: Hyperliquid TRIGGER orders require larger tick sizes than limit orders
            # BTC/ETH triggers need tick=1.0 (whole dollars), not 0.01 from meta
            TRIGGER_TICK_OVERRIDES = {
                "BTC": 1.0,
                "ETH": 0.1,
                "SOL": 0.01,
                "DOGE": 0.00001,
                "XRP": 0.0001,
                "HYPE": 0.01,
            }
            trigger_tick = TRIGGER_TICK_OVERRIDES.get(symbol, max(tick_sz, 0.01))
            
            # Use quantize_to_tick helper for robust price normalization
            trigger_px_rounded = quantize_to_tick(trigger_px_f, trigger_tick, mode="nearest")
            
            # Log types for debugging
            print(f"[HL] place_trigger_order symbol={symbol} triggerPx={trigger_px_rounded} size={size_f}")
            
            # Build trigger order - CRITICAL: all values must be float/int, NOT string
            # Signature: order(name, is_buy, sz, limit_px, order_type, reduce_only, cloid, builder)
            # order_type for trigger: {"trigger": {"triggerPx": float, "isMarket": bool, "tpsl": str}}
            order_type = {
                "trigger": {
                    "triggerPx": trigger_px_rounded,  # MUST be float
                    "isMarket": True,
                    "tpsl": "sl" if is_stop_loss else "tp"
                }
            }
            
            response = self.exchange_client.order(
                name=symbol,
                is_buy=is_buy,
                sz=size_f,  # MUST be float
                limit_px=trigger_px_rounded,  # MUST be float
                order_type=order_type,
                reduce_only=reduce_only
            )
            
            return response
            
        except Exception as e:
            print(f"[HL][ERROR] place_trigger_order failed: {e}")
            traceback.print_exc()
            return {"status": "error", "response": str(e)}
    
    def cancel_order(self, symbol: str, oid) -> bool:
        """
        Cancel an open order by OID
        CRITICAL FIX: This method was MISSING causing bracket manager to fail!
        
        Args:
            symbol: Trading symbol (coin name)
            oid: Order ID to cancel
            
        Returns:
            bool: True if canceled successfully, False otherwise
        """
        try:
            if not self.exchange_client:
                print(f"[HL][ERROR] cancel_order - exchange_client not initialized")
                return False
            
            # Convert OID to int if string
            try:
                oid_int = int(oid)
            except (ValueError, TypeError):
                print(f"[HL][ERROR] cancel_order - invalid OID format: {oid}")
                return False
            
            print(f"[HL] Canceling order symbol={symbol} oid={oid_int}")
            
            # SDK cancel signature: cancel(name, oid)
            response = self.exchange_client.cancel(symbol, oid_int)
            
            # Check response status
            if isinstance(response, dict):
                status = response.get("status")
                if status == "ok":
                    print(f"[HL][OK] Canceled oid={oid_int}")
                    return True
                else:
                    error_msg = response.get("response", "unknown_error")
                    print(f"[HL][FAIL] Cancel failed oid={oid_int} status={status} error={error_msg}")
                    return False
            else:
                # Some SDKs return None/True on success
                print(f"[HL][OK] Canceled oid={oid_int} (non-dict response)")
                return True
                
        except Exception as e:
            print(f"[HL][ERROR] cancel_order({symbol}, {oid}) exception: {e}")
            traceback.print_exc()
            return False
