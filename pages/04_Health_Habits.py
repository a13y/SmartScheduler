import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import uuid
from utils.data_manager import (
    initialize_session_state,
    save_user_data,
    add_habit,
    check_in_habit,
    delete_habit
)
from utils.visualization import habit_streak_chart, habit_heatmap
from assets.icons import get_icon

# Initialize session state
initialize_session_state()

# Page configuration
st.set_page_config(
    page_title="Health & Habits | AI Planner",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Health & Habits Tracker")
st.write("Track your daily habits and monitor your health metrics to build a healthier lifestyle.")

# Sidebar for quick check-ins
with st.sidebar:
    st.header("Today's Check-ins")
    
    # Get today's date
    today = datetime.now().date().isoformat()
    
    # Get habits
    habits = st.session_state.get("habits", [])
    
    if habits:
        for habit in habits:
            # Check if already checked in for today
            is_checked = today in habit.get("check_ins", [])
            
            col1, col2 = st.columns([0.7, 0.3])
            
            with col1:
                st.write(habit["title"])
            
            with col2:
                if st.button(
                    "✓" if is_checked else "○", 
                    key=f"quick_checkin_{habit['id']}",
                    help="Click to mark as completed"
                ):
                    # Toggle check-in status
                    if not is_checked:
                        check_in_habit(habit["id"])
                        st.success(f"Checked in for {habit['title']}!")
                    st.rerun()
        
        # Show streaks
        st.write("---")
        st.subheader("Current Streaks")
        
        for habit in sorted(habits, key=lambda x: x.get("current_streak", 0), reverse=True):
            st.markdown(f"""
            <div style='display: flex; justify-content: space-between;'>
                <span>{habit['title']}</span>
                <span><b>{habit.get('current_streak', 0)}</b> days</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No habits added yet. Add habits in the Habits tab below.")
    
    # Health priorities from user profile
    st.write("---")
    st.subheader("Your Health Priorities")
    
    health_priorities = st.session_state.get("user_profile", {}).get("health_priority", [])
    
    if health_priorities:
        for priority in health_priorities:
            st.markdown(f"* {priority}")
    else:
        st.info("No health priorities set. Update your profile in Settings.")

# Main content tabs
tab1, tab2, tab3 = st.tabs(["Habits", "Health Dashboard", "Add New Habit"])

# Habits tab
with tab1:
    habits = st.session_state.get("habits", [])
    
    if habits:
        # Sort habits by current streak (descending)
        sorted_habits = sorted(habits, key=lambda x: x.get("current_streak", 0), reverse=True)
        
        # Create columns for habits
        cols = st.columns(3)
        
        for i, habit in enumerate(sorted_habits):
            with cols[i % 3]:
                # Get category info
                category = next((c for c in st.session_state.get("categories", []) 
                               if c["id"] == habit.get("category_id")), None)
                category_color = category["color"] if category else "#808080"
                category_name = category["name"] if category else "Uncategorized"
                
                # Create habit card
                st.markdown(f"""
                <div style='border: 1px solid {category_color}; border-radius: 5px; padding: 10px; margin-bottom: 15px;'>
                    <h3 style='color: {category_color}; margin-top: 0;'>{habit['title']}</h3>
                    <div style='display: flex; justify-content: space-between; margin-bottom: 5px;'>
                        <span style='color: #888;'>{category_name}</span>
                        <span style='color: #888;'>Frequency: {habit.get('frequency', 'daily')}</span>
                    </div>
                    <div style='margin-bottom: 10px;'>{habit.get('description', '')}</div>
                    <div style='display: flex; justify-content: space-between;'>
                        <div>
                            <span style='font-weight: bold;'>{habit.get('current_streak', 0)}</span> day streak
                        </div>
                        <div>
                            Best: <span style='font-weight: bold;'>{habit.get('best_streak', 0)}</span> days
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Check-in button
                if st.button("Check In", key=f"checkin_{habit['id']}"):
                    today = datetime.now().date().isoformat()
                    
                    if today not in habit.get("check_ins", []):
                        check_in_habit(habit["id"])
                        st.success(f"Checked in for {habit['title']}!")
                        st.rerun()
                    else:
                        st.info("Already checked in today!")
                
                # Action buttons
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("View History", key=f"history_{habit['id']}"):
                        st.session_state["selected_habit_id"] = habit["id"]
                        st.rerun()
                
                with col2:
                    if st.button("Delete", key=f"delete_{habit['id']}"):
                        if delete_habit(habit["id"]):
                            st.success(f"Deleted habit: {habit['title']}")
                            st.rerun()
        
        # Show habit history if selected
        if "selected_habit_id" in st.session_state:
            selected_habit = next((h for h in habits if h["id"] == st.session_state["selected_habit_id"]), None)
            
            if selected_habit:
                st.markdown("---")
                st.subheader(f"History for: {selected_habit['title']}")
                
                # Generate heatmap
                heatmap = habit_heatmap(selected_habit)
                
                if heatmap:
                    st.plotly_chart(heatmap, use_container_width=True)
                
                # Check-in history
                if selected_habit.get("check_ins"):
                    # Convert to datetime objects and sort
                    check_in_dates = [datetime.fromisoformat(d) for d in selected_habit["check_ins"]]
                    check_in_dates.sort(reverse=True)
                    
                    st.write("Recent check-ins:")
                    
                    # Show recent check-ins
                    for date in check_in_dates[:10]:
                        st.write(f"- {date.strftime('%Y-%m-%d')}")
                    
                    # Show option to clear history
                    if st.button("Clear Check-in History"):
                        # Confirm
                        if "confirm_clear" not in st.session_state:
                            st.session_state["confirm_clear"] = True
                            st.warning("Are you sure? This will reset your streak. Click again to confirm.")
                        else:
                            # Clear check-ins
                            for i, habit in enumerate(st.session_state["habits"]):
                                if habit["id"] == selected_habit["id"]:
                                    st.session_state["habits"][i]["check_ins"] = []
                                    st.session_state["habits"][i]["current_streak"] = 0
                                    save_user_data()
                                    break
                            
                            # Clear confirmation and selected habit
                            del st.session_state["confirm_clear"]
                            del st.session_state["selected_habit_id"]
                            
                            st.success("Check-in history cleared!")
                            st.rerun()
                else:
                    st.info("No check-ins recorded yet.")
                
                # Button to go back
                if st.button("Back to All Habits"):
                    if "selected_habit_id" in st.session_state:
                        del st.session_state["selected_habit_id"]
                    st.rerun()
    else:
        st.info("No habits tracked yet. Add some habits to get started!")
        
        # Show example habits
        st.markdown("### Example Habits to Track")
        
        example_habits = [
            {"title": "Drink 8 glasses of water", "description": "Stay hydrated throughout the day", "category": "Health"},
            {"title": "Exercise for 30 minutes", "description": "Any physical activity counts", "category": "Health"},
            {"title": "8 hours of sleep", "description": "Maintain a consistent sleep schedule", "category": "Health"},
            {"title": "Meditate for 10 minutes", "description": "Practice mindfulness daily", "category": "Mindfulness"},
            {"title": "Read for 30 minutes", "description": "Read books, articles, or anything you enjoy", "category": "Learning"}
        ]
        
        cols = st.columns(3)
        for i, habit in enumerate(example_habits):
            with cols[i % 3]:
                st.markdown(f"""
                <div style='border: 1px solid #808080; border-radius: 5px; padding: 10px; margin-bottom: 15px;'>
                    <h3 style='margin-top: 0;'>{habit['title']}</h3>
                    <div style='color: #888;'>{habit['category']}</div>
                    <div style='margin-top: 5px;'>{habit['description']}</div>
                </div>
                """, unsafe_allow_html=True)

# Health Dashboard tab
with tab2:
    st.subheader("Habit Streaks")
    
    habits = st.session_state.get("habits", [])
    
    if habits:
        # Generate streak chart
        streak_chart = habit_streak_chart(habits)
        
        if streak_chart:
            st.plotly_chart(streak_chart, use_container_width=True)
        
        # Show habit completion rate
        st.subheader("Habit Completion Rate")
        
        # Calculate completion rate for the last 7 days
        today = datetime.now().date()
        last_week = [(today - timedelta(days=i)).isoformat() for i in range(7)]
        
        completion_data = []
        for habit in habits:
            check_ins = habit.get("check_ins", [])
            days_checked = sum(1 for day in last_week if day in check_ins)
            completion_rate = (days_checked / 7) * 100
            
            completion_data.append({
                "habit": habit["title"],
                "completion_rate": completion_rate
            })
        
        if completion_data:
            df = pd.DataFrame(completion_data)
            
            import altair as alt
            
            chart = alt.Chart(df).mark_bar().encode(
                x=alt.X('habit:N', title='Habit'),
                y=alt.Y('completion_rate:Q', title='Completion Rate (%)')
            ).properties(
                title='7-Day Habit Completion Rate',
                height=300
            )
            
            st.altair_chart(chart, use_container_width=True)
        
        # Show which days have the highest check-in rate
        st.subheader("Check-ins by Day of Week")
        
        # Gather all check-ins for all habits
        all_check_ins = []
        for habit in habits:
            all_check_ins.extend(habit.get("check_ins", []))
        
        if all_check_ins:
            # Convert to day of week
            day_counts = {}
            for check_in in all_check_ins:
                day = datetime.fromisoformat(check_in).strftime("%A")
                if day not in day_counts:
                    day_counts[day] = 0
                day_counts[day] += 1
            
            # Order days of week correctly
            days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            ordered_days = {day: day_counts.get(day, 0) for day in days_order}
            
            df = pd.DataFrame({
                "day": list(ordered_days.keys()),
                "count": list(ordered_days.values())
            })
            
            import altair as alt
            
            chart = alt.Chart(df).mark_bar().encode(
                x=alt.X('day:N', title='Day of Week', sort=days_order),
                y=alt.Y('count:Q', title='Number of Check-ins')
            ).properties(
                title='Check-ins by Day of Week',
                height=300
            )
            
            st.altair_chart(chart, use_container_width=True)
            
            # Identify best and worst days
            best_day = max(ordered_days.items(), key=lambda x: x[1])
            worst_day = min(ordered_days.items(), key=lambda x: x[1])
            
            st.write(f"Your most consistent day is **{best_day[0]}** with {best_day[1]} check-ins.")
            st.write(f"Your least consistent day is **{worst_day[0]}** with {worst_day[1]} check-ins.")
    else:
        st.info("No habits tracked yet. Add some habits to see your health dashboard.")
        
    # Health Tips
    st.markdown("---")
    st.subheader("Health Tips")
    
    health_tips = [
        {
            "title": "Consistency Over Intensity",
            "description": "It's better to exercise moderately for 10 minutes every day than intensely for an hour once a week.",
            "icon": "exercise"
        },
        {
            "title": "Make it Obvious",
            "description": "Place visual cues in your environment to remind you of your habits. For example, put your running shoes by the door.",
            "icon": "habit"
        },
        {
            "title": "Two-Minute Rule",
            "description": "Make new habits take less than two minutes to do. Then, once you've started, it's easier to continue.",
            "icon": "clock"
        },
        {
            "title": "Track Your Progress",
            "description": "Maintain a record of your habits. Don't break the chain of consecutive days.",
            "icon": "check"
        },
        {
            "title": "Habit Stacking",
            "description": "Link a new habit with an existing one. For example, 'After I brush my teeth, I will meditate for one minute.'",
            "icon": "category"
        }
    ]
    
    cols = st.columns(3)
    
    for i, tip in enumerate(health_tips):
        with cols[i % 3]:
            st.markdown(f"""
            <div style='border: 1px solid #888; border-radius: 5px; padding: 15px; margin-bottom: 15px;'>
                <div style='display: flex; align-items: center; margin-bottom: 10px;'>
                    {get_icon(tip['icon'], color="#7792E3", size=20)}
                    <span style='font-weight: bold; margin-left: 5px;'>{tip['title']}</span>
                </div>
                <div>{tip['description']}</div>
            </div>
            """, unsafe_allow_html=True)

# Add New Habit tab
with tab3:
    st.subheader("Add a New Habit to Track")
    
    with st.form(key="habit_form"):
        title = st.text_input("Habit Title", placeholder="e.g., Drink 8 glasses of water")
        
        description = st.text_area(
            "Description (optional)",
            placeholder="Describe your habit and why it's important"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            frequency = st.selectbox(
                "Frequency",
                options=["daily", "weekdays", "weekends", "weekly"],
                index=0
            )
        
        with col2:
            # Get categories with 'Health' or similar categories first
            categories = st.session_state.get("categories", [])
            health_categories = [c for c in categories if "health" in c["name"].lower()]
            other_categories = [c for c in categories if "health" not in c["name"].lower()]
            sorted_categories = health_categories + other_categories
            
            category_id = st.selectbox(
                "Category",
                options=[c["id"] for c in sorted_categories],
                format_func=lambda x: next((c["name"] for c in categories if c["id"] == x), ""),
                index=0 if not health_categories else [i for i, c in enumerate(sorted_categories) if c["id"] == health_categories[0]["id"]][0]
            )
        
        # Reminder settings
        st.write("Reminder Settings (coming soon)")
        reminder_enabled = st.checkbox("Enable reminders", value=False, disabled=True)
        
        if reminder_enabled:
            reminder_time = st.time_input("Reminder time", value=datetime.now().replace(hour=8, minute=0).time())
        
        submit = st.form_submit_button("Add Habit")
        
        if submit:
            if not title:
                st.error("Habit title is required.")
            else:
                # Add the habit
                new_habit = add_habit(
                    title=title,
                    description=description,
                    frequency=frequency,
                    category_id=category_id
                )
                
                st.success(f"Added new habit: {title}")
                st.rerun()
    
    # Common habits suggestions
    st.markdown("---")
    st.subheader("Looking for ideas? Try these common habits:")
    
    common_habits = [
        "Drink 8 glasses of water daily",
        "Exercise for 30 minutes",
        "Meditate for 10 minutes",
        "Read for 20 minutes",
        "Take a multivitamin",
        "Stretch for 5 minutes",
        "Get 8 hours of sleep",
        "Practice gratitude",
        "Eat 5 servings of vegetables",
        "No screens before bed",
        "Take the stairs instead of elevator",
        "Stand up and move every hour"
    ]
    
    # Create buttons for quick addition
    cols = st.columns(3)
    
    for i, habit in enumerate(common_habits):
        with cols[i % 3]:
            if st.button(habit, key=f"quickadd_{i}"):
                # Find a suitable health category, or use the first category
                health_categories = [c for c in categories if "health" in c["name"].lower()]
                category_id = health_categories[0]["id"] if health_categories else categories[0]["id"] if categories else None
                
                # Add the habit
                new_habit = add_habit(
                    title=habit,
                    frequency="daily",
                    category_id=category_id
                )
                
                st.success(f"Added new habit: {habit}")
                st.rerun()
