import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import uuid
from utils.data_manager import (
    initialize_session_state,
    save_user_data,
    load_user_data,
)
from utils.task_classifier import classify_task, suggest_time_slot
from assets.icons import get_icon

# Page configuration
st.set_page_config(
    page_title="AI Planner",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
initialize_session_state()

# App title and description
def main():
    # Display welcome message for first-time users
    if st.session_state.get("first_time", True):
        display_welcome()
    else:
        display_dashboard()

def display_welcome():
    st.title("Welcome to Your AI-Powered Schedule Planner")
    st.write("""
    This comprehensive planner helps you manage tasks, track goals, and build healthy habits using AI to optimize your schedule.
    
    Let's start by understanding your preferences to personalize your experience.
    """)
    
    # Onboarding form
    with st.form(key="onboarding_form"):
        st.header("Tell us about yourself")
        
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Your Name", placeholder="Enter your name")
            
            st.subheader("Productivity Preferences")
            productivity_peak = st.selectbox(
                "When are you most productive?",
                options=["Morning", "Afternoon", "Evening", "Night"]
            )
            
            work_routine = st.select_slider(
                "Work Routine Preference",
                options=["Strict Schedule", "Flexible with Structure", "Completely Flexible"]
            )
            
            break_frequency = st.select_slider(
                "Break Frequency",
                options=["Frequent Short Breaks", "Few Longer Breaks", "Minimal Breaks"]
            )
            
        with col2:
            st.subheader("Goal & Habit Preferences")
            
            goal_timeframe = st.selectbox(
                "Goal Planning Preference",
                options=["Daily Goals", "Weekly Goals", "Monthly Goals", "Quarterly Goals"]
            )
            
            habit_formation = st.select_slider(
                "Habit Formation Approach",
                options=["Start Small", "Moderate Changes", "Challenge Myself"]
            )
            
            health_priority = st.multiselect(
                "Health Priorities",
                options=["Sleep", "Exercise", "Nutrition", "Mindfulness", "Water Intake"],
                default=["Sleep", "Exercise"]
            )
        
        st.info("Your answers will help our AI tailor scheduling recommendations to your preferences.")
        submit = st.form_submit_button("Set Up My Planner")
        
        if submit:
            if not name:
                st.error("Please enter your name to continue.")
            else:
                # Save user preferences
                st.session_state["user_profile"] = {
                    "name": name,
                    "productivity_peak": productivity_peak,
                    "work_routine": work_routine,
                    "break_frequency": break_frequency,
                    "goal_timeframe": goal_timeframe,
                    "habit_formation": habit_formation,
                    "health_priority": health_priority,
                    "theme": "dark",
                    "onboarded_at": datetime.now().isoformat(),
                }
                
                # Create default categories
                st.session_state["categories"] = [
                    {"id": str(uuid.uuid4()), "name": "Work", "color": "#FF5733"},
                    {"id": str(uuid.uuid4()), "name": "Personal", "color": "#33FF57"},
                    {"id": str(uuid.uuid4()), "name": "Health", "color": "#3357FF"},
                    {"id": str(uuid.uuid4()), "name": "Learning", "color": "#F033FF"},
                ]
                
                # Create default empty lists
                st.session_state["tasks"] = []
                st.session_state["goals"] = []
                st.session_state["habits"] = []
                st.session_state["calendar_events"] = []
                
                # Mark as not first time
                st.session_state["first_time"] = False
                
                # Save data
                save_user_data()
                
                st.success("Your planner is all set up! Redirecting to your dashboard...")
                st.rerun()

def display_dashboard():
    # Header with greeting and date
    col1, col2 = st.columns([3, 1])
    
    with col1:
        user_name = st.session_state.get("user_profile", {}).get("name", "there")
        st.title(f"Hello, {user_name}! 👋")
        
    with col2:
        today = datetime.now()
        st.write(f"**{today.strftime('%A, %B %d, %Y')}**")
    
    # Main dashboard content
    st.subheader("Your Day at a Glance")
    
    # Show today's schedule
    today_events = [event for event in st.session_state.get("calendar_events", []) 
                   if datetime.fromisoformat(event["start_time"]).date() == today.date()]
    today_tasks = [task for task in st.session_state.get("tasks", []) 
                  if task.get("due_date") and datetime.fromisoformat(task["due_date"]).date() == today.date()]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Today's Schedule")
        if today_events:
            for event in sorted(today_events, key=lambda x: x["start_time"]):
                start = datetime.fromisoformat(event["start_time"])
                category = next((c for c in st.session_state.get("categories", []) if c["id"] == event["category_id"]), None)
                category_color = category["color"] if category else "#808080"
                
                st.markdown(f"""
                <div style='padding: 10px; border-left: 5px solid {category_color}; margin-bottom: 10px;'>
                    <div style='color: #888;'>{start.strftime('%I:%M %p')}</div>
                    <div style='font-weight: bold;'>{event["title"]}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No events scheduled for today.")
            
    with col2:
        st.markdown("### Today's Tasks")
        if today_tasks:
            for task in sorted(today_tasks, key=lambda x: x.get("importance", 0) * x.get("urgency", 0), reverse=True):
                category = next((c for c in st.session_state.get("categories", []) if c["id"] == task["category_id"]), None)
                category_color = category["color"] if category else "#808080"
                
                st.markdown(f"""
                <div style='padding: 10px; border-left: 5px solid {category_color}; margin-bottom: 10px;'>
                    <div style='font-weight: bold;'>{task["title"]}</div>
                    <div style='color: #888;'>Priority: {calculate_priority_label(task)}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No tasks due today.")
    
    # Quick actions and stats
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### Quick Add")
        with st.form(key="quick_add_form"):
            task_title = st.text_input("Add a task", placeholder="Enter task title")
            add_task = st.form_submit_button("Add Task")
            
            if add_task and task_title:
                new_task = {
                    "id": str(uuid.uuid4()),
                    "title": task_title,
                    "description": "",
                    "category_id": st.session_state["categories"][0]["id"], # Default to first category
                    "created_at": datetime.now().isoformat(),
                    "due_date": None,
                    "completed": False,
                    "importance": 3,  # Medium importance by default
                    "urgency": 3,     # Medium urgency by default
                }
                
                # Use AI to classify task
                category_suggestion = classify_task(task_title, st.session_state["categories"])
                if category_suggestion:
                    new_task["category_id"] = category_suggestion
                
                st.session_state["tasks"].append(new_task)
                save_user_data()
                st.success(f"Added task: {task_title}")
                st.rerun()
    
    with col2:
        st.markdown("### Progress")
        
        # Calculate task completion rate
        all_tasks = st.session_state.get("tasks", [])
        completed_tasks = sum(1 for task in all_tasks if task.get("completed", False))
        total_tasks = len(all_tasks)
        
        if total_tasks > 0:
            completion_rate = completed_tasks / total_tasks
            st.progress(completion_rate)
            st.write(f"Task Completion: {int(completion_rate * 100)}% ({completed_tasks}/{total_tasks})")
        else:
            st.progress(0.0)
            st.write("No tasks added yet")
            
        # Show active goals
        active_goals = [goal for goal in st.session_state.get("goals", []) 
                       if not goal.get("completed", False)]
        st.write(f"Active Goals: {len(active_goals)}")
    
    with col3:
        st.markdown("### Habit Streaks")
        
        habits = st.session_state.get("habits", [])
        if habits:
            for habit in sorted(habits, key=lambda x: x.get("current_streak", 0), reverse=True)[:3]:
                st.markdown(f"""
                <div style='margin-bottom: 5px;'>
                    {habit["title"]} - {habit.get("current_streak", 0)} days
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No habits tracked yet. Add some in the Health & Habits section.")
    
    # Suggested focus
    st.markdown("---")
    st.subheader("AI Suggestions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Suggested Focus")
        
        # Get incomplete tasks
        incomplete_tasks = [task for task in st.session_state.get("tasks", []) 
                           if not task.get("completed", False)]
        
        if incomplete_tasks:
            # Sort by importance * urgency
            prioritized_tasks = sorted(
                incomplete_tasks, 
                key=lambda x: (x.get("importance", 1) * x.get("urgency", 1)), 
                reverse=True
            )
            
            # Take top 3 tasks
            for task in prioritized_tasks[:3]:
                category = next((c for c in st.session_state.get("categories", []) if c["id"] == task["category_id"]), None)
                category_color = category["color"] if category else "#808080"
                
                st.markdown(f"""
                <div style='padding: 10px; border-left: 5px solid {category_color}; margin-bottom: 10px;'>
                    <div style='font-weight: bold;'>{task["title"]}</div>
                    <div style='color: #888;'>Priority: {calculate_priority_label(task)}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No tasks to focus on. Add some tasks to get AI suggestions.")
    
    with col2:
        st.markdown("### Optimal Schedule")
        
        # Get user's productivity peak
        productivity_peak = st.session_state.get("user_profile", {}).get("productivity_peak", "Morning")
        
        if productivity_peak == "Morning":
            st.write("Based on your preferences, schedule high-priority tasks in the morning when your energy is highest.")
        elif productivity_peak == "Afternoon":
            st.write("Based on your preferences, schedule high-priority tasks in the afternoon when your energy is highest.")
        elif productivity_peak == "Evening":
            st.write("Based on your preferences, schedule high-priority tasks in the evening when your energy is highest.")
        else:
            st.write("Based on your preferences, schedule high-priority tasks at night when your energy is highest.")
        
        # Get break frequency
        break_frequency = st.session_state.get("user_profile", {}).get("break_frequency", "Frequent Short Breaks")
        
        if break_frequency == "Frequent Short Breaks":
            st.write("Suggestion: Use the Pomodoro technique - 25 minutes of work followed by 5-minute breaks.")
        elif break_frequency == "Few Longer Breaks":
            st.write("Suggestion: Work in 50-90 minute blocks followed by 15-20 minute breaks for optimal productivity.")
        else:
            st.write("Suggestion: Set aside 2-3 hours of focused work time with minimal interruptions.")

def calculate_priority_label(task):
    importance = task.get("importance", 1)
    urgency = task.get("urgency", 1)
    
    score = importance * urgency
    
    if score >= 20:
        return "Critical"
    elif score >= 12:
        return "High"
    elif score >= 6:
        return "Medium"
    else:
        return "Low"

if __name__ == "__main__":
    main()
