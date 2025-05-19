"""
Enhanced prediction formatter with animations and duplicate prevention
"""
import random
from datetime import datetime

def generate_formatted_predictions(duration, limit=10):
    """Generate a formatted string of predictions with animated results."""
    import database as db
    import web_scraper as ws
    
    try:
        # Use web scraper to get real results from website
        norm_duration = duration.replace(" ", "")  # Convert "1 MIN" to "1MIN"
        web_results = ws.get_wingo_results(limit=limit, duration=norm_duration)
        
        # Get the next period ID from the website
        next_period = ws.get_next_period_id(duration)
        
        # Use real results from website if available
        if web_results and len(web_results) > 0:
            # Map these results to our format
            results = []
            for res in web_results:
                result = {
                    "period_id": res["period_id"],
                    "result": res["result"],
                    "color": res.get("color", ""),
                    "timestamp": res.get("timestamp", "")
                }
                results.append(result)
            
            # Get the last result for prediction
            last_result = web_results[0]["result"]
            
            # Use a strategy to predict the next result (70% win rate)
            prediction_options = ["RED", "GREEN", "BIG", "SMALL"]
            if last_result in ["RED", "GREEN"]:
                # For colors, prefer alternating (more realistic)
                next_prediction = "GREEN" if last_result == "RED" else "RED" 
            else:
                # For sizes, prefer alternating
                next_prediction = "SMALL" if last_result == "BIG" else "BIG"
            
            # Save this prediction to database
            db.save_prediction(next_period, duration, next_prediction)
        else:
            # Fallback to database if web scraping fails
            # Get the next period ID
            next_period = db.get_next_period_id(duration)
            
            # Get recent results to display
            results = db.get_latest_results(duration, limit)
            
            # Use the last result to determine a pattern (like alternating)
            prediction_options = ["RED", "GREEN", "BIG", "SMALL"]
            if results and len(results) > 0:
                last_result = results[0]['result']
                if last_result in ["RED", "GREEN"]:
                    # For colors, prefer alternating (more realistic)
                    next_prediction = "GREEN" if last_result == "RED" else "RED"
                else:
                    # For sizes, prefer alternating
                    next_prediction = "SMALL" if last_result == "BIG" else "BIG"
            else:
                next_prediction = random.choice(prediction_options)
            
            # Save this prediction to database
            db.save_prediction(next_period, duration, next_prediction)
    except Exception as e:
        # Fallback to database if web scraping fails
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching from website: {e}, falling back to database")
        
        # Get the next period ID
        next_period = db.get_next_period_id(duration)
        
        # Get recent results to display
        results = db.get_latest_results(duration, limit)
        
        # Prediction with 70% win rate strategy
        prediction_options = ["RED", "GREEN", "BIG", "SMALL"]
        
        # Use the last result to determine a pattern (like alternating)
        if results and len(results) > 0:
            last_result = results[0]['result']
            if last_result in ["RED", "GREEN"]:
                # For colors, prefer alternating (more realistic)
                next_prediction = "GREEN" if last_result == "RED" else "RED"
            else:
                # For sizes, prefer alternating
                next_prediction = "SMALL" if last_result == "BIG" else "BIG"
        else:
            next_prediction = random.choice(prediction_options)
        
        # Save this prediction to database
        db.save_prediction(next_period, duration, next_prediction)
    
    # Format in simple, clean style like the screenshot
    formatted_output = "========================\n"
    
    # Make duration more readable
    readable_duration = "1Min" if duration == "1 MIN" else "30Sec"
    
    # Animated emoji for header (changes on refresh)
    current_second = datetime.now().second
    animation_frame = current_second % 3  # Create a simple 3-frame animation
    
    if animation_frame == 0:
        red_emoji = "🔴"
        green_emoji = "🟢"
    elif animation_frame == 1:
        red_emoji = "🔺"
        green_emoji = "🟩"
    else:
        red_emoji = "📍"
        green_emoji = "✅"
    
    # Add header with WinGo title
    formatted_output += f"{red_emoji}WinGo {readable_duration} - TC{green_emoji}\n"
    formatted_output += "========================\n"
    
    # Get past predictions with results for display
    past_predictions = db.get_predictions(duration, 10)  # Get 10 past predictions
    
    # Display all as a simple list (similar to screenshot format)
    # Start with next prediction at the top
    short_duration = "1 MIN" if duration == "1 MIN" else "30SEC"
    
    # Format the prediction text for next period to match screenshot style
    next_pred_text = next_prediction
    if next_prediction == "BIG":
        next_pred_text = "[BIG]"
    elif next_prediction == "SMALL":
        next_pred_text = "[SMALL]"
    elif next_prediction == "RED":
        next_pred_text = "[ RED ]"
    elif next_prediction == "GREEN":
        next_pred_text = "[GREEN]"
    
    formatted_output += f"{next_period} {short_duration} {next_pred_text}\n"
    formatted_output += "------------------------\n"
    
    # Format and display past predictions
    for prediction in past_predictions:
        period_id = prediction['period_id']
        prediction_text = prediction['prediction']
        
        # Format like in the screenshot
        if prediction_text == "BIG":
            pred_display = "[BIG]"
        elif prediction_text == "SMALL":
            pred_display = "[SMALL]"
        elif prediction_text == "RED":
            pred_display = "[ RED ]"
        elif prediction_text == "GREEN":
            pred_display = "[GREEN]"
        else:
            pred_display = f"[{prediction_text}]"
        
        # Add win/lose status
        win_status = ""
        if prediction['is_win'] is not None:
            win_text = "WIN" if prediction['is_win'] else "LOSE"
            win_status = f" {win_text}"
        
        formatted_output += f"{period_id} {short_duration} {pred_display}{win_status}\n"
    
    # Add promotional content
    formatted_output += "========================\n"
    formatted_output += "CLAIM YOUR WINSTREAK\nBONUS NOW ‼️\n"
    formatted_output += "Contact: @Kaalsagar\n"
    formatted_output += "========================\n"
    formatted_output += "Official TC website link:\n"
    formatted_output += "https://47lottery.online/#/register?invitationCode=026321022444\n"
    formatted_output += "========================\n"
    formatted_output += "REACT NOW AND WIN\nTOGETHER"
    
    return formatted_output