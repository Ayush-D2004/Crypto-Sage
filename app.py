import os
import streamlit as st
from dotenv import load_dotenv
import logging
import time
import pandas as pd
import plotly.express as px

from src.graph import build_research_graph
from src.state import AgentState

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="CryptoSage - Web3 Autonomous Research Agent",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better aesthetics
st.markdown("""
<style>
    .report-container {
        padding: 2rem;
        border-radius: 10px;
        background-color: #f8f9fa;
        color: #1e1e1e;
        margin-top: 2rem;
    }
    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
        .report-container {
            background-color: #1e1e1e;
            color: #f8f9fa;
            border: 1px solid #333;
        }
    }
</style>
""", unsafe_allow_html=True)

st.title("🔮 CryptoSage")
st.subheader("Autonomous Web3 Research Agent")

st.sidebar.header("Configuration")
st.sidebar.info(
    "CryptoSage uses LangGraph, Groq, Tavily, and CoinGecko to compile professional-grade crypto research reports."
)

# Check API Keys
groq_api_key = os.getenv("GROQ_API_KEY")
tavily_api_key = os.getenv("TAVILY_API_KEY")

if not groq_api_key or not tavily_api_key:
    st.sidebar.error("API Keys missing. Please ensure GROQ_API_KEY and TAVILY_API_KEY are set in your .env file.")
else:
    st.sidebar.success("API Keys loaded successfully.")

# Input Section
st.write("Enter a cryptocurrency token or name to generate a comprehensive research report.")
col1, col2 = st.columns([3, 1])

with col1:
    query = st.text_input("Token Name or Query (e.g., 'Bitcoin', 'Ethereum', 'Solana')", placeholder="e.g. Solana")

with col2:
    coin_id = st.text_input("CoinGecko ID (optional)", placeholder="e.g. solana", help="If left blank, we will try to infer it from the query.")

if st.button("Generate Research Report", type="primary", width='stretch'):
    if not query:
        st.warning("Please enter a token name or query.")
    elif not groq_api_key or not tavily_api_key:
        st.error("Cannot proceed without API keys.")
    else:
        # Infer coin_id if not provided
        inferred_coin_id = coin_id.strip().lower() if coin_id else query.strip().lower().replace(" ", "-")
        
        st.info(f"Initializing CryptoSage for **{query}** (ID: {inferred_coin_id})...")
        
        # Initialize Graph
        app = build_research_graph()
        
        # Initial State
        initial_state = {
            "query": query,
            "coin_id": inferred_coin_id,
            "market_data": {},
            "news_articles": [],
            "analysis": "",
            "report": "",
            "error": ""
        }
        
        # Progress Tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            start_time = time.time()
            current_state = initial_state.copy()
            
            # Stream events from LangGraph
            for event in app.stream(initial_state):
                for key, value in event.items():
                    # Update our local state with the diff
                    current_state.update(value)
                    
                    if "error" in value and value["error"]:
                        st.error(f"Error in {key}: {value['error']}")
                        st.stop()
                        
                    if key == "market_fetcher":
                        status_text.write("📈 Fetched Market Data from CoinGecko...")
                        progress_bar.progress(25)
                    elif key == "news_fetcher":
                        status_text.write("📰 Fetched Recent News from Tavily...")
                        progress_bar.progress(50)
                    elif key == "analyzer":
                        status_text.write("🧠 Analyzing Data and Identifying Catalysts/Risks with Groq LLM...")
                        progress_bar.progress(75)
                    elif key == "reporter":
                        status_text.write("📝 Synthesizing Final Report...")
                        progress_bar.progress(100)
            
            end_time = time.time()
            latency = end_time - start_time

            st.success("Research Report Generated Successfully!")
            
            # Display Performance Metrics
            st.subheader("Performance Metrics")
            st.metric(label="Total Execution Latency", value=f"{latency:.2f} s")

            # Display Data Visualization
            if "historical_data" in current_state and "prices" in current_state["historical_data"]:
                st.subheader("Historical Price Trend (7 Days)")
                prices = current_state["historical_data"]["prices"]
                df = pd.DataFrame(prices, columns=["timestamp", "price"])
                df["date"] = pd.to_datetime(df["timestamp"], unit="ms")
                fig = px.line(df, x="date", y="price", title=f"{query.capitalize()} Price Trend", template="plotly_white")
                st.plotly_chart(fig, width='stretch')

            # Display Report
            st.markdown("<div class='report-container'>", unsafe_allow_html=True)
            st.markdown(current_state["report"])
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Expandable Raw Data
            with st.expander("View Raw Data"):
                st.write("### Market Data")
                st.json(current_state["market_data"])
                st.write("### News Articles")
                st.json(current_state["news_articles"])
                
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")
            st.stop()
