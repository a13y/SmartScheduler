import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from datetime import datetime, timedelta
import streamlit as st
import random

# Simple keywords for basic classification
CATEGORY_KEYWORDS = {
    "work": ["meeting", "project", "report", "presentation", "client", "boss", "deadline", "email", "call", "office"],
    "personal": ["home", "family", "friend", "shopping", "clean", "appointment", "personal", "party", "visit", "social"],
    "health": ["exercise", "workout", "gym", "run", "jog", "swim", "doctor", "dentist", "meal", "diet", "sleep", "rest", "meditate"],
    "learning": ["study", "learn", "read", "book", "course", "class", "lecture", "tutorial", "homework", "assignment"]
}

def train_classifier(tasks):
    """Train a simple classifier on existing tasks if enough data is available"""
    if len(tasks) < 10:  # Not enough data for reliable training
        return None, None
    
    # Extract task titles and categories
    X = [task["title"] for task in tasks]
    y = [task["category_id"] for task in tasks]
    
    # Create a TF-IDF vectorizer
    vectorizer = TfidfVectorizer(max_features=100)
    X_vectorized = vectorizer.fit_transform(X)
    
    # Train a Naive Bayes classifier
    classifier = MultinomialNB()
    classifier.fit(X_vectorized, y)
    
    return vectorizer, classifier

def classify_task(task_title, categories, existing_tasks=None):
    """Classify a task into a category based on its title"""
    if not categories:
        return None
    
    # Check if there's enough existing data to train a classifier
    if existing_tasks and len(existing_tasks) >= 10:
        vectorizer, classifier = train_classifier(existing_tasks)
        
        if vectorizer and classifier:
            # Vectorize the new task title
            X_new = vectorizer.transform([task_title])
            
            # Predict category
            predicted_category_id = classifier.predict(X_new)[0]
            
            # Return the predicted category ID
            return predicted_category_id
    
    # Fall back to keyword-based classification
    task_title_lower = task_title.lower()
    
    # Map category names to their IDs
    category_id_map = {category["name"].lower(): category["id"] for category in categories}
    
    # Count keyword matches for each category
    category_scores = {cat_name: 0 for cat_name in category_id_map.keys()}
    
    for category_name, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in task_title_lower:
                # Find the closest category in our categories
                best_match = find_best_category_match(category_name, category_id_map.keys())
                if best_match:
                    category_scores[best_match] += 1
    
    # Get the category with the highest score
    if any(category_scores.values()):
        best_category = max(category_scores.items(), key=lambda x: x[1])[0]
        return category_id_map[best_category]
    
    # If no matching keywords, return the first category as default
    return categories[0]["id"]

def find_best_category_match(keyword_category, available_categories):
    """Find the closest matching category from available categories"""
    # Direct match
    if keyword_category in available_categories:
        return keyword_category
    
    # Try to find a partial match
    for category in available_categories:
        if keyword_category in category or category in keyword_category:
            return category
    
    # Return the first category as default if no match
    return next(iter(available_categories)) if available_categories else None

def estimate_task_parameters(task_title, task_description=""):
    """Estimate task importance and urgency based on title and description"""
    text = f"{task_title} {task_description}".lower()
    
    # Keywords indicating high importance
    importance_keywords = {
        "high": ["important", "critical", "crucial", "essential", "key", "major", "significant", "vital", "priority"],
        "medium": ["necessary", "needed", "required", "should", "useful"],
        "low": ["optional", "minor", "trivial", "if time", "sometime", "eventually", "when possible"]
    }
    
    # Keywords indicating high urgency
    urgency_keywords = {
        "high": ["urgent", "asap", "immediately", "now", "today", "tonight", "deadline", "due", "overdue", "soon", "quickly", "fast"],
        "medium": ["this week", "next few days", "tomorrow", "upcoming"],
        "low": ["when convenient", "sometime", "later", "eventually", "no rush", "take time", "next month"]
    }
    
    # Calculate importance score
    importance = 3  # Default medium importance
    for level, keywords in importance_keywords.items():
        for keyword in keywords:
            if keyword in text:
                if level == "high":
                    importance = 5
                elif level == "medium":
                    importance = 3
                else:
                    importance = 1
                break
        if importance != 3:  # If we found a match, break
            break
    
    # Calculate urgency score
    urgency = 3  # Default medium urgency
    for level, keywords in urgency_keywords.items():
        for keyword in keywords:
            if keyword in text:
                if level == "high":
                    urgency = 5
                elif level == "medium":
                    urgency = 3
                else:
                    urgency = 1
                break
        if urgency != 3:  # If we found a match, break
            break
    
    # Check for date patterns to estimate urgency
    date_patterns = [
        r'due (?:on|by)? (\d{1,2}(?:st|nd|rd|th)? (?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec))',
        r'due (?:on|by)? (\d{1,2}/\d{1,2}(?:/\d{2,4})?)',
        r'by (?:this|next) (monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
        r'(?:this|next) (week|month)'
    ]
    
    for pattern in date_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            # If we found a date reference, increase urgency
            urgency = max(urgency, 4)
            break
    
    return importance, urgency

def suggest_time_slot(task, user_profile, existing_events=None):
    """Suggest an optimal time slot for a task based on user preferences and existing schedule"""
    if not user_profile:
        # Default to suggesting a time during standard work hours
        start_hour = 9
        task_duration = 60  # minutes
        return start_hour, task_duration
    
    # Get user's productivity peak preference
    productivity_peak = user_profile.get("productivity_peak", "Morning")
    
    # Map productivity peak to hours
    peak_hours = {
        "Morning": range(8, 12),
        "Afternoon": range(12, 17),
        "Evening": range(17, 22),
        "Night": range(20, 24)
    }
    
    # Get the hours for the user's peak
    preferred_hours = list(peak_hours.get(productivity_peak, range(9, 17)))
    
    # Check for existing events to avoid conflicts
    if existing_events:
        # Convert to datetime objects for easier comparison
        event_periods = []
        for event in existing_events:
            try:
                start = datetime.fromisoformat(event["start_time"])
                end = datetime.fromisoformat(event["end_time"])
                event_periods.append((start, end))
            except (ValueError, TypeError):
                # Skip events with invalid datetime format
                continue
        
        # Start with tomorrow
        suggested_date = datetime.now().date() + timedelta(days=1)
        
        # Find an available slot during preferred hours
        for _ in range(7):  # Look up to a week ahead
            for hour in preferred_hours:
                potential_start = datetime.combine(suggested_date, datetime.min.time()) + timedelta(hours=hour)
                potential_end = potential_start + timedelta(minutes=60)
                
                # Check if this slot conflicts with any existing events
                if not any(start <= potential_start < end or start < potential_end <= end 
                          for start, end in event_periods):
                    return potential_start, 60
            
            # If no slot found today, try the next day
            suggested_date += timedelta(days=1)
        
        # If we couldn't find an ideal slot, just return the earliest available preferred hour tomorrow
        return (datetime.combine(datetime.now().date() + timedelta(days=1), 
                               datetime.min.time()) + timedelta(hours=preferred_hours[0])), 60
    
    # If no existing events or couldn't find a slot, suggest default time in preferred hours
    current_date = datetime.now().date()
    preferred_hour = preferred_hours[0] if preferred_hours else 9
    
    # If it's already past that hour today, suggest tomorrow
    if datetime.now().hour >= preferred_hour:
        current_date += timedelta(days=1)
    
    suggested_time = datetime.combine(current_date, datetime.min.time()) + timedelta(hours=preferred_hour)
    
    # Estimate task duration based on complexity
    task_duration = estimate_task_duration(task)
    
    return suggested_time, task_duration

def estimate_task_duration(task):
    """Estimate task duration based on its properties"""
    # Default duration in minutes
    duration = 60
    
    # Adjust based on importance and urgency if available
    importance = task.get("importance", 3)
    urgency = task.get("urgency", 3)
    
    if importance >= 4 or urgency >= 4:
        # More important/urgent tasks might need more time
        duration = 90
    elif importance <= 2 and urgency <= 2:
        # Less important/urgent tasks might be quicker
        duration = 30
    
    # Adjust based on title length as a proxy for complexity
    title_length = len(task.get("title", ""))
    if title_length > 50:
        duration += 30
    elif title_length < 20:
        duration -= 15
    
    # Adjust based on description length if available
    description_length = len(task.get("description", ""))
    if description_length > 200:
        duration += 30
    
    # Ensure minimum duration of 15 minutes
    return max(15, duration)

def get_next_tasks(tasks, top_n=3):
    """Get the next n tasks to focus on based on priority"""
    if not tasks:
        return []
    
    # Filter incomplete tasks
    incomplete_tasks = [task for task in tasks if not task.get("completed", False)]
    
    # Calculate priority score for each task
    for task in incomplete_tasks:
        importance = task.get("importance", 3)
        urgency = task.get("urgency", 3)
        task["priority_score"] = importance * urgency
    
    # Sort by priority score
    sorted_tasks = sorted(incomplete_tasks, key=lambda x: x.get("priority_score", 0), reverse=True)
    
    # Return top N tasks
    return sorted_tasks[:top_n]
