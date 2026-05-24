import logging
from langgraph.graph import StateGraph, END
from .state import AgentState
from .agents import market_fetcher_node, news_fetcher_node, analyzer_node, reporter_node

logger = logging.getLogger(__name__)

def build_research_graph() -> StateGraph:
    """
    Builds and compiles the LangGraph workflow for the Web3 Research Agent.
    """
    logger.info("Building the LangGraph workflow...")
    
    # Initialize the StateGraph with our TypedDict
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("market_fetcher", market_fetcher_node)
    workflow.add_node("news_fetcher", news_fetcher_node)
    workflow.add_node("analyzer", analyzer_node)
    workflow.add_node("reporter", reporter_node)
    
    # Define edges (Sequential execution)
    # The entrypoint is not explicitly a node, we set it below
    workflow.set_entry_point("market_fetcher")
    workflow.add_edge("market_fetcher", "news_fetcher")
    workflow.add_edge("news_fetcher", "analyzer")
    workflow.add_edge("analyzer", "reporter")
    workflow.add_edge("reporter", END)
    
    # Compile the graph
    app = workflow.compile()
    logger.info("LangGraph workflow compiled successfully.")
    
    return app
