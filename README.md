# AI Car Finder App

A Streamlit application that helps users find their perfect car on Facebook Marketplace using natural language processing powered by Google's Gemini AI.

## Features

- **Natural Language Input**: Describe what you're looking for in a car using everyday language
- **AI-Powered Analysis**: Gemini AI interprets your preferences and converts them to structured search parameters
- **Automated Marketplace Search**: Searches Facebook Marketplace for cars matching your preferences
- **Visual Results**: Displays car listings with images, prices, and key details
- **Modern UI**: Professional dark theme with responsive design

## How It Works

1. Enter your car preferences in natural language (e.g., "I need a reliable family car with good fuel economy under $15,000")
2. The app uses Gemini AI to analyze your preferences and extract key parameters
3. It then searches Facebook Marketplace for matching listings
4. The top results are displayed with images and details
5. You can click through to view the original listings on Facebook Marketplace

## Technologies Used

- **Streamlit**: For the web application interface
- **Google Gemini AI**: For natural language processing
- **Selenium/Splinter**: For web scraping and browser automation
- **Python**: Core programming language
- **CSS**: Custom styling for a professional look and feel

## Setup Instructions

### Prerequisites

- Python 3.8+
- Chrome browser
- Google Gemini API key

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/car-finder-app.git
   cd car-finder-app
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your API key:
   - Create a `.streamlit/secrets.toml` file with:
     ```toml
     GEMINI_API_KEY = "your_api_key_here"
     ```
   - Or set an environment variable:
     ```bash
     export GOOGLE_API_KEY="your_api_key_here"
     ```

4. Run the app:
   ```bash
   streamlit run car_finder_app.py
   ```

## Deployment

This app is configured for deployment on Render. See the `render.yaml` file for configuration details.

## License

MIT

## Acknowledgements

- Facebook Marketplace for providing the car listings data
- Google Gemini for the AI capabilities
- Streamlit for the web app framework
