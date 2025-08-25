# Gemini 2.5 Pro + BMasterAI + Tavily + Firecrawl Integration

A comprehensive Streamlit application that demonstrates **real-time BMasterAI reasoning transparency** by showing how Gemini 2.5 Pro thinks through complex tasks like finding AI podcast influencers using Tavily API for web searches and Firecrawl API for email extraction. Watch every step of the AI's thinking process unfold in real-time!

## 🌟 Key Features

### 🎙️ **AI Podcast Influencer Search with Email Extraction**
- **Two-Stage Process**: Tavily finds podcast websites → Firecrawl extracts contact information
- **Real-Time Reasoning**: Watch Gemini plan, search, and analyze step-by-step
- **Verified Contacts**: Get actual email addresses from podcast websites
- **Complete Transparency**: See every decision and API call with full context

### 🧠 **Real-Time BMasterAI Reasoning Display**
- **Live Thinking Steps**: See Gemini's reasoning process as it happens
- **Process Flow Visualization**: Track progress through each stage
- **Interactive Updates**: UI updates dynamically with each reasoning step
- **Organized Log Structure**: Logs automatically organized in folders by session

### 🌐 **Multi-API Integration**
- **Tavily API**: Advanced web search for finding podcast websites
- **Firecrawl API**: Intelligent email extraction from web pages
- **Gemini 2.5 Pro**: Natural language processing and reasoning
- **BMasterAI**: Complete reasoning transparency and logging

## 🎯 Primary Use Case: AI Podcast Influencer Research

This app excels at helping you find AI podcast influencers who might be willing to have guests. The **real-time process** shows:

1. **🧠 Planning Phase**: Watch Gemini formulate search strategies
2. **🌐 Tavily Search**: See targeted queries find relevant podcast websites
3. **🔍 Firecrawl Extraction**: Observe email addresses being extracted from sites
4. **📊 Analysis Phase**: Watch results being structured and validated
5. **✅ Final Results**: Get verified influencer profiles with contact information

## 📦 Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

#### Option A: Using .env file (Recommended)

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file and add your API keys:
   ```
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   TAVILY_API_KEY=your_actual_tavily_api_key_here
   FIRECRAWL_API_KEY=your_actual_firecrawl_api_key_here
   ```

3. Get your API keys:
   - **Gemini**: [Google AI Studio](https://makersuite.google.com/app/apikey) (Required)
   - **Tavily**: [Tavily API](https://tavily.com/) (Optional but recommended)
   - **Firecrawl**: [Firecrawl API](https://firecrawl.dev/) (Optional but recommended)

#### Option B: Direct input in the app

If you don't set up a .env file, you can enter your API keys directly in the Streamlit app's sidebar.

### 3. Run the Application

```bash
streamlit run streamlit_app.py
```

The app will open in your default web browser at `http://localhost:8501`

## 🚀 Usage Guide

### Real-Time AI Podcast Influencer Search

1. **Configure APIs**: Set up your Gemini (required), Tavily, and Firecrawl API keys
2. **Set Parameters**: Choose target number of influencers (1-20) and focus area
3. **Start Search**: Click "🚀 Start AI Podcast Influencer Search"
4. **Watch Real-Time Process**:
   - 🧠 **Planning**: See Gemini formulate the search strategy
   - 💭 **Thinking**: Watch reasoning steps appear in real-time
   - 🌐 **Tavily Search**: Observe targeted web searches for podcast sites
   - 🔍 **Firecrawl Extract**: See email addresses being extracted from websites
   - 📊 **Analysis**: Watch Gemini structure and validate the results
   - ✅ **Complete**: Get final influencer profiles with verified contacts

### API Modes

- **🟢 Live Mode**: With all API keys → Real searches and email extraction
- **🟡 Hybrid Mode**: With some API keys → Partial live functionality + demos
- **🔵 Demo Mode**: Without API keys → Complete reasoning process demonstration

## 🧠 Real-Time BMasterAI Integration Benefits

### 🎭 **Complete Process Transparency**
- See every step of Gemini's reasoning process as it happens
- Track all API calls with full context and rationale
- Understand decision points and alternatives considered
- Watch the AI adapt its strategy based on results

### 📊 **Organized Real-Time Logging**
```
logs/
├── bmasterai.jsonl                              # Main application logs
├── reasoning/
│   ├── gemini_tavily_firecrawl_reasoning.jsonl # Real-time reasoning logs
│   └── sessions/
│       ├── session_001_podcast_search/
│       │   ├── metadata.json                    # Search parameters & timing
│       │   ├── steps.jsonl                     # Step-by-step reasoning
│       │   ├── tavily_queries.json             # Actual API queries used
│       │   ├── firecrawl_extractions.json      # Email extraction results
│       │   ├── gemini_analysis.json            # Gemini's final analysis
│       │   └── summary.md                      # Human-readable summary
│       └── ...
└── metrics/
    ├── performance.jsonl                        # API response times
    ├── reasoning_patterns.json                 # Decision patterns
    └── search_effectiveness.json               # Search success rates
```

### 🎯 **Interactive UI Features**
- **Progress Indicators**: Visual progress through each process stage
- **Real-Time Updates**: UI updates dynamically with each reasoning step
- **Expandable Results**: Click to view detailed search and extraction results
- **Error Handling**: Clear error messages with reasoning context
- **Export Functionality**: Download complete reasoning logs

## 🔧 Technical Architecture

### Core Components

**GeminiReasoningAgent**: Enhanced reasoning agent that:
- Manages BMasterAI reasoning sessions with real-time callbacks
- Interfaces with Gemini 2.5 Pro API for natural language processing
- Executes Tavily API searches with strategic query formulation
- Performs Firecrawl API extractions for email discovery
- Provides comprehensive real-time logging and UI updates

**Real-Time UI System**: Streamlit interface that:
- Displays live reasoning steps as they occur
- Shows process flow with visual progress indicators
- Updates dynamically with search results and extractions
- Provides interactive exploration of results and logs

**Multi-API Integration**: Seamless coordination of:
- **Gemini 2.5 Pro**: For reasoning, analysis, and natural language processing
- **Tavily API**: For comprehensive web searches and content discovery
- **Firecrawl API**: For intelligent email extraction from web pages
- **BMasterAI**: For structured reasoning logs and transparency

## 💡 Real-Time Value Demonstration

### ❌ **Without Real-Time BMasterAI Logging**
- Black box AI operations with no visibility
- Unknown search strategies and decision processes
- No insight into API usage patterns or effectiveness
- Difficult to debug failures or optimize performance
- Poor reproducibility and learning opportunities

### ✅ **With Real-Time BMasterAI Logging**
- **Complete Process Transparency**: See every reasoning step as it happens
- **Strategic Visibility**: Watch search strategy formulation and adaptation
- **API Call Tracking**: Monitor all external API calls with full context
- **Decision Analysis**: Understand every choice and alternative considered
- **Performance Insights**: Track timing, effectiveness, and optimization opportunities
- **Interactive Learning**: Explore the AI's reasoning process in real-time

## 🎯 Real-World Applications

1. **🎙️ Podcast Guest Booking**: Find relevant podcast hosts with verified contact information
2. **🔍 Influencer Research**: Identify thought leaders in specific domains with extraction
3. **📊 Content Strategy**: Understand successful search and analysis patterns
4. **⚡ API Optimization**: Monitor and optimize multi-API usage in real-time
5. **🐛 AI Debugging**: Trace reasoning paths for complex multi-step tasks
6. **📚 AI Education**: Learn from watching AI reasoning processes unfold

## 🌟 Example Real-Time Process Flow

When searching for AI podcast influencers, watch the complete process:

1. **🧠 Strategic Planning**
   - Gemini formulates comprehensive search approach
   - Considers target count, focus area, and API capabilities
   - Plans two-stage process: discovery → extraction

2. **🌐 Tavily Web Search**
   - Executes targeted queries for AI podcast websites
   - Shows each search query with rationale
   - Displays results with relevance assessment

3. **🔍 Firecrawl Email Extraction**
   - Crawls discovered websites for contact information
   - Extracts email addresses and contact methods
   - Shows extraction success/failure for each site

4. **📊 Gemini Analysis**
   - Combines search and extraction results
   - Structures influencer profiles with confidence scores
   - Validates contact information quality

5. **✅ Final Results**
   - Presents verified influencer profiles
   - Shows contact confidence scores
   - Provides actionable next steps

## 🛠️ Troubleshooting

### Common Issues

1. **"BMasterAI library not found"**
   - Run `pip install bmasterai`
   - Ensure you're using the correct Python environment

2. **"No API key found"**
   - Check your `.env` file is in the same directory
   - Verify API keys are correctly set (GEMINI_API_KEY required)
   - For full functionality, set TAVILY_API_KEY and FIRECRAWL_API_KEY

3. **"Real-time updates not showing"**
   - Ensure BMasterAI is properly initialized
   - Check browser console for JavaScript errors
   - Try refreshing the page

4. **"Search results empty"**
   - Verify your Tavily API key is valid and has quota
   - Check your internet connection
   - Try different search terms or focus areas

5. **"Email extraction failing"**
   - Verify your Firecrawl API key is valid
   - Check API quota and rate limits
   - Some websites may block automated extraction

## 📊 Performance Considerations

- **API Costs**: Monitor usage through real-time BMasterAI logs
- **Rate Limits**: Tavily and Firecrawl APIs have rate limits - timing shown in logs
- **Response Times**: Track API performance in real-time reasoning logs
- **Log Storage**: Logs accumulate over time - consider periodic cleanup
- **UI Performance**: Real-time updates may affect browser performance with large datasets

## 🔒 Security & Privacy

- API keys are handled securely through environment variables
- No sensitive data is logged in plain text
- All searches are performed through official APIs
- Local log storage ensures data privacy
- Firecrawl extractions respect robots.txt and rate limits

## 🤝 Contributing

This project demonstrates advanced BMasterAI integration patterns with real-time UI updates. Feel free to:
- Submit issues for bugs or feature requests
- Propose improvements to reasoning strategies or UI components
- Share successful search patterns and optimization techniques
- Contribute additional use cases or API integrations

## 📄 License

This project is provided as-is for educational and demonstration purposes.

---

🧠 **Powered by Gemini 2.5 Pro + BMasterAI + Tavily + Firecrawl | Built with Streamlit**

*Real-time reasoning transparency for complex AI tasks with multi-API integrations and live email extraction.*

