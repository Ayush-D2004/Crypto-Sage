import operator
from typing import TypedDict, List, Annotated, Dict, Any

class AgentState(TypedDict):
    """
    Represents the state of our Web3 research agent.
    """
    query: str
    coin_id: str
    market_data: Dict[str, Any]
    news_articles: List[Dict[str, str]]
    historical_data: Dict[str, Any]
    metrics: Dict[str, float]
    analysis: str
    report: str
    error: str
