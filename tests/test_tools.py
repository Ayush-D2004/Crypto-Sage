import pytest
from unittest.mock import patch
from src.tools import fetch_market_data, fetch_historical_data

@patch("src.tools.requests.get")
def test_fetch_market_data(mock_get):
    # Setup mock
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "name": "Ethereum",
        "symbol": "eth",
        "market_cap_rank": 2,
        "market_data": {
            "current_price": {"usd": 2000},
            "market_cap": {"usd": 240000000000},
            "total_volume": {"usd": 10000000000},
            "ath": {"usd": 4800},
            "price_change_percentage_24h": 5.5
        }
    }
    
    # Call function
    data = fetch_market_data("ethereum")
    
    # Assertions
    assert data["name"] == "Ethereum"
    assert data["symbol"] == "eth"
    assert data["current_price_usd"] == 2000
    assert data["market_cap_rank"] == 2
    mock_get.assert_called_once()

@patch("src.tools.requests.get")
def test_fetch_historical_data(mock_get):
    # Setup mock
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "prices": [[1620000000000, 2000], [1620086400000, 2100]],
        "market_caps": [],
        "total_volumes": []
    }
    
    # Call function
    data = fetch_historical_data("ethereum", days=7)
    
    # Assertions
    assert "prices" in data
    assert len(data["prices"]) == 2
    assert data["prices"][0][1] == 2000
    mock_get.assert_called_once()
