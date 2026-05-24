import os
import logging
import requests
from typing import Dict, Any, List
from ratelimit import limits, sleep_and_retry
from tenacity import retry, stop_after_attempt, wait_exponential
import streamlit as st
from tavily import TavilyClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"

# Rate limits for CoinGecko (e.g. 15 calls per 60 seconds)
CALLS = 15
RATE_LIMIT = 60

@st.cache_data(ttl=3600, show_spinner=False)
@sleep_and_retry
@limits(calls=CALLS, period=RATE_LIMIT)
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_market_data(coin_id: str) -> Dict[str, Any]:
    """
    Fetches market data for a given cryptocurrency from CoinGecko API.
    Includes retries with exponential backoff for resilience.
    """
    logger.info(f"Fetching market data for {coin_id} from CoinGecko...")
    url = f"{COINGECKO_BASE_URL}/coins/{coin_id}"
    params = {
        "localization": "false",
        "tickers": "false",
        "community_data": "false",
        "developer_data": "false",
        "sparkline": "false"
    }
    
    headers = {
        "accept": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Extract relevant fields
        market_data = {
            "name": data.get("name"),
            "symbol": data.get("symbol"),
            "current_price_usd": data.get("market_data", {}).get("current_price", {}).get("usd"),
            "market_cap_usd": data.get("market_data", {}).get("market_cap", {}).get("usd"),
            "market_cap_rank": data.get("market_cap_rank"),
            "total_volume_usd": data.get("market_data", {}).get("total_volume", {}).get("usd"),
            "ath_usd": data.get("market_data", {}).get("ath", {}).get("usd"),
            "price_change_percentage_24h": data.get("market_data", {}).get("price_change_percentage_24h")
        }
        logger.info(f"Successfully fetched market data for {coin_id}")
        return market_data
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data from CoinGecko for {coin_id}: {str(e)}")
        raise

@st.cache_data(ttl=3600, show_spinner=False)
@sleep_and_retry
@limits(calls=CALLS, period=RATE_LIMIT)
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_historical_data(coin_id: str, days: int = 7) -> Dict[str, Any]:
    """
    Fetches historical market data (prices) for a given cryptocurrency from CoinGecko API.
    """
    logger.info(f"Fetching {days} days of historical data for {coin_id} from CoinGecko...")
    url = f"{COINGECKO_BASE_URL}/coins/{coin_id}/market_chart"
    params = {
        "vs_currency": "usd",
        "days": str(days)
    }
    
    headers = {
        "accept": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Successfully fetched historical data for {coin_id}")
        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching historical data from CoinGecko for {coin_id}: {str(e)}")
        raise

@st.cache_data(ttl=3600, show_spinner=False)
@sleep_and_retry
@limits(calls=CALLS, period=RATE_LIMIT)
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def resolve_coin_id(query: str) -> str:
    """
    Resolves a cryptocurrency name to its exact CoinGecko ID using their search API.
    """
    query_lower = query.strip().lower()
    
    # Hardcoded map for popular coins that CoinGecko's search API struggles with
    POPULAR_COINS = {
        "binance coin": "binancecoin",
        "bnb": "binancecoin",
        "bitcoin": "bitcoin",
        "btc": "bitcoin",
        "ethereum": "ethereum",
        "eth": "ethereum",
        "solana": "solana",
        "sol": "solana",
        "ripple": "ripple",
        "xrp": "ripple",
        "cardano": "cardano",
        "ada": "cardano"
    }
    if query_lower in POPULAR_COINS:
        return POPULAR_COINS[query_lower]

    logger.info(f"Resolving CoinGecko ID for query: '{query}'...")
    url = f"{COINGECKO_BASE_URL}/search"
    params = {"query": query}
    headers = {"accept": "application/json"}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        coins = data.get("coins", [])
        if coins:
            # Filter and sort by market cap rank to avoid obscure/dead tokens
            valid_coins = [c for c in coins if c.get("market_cap_rank") is not None]
            if valid_coins:
                valid_coins.sort(key=lambda x: x["market_cap_rank"])
                coin_id = valid_coins[0].get("id")
            else:
                coin_id = coins[0].get("id")
            
            logger.info(f"Resolved query '{query}' to coin_id '{coin_id}'")
            return coin_id
        
        # Fallback naive approach
        fallback_id = query_lower.replace(" ", "-")
        logger.warning(f"Could not resolve query '{query}', falling back to '{fallback_id}'")
        return fallback_id
    except requests.exceptions.RequestException as e:
        logger.error(f"Error resolving coin_id for '{query}': {str(e)}")
        return query_lower.replace(" ", "-")

@st.cache_data(ttl=3600, show_spinner=False)
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_news(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Fetches recent news articles using the Tavily Search API.
    """
    logger.info(f"Fetching news for query: '{query}' from Tavily...")
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    if not tavily_api_key:
        logger.error("TAVILY_API_KEY environment variable is missing.")
        raise ValueError("TAVILY_API_KEY is not set.")

    try:
        client = TavilyClient(api_key=tavily_api_key)
        # We use a focused search query to get the most relevant crypto news
        search_query = f"{query} cryptocurrency news"
        response = client.search(query=search_query, search_depth="advanced", max_results=max_results)
        
        articles = []
        for result in response.get("results", []):
            articles.append({
                "title": result.get("title", "No Title"),
                "url": result.get("url", ""),
                "content": result.get("content", "No Content")
            })
            
        logger.info(f"Successfully fetched {len(articles)} news articles for '{query}'")
        return articles
    except Exception as e:
        logger.error(f"Error fetching news from Tavily for '{query}': {str(e)}")
        raise
