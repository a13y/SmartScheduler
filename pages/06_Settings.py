import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
import uuid
import os
from utils.data_manager import (
    initialize_session_state,
    save_user_data,
    load_user_data,
    add_category,
    update_category,
    delete_category
)
from assets.icons import get_icon

# Initialize session state
initialize_session_state()

# Page configuration
st.set_page_config(
    page_title="Settings | AI Planner",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Settings")
st.write("Customize your planner, manage categories, and configure application preferences.")

# Main content
tab1, tab2, tab3, tab4 = st.tabs(["Profile", "Categories", "Appearance", "Data Management"])

# Profile tab
with tab1:
    st.subheader("User Profile")
    
    user_profile = st.session_state.get("user_profile", {})
    
    with st.form(key="profile_form"):
        name = st.text_input("Your Name", value=user_profile.get("name", ""))
        
        st.subheader("Productivity Preferences")
        
        productivity_peak = st.selectbox(
            "When are you most productive?",
            options=["Morning", "Afternoon", "Evening", "Night"],
            index=["Morning", "Afternoon", "Evening", "Night"].index(user_profile.get("productivity_peak", "Morning"))
        )
        
        work_routine = st.select_slider(
            "Work Routine Preference",
            options=["Strict Schedule", "Flexible with Structure", "Completely Flexible"],
            value=user_profile.get("work_routine", "Flexible with Structure")
        )
        
        break_frequency = st.select_slider(
            "Break Frequency",
            options=["Frequent Short Breaks", "Few Longer Breaks", "Minimal Breaks"],
            value=user_profile.get("break_frequency", "Frequent Short Breaks")
        )
        
        st.subheader("Goal & Habit Preferences")
        
        goal_timeframe = st.selectbox(
            "Goal Planning Preference",
            options=["Daily Goals", "Weekly Goals", "Monthly Goals", "Quarterly Goals"],
            index=["Daily Goals", "Weekly Goals", "Monthly Goals", "Quarterly Goals"].index(user_profile.get("goal_timeframe", "Weekly Goals"))
        )
        
        habit_formation = st.select_slider(
            "Habit Formation Approach",
            options=["Start Small", "Moderate Changes", "Challenge Myself"],
            value=user_profile.get("habit_formation", "Start Small")
        )
        
        health_priority = st.multiselect(
            "Health Priorities",
            options=["Sleep", "Exercise", "Nutrition", "Mindfulness", "Water Intake"],
            default=user_profile.get("health_priority", ["Sleep", "Exercise"])
        )
        
        save_profile = st.form_submit_button("Save Profile")
        
        if save_profile:
            # Update user profile
            user_profile["name"] = name
            user_profile["productivity_peak"] = productivity_peak
            user_profile["work_routine"] = work_routine
            user_profile["break_frequency"] = break_frequency
            user_profile["goal_timeframe"] = goal_timeframe
            user_profile["habit_formation"] = habit_formation
            user_profile["health_priority"] = health_priority
            
            # Save to session state
            st.session_state["user_profile"] = user_profile
            save_user_data()
            
            st.success("Profile updated successfully!")

# Categories tab
with tab2:
    st.subheader("Manage Categories")
    st.write("Organize your tasks, goals, habits, and events with customized categories.")
    
    # Existing categories
    categories = st.session_state.get("categories", [])
    
    # Display current categories
    st.write("### Current Categories")
    
    if categories:
        # Create a grid of categories
        cols = st.columns(3)
        
        for i, category in enumerate(categories):
            with cols[i % 3]:
                with st.container():
                    # Category box
                    st.markdown(f"""
                    <div style='
                        border: 1px solid {category["color"]};
                        border-radius: 5px;
                        padding: 10px;
                        margin-bottom: 15px;
                    '>
                        <div style='
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                        '>
                            <div>
                                <div style='
                                    width: 15px;
                                    height: 15px;
                                    background-color: {category["color"]};
                                    display: inline-block;
                                    margin-right: 5px;
                                    border-radius: 3px;
                                '></div>
                                <span style='font-weight: bold;'>{category["name"]}</span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("Edit", key=f"edit_{category['id']}"):
                            st.session_state["edit_category_id"] = category["id"]
                            st.session_state["edit_category_name"] = category["name"]
                            st.session_state["edit_category_color"] = category["color"]
                            st.rerun()
                    
                    with col2:
                        if st.button("Delete", key=f"delete_{category['id']}"):
                            # Check if category is in use
                            in_use = False
                            
                            # Check tasks
                            for task in st.session_state.get("tasks", []):
                                if task.get("category_id") == category["id"]:
                                    in_use = True
                                    break
                            
                            # Check goals
                            if not in_use:
                                for goal in st.session_state.get("goals", []):
                                    if goal.get("category_id") == category["id"]:
                                        in_use = True
                                        break
                            
                            # Check habits
                            if not in_use:
                                for habit in st.session_state.get("habits", []):
                                    if habit.get("category_id") == category["id"]:
                                        in_use = True
                                        break
                            
                            # Check events
                            if not in_use:
                                for event in st.session_state.get("calendar_events", []):
                                    if event.get("category_id") == category["id"]:
                                        in_use = True
                                        break
                            
                            if in_use:
                                st.warning("This category is in use and cannot be deleted. Reassign items first.")
                            else:
                                delete_category(category["id"])
                                st.success(f"Deleted category: {category['name']}")
                                st.rerun()
    else:
        st.info("No categories found. Add some categories below.")
    
    # Add or edit category form
    st.write("---")
    
    category_id = st.session_state.get("edit_category_id")
    
    if category_id:
        st.subheader("Edit Category")
    else:
        st.subheader("Add New Category")
    
    with st.form(key="category_form"):
        name = st.text_input(
            "Category Name",
            value=st.session_state.get("edit_category_name", "")
        )
        
        color = st.color_picker(
            "Category Color",
            value=st.session_state.get("edit_category_color", "#FF5733")
        )
        
        submit_label = "Update Category" if category_id else "Add Category"
        submit = st.form_submit_button(submit_label)
        
        if submit:
            if not name:
                st.error("Category name is required.")
            else:
                if category_id:
                    # Update existing category
                    update_category(
                        category_id,
                        name=name,
                        color=color
                    )
                    
                    # Clear edit state
                    for key in ["edit_category_id", "edit_category_name", "edit_category_color"]:
                        if key in st.session_state:
                            del st.session_state[key]
                    
                    st.success("Category updated successfully!")
                else:
                    # Add new category
                    add_category(
                        name=name,
                        color=color
                    )
                    
                    st.success("Category added successfully!")
                
                # Clear form
                st.rerun()
    
    # Cancel button for edit mode
    if category_id:
        if st.button("Cancel Editing"):
            # Clear edit state
            for key in ["edit_category_id", "edit_category_name", "edit_category_color"]:
                if key in st.session_state:
                    del st.session_state[key]
            
            st.rerun()
    
    # Category usage statistics
    st.write("---")
    st.subheader("Category Usage")
    
    if categories:
        # Count items by category
        category_counts = {c["id"]: {"name": c["name"], "color": c["color"], "tasks": 0, "goals": 0, "habits": 0, "events": 0} for c in categories}
        
        # Count tasks
        for task in st.session_state.get("tasks", []):
            category_id = task.get("category_id")
            if category_id in category_counts:
                category_counts[category_id]["tasks"] += 1
        
        # Count goals
        for goal in st.session_state.get("goals", []):
            category_id = goal.get("category_id")
            if category_id in category_counts:
                category_counts[category_id]["goals"] += 1
        
        # Count habits
        for habit in st.session_state.get("habits", []):
            category_id = habit.get("category_id")
            if category_id in category_counts:
                category_counts[category_id]["habits"] += 1
        
        # Count events
        for event in st.session_state.get("calendar_events", []):
            category_id = event.get("category_id")
            if category_id in category_counts:
                category_counts[category_id]["events"] += 1
        
        # Create dataframe for display
        df = pd.DataFrame([
            {
                "Category": data["name"],
                "Tasks": data["tasks"],
                "Goals": data["goals"],
                "Habits": data["habits"],
                "Events": data["events"],
                "Total": data["tasks"] + data["goals"] + data["habits"] + data["events"]
            }
            for cat_id, data in category_counts.items()
        ])
        
        # Sort by total count
        df = df.sort_values("Total", ascending=False)
        
        # Display table
        st.dataframe(df, use_container_width=True)
        
        # Create bar chart of category usage
        import plotly.express as px
        
        fig = px.bar(
            df,
            x="Category",
            y=["Tasks", "Goals", "Habits", "Events"],
            title="Items per Category",
            labels={"value": "Number of Items", "Category": "Category", "variable": "Item Type"},
            height=400,
            barmode="stack"
        )
        
        st.plotly_chart(fig, use_container_width=True)

# Appearance tab
with tab3:
    st.subheader("Appearance Settings")
    
    # Theme selection
    st.write("### Theme")
    
    current_theme = st.session_state.get("user_profile", {}).get("theme", "dark")
    
    theme_options = ["Dark Mode", "Light Mode"]
    theme_descriptions = [
        "Dark background with light text (easier on the eyes)",
        "Light background with dark text (high contrast)"
    ]
    
    selected_theme = st.radio(
        "Select Theme",
        options=range(len(theme_options)),
        format_func=lambda i: theme_options[i],
        index=0 if current_theme == "dark" else 1
    )
    
    st.caption(theme_descriptions[selected_theme])
    
    if st.button("Apply Theme"):
        # Update theme in user profile
        user_profile = st.session_state.get("user_profile", {})
        user_profile["theme"] = "dark" if selected_theme == 0 else "light"
        
        # Save to session state
        st.session_state["user_profile"] = user_profile
        save_user_data()
        
        st.success("Theme updated! Refresh the page to see changes.")
        st.info("Note: Theme changes are applied via the config.toml file and require a page refresh.")
    
    # Color preferences
    st.write("---")
    st.write("### Color Preferences")
    st.info("Color preferences can be customized through categories. Each category has its own color that will be used for items in that category.")

    # Coming soon features
    st.write("---")
    st.write("### Coming Soon")
    
    st.markdown("""
    - Custom dashboard layouts
    - Font size adjustments
    - Additional theme options
    - Calendar view customization
    - Printable planner templates
    """)

# Data Management tab
with tab4:
    st.subheader("Data Management")
    
    # Export data
    st.write("### Export Data")
    
    if st.button("Export All Data"):
        # Prepare data for export
        export_data = {
            "user_profile": st.session_state.get("user_profile", {}),
            "categories": st.session_state.get("categories", []),
            "tasks": st.session_state.get("tasks", []),
            "goals": st.session_state.get("goals", []),
            "habits": st.session_state.get("habits", []),
            "calendar_events": st.session_state.get("calendar_events", []),
            "exported_at": datetime.now().isoformat()
        }
        
        # Convert to JSON
        export_json = json.dumps(export_data, indent=2)
        
        # Provide download link
        st.download_button(
            label="Download Data (JSON)",
            data=export_json,
            file_name=f"planner_data_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )
    
    # Import data
    st.write("---")
    st.write("### Import Data")
    
    uploaded_file = st.file_uploader("Upload Data File", type=["json"])
    
    if uploaded_file is not None:
        try:
            # Load JSON data
            import_data = json.load(uploaded_file)
            
            # Validate data structure
            required_keys = ["user_profile", "categories", "tasks", "goals", "habits", "calendar_events"]
            if all(key in import_data for key in required_keys):
                if st.button("Apply Imported Data"):
                    # Update session state with imported data
                    for key in required_keys:
                        st.session_state[key] = import_data[key]
                    
                    # Save data
                    save_user_data()
                    
                    st.success("Data imported successfully!")
                    st.rerun()
            else:
                st.error("Invalid data format. Missing required sections.")
        except json.JSONDecodeError:
            st.error("Invalid JSON file. Please upload a valid data file.")
    
    # Reset options
    st.write("---")
    st.write("### Reset Options")
    
    reset_options = st.multiselect(
        "Select data to reset",
        options=["Tasks", "Goals", "Habits", "Calendar Events", "Categories", "User Profile", "Everything"],
        help="Warning: This will permanently delete the selected data!"
    )
    
    if reset_options:
        if st.button("Reset Selected Data", type="primary"):
            # Confirm reset
            if "confirm_reset" not in st.session_state:
                st.session_state["confirm_reset"] = True
                st.warning("⚠️ This will permanently delete the selected data! Click again to confirm.")
            else:
                # Perform reset
                if "Everything" in reset_options:
                    # Reset all data
                    st.session_state["user_profile"] = {}
                    st.session_state["categories"] = []
                    st.session_state["tasks"] = []
                    st.session_state["goals"] = []
                    st.session_state["habits"] = []
                    st.session_state["calendar_events"] = []
                    st.session_state["points"] = 0
                    st.session_state["rewards"] = []
                    st.session_state["unlocked_rewards"] = []
                    st.session_state["first_time"] = True
                else:
                    # Reset specific data
                    if "Tasks" in reset_options:
                        st.session_state["tasks"] = []
                    
                    if "Goals" in reset_options:
                        st.session_state["goals"] = []
                    
                    if "Habits" in reset_options:
                        st.session_state["habits"] = []
                    
                    if "Calendar Events" in reset_options:
                        st.session_state["calendar_events"] = []
                    
                    if "Categories" in reset_options:
                        st.session_state["categories"] = []
                    
                    if "User Profile" in reset_options:
                        st.session_state["user_profile"] = {}
                        st.session_state["first_time"] = True
                
                # Save changes
                save_user_data()
                
                # Clear confirmation state
                del st.session_state["confirm_reset"]
                
                st.success("Selected data has been reset!")
                
                # If user profile was reset, redirect to welcome screen
                if "User Profile" in reset_options or "Everything" in reset_options:
                    st.info("Redirecting to welcome screen...")
                    st.rerun()
    
    # Data statistics
    st.write("---")
    st.write("### Data Statistics")
    
    # Count items
    task_count = len(st.session_state.get("tasks", []))
    goal_count = len(st.session_state.get("goals", []))
    habit_count = len(st.session_state.get("habits", []))
    event_count = len(st.session_state.get("calendar_events", []))
    category_count = len(st.session_state.get("categories", []))
    
    # Calculate completed items
    completed_tasks = sum(1 for task in st.session_state.get("tasks", []) if task.get("completed", False))
    completed_goals = sum(1 for goal in st.session_state.get("goals", []) if goal.get("completed", False))
    
    # Display statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Tasks", task_count, f"{completed_tasks} completed")
        st.metric("Total Goals", goal_count, f"{completed_goals} completed")
    
    with col2:
        st.metric("Total Habits", habit_count)
        st.metric("Total Events", event_count)
    
    with col3:
        st.metric("Categories", category_count)
        
        # Find oldest data point
        oldest_date = None
        
        for key in ["tasks", "goals", "habits", "calendar_events"]:
            for item in st.session_state.get(key, []):
                if "created_at" in item:
                    try:
                        created_date = datetime.fromisoformat(item["created_at"]).date()
                        if oldest_date is None or created_date < oldest_date:
                            oldest_date = created_date
                    except (ValueError, TypeError):
                        pass
        
        days_using = (datetime.now().date() - oldest_date).days if oldest_date else 0
        st.metric("Days Using Planner", days_using)

# App information
st.sidebar.markdown("---")
st.sidebar.header("About AI Planner")
st.sidebar.info("""
This comprehensive planner helps you manage tasks, track goals, and build healthy habits using AI to optimize your schedule.

It leverages principles from 'Atomic Habits' and 'The 7 Habits of Highly Effective People' to help you build better productivity systems.
""")

st.sidebar.markdown("**Version:** 1.0.0")
