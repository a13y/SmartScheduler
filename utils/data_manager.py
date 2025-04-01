import streamlit as st
import json
import os
from datetime import datetime, timedelta
import uuid

# Data files
DATA_DIR = "data"
USER_DATA_FILE = os.path.join(DATA_DIR, "user_data.json")

def ensure_data_dir():
    """Ensure the data directory exists"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def initialize_session_state():
    """Initialize the session state with default values if not already set"""
    if "initialized" not in st.session_state:
        # Load user data if exists
        user_data = load_user_data()
        
        if user_data:
            # Set session state from loaded data
            for key, value in user_data.items():
                st.session_state[key] = value
            st.session_state["first_time"] = False
        else:
            # Default session state for new users
            st.session_state["first_time"] = True
            st.session_state["user_profile"] = {}
            st.session_state["categories"] = []
            st.session_state["tasks"] = []
            st.session_state["goals"] = []
            st.session_state["habits"] = []
            st.session_state["calendar_events"] = []
            st.session_state["points"] = 0
            st.session_state["rewards"] = []
            st.session_state["unlocked_rewards"] = []
        
        st.session_state["initialized"] = True

def save_user_data():
    """Save user data to file"""
    ensure_data_dir()
    
    user_data = {
        "user_profile": st.session_state.get("user_profile", {}),
        "categories": st.session_state.get("categories", []),
        "tasks": st.session_state.get("tasks", []),
        "goals": st.session_state.get("goals", []),
        "habits": st.session_state.get("habits", []),
        "calendar_events": st.session_state.get("calendar_events", []),
        "points": st.session_state.get("points", 0),
        "rewards": st.session_state.get("rewards", []),
        "unlocked_rewards": st.session_state.get("unlocked_rewards", [])
    }
    
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(user_data, f, indent=2)

def load_user_data():
    """Load user data from file"""
    if not os.path.exists(USER_DATA_FILE):
        return None
    
    try:
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return None

def add_task(title, description="", category_id=None, due_date=None, importance=3, urgency=3):
    """Add a new task to the session state"""
    if not category_id and st.session_state.get("categories"):
        category_id = st.session_state["categories"][0]["id"]
        
    new_task = {
        "id": str(uuid.uuid4()),
        "title": title,
        "description": description,
        "category_id": category_id,
        "created_at": datetime.now().isoformat(),
        "due_date": due_date.isoformat() if due_date else None,
        "completed": False,
        "importance": importance,
        "urgency": urgency
    }
    
    if "tasks" not in st.session_state:
        st.session_state["tasks"] = []
        
    st.session_state["tasks"].append(new_task)
    save_user_data()
    return new_task

def update_task(task_id, **kwargs):
    """Update a task with new values"""
    if "tasks" not in st.session_state:
        return False
    
    for i, task in enumerate(st.session_state["tasks"]):
        if task["id"] == task_id:
            for key, value in kwargs.items():
                task[key] = value
            st.session_state["tasks"][i] = task
            save_user_data()
            return True
    
    return False

def delete_task(task_id):
    """Delete a task by ID"""
    if "tasks" not in st.session_state:
        return False
    
    initial_count = len(st.session_state["tasks"])
    st.session_state["tasks"] = [task for task in st.session_state["tasks"] if task["id"] != task_id]
    
    if initial_count != len(st.session_state["tasks"]):
        save_user_data()
        return True
    
    return False

def complete_task(task_id):
    """Mark a task as completed and award points"""
    result = update_task(task_id, completed=True, completed_at=datetime.now().isoformat())
    
    if result:
        # Award points for task completion
        award_points(10)
        return True
    
    return False

def add_goal(title, description="", target_date=None, category_id=None, milestones=None):
    """Add a new goal to the session state"""
    if not category_id and st.session_state.get("categories"):
        category_id = st.session_state["categories"][0]["id"]
        
    new_goal = {
        "id": str(uuid.uuid4()),
        "title": title,
        "description": description,
        "category_id": category_id,
        "created_at": datetime.now().isoformat(),
        "target_date": target_date.isoformat() if target_date else None,
        "completed": False,
        "milestones": milestones or [],
        "progress": 0
    }
    
    if "goals" not in st.session_state:
        st.session_state["goals"] = []
        
    st.session_state["goals"].append(new_goal)
    save_user_data()
    return new_goal

def update_goal(goal_id, **kwargs):
    """Update a goal with new values"""
    if "goals" not in st.session_state:
        return False
    
    for i, goal in enumerate(st.session_state["goals"]):
        if goal["id"] == goal_id:
            for key, value in kwargs.items():
                goal[key] = value
            st.session_state["goals"][i] = goal
            save_user_data()
            return True
    
    return False

def delete_goal(goal_id):
    """Delete a goal by ID"""
    if "goals" not in st.session_state:
        return False
    
    initial_count = len(st.session_state["goals"])
    st.session_state["goals"] = [goal for goal in st.session_state["goals"] if goal["id"] != goal_id]
    
    if initial_count != len(st.session_state["goals"]):
        save_user_data()
        return True
    
    return False

def complete_goal(goal_id):
    """Mark a goal as completed and award points"""
    result = update_goal(goal_id, completed=True, completed_at=datetime.now().isoformat())
    
    if result:
        # Award points for goal completion
        award_points(50)
        return True
    
    return False

def add_habit(title, description="", frequency="daily", category_id=None):
    """Add a new habit to the session state"""
    if not category_id and st.session_state.get("categories"):
        category_id = st.session_state["categories"][0]["id"]
        
    new_habit = {
        "id": str(uuid.uuid4()),
        "title": title,
        "description": description,
        "category_id": category_id,
        "created_at": datetime.now().isoformat(),
        "frequency": frequency,
        "current_streak": 0,
        "best_streak": 0,
        "check_ins": []
    }
    
    if "habits" not in st.session_state:
        st.session_state["habits"] = []
        
    st.session_state["habits"].append(new_habit)
    save_user_data()
    return new_habit

def check_in_habit(habit_id, date=None):
    """Record a check-in for a habit and update streaks"""
    if "habits" not in st.session_state:
        return False
    
    check_in_date = date or datetime.now().date()
    check_in_str = check_in_date.isoformat()
    
    for i, habit in enumerate(st.session_state["habits"]):
        if habit["id"] == habit_id:
            # Check if already checked in for this date
            if check_in_str in habit.get("check_ins", []):
                return False
            
            # Add check-in
            if "check_ins" not in habit:
                habit["check_ins"] = []
                
            habit["check_ins"].append(check_in_str)
            
            # Update streak
            sorted_check_ins = sorted([datetime.fromisoformat(d) for d in habit["check_ins"]])
            
            # Calculate current streak
            current_streak = 1
            best_streak = max(habit.get("best_streak", 0), 1)
            
            # Check backwards from most recent date
            most_recent = sorted_check_ins[-1].date()
            
            if most_recent == check_in_date:  # If today's check-in is the most recent
                for i in range(1, len(sorted_check_ins)):
                    prev_date = sorted_check_ins[-i-1].date()
                    curr_date = sorted_check_ins[-i].date()
                    
                    # Check if dates are consecutive
                    if (curr_date - prev_date).days == 1:
                        current_streak += 1
                    else:
                        break
            
            # Update habit with new streak information
            habit["current_streak"] = current_streak
            habit["best_streak"] = max(best_streak, current_streak)
            
            # Save changes
            st.session_state["habits"][i] = habit
            save_user_data()
            
            # Award points for habit check-in
            award_points(5)
            
            return True
    
    return False

def delete_habit(habit_id):
    """Delete a habit by ID"""
    if "habits" not in st.session_state:
        return False
    
    initial_count = len(st.session_state["habits"])
    st.session_state["habits"] = [habit for habit in st.session_state["habits"] if habit["id"] != habit_id]
    
    if initial_count != len(st.session_state["habits"]):
        save_user_data()
        return True
    
    return False

def add_calendar_event(title, start_time, end_time, category_id=None, description="", location=""):
    """Add a new calendar event to the session state"""
    if not category_id and st.session_state.get("categories"):
        category_id = st.session_state["categories"][0]["id"]
        
    new_event = {
        "id": str(uuid.uuid4()),
        "title": title,
        "description": description,
        "location": location,
        "category_id": category_id,
        "start_time": start_time.isoformat() if isinstance(start_time, datetime) else start_time,
        "end_time": end_time.isoformat() if isinstance(end_time, datetime) else end_time,
        "created_at": datetime.now().isoformat()
    }
    
    if "calendar_events" not in st.session_state:
        st.session_state["calendar_events"] = []
        
    st.session_state["calendar_events"].append(new_event)
    save_user_data()
    return new_event

def update_calendar_event(event_id, **kwargs):
    """Update a calendar event with new values"""
    if "calendar_events" not in st.session_state:
        return False
    
    for i, event in enumerate(st.session_state["calendar_events"]):
        if event["id"] == event_id:
            for key, value in kwargs.items():
                event[key] = value
            st.session_state["calendar_events"][i] = event
            save_user_data()
            return True
    
    return False

def delete_calendar_event(event_id):
    """Delete a calendar event by ID"""
    if "calendar_events" not in st.session_state:
        return False
    
    initial_count = len(st.session_state["calendar_events"])
    st.session_state["calendar_events"] = [event for event in st.session_state["calendar_events"] if event["id"] != event_id]
    
    if initial_count != len(st.session_state["calendar_events"]):
        save_user_data()
        return True
    
    return False

def add_category(name, color="#808080"):
    """Add a new category to the session state"""
    new_category = {
        "id": str(uuid.uuid4()),
        "name": name,
        "color": color,
        "created_at": datetime.now().isoformat()
    }
    
    if "categories" not in st.session_state:
        st.session_state["categories"] = []
        
    st.session_state["categories"].append(new_category)
    save_user_data()
    return new_category

def update_category(category_id, **kwargs):
    """Update a category with new values"""
    if "categories" not in st.session_state:
        return False
    
    for i, category in enumerate(st.session_state["categories"]):
        if category["id"] == category_id:
            for key, value in kwargs.items():
                category[key] = value
            st.session_state["categories"][i] = category
            save_user_data()
            return True
    
    return False

def delete_category(category_id):
    """Delete a category by ID"""
    if "categories" not in st.session_state:
        return False
    
    initial_count = len(st.session_state["categories"])
    st.session_state["categories"] = [category for category in st.session_state["categories"] if category["id"] != category_id]
    
    if initial_count != len(st.session_state["categories"]):
        save_user_data()
        return True
    
    return False

def award_points(points):
    """Award points to the user"""
    if "points" not in st.session_state:
        st.session_state["points"] = 0
        
    st.session_state["points"] += points
    save_user_data()
    
    # Check if any rewards should be unlocked
    check_for_unlockable_rewards()
    
    return st.session_state["points"]

def add_reward(title, description="", point_cost=100, reward_type="template"):
    """Add a new reward to the session state"""
    new_reward = {
        "id": str(uuid.uuid4()),
        "title": title,
        "description": description,
        "point_cost": point_cost,
        "reward_type": reward_type,
        "created_at": datetime.now().isoformat()
    }
    
    if "rewards" not in st.session_state:
        st.session_state["rewards"] = []
        
    st.session_state["rewards"].append(new_reward)
    save_user_data()
    return new_reward

def check_for_unlockable_rewards():
    """Check if any rewards can be unlocked with current points"""
    if "rewards" not in st.session_state or "points" not in st.session_state:
        return
    
    points = st.session_state["points"]
    
    if "unlocked_rewards" not in st.session_state:
        st.session_state["unlocked_rewards"] = []
    
    # Get IDs of already unlocked rewards
    unlocked_ids = [r["id"] for r in st.session_state["unlocked_rewards"]]
    
    # Check for rewards that can be unlocked
    for reward in st.session_state["rewards"]:
        if reward["id"] not in unlocked_ids and reward["point_cost"] <= points:
            # Unlock this reward
            unlocked_reward = reward.copy()
            unlocked_reward["unlocked_at"] = datetime.now().isoformat()
            
            st.session_state["unlocked_rewards"].append(unlocked_reward)
            save_user_data()

def redeem_reward(reward_id):
    """Redeem a reward with points"""
    if "rewards" not in st.session_state or "points" not in st.session_state:
        return False
    
    # Find the reward
    reward = next((r for r in st.session_state["rewards"] if r["id"] == reward_id), None)
    
    if not reward:
        return False
    
    # Check if enough points
    if st.session_state["points"] < reward["point_cost"]:
        return False
    
    # Deduct points
    st.session_state["points"] -= reward["point_cost"]
    
    # Add to unlocked rewards if not already there
    if "unlocked_rewards" not in st.session_state:
        st.session_state["unlocked_rewards"] = []
    
    # Check if already unlocked
    if not any(r["id"] == reward_id for r in st.session_state["unlocked_rewards"]):
        unlocked_reward = reward.copy()
        unlocked_reward["unlocked_at"] = datetime.now().isoformat()
        unlocked_reward["redeemed_at"] = datetime.now().isoformat()
        
        st.session_state["unlocked_rewards"].append(unlocked_reward)
    else:
        # Mark as redeemed
        for i, r in enumerate(st.session_state["unlocked_rewards"]):
            if r["id"] == reward_id:
                r["redeemed_at"] = datetime.now().isoformat()
                st.session_state["unlocked_rewards"][i] = r
                break
    
    save_user_data()
    return True
