#!/usr/bin/env python3
"""
Car Finder App

A Streamlit application that:
1. Takes user preferences for a car in natural language
2. Uses Google's Gemini AI to interpret these preferences into structured data
3. Searches Facebook Marketplace for matching cars
4. Displays the top 5 results

Requirements:
- streamlit
- google-generativeai
- pandas
- Facebook_Marketplace_Scraper.py (must be in the same directory)
"""

import os
import re
import json
import streamlit as st
import pandas as pd
import google.generativeai as genai
from Facebook_Marketplace_Scraper import FacebookMarketplaceScraper
from dotenv import load_dotenv

# Define the Gemini model name
GEMINI_MODEL = "gemini-2.5-pro-exp-03-25"

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env'))

# Function to load and apply CSS from external file
def load_css():
    css_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "style.css")
    with open(css_file, "r") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# Configure the page
st.set_page_config(
    page_title="AI Car Finder",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apply CSS
load_css()

# Configure Gemini API
def configure_gemini():
    """Configure the Gemini API with the API key."""
    # Try to get API key from different sources in order of preference
    api_key = (
        st.secrets.get("GEMINI_API_KEY", None) or  # Streamlit secrets
        os.environ.get("GOOGLE_API_KEY", None) or  # Environment variable
        os.environ.get("GEMINI_API_KEY", None) or  # Alternative environment variable
        ""
    )
    
    if not api_key:
        st.error("⚠️ No Gemini API key found. Please add it to your secrets or environment variables.")
        st.stop()
    
    # Don't show success message in sidebar
    genai.configure(api_key=api_key)
    return genai

# Function to analyze user preferences with Gemini
def analyze_preferences(user_input):
    """
    Use Gemini to analyze user preferences and return structured data.
    
    Args:
        user_input (str): User's car preferences in natural language
        
    Returns:
        dict: Structured car preferences
    """
    genai_client = configure_gemini()
    
    # Create the prompt for Gemini
    prompt = f"""
    Based on the following user preferences for a car, extract key information and provide recommendations.
    
    User input: "{user_input}"
    
    First, analyze what type of car would best suit their needs and preferences.
    
    Then, extract the following specific information in JSON format:
    {{
        "recommendation": "A detailed explanation of what type of car would suit them and why",
        "make": "Recommended car make (e.g., Honda, Toyota)",
        "model": "Recommended car model (e.g., Civic, Corolla)",
        "min_price": integer value in dollars (e.g., 5000),
        "max_price": integer value in dollars (e.g., 15000),
        "min_year": integer value (e.g., 2015),
        "max_year": integer value (e.g., 2022)
    }}
    
    If the user doesn't specify any of these fields, use reasonable defaults based on their other preferences.
    Only return the JSON object, nothing else.
    """
    
    # Generate response from Gemini
    model = genai_client.GenerativeModel(GEMINI_MODEL)
    response = model.generate_content(prompt)
    
    # Extract and parse JSON from the response
    try:
        # Try to extract JSON from the response
        json_match = re.search(r'({.*})', response.text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            return json.loads(json_str)
        else:
            # If no JSON pattern found, try to parse the entire response
            return json.loads(response.text)
    except Exception as e:
        st.error(f"Error parsing Gemini response: {e}")
        st.write("Raw response:", response.text)
        return None

# Function to search Facebook Marketplace
def search_marketplace(preferences):
    """
    Search Facebook Marketplace based on user preferences.
    
    Args:
        preferences (dict): Structured car preferences
        
    Returns:
        list: Top 5 car listings
    """
    try:
        # Initialize the scraper
        scraper = FacebookMarketplaceScraper(headless=True, debug=False)
        
        # Build the search URL
        location = "toronto"  # Default location, can be made configurable
        make = preferences.get('make', '')
        model = preferences.get('model', '')
        min_price = preferences.get('min_price', None)
        max_price = preferences.get('max_price', None)
        min_year = preferences.get('min_year', None)
        max_year = preferences.get('max_year', None)
        
        # Create the search URL
        url = scraper.build_search_url(
            location=location,
            min_price=min_price,
            max_price=max_price,
            min_year=min_year,
            max_year=max_year,
            make=make,
            model=model
        )
        
        # Scrape the listings
        listings = scraper.scrape_listings(url, scroll_count=2, scroll_delay=2)
        
        # Close the browser
        scraper.close_browser()
        
        # Return the top 5 listings
        return listings[:5] if listings else []
    
    except Exception as e:
        st.error(f"Error searching Facebook Marketplace: {e}")
        import traceback
        st.write(traceback.format_exc())
        return []

# Function to display car listings
def display_listings(listings, preferences):
    """
    Display car listings in a nice format.
    
    Args:
        listings (list): List of car listings
        preferences (dict): User preferences for context
    """
    if not listings:
        st.warning("No matching cars found. Try adjusting your preferences.")
        return
    
    st.subheader(f"Top {len(listings)} Matches")
    
    # Create columns for the listings
    cols = st.columns(len(listings))
    
    for i, listing in enumerate(cols):
        with listing:
            car = listings[i]
            
            # Create a card container with custom CSS
            with st.container():
                st.markdown('<div class="car-card">', unsafe_allow_html=True)
                
                # Display the car image
                if "ImageURL" in car and car["ImageURL"]:
                    st.image(car["ImageURL"], use_column_width=True)
                
                # Create a card-like display
                st.markdown(f"### {car['Year']} {car['Make']} {car['Model']}")
                st.markdown(f'<p class="price">${car["Price"]:,.2f}</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="detail"><strong>Mileage:</strong> {car["Mileage"]:,} km</p>', unsafe_allow_html=True)
                
                # Add a link to the original listing
                st.markdown(f"[View on Facebook Marketplace]({car['URL']})")
                
                st.markdown('</div>', unsafe_allow_html=True)

# Main app function
def main():
    # App title and description
    st.title("🚗 AI Car Finder")
    st.markdown("""
    <p style="font-size: 1.2rem; margin-bottom: 2rem;">
    Tell me what you're looking for in a car, and I'll help you find the perfect match on Facebook Marketplace!
    </p>
    """, unsafe_allow_html=True)
    
    # User input
    user_input = st.text_area(
        "Describe what you're looking for in a car:",
        height=150,
        placeholder="Example: I need a reliable family car with good fuel economy. My budget is around $15,000. I prefer Japanese brands and need something not older than 2015."
    )
    
    # Process button
    if st.button("Find My Perfect Car"):
        if not user_input:
            st.warning("Please describe what you're looking for in a car.")
            return
        
        # Show processing message with progress bar
        with st.spinner("Analyzing your preferences..."):
            progress_bar = st.progress(0)
            
            # Analyze user preferences with Gemini
            progress_bar.progress(25)
            preferences = analyze_preferences(user_input)
            
            if not preferences:
                st.error("Could not analyze your preferences. Please try again with more details.")
                return
            
            progress_bar.progress(50)
        
        # Display the AI's recommendation
        st.subheader("AI Recommendation")
        st.markdown(f'<div style="background-color: #1e1e1e; padding: 1rem; border-radius: 10px; border: 1px solid #333333;">{preferences.get("recommendation", "No recommendation available.")}</div>', unsafe_allow_html=True)
        
        # Display the structured preferences
        st.subheader("Your Preferences")
        pref_cols = st.columns(3)
        with pref_cols[0]:
            st.markdown(f'<div style="background-color: #1e1e1e; padding: 1rem; border-radius: 10px; border: 1px solid #333333;"><strong>Make:</strong> {preferences.get("make", "Any")}<br><strong>Model:</strong> {preferences.get("model", "Any")}</div>', unsafe_allow_html=True)
        with pref_cols[1]:
            st.markdown(f'<div style="background-color: #1e1e1e; padding: 1rem; border-radius: 10px; border: 1px solid #333333;"><strong>Price Range:</strong> ${preferences.get("min_price", 0):,} - ${preferences.get("max_price", 100000):,}</div>', unsafe_allow_html=True)
        with pref_cols[2]:
            st.markdown(f'<div style="background-color: #1e1e1e; padding: 1rem; border-radius: 10px; border: 1px solid #333333;"><strong>Year Range:</strong> {preferences.get("min_year", "Any")} - {preferences.get("max_year", "Any")}</div>', unsafe_allow_html=True)
        
        # Search Facebook Marketplace
        with st.spinner("Searching Facebook Marketplace..."):
            progress_bar.progress(75)
            listings = search_marketplace(preferences)
            progress_bar.progress(100)
        
        # Display the results
        display_listings(listings, preferences)
        
        # Option to save results
        if listings:
            df = pd.DataFrame(listings)
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download Results as CSV",
                data=csv,
                file_name="car_search_results.csv",
                mime="text/csv"
            )
    
    # Add footer
    st.markdown('<div class="footer"> 2025 AI Car Finder | Powered by Gemini AI & Facebook Marketplace</div>', unsafe_allow_html=True)

# Run the app
if __name__ == "__main__":
    main()
