"""
Web scraper to get real WinGo results from the 47lottery website
"""
import logging
import requests
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# The base URL of the lottery site
LOTTERY_BASE_URL = "https://47lottery.online"

# API endpoint for getting game results
API_URL = "https://wapi.m2.app/api/game/recordsAsFast"

# Default parameters for API call
DEFAULT_PARAMS = {
    "id": 3,  # Game ID for WinGo
    "count": 10,  # Number of records to return
    "language": "en",  # Language setting
}

# Headers to simulate a browser request
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://47lottery.online/",
    "Origin": "https://47lottery.online",
}

def get_wingo_results(limit: int = 10, duration: str = "1MIN") -> List[Dict[str, Any]]:
    """
    Get real WinGo results from the 47lottery website.
    
    Args:
        limit: Number of results to return
        duration: The game duration ("1MIN" or "30SEC")
    
    Returns:
        List of result dictionaries with period_id, result, color, etc.
    """
    try:
        # Set parameters for API call
        params = DEFAULT_PARAMS.copy()
        params["count"] = limit
        
        # Determine the right game ID based on duration
        game_id = 3  # Default to 1MIN
        if duration == "30SEC":
            game_id = 4  # Use game ID 4 for 30SEC games
        params["id"] = game_id
        
        # Make the API call
        response = requests.get(API_URL, params=params, headers=HEADERS, timeout=10)
        
        # Check if the response is valid
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and "data" in data:
                results = []
                
                # Process each record
                for record in data["data"]:
                    result_text = ""
                    color = ""
                    
                    # Determine result based on color and size
                    if record.get("colorType") == 1:
                        color = "RED"
                        result_text = "RED"
                    elif record.get("colorType") == 2:
                        color = "GREEN" 
                        result_text = "GREEN"
                    
                    # Override with size if specified
                    if record.get("sizeType") == 1:
                        result_text = "BIG"
                    elif record.get("sizeType") == 2:
                        result_text = "SMALL"
                    
                    # Create result entry
                    result = {
                        "period_id": record.get("issueNumber", 0),
                        "result": result_text,
                        "color": color,
                        "size": "BIG" if record.get("sizeType") == 1 else "SMALL" if record.get("sizeType") == 2 else "",
                        "timestamp": datetime.fromtimestamp(record.get("createdTime", 0)/1000).strftime('%Y-%m-%d %H:%M:%S')
                    }
                    results.append(result)
                
                return results
        
        # Log the error if the response is not successful
        logger.error(f"Error fetching results: {response.status_code} - {response.text}")
        return []
    
    except Exception as e:
        logger.error(f"Exception while fetching results: {e}")
        return []

def get_next_period_id(duration: str) -> int:
    """
    Get the next period ID for the given duration.
    
    Args:
        duration: The game duration ("1MIN" or "30SEC" or "1 MIN" or "30 SEC")
    
    Returns:
        The next period ID as integer
    """
    try:
        # Normalize duration format
        norm_duration = duration.replace(" ", "")
        
        # Get the latest result
        results = get_wingo_results(limit=1, duration=norm_duration)
        
        if results and len(results) > 0:
            latest_period = results[0]["period_id"]
            # Convert to integer and add 1 for next period
            return int(latest_period) + 1
        
        # Fallback if no results found
        return 1000
    
    except Exception as e:
        logger.error(f"Exception getting next period ID: {e}")
        return 1000

# Test function
if __name__ == "__main__":
    print("Testing 1MIN results:")
    results = get_wingo_results(duration="1MIN")
    for result in results:
        print(f"Period {result['period_id']}: {result['result']}")
    
    print("\nTesting 30SEC results:")
    results = get_wingo_results(duration="30SEC")
    for result in results:
        print(f"Period {result['period_id']}: {result['result']}")
    
    print("\nNext 1MIN period ID:", get_next_period_id("1MIN"))
    print("Next 30SEC period ID:", get_next_period_id("30SEC"))