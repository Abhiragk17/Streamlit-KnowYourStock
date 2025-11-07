import streamlit as st
import requests
from typing import Dict, Any, Optional,List
import json
import os
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

# Page configuration
st.set_page_config(
    page_title="KnowYourStock",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Programmatic settings replacing .streamlit/config.toml
try:
    st.set_option('server.enableCORS', False)
    st.set_option('server.enableXsrfProtection', True)
except Exception:
    pass

# API Configuration - Check environment variable, then secrets, then default
try:
    API_BASE_URL = os.getenv("API_BASE_URL") or st.secrets.get("API_BASE_URL", "http://localhost:8000")
except Exception:
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Custom CSS for attractive UI
st.markdown("""
    <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: bold;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 2rem;
        }
        .stock-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1.5rem;
            border-radius: 10px;
            color: white;
            margin-bottom: 1rem;
        }
        .metric-card {
            background: #f0f2f6;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #1f77b4;
            margin: 0.5rem 0;
        }
        .news-card {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            margin: 1rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .news-title {
            font-size: 1.1rem;
            font-weight: bold;
            color: #1f77b4;
            margin-bottom: 0.5rem;
        }
        .stButton>button {
            width: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            font-weight: bold;
        }
        .stButton>button:hover {
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        }
        .chat-message {
            padding: 1rem;
            border-radius: 8px;
            margin: 0.5rem 0;
        }
        .user-message {
            background: #e3f2fd;
            text-align: right;
        }
        .bot-message {
            background: #f5f5f5;
            text-align: left;
        }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'home'
if 'stock_data' not in st.session_state:
    st.session_state.stock_data = None
if 'stock_name' not in st.session_state:
    st.session_state.stock_name = None
if 'ticker_symbol' not in st.session_state:
    st.session_state.ticker_symbol = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []  # Store as BaseMessage objects
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []  # For LangGraph workflow memory (dict format)
if 'loading' not in st.session_state:
    st.session_state.loading = False

def process_message_for_display(message: BaseMessage) -> Dict[str, str]:
    """Convert BaseMessage to dict format for display/rendering"""
    if isinstance(message, HumanMessage):
        return {"role": "user", "content": message.content}
    elif isinstance(message, AIMessage):
        return {"role": "assistant", "content": message.content}
    elif isinstance(message, SystemMessage):
        return {"role": "system", "content": message.content}
    else:
        # Fallback for unknown message types
        return {"role": "unknown", "content": str(message.content) if hasattr(message, 'content') else str(message)}

def convert_messages_to_dict(messages: List[BaseMessage]) -> List[Dict[str, str]]:
    """Convert list of BaseMessage objects to list of dicts for API calls"""
    return [process_message_for_display(msg) for msg in messages]

def convert_dict_to_messages(message_dicts: List[Dict[str, str]]) -> List[BaseMessage]:
    """Convert list of dicts to BaseMessage objects"""
    messages = []
    for msg_dict in message_dicts:
        role = msg_dict.get("role", "user")
        content = msg_dict.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
        elif role == "system":
            messages.append(SystemMessage(content=content))
    return messages

def call_langgraph_api(stock_name: str) -> Optional[Dict[str, Any]]:
    """Call the LangGraph FastAPI endpoint"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/langgraph",
            json={"stock_name": stock_name},
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error calling API: {str(e)}")
        return None

def call_chat_api(message: str, context: Optional[Dict] = None, messages: Optional[List[BaseMessage]] = None) -> tuple[Optional[str], Optional[List[BaseMessage]]]:
    """Call the chat FastAPI endpoint
    
    Args:
        message: Current user message
        context: Optional context dict
        messages: List of BaseMessage objects (last 5 messages)
    
    Returns:
        tuple: (response_text, updated_messages as BaseMessage objects)
    """
    try:
        # Convert BaseMessage objects to dict format for API
        messages_dict = convert_messages_to_dict(messages) if messages else None
        
        payload = {"message": message}
        if context:
            payload["context"] = context
        if messages_dict:
            payload["messages"] = messages_dict
        
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        response_data = result.get("response", "No response received")
        updated_messages_dict = result.get("messages", messages_dict or [])
        
        # Convert dict format back to BaseMessage objects
        updated_messages = convert_dict_to_messages(updated_messages_dict)
        
        # Handle different response types (string, dict, etc.)
        if isinstance(response_data, dict):
            # If response is a dict, try to extract content or convert to string
            if "content" in response_data:
                return response_data["content"], updated_messages
            return str(response_data), updated_messages
        elif hasattr(response_data, 'content'):
            # Handle LangChain message objects
            return response_data.content, updated_messages
        else:
            return str(response_data), updated_messages
    except requests.exceptions.RequestException as e:
        st.error(f"Error calling chat API: {str(e)}")
        return None, None

def check_api_connection() -> bool:
    """Check if API is reachable"""
    try:
        response = requests.get(f"{API_BASE_URL}", timeout=2)
        return response.status_code == 200
    except:
        return False

def render_home_page():
    """Render the main home page with stock search"""
    st.markdown('<div class="main-header">📈 KnowYourStock </div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🔍 Navigation")
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.current_page = 'home'
            st.rerun()
        if st.button("💬 Chat", use_container_width=True):
            st.session_state.current_page = 'chat'
            st.rerun()
        
        st.markdown("---")
        
        # API Connection Status
        api_status = check_api_connection()
        if api_status:
            st.success(f"✅ API Connected\n`{API_BASE_URL}`")
        else:
            st.error(f"❌ API Not Connected\n`{API_BASE_URL}`\n\nMake sure FastAPI server is running!")
        
        st.markdown("---")
        st.markdown("### 📊 Quick Info")
        st.info("Enter a stock name to get comprehensive financial information, news, and analysis.")
    
    # Main content area
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### Enter Stock Name")
        stock_input = st.text_input(
            "Stock Name",
            value=st.session_state.stock_name or "",
            placeholder="e.g., Reliance, TCS, Infosys",
            label_visibility="collapsed"
        )
        
        if st.button("🔍 Get Stock Information", type="primary", use_container_width=True):
            if stock_input.strip():
                st.session_state.stock_name = stock_input.strip()
                st.session_state.loading = True
                
                with st.spinner("Fetching stock information... This may take a moment."):
                    result = call_langgraph_api(stock_input.strip())
                
                st.session_state.loading = False
                
                if result and result.get("status") == "ok":
                    st.session_state.stock_data = result.get("result", {})
                    # Store only TickerSymbol in session state for chat context
                    st.session_state.ticker_symbol = st.session_state.stock_data.get("TickerSymbol", None)
                    st.success("Stock information retrieved successfully!")
                else:
                    st.error("Failed to retrieve stock information. Please try again.")
    
    # Display results if available
    if st.session_state.stock_data:
        display_stock_results(st.session_state.stock_data)

def display_stock_results(data: Dict[str, Any]):
    """Display stock information in tabs"""
    st.markdown("---")
    
    # Display stock name and ticker in header
    stock_name = data.get("User_stock_name", st.session_state.stock_name or "Unknown")
    ticker = data.get("TickerSymbol", "N/A")
    
    st.markdown(f"""
    <div class="stock-card">
        <h2>{stock_name}</h2>
        <p>Ticker: <strong>{ticker}</strong></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["Company Information (Screenerinfo)", "Additional Information (Stocksinfo)", " News"])
    
    # Tab 1: Screener Information
    with tab1:
        st.markdown("### Company Information from Screener.in")
        screener_data = data.get("screener_data", "")
        
        if screener_data:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown(screener_data)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No screener data available for this stock.")
    
    # Tab 2: Stock Information
    with tab2:
        st.markdown("### Additional Stock Information")
        stocks_info = data.get("stocks_info", {})
        
        if stocks_info:
            # Display ticker symbol
            if isinstance(stocks_info, dict) and "ticker_symbol" in stocks_info:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Ticker Symbol", stocks_info.get("ticker_symbol", "N/A"))
                
                # Display business model
                st.markdown("#### Business Model")
                st.markdown(f'<div class="metric-card">{stocks_info.get("business_model", "N/A")}</div>', unsafe_allow_html=True)
                
                # Display geographical revenue mix
                st.markdown("#### Geographical Revenue Mix")
                st.markdown(f'<div class="metric-card">{stocks_info.get("geographical_revenue_mix", "N/A")}</div>', unsafe_allow_html=True)
                
                # Display sectoral tailwinds/headwinds
                st.markdown("#### Sectoral Tailwinds & Headwinds")
                st.markdown(f'<div class="metric-card">{stocks_info.get("sectoral_tailwinds_headwinds", "N/A")}</div>', unsafe_allow_html=True)
                
                # Display capex expansion plans
                st.markdown("#### CAPEX & Expansion Plans")
                st.markdown(f'<div class="metric-card">{stocks_info.get("capex_expansion_plans", "N/A")}</div>', unsafe_allow_html=True)
                
                # Display management commentary
                st.markdown("#### Management Commentary & Forward Guidance")
                st.markdown(f'<div class="metric-card">{stocks_info.get("management_commentary_forward_guidance", "N/A")}</div>', unsafe_allow_html=True)
            else:
                st.json(stocks_info)
        else:
            st.info("No additional stock information available.")
    
    # Tab 3: News Articles
    with tab3:
        st.markdown("### Latest News Articles")
        news_articles = data.get("news_articles", [])
        
        if news_articles:
            for idx, article in enumerate(news_articles, 1):
                if isinstance(article, dict):
                    title = article.get("title", "No Title")
                    url = article.get("url", "#")
                    content = article.get("content", "No content available")
                    
                    st.markdown(f"""
                    <div class="news-card">
                        <div class="news-title">{idx}. {title}</div>
                        <p>{content[:300]}...</p>
                        <a href="{url}" target="_blank">Read more →</a>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.json(article)
        else:
            st.info("No news articles available for this stock.")
    
    # Navigation button to chat
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("💬 Go to Chat Page", type="primary", use_container_width=True):
            st.session_state.current_page = 'chat'
            st.rerun()

def render_chat_page():
    """Render the chat page"""
    st.markdown('<div class="main-header">💬 Finance Chat Assistant</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🔍 Navigation")
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.current_page = 'home'
            st.rerun()
        if st.button("💬 Chat", use_container_width=True, disabled=True):
            pass
        
        st.markdown("---")
        
        # API Connection Status
        api_status = check_api_connection()
        if api_status:
            st.success(f"✅ API Connected\n`{API_BASE_URL}`")
        else:
            st.error(f"❌ API Not Connected\n`{API_BASE_URL}`\n\nMake sure FastAPI server is running!")
        
        st.markdown("---")
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.chat_history = []  # Clear BaseMessage objects
            st.session_state.chat_messages = []  # Also clear LangGraph memory
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📊 Context")
        if st.session_state.stock_name and st.session_state.ticker_symbol:
            st.info(f"Current Stock: **{st.session_state.stock_name}**\n\nTicker: **{st.session_state.ticker_symbol}**")
        elif st.session_state.stock_name:
            st.info(f"Current Stock: **{st.session_state.stock_name}**")
        else:
            st.warning("No stock selected. Go to Home to search for a stock first.")
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.chat_history:
            # Convert BaseMessage to dict for display
            msg_dict = process_message_for_display(message)
            if msg_dict["role"] == "user":
                st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>You:</strong> {msg_dict["content"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message bot-message">
                    <strong>Assistant:</strong> {msg_dict["content"]}
                </div>
                """, unsafe_allow_html=True)
    
    # Chat input
    st.markdown("---")
    user_input = st.chat_input("Ask me anything about finance or the selected stock...")
    
    if user_input:
        # Add user message to history as BaseMessage
        user_msg = HumanMessage(content=user_input)
        st.session_state.chat_history.append(user_msg)
        
        # Prepare context if stock data is available
        context = None
        if st.session_state.ticker_symbol:
            context = {
                "TickerSymbol": st.session_state.ticker_symbol
            }
        
        # Get last 5 messages (2 AI + 2 user + current user) for API call
        # Get last 4 messages from history (before adding current user message)
        last_four = st.session_state.chat_history[-4:] if len(st.session_state.chat_history) > 4 else st.session_state.chat_history[:-1]
        # Add current user message
        messages_for_api = last_four + [user_msg]
        # Ensure we only send 5 messages max
        messages_for_api = messages_for_api[-5:]
        
        # Get bot response with message history for LangGraph workflow
        with st.spinner("Thinking..."):
            bot_response, updated_messages = call_chat_api(
                user_input, 
                context, 
                messages=messages_for_api
            )
        
        if bot_response:
            # Add assistant response as BaseMessage
            assistant_msg = AIMessage(content=bot_response)
            st.session_state.chat_history.append(assistant_msg)
            
            # Update chat_messages for LangGraph workflow memory (convert to dict, keep last 2 pairs)
            if updated_messages:
                updated_dicts = convert_messages_to_dict(updated_messages)
                # Keep only last 2 pairs (4 messages)
                st.session_state.chat_messages = updated_dicts[-4:] if len(updated_dicts) > 4 else updated_dicts
        else:
            # Add error message as BaseMessage
            error_msg = AIMessage(content="Sorry, I encountered an error. Please try again.")
            st.session_state.chat_history.append(error_msg)
        
        st.rerun()

# Main app routing
def main():
    if st.session_state.current_page == 'home':
        render_home_page()
    elif st.session_state.current_page == 'chat':
        render_chat_page()

if __name__ == "__main__":
    main()

