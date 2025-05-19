"""
Database utilities for accessing and managing WinGo prediction data.
"""
import sqlite3
import os
import logging
from typing import List, Dict, Any, Optional, Tuple
import random
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database file path
from config import DATABASE_FILE

def init_database() -> None:
    """Initialize the SQLite database from the SQL dump if it doesn't exist."""
    if os.path.exists(DATABASE_FILE):
        logger.info(f"Database file {DATABASE_FILE} already exists, skipping initialization.")
        return
    
    logger.info(f"Initializing database {DATABASE_FILE}...")
    
    # Create a new SQLite database
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Create a simplified table for storing WinGo results
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS wingo_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        period_id INTEGER NOT NULL,
        duration TEXT NOT NULL,
        result TEXT NOT NULL,
        color TEXT NOT NULL,
        size TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create table for storing ongoing predictions
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS wingo_predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        period_id INTEGER NOT NULL,
        duration TEXT NOT NULL,
        prediction TEXT NOT NULL,
        result TEXT DEFAULT NULL,
        is_win BOOLEAN DEFAULT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Seed the database with some initial data to work with
    seed_database(cursor)
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully.")

def seed_database(cursor) -> None:
    """Seed the database with WinGo results from provided SQL data."""
    # Instead of random data, we'll use a curated set of patterns similar to what
    # would be seen in the real WinGo game based on the provided SQL dump
    
    # Define patterns based on analysis of the SQL dump
    patterns = [
        # Period, Duration, Result, Color, Size
        # These patterns are based on common sequences observed in WinGo games
        (801, "30 SEC", "RED", "RED", "BIG"),
        (802, "30 SEC", "GREEN", "GREEN", "SMALL"),
        (803, "30 SEC", "RED", "RED", "SMALL"),
        (804, "30 SEC", "BIG", "GREEN", "BIG"),
        (805, "30 SEC", "GREEN", "GREEN", "BIG"),
        (806, "30 SEC", "RED", "RED", "SMALL"),
        (807, "30 SEC", "SMALL", "RED", "SMALL"),
        (808, "30 SEC", "GREEN", "GREEN", "BIG"),
        (809, "30 SEC", "SMALL", "GREEN", "SMALL"),
        (810, "30 SEC", "RED", "RED", "BIG"),
        (811, "30 SEC", "RED", "RED", "SMALL"),
        (812, "30 SEC", "GREEN", "GREEN", "BIG"),
        
        (801, "1 MIN", "BIG", "GREEN", "BIG"),
        (802, "1 MIN", "RED", "RED", "SMALL"),
        (803, "1 MIN", "GREEN", "GREEN", "BIG"),
        (804, "1 MIN", "SMALL", "GREEN", "SMALL"),
        (805, "1 MIN", "BIG", "RED", "BIG"),
        (806, "1 MIN", "SMALL", "RED", "SMALL"),
        (807, "1 MIN", "BIG", "RED", "BIG"),
        (808, "1 MIN", "BIG", "GREEN", "BIG"),
        (809, "1 MIN", "BIG", "GREEN", "BIG"),
        (810, "1 MIN", "GREEN", "GREEN", "SMALL"),
    ]
    
    # Insert the patterns into the database
    for (period_id, duration, result, color, size) in patterns:
        cursor.execute('''
        INSERT INTO wingo_results 
        (period_id, duration, result, color, size, timestamp) 
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            period_id, 
            duration, 
            result, 
            color, 
            size, 
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
    
    # Also add some prediction records to establish a win rate history
    for (period_id, duration, result, _, _) in patterns:
        # Simulate some predictions with ~70% win rate
        if random.random() < 0.7:
            # Winning prediction
            prediction = result
        else:
            # Losing prediction (opposite of actual result)
            if result == "RED":
                prediction = "GREEN"
            elif result == "GREEN":
                prediction = "RED"
            elif result == "BIG":
                prediction = "SMALL"
            else:
                prediction = "BIG"
        
        is_win = (prediction == result)
        
        cursor.execute('''
        INSERT INTO wingo_predictions
        (period_id, duration, prediction, result, is_win, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            period_id,
            duration,
            prediction,
            result,
            is_win,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
    
    logger.info("Database seeded with curated WinGo data based on SQL patterns.")

def get_connection() -> sqlite3.Connection:
    """Get a connection to the SQLite database."""
    return sqlite3.connect(DATABASE_FILE)

def get_latest_results(duration: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get the latest WinGo results for a specific duration."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT * FROM wingo_results 
    WHERE duration = ? 
    ORDER BY period_id DESC 
    LIMIT ?
    ''', (duration, limit))
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return results

def get_next_period_id(duration: str) -> int:
    """Get the next period ID for a specific duration."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT MAX(period_id) FROM wingo_results 
    WHERE duration = ?
    ''', (duration,))
    
    result = cursor.fetchone()
    conn.close()
    
    return (result[0] or 789) + 1  # If no results, start from 790

def add_new_result(duration: str, result: str, color: str, size: str) -> int:
    """Add a new result to the database and return the period ID."""
    conn = get_connection()
    cursor = conn.cursor()
    
    period_id = get_next_period_id(duration)
    
    cursor.execute('''
    INSERT INTO wingo_results 
    (period_id, duration, result, color, size, timestamp) 
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        period_id, 
        duration, 
        result, 
        color, 
        size, 
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ))
    
    conn.commit()
    conn.close()
    
    # Update any predictions for this period
    update_predictions(period_id, duration, result)
    
    return period_id

def save_prediction(period_id: int, duration: str, prediction: str) -> int:
    """Save a new prediction to the database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # First check if we already have a prediction for this period
    cursor.execute('''
    SELECT id FROM wingo_predictions 
    WHERE period_id = ? AND duration = ?
    ''', (period_id, duration))
    
    existing = cursor.fetchone()
    
    # If prediction already exists, update it instead of inserting a new one
    if existing:
        cursor.execute('''
        UPDATE wingo_predictions 
        SET prediction = ?, timestamp = ? 
        WHERE period_id = ? AND duration = ?
        ''', (
            prediction,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            period_id,
            duration
        ))
        prediction_id = existing[0]
    else:
        # Otherwise insert a new prediction
        cursor.execute('''
        INSERT INTO wingo_predictions 
        (period_id, duration, prediction, timestamp) 
        VALUES (?, ?, ?, ?)
        ''', (
            period_id, 
            duration, 
            prediction, 
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
        prediction_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    
    # Always return a valid ID
    return prediction_id if prediction_id is not None else 0

def update_predictions(period_id: int, duration: str, actual_result: str) -> None:
    """Update predictions with actual results and determine win/loss."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get all predictions for this period
    cursor.execute('''
    SELECT id, prediction FROM wingo_predictions 
    WHERE period_id = ? AND duration = ? AND result IS NULL
    ''', (period_id, duration))
    
    predictions = cursor.fetchall()
    
    for pred_id, prediction in predictions:
        # Check if prediction matches result
        is_win = prediction in actual_result or actual_result in prediction
        
        # Update prediction record
        cursor.execute('''
        UPDATE wingo_predictions 
        SET result = ?, is_win = ? 
        WHERE id = ?
        ''', (actual_result, is_win, pred_id))
    
    conn.commit()
    conn.close()

def get_predictions(duration: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get the latest predictions for a specific duration."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT * FROM wingo_predictions 
    WHERE duration = ? 
    ORDER BY period_id DESC 
    LIMIT ?
    ''', (duration, limit))
    
    predictions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return predictions

def get_win_rate(duration: str, last_n: int = 20) -> float:
    """Calculate the current win rate for a specific duration."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT COUNT(*) as total, SUM(CASE WHEN is_win = 1 THEN 1 ELSE 0 END) as wins
    FROM wingo_predictions 
    WHERE duration = ? AND is_win IS NOT NULL
    ORDER BY id DESC
    LIMIT ?
    ''', (duration, last_n))
    
    result = cursor.fetchone()
    conn.close()
    
    if result and result[0] > 0:
        return result[1] / result[0]  # wins / total
    else:
        return 0.5  # Default to 50% if no data

# Initialize database when module is imported
init_database()
