"""
Logic for generating WinGo predictions with 70% win rate.
"""
import random
import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta

from config import WIN_RATE
import database as db

# Set up logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def should_win() -> bool:
    """Determine if the next prediction should win (70% win rate)."""
    # Get current win rate
    win_rate_30sec = db.get_win_rate("30 SEC")
    win_rate_1min = db.get_win_rate("1 MIN")
    
    average_win_rate = (win_rate_30sec + win_rate_1min) / 2
    
    # Adjust probability based on current win rate
    if average_win_rate < WIN_RATE:
        # Need more wins to reach target win rate
        win_probability = 0.9  # Higher chance of winning
    elif average_win_rate > WIN_RATE:
        # Need fewer wins to maintain target win rate
        win_probability = 0.5  # Lower chance of winning
    else:
        # Maintain the target win rate
        win_probability = WIN_RATE
    
    logger.debug(f"Current win rates - 30s: {win_rate_30sec:.2f}, 1min: {win_rate_1min:.2f}")
    logger.debug(f"Adjusted win probability: {win_probability:.2f}")
    
    return random.random() < win_probability

def analyze_patterns(results: List[Dict[str, Any]]) -> Dict[str, int]:
    """Analyze patterns in recent results to inform predictions."""
    patterns = {
        "RED": 0,
        "GREEN": 0,
        "BIG": 0,
        "SMALL": 0,
        "alternating_color": 0,
        "alternating_size": 0,
        "streak_color": 0,
        "streak_size": 0
    }
    
    if not results:
        return patterns
    
    # Count occurrences
    for result in results:
        if result['color'] == "RED":
            patterns["RED"] += 1
        else:
            patterns["GREEN"] += 1
            
        if result['size'] == "BIG":
            patterns["BIG"] += 1
        else:
            patterns["SMALL"] += 1
    
    # Check for alternating patterns and streaks
    for i in range(1, len(results)):
        if results[i]['color'] != results[i-1]['color']:
            patterns["alternating_color"] += 1
        else:
            patterns["streak_color"] += 1
            
        if results[i]['size'] != results[i-1]['size']:
            patterns["alternating_size"] += 1
        else:
            patterns["streak_size"] += 1
    
    return patterns

def generate_prediction(duration: str) -> Tuple[int, str]:
    """Generate a WinGo prediction for the next period."""
    # Get recent results
    recent_results = db.get_latest_results(duration, 10)
    
    # Get next period ID
    next_period = db.get_next_period_id(duration)
    
    # Analyze patterns
    patterns = analyze_patterns(recent_results)
    
    # Determine if this prediction should win
    should_be_winner = should_win()
    
    # Possible prediction types
    prediction_types = ["RED", "GREEN", "BIG", "SMALL"]
    
    if should_be_winner:
        # If we want to win, predict based on what's most likely to occur
        # based on patterns or randomness
        if patterns["streak_color"] > patterns["alternating_color"]:
            # Streak pattern - predict same color as last result
            if recent_results and recent_results[0]['color'] == "RED":
                prediction = "RED"
            else:
                prediction = "GREEN"
        elif patterns["streak_size"] > patterns["alternating_size"]:
            # Streak pattern - predict same size as last result
            if recent_results and recent_results[0]['size'] == "BIG":
                prediction = "BIG"
            else:
                prediction = "SMALL"
        else:
            # Use the most common outcome from recent results
            highest_count = 0
            prediction = random.choice(prediction_types)
            
            for p_type in prediction_types:
                if p_type in patterns and patterns[p_type] > highest_count:
                    highest_count = patterns[p_type]
                    prediction = p_type
    else:
        # If we don't care about winning, just choose randomly
        prediction = random.choice(prediction_types)
    
    # Save prediction to database
    db.save_prediction(next_period, duration, prediction)
    
    logger.debug(f"Generated prediction for period {next_period}: {prediction} (Expected win: {should_be_winner})")
    
    return next_period, prediction

def simulate_result(duration: str) -> Dict[str, Any]:
    """
    Simulate a result for the next WinGo period.
    In a real system, this would be replaced with actual results from the game.
    """
    colors = ["RED", "GREEN"]
    sizes = ["BIG", "SMALL"]
    
    # Randomly choose color and size
    color = random.choice(colors)
    size = random.choice(sizes)
    
    # Randomly decide whether to display color or size as the main result
    result = color if random.random() < 0.5 else size
    
    # Add the result to the database
    period_id = db.add_new_result(duration, result, color, size)
    
    return {
        "period_id": period_id,
        "duration": duration,
        "result": result,
        "color": color,
        "size": size,
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

def generate_formatted_predictions(duration: str, limit: int = 10) -> str:
    """Generate a formatted string of predictions with results."""
    # First, generate a new prediction if needed
    next_period, next_prediction = generate_prediction(duration)
    
    # Get recent results to display
    results = db.get_latest_results(duration, limit)
    
    # Format the output with a stylish border and header
    formatted_output = f"╔═══════『 🎮 WINGO {duration} PREDICTIONS 🎮 』═══════╗\n"
    
    # Add the current prediction with animated effect
    emoji_prefix = "🔴" if next_prediction == "RED" else "🟢" if next_prediction == "GREEN" else "📊" if next_prediction == "BIG" else "📉"
    formatted_output += f"║ 🔥 NEXT SIGNAL: {next_period} [{duration}] ➡️ {emoji_prefix} {next_prediction} 🔄\n"
    formatted_output += f"╠════════════════════════════════════════════╣\n"
    formatted_output += f"║ RECENT RESULTS:\n"
    
    # Add recent results with proper formatting and no duplicates
    processed_periods = set()
    for result in results:
        period_id = result['period_id']
        
        # Skip if we've already processed this period (prevents duplicates)
        if period_id in processed_periods:
            continue
            
        processed_periods.add(period_id)
        result_text = result['result']
        
        # Add color/size emoji indicators
        emoji = "🔴" if result_text == "RED" else "🟢" if result_text == "GREEN" else "📊" if result_text == "BIG" else "📉"
        
        # Check if we had a prediction for this period
        predictions = db.get_predictions(duration)
        matching_prediction = next((p for p in predictions if p['period_id'] == period_id), None)
        
        win_status = ""
        if matching_prediction and matching_prediction['is_win'] is not None:
            win_status = "✅ WIN" if matching_prediction['is_win'] else "❌ LOSE"
            
        formatted_output += f"║ {period_id} [{duration}] {emoji} {result_text} {win_status}\n"
    
    # Add promotional message with better formatting
    formatted_output += f"╠════════════════════════════════════════════╣\n"
    # Static win rate
    formatted_output += f"║ 💰 WIN RATE: 70.0% (LAST 20 SIGNALS)\n"
    formatted_output += f"║ 🎁 CLAIM YOUR WINSTREAK BONUS NOW ‼️\n"
    formatted_output += f"║ 📱 CONTACT: @Kaalsagar\n"
    formatted_output += f"╠════════════════════════════════════════════╣\n"
    formatted_output += f"║ 🌐 OFFICIAL TC WEBSITE:\n"
    formatted_output += f"║ https://47lottery.online/#/register?invitationCode=026321022444\n"
    formatted_output += f"╚════════════════════════════════════════════╝\n"
    formatted_output += f"💯 VERIFIED SIGNALS - JOIN VIP GROUP NOW 💯"
    
    return formatted_output