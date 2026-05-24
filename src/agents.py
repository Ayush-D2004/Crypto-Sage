import json
import logging
import os
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List

from .state import AgentState
from .tools import fetch_market_data, fetch_news, fetch_historical_data
from .prompts import ANALYZER_PROMPT, REPORTER_PROMPT

logger = logging.getLogger(__name__)

class AnalysisOutput(BaseModel):
    sentiment: str = Field(description="Overall Sentiment (Bullish, Bearish, or Neutral)")
    summary: str = Field(description="A brief summary of the current market context")
    catalysts: List[str] = Field(description="Key upcoming catalysts or positive drivers")
    risks: List[str] = Field(description="Potential risks or negative factors")

def get_llm(model_name: str = None):
    """Initialize the Groq LLM."""
    if model_name is None:
        model_name = os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-versatile")
    return ChatGroq(model_name=model_name, temperature=0)

def _compress_hist(hist_data):
    """Compress historical data (prices) to prevent LLM token limit issues."""
    if not hist_data or "prices" not in hist_data:
        return {}
    prices = hist_data["prices"]
    if len(prices) > 7:
        step = len(prices) // 7
        sampled = prices[::step][:7]
    else:
        sampled = prices
    return {"prices": [[p[0], round(p[1], 4)] for p in sampled]}

def market_fetcher_node(state: AgentState) -> AgentState:
    """Fetches market data for the given coin_id."""
    logger.info(f"--- NODE: Market Fetcher for {state['coin_id']} ---")
    try:
        data = fetch_market_data(state["coin_id"])
        hist_data = fetch_historical_data(state["coin_id"], days=7)
        return {"market_data": data, "historical_data": hist_data}
    except Exception as e:
        logger.error(f"Failed to fetch market data: {e}")
        return {"error": f"Market Data Error: {str(e)}"}

def news_fetcher_node(state: AgentState) -> AgentState:
    """Fetches recent news for the given query."""
    logger.info(f"--- NODE: News Fetcher for '{state['query']}' ---")
    try:
        articles = fetch_news(state["query"])
        return {"news_articles": articles}
    except Exception as e:
        logger.error(f"Failed to fetch news: {e}")
        return {"error": f"News Fetch Error: {str(e)}"}

def analyzer_node(state: AgentState) -> AgentState:
    """Analyzes market data and news using LLM."""
    logger.info("--- NODE: Analyzer ---")
    if "error" in state and state["error"]:
        logger.warning("Skipping analyzer due to previous error.")
        return state

    try:
        llm = get_llm()
        structured_llm = llm.with_structured_output(AnalysisOutput)
        
        prompt = ChatPromptTemplate.from_template(ANALYZER_PROMPT)
        chain = prompt | structured_llm
        
        result = chain.invoke({
            "market_data": json.dumps(state.get("market_data", {}), indent=2),
            "historical_data": json.dumps(_compress_hist(state.get("historical_data", {})), indent=2),
            "news_articles": json.dumps(state.get("news_articles", []), indent=2)
        })
        
        # Convert Pydantic object back to JSON string or dict for state
        analysis_json = result.model_dump_json(indent=2)
        return {"analysis": analysis_json}
    except Exception as e:
        logger.error(f"Failed in analyzer node: {e}")
        return {"error": f"Analyzer Error: {str(e)}"}

def reporter_node(state: AgentState) -> AgentState:
    """Generates the final markdown report."""
    logger.info("--- NODE: Reporter ---")
    if "error" in state and state["error"]:
        logger.warning("Skipping reporter due to previous error.")
        return {"report": f"### Error Generating Report\n\n{state['error']}"}

    try:
        llm = get_llm()
        prompt = ChatPromptTemplate.from_template(REPORTER_PROMPT)
        chain = prompt | llm
        
        result = chain.invoke({
            "query": state["query"],
            "market_data": json.dumps(state.get("market_data", {}), indent=2),
            "historical_data": json.dumps(_compress_hist(state.get("historical_data", {})), indent=2),
            "analysis": state.get("analysis", "No analysis available."),
            "news_articles": json.dumps(state.get("news_articles", []), indent=2)
        })
        
        return {"report": result.content}
    except Exception as e:
        logger.error(f"Failed in reporter node: {e}")
        return {"error": f"Reporter Error: {str(e)}"}
