# CryptoSage

CryptoSage is an **Autonomous Web3 Research Agent** built to provide high-quality, institutional-grade cryptocurrency research reports. Powered by advanced Large Language Models (LLMs) via **Groq**, orchestrated via **LangGraph**, and featuring a UI with **Streamlit**, CryptoSage synthesizes live market data, historical price trends, and the latest news into structured, actionable intelligence.

---

## Features

- **Autonomous Research Pipeline**: Automatically fetches current market data, historical pricing trends, and breaking news.
- **Lightning Fast LLM Analysis**: Uses the ultra-fast Groq API (`llama-3.3-70b-versatile`) to generate bullish/bearish sentiments, risk factors, and key catalysts.
- **Interactive Visualizations**: Includes responsive, interactive charts rendered with **Plotly** to visualize 7-day historical price movements.
- **Performance Optimized**: Implements intelligent API caching, rate-limiting (via `ratelimit` & `tenacity`), and real-time execution latency tracking.
- **Enterprise-Ready Infrastructure**: Includes fully functional **Docker** support and a continuous integration (CI) pipeline via **GitHub Actions**.

---

## Architecture

CryptoSage uses a state-driven agent architecture built on **LangGraph**. The workflow executes sequentially:

1. **Market Fetcher**: Connects to CoinGecko to grab real-time prices, market cap, and 7-day historical trends. (Features smart caching & rate limiting)
2. **News Fetcher**: Uses Tavily Search API to scan the web for the latest high-signal cryptocurrency news.
3. **Analyzer**: Feeds data into Groq's LLM to generate a structured JSON analysis (Sentiment, Summary, Catalysts, Risks).
4. **Reporter**: Compiles the raw data and analysis into a polished Markdown report for the user interface.

---

## Prerequisites

To run CryptoSage locally, you will need:

- **Python 3.10+** (if running via Python)
- **Docker & Docker Compose** (if running via container)
- A **Groq API Key** (Get one at [console.groq.com](https://console.groq.com/keys))
- A **Tavily API Key** (Get one at [tavily.com](https://tavily.com/))

---

## Installation & Usage

### 1. Clone the Repository

```bash
git clone https://github.com/Ayush-D2004/Crypto-Sage.git
cd Crypto-Sage
```

### 2. Configure Environment Variables

Create a `.env` file in the project root and add your API keys:

```env
GROQ_API_KEY=your_groq_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
GROQ_MODEL_NAME=llama-3.3-70b-versatile # Optional
```

### 3. Option A: Run via Python Virtual Environment

```bash
python -m venv venv

source venv/Scripts/activate

pip install -r requirements.txt

streamlit run app.py
```

### 3. Option B: Run via Docker (Recommended)

```bash
# Build and run the container in detached mode
docker-compose up -d

# The app will be available at http://localhost:8501
```

---

## Testing

The project includes a robust test suite using `pytest`. Mocks are utilized to avoid burning API limits during testing.

To run the tests:

```bash
pytest tests/ -v
```

---

## Performance Metrics

CryptoSage is built for speed:

- **Streaming UI**: LangGraph streams state updates to the UI in real-time, providing immediate visual feedback.
- **Caching**: `@st.cache_data` is heavily utilized to prevent redundant network calls.
- **Latency Monitoring**: The UI displays end-to-end latency metrics upon report generation, typically taking under ~5 seconds for the entire pipeline!

---
