# Streamlit Frontend - Finance Tweet Assistant

A beautiful and modern Streamlit frontend for the Finance Tweet Assistant application.

## Features

- 📊 **Stock Information Search**: Enter a stock name to get comprehensive financial information
- 📈 **Three Information Tabs**:
  - Company Information (Screenerinfo): Displays data from Screener.in
  - Additional Information (Stocksinfo): Shows detailed stock metrics and analysis
  - News: Lists recent news articles related to the stock
- 💬 **Interactive Chat**: Chat with the AI assistant about finance and stocks
- 🎨 **Attractive UI**: Modern, responsive design with beautiful styling
- 💾 **Session State Management**: Proper state management for navigation and data persistence

## Setup

1. **Configure API URL**:
   - Create a `.streamlit/secrets.toml` file (see `secrets.toml.example`)
   - Set `API_BASE_URL` to your FastAPI server URL (default: `http://localhost:8000`)

2. **Install Dependencies**:
   ```bash
   pip install -r ../requirements.txt
   ```

## Running the Application

1. **Start the FastAPI Server**:
   ```bash
   # From the project root
   python FastAPI_main.py
   ```
   The API will run on `http://localhost:8000` by default.

2. **Start the Streamlit App**:
   ```bash
   # From the project root or Streamlit_Frontend directory
   streamlit run Streamlit_Frontend/app.py
   ```
   The app will open in your browser at `http://localhost:8501`

## Usage

1. **Home Page**:
   - Enter a stock name (e.g., "Reliance", "TCS", "Infosys")
   - Click "Get Stock Information"
   - View results in the three tabs

2. **Chat Page**:
   - Click "Chat" in the sidebar or use the "Go to Chat Page" button
   - Ask questions about finance or the selected stock
   - The chat history is maintained during your session

## Session State Management

The application properly manages:
- Current page (Home/Chat)
- Stock search results
- Selected stock name
- Chat history
- Loading states

## Customization

- **Theme**: Edit `.streamlit/config.toml` to customize colors and appearance
- **API URL**: Set in `.streamlit/secrets.toml` or as environment variable
- **Styling**: Modify CSS in `app.py` for custom styling

