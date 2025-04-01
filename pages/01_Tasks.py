import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import uuid
from utils.data_manager import (
    initialize_session_state,
    save_user_data,
    load_user_data,
    add_task,
    update_task,
    delete_task,
    complete_task
)
from utils.task_classifier import (
    classify_task,
    estimate_task_parameters,
    get_next_tasks
)
from utils.visualization import (
    task_completion_by_category,
    priority_matrix_chart
)
from assets.icons import get_icon

# Initialize session state
initialize_session_state()

# Page configuration
st.set_page_config(
    page_title="Tasks | AI Planner",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Task Management")

# Sidebar filters
with st.sidebar:
    st.header("Filters")
    
    # Category filter
    categories = st.session_state.get("categories", [])
    category_options = ["All Categories"] + [c["name"] for c in categories]
    
    selected_category = st.selectbox(
        "Category",
        options=category_options,
        index=0
    )
    
    # Status filter
    status_options = ["All Tasks", "Incomplete", "Completed"]
    selected_status = st.selectbox(
        "Status",
        options=status_options,
        index=0
    )
    
    # Priority filter
    priority_options = ["All Priorities", "Critical", "High", "Medium", "Low"]
    selected_priority = st.selectbox(
        "Priority",
        options=priority_options,
        index=0
    )
    
    # Date range filter
    date_options = ["All Time", "Today", "Next 7 Days", "This Month", "Custom Range"]
    selected_date_option = st.selectbox(
        "Due Date",
        options=date_options,
        index=0
    )
    
    custom_date_range = None
    if selected_date_option == "Custom Range":
        start_date = st.date_input("Start Date", datetime.now().date())
        end_date = st.date_input("End Date", (datetime.now() + timedelta(days=7)).date())
        custom_date_range = (start_date, end_date)

# Main content
tab1, tab2, tab3 = st.tabs(["Task List", "Add New Task", "Task Matrix"])

# Task List tab
with tab1:
    # Get and filter tasks
    tasks = st.session_state.get("tasks", [])
    
    # Apply filters
    if selected_category != "All Categories":
        category_id = next((c["id"] for c in categories if c["name"] == selected_category), None)
        if category_id:
            tasks = [task for task in tasks if task.get("category_id") == category_id]
    
    if selected_status != "All Tasks":
        is_completed = selected_status == "Completed"
        tasks = [task for task in tasks if task.get("completed", False) == is_completed]
    
    if selected_priority != "All Priorities":
        if selected_priority == "Critical":
            tasks = [task for task in tasks if (task.get("importance", 1) * task.get("urgency", 1)) >= 20]
        elif selected_priority == "High":
            tasks = [task for task in tasks if 12 <= (task.get("importance", 1) * task.get("urgency", 1)) < 20]
        elif selected_priority == "Medium":
            tasks = [task for task in tasks if 6 <= (task.get("importance", 1) * task.get("urgency", 1)) < 12]
        elif selected_priority == "Low":
            tasks = [task for task in tasks if (task.get("importance", 1) * task.get("urgency", 1)) < 6]
    
    if selected_date_option == "Today":
        today = datetime.now().date()
        tasks = [task for task in tasks if task.get("due_date") and datetime.fromisoformat(task["due_date"]).date() == today]
    elif selected_date_option == "Next 7 Days":
        today = datetime.now().date()
        end_date = today + timedelta(days=7)
        tasks = [task for task in tasks if task.get("due_date") and 
                 today <= datetime.fromisoformat(task["due_date"]).date() <= end_date]
    elif selected_date_option == "This Month":
        today = datetime.now().date()
        tasks = [task for task in tasks if task.get("due_date") and 
                 datetime.fromisoformat(task["due_date"]).date().month == today.month and
                 datetime.fromisoformat(task["due_date"]).date().year == today.year]
    elif selected_date_option == "Custom Range" and custom_date_range:
        start_date, end_date = custom_date_range
        tasks = [task for task in tasks if task.get("due_date") and 
                 start_date <= datetime.fromisoformat(task["due_date"]).date() <= end_date]
    
    # Show filtered tasks
    if tasks:
        # Sort by priority (importance * urgency)
        sorted_tasks = sorted(
            tasks, 
            key=lambda x: (
                (not x.get("completed", False)),  # Incomplete tasks first
                x.get("due_date") is not None,  # Tasks with due date first
                x.get("due_date", "9999-12-31"),  # Sort by due date
                x.get("importance", 0) * x.get("urgency", 0)  # Then by priority
            ),
            reverse=True
        )
        
        for task in sorted_tasks:
            with st.container():
                col1, col2, col3 = st.columns([0.1, 0.7, 0.2])
                
                with col1:
                    # Checkbox for completion
                    completed = task.get("completed", False)
                    new_status = st.checkbox("", value=completed, key=f"task_{task['id']}")
                    
                    # Update completion status if changed
                    if new_status != completed:
                        if new_status:
                            complete_task(task["id"])
                        else:
                            update_task(task["id"], completed=False, completed_at=None)
                        st.rerun()
                
                with col2:
                    # Task details
                    category = next((c for c in categories if c["id"] == task.get("category_id")), None)
                    category_color = category["color"] if category else "#808080"
                    category_name = category["name"] if category else "Uncategorized"
                    
                    # Calculate priority label
                    importance = task.get("importance", 1)
                    urgency = task.get("urgency", 1)
                    priority_score = importance * urgency
                    
                    if priority_score >= 20:
                        priority_label = "Critical"
                    elif priority_score >= 12:
                        priority_label = "High"
                    elif priority_score >= 6:
                        priority_label = "Medium"
                    else:
                        priority_label = "Low"
                    
                    # Style based on completion status
                    title_style = "text-decoration: line-through;" if completed else ""
                    
                    st.markdown(f"""
                    <div style='padding-left: 5px; border-left: 5px solid {category_color};'>
                        <span style='font-weight: bold; {title_style}'>{task['title']}</span>
                        <div style='display: flex; gap: 10px; margin-top: 5px;'>
                            <span style='font-size: 0.8em; color: #888;'>{category_name}</span>
                            <span style='font-size: 0.8em; color: #888;'>Priority: {priority_label}</span>
                            {f"<span style='font-size: 0.8em; color: #888;'>Due: {datetime.fromisoformat(task['due_date']).strftime('%Y-%m-%d')}</span>" if task.get('due_date') else ""}
                        </div>
                        {f"<div style='margin-top: 5px; font-size: 0.9em;'>{task['description']}</div>" if task.get('description') else ""}
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    # Actions
                    col3_1, col3_2 = st.columns(2)
                    
                    with col3_1:
                        if st.button("Edit", key=f"edit_{task['id']}"):
                            st.session_state["edit_task_id"] = task["id"]
                            st.session_state["edit_task_title"] = task["title"]
                            st.session_state["edit_task_description"] = task.get("description", "")
                            st.session_state["edit_task_category"] = task.get("category_id", "")
                            st.session_state["edit_task_due_date"] = datetime.fromisoformat(task["due_date"]).date() if task.get("due_date") else None
                            st.session_state["edit_task_importance"] = task.get("importance", 3)
                            st.session_state["edit_task_urgency"] = task.get("urgency", 3)
                            st.rerun()
                    
                    with col3_2:
                        if st.button("Delete", key=f"delete_{task['id']}"):
                            delete_task(task["id"])
                            st.rerun()
            
            st.markdown("---")
    else:
        st.info("No tasks found matching your filters.")

# Add New Task tab
with tab2:
    task_id = st.session_state.get("edit_task_id")
    
    if task_id:
        st.subheader("Edit Task")
    else:
        st.subheader("Add New Task")
    
    with st.form(key="task_form"):
        title = st.text_input(
            "Task Title",
            value=st.session_state.get("edit_task_title", "")
        )
        
        description = st.text_area(
            "Description",
            value=st.session_state.get("edit_task_description", "")
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            category_id = st.selectbox(
                "Category",
                options=[c["id"] for c in categories],
                format_func=lambda x: next((c["name"] for c in categories if c["id"] == x), ""),
                index=0 if not st.session_state.get("edit_task_category") else 
                    [i for i, c in enumerate(categories) if c["id"] == st.session_state.get("edit_task_category")][0]
                    if any(c["id"] == st.session_state.get("edit_task_category") for c in categories) else 0
            )
            
            due_date = st.date_input(
                "Due Date",
                value=st.session_state.get("edit_task_due_date")
            )
        
        with col2:
            importance = st.slider(
                "Importance (1-5)",
                min_value=1,
                max_value=5,
                value=st.session_state.get("edit_task_importance", 3),
                help="How important is this task to your goals?"
            )
            
            urgency = st.slider(
                "Urgency (1-5)",
                min_value=1,
                max_value=5,
                value=st.session_state.get("edit_task_urgency", 3),
                help="How time-sensitive is this task?"
            )
        
        # AI suggestion for category if it's a new task
        if not task_id and title:
            suggested_category_id = classify_task(title, categories, st.session_state.get("tasks", []))
            if suggested_category_id:
                suggested_category = next((c["name"] for c in categories if c["id"] == suggested_category_id), None)
                if suggested_category:
                    st.info(f"AI suggests categorizing this as: {suggested_category}")
        
        # AI suggestion for importance and urgency if it's a new task
        if not task_id and title:
            suggested_importance, suggested_urgency = estimate_task_parameters(title, description)
            if suggested_importance != 3 or suggested_urgency != 3:
                st.info(f"AI suggests importance: {suggested_importance}/5, urgency: {suggested_urgency}/5")
        
        submit_label = "Update Task" if task_id else "Add Task"
        submit = st.form_submit_button(submit_label)
        
        if submit:
            if not title:
                st.error("Task title is required.")
            else:
                due_date_str = due_date.isoformat() if due_date else None
                
                if task_id:
                    # Update existing task
                    update_task(
                        task_id,
                        title=title,
                        description=description,
                        category_id=category_id,
                        due_date=due_date_str,
                        importance=importance,
                        urgency=urgency
                    )
                    
                    # Clear edit state
                    for key in ["edit_task_id", "edit_task_title", "edit_task_description", 
                               "edit_task_category", "edit_task_due_date", 
                               "edit_task_importance", "edit_task_urgency"]:
                        if key in st.session_state:
                            del st.session_state[key]
                    
                    st.success("Task updated successfully!")
                else:
                    # Add new task
                    new_task = add_task(
                        title=title,
                        description=description,
                        category_id=category_id,
                        due_date=datetime.combine(due_date, datetime.min.time()) if due_date else None,
                        importance=importance,
                        urgency=urgency
                    )
                    
                    st.success("Task added successfully!")
                
                # Clear form
                st.rerun()
    
    # Cancel button for edit mode
    if task_id:
        if st.button("Cancel Editing"):
            # Clear edit state
            for key in ["edit_task_id", "edit_task_title", "edit_task_description", 
                       "edit_task_category", "edit_task_due_date", 
                       "edit_task_importance", "edit_task_urgency"]:
                if key in st.session_state:
                    del st.session_state[key]
            
            st.rerun()

# Task Matrix tab
with tab3:
    st.subheader("Priority Matrix (Eisenhower Matrix)")
    st.write("Visualize your tasks based on importance and urgency to focus on what matters most.")
    
    # Filter for incomplete tasks
    incomplete_tasks = [task for task in st.session_state.get("tasks", []) if not task.get("completed", False)]
    
    if incomplete_tasks:
        # Generate the priority matrix chart
        matrix_chart = priority_matrix_chart(incomplete_tasks)
        
        if matrix_chart:
            st.plotly_chart(matrix_chart, use_container_width=True)
        else:
            st.info("No data available to generate the matrix chart.")
    else:
        st.info("No incomplete tasks found. Add some tasks to see them in the priority matrix.")
    
    # Additional visualization: Task completion by category
    st.subheader("Task Completion by Category")
    
    completion_chart = task_completion_by_category(st.session_state.get("tasks", []), categories)
    
    if completion_chart:
        st.plotly_chart(completion_chart, use_container_width=True)
    else:
        st.info("Not enough data to generate the category chart.")
    
    # Task Recommendations
    st.subheader("AI Task Recommendations")
    
    if incomplete_tasks:
        next_tasks = get_next_tasks(incomplete_tasks)
        
        if next_tasks:
            st.write("Based on your priorities, focus on these tasks next:")
            
            for i, task in enumerate(next_tasks, 1):
                category = next((c for c in categories if c["id"] == task.get("category_id")), None)
                category_color = category["color"] if category else "#808080"
                
                st.markdown(f"""
                <div style='padding: 10px; border-left: 5px solid {category_color}; margin-bottom: 10px;'>
                    <div style='font-weight: bold;'>{i}. {task['title']}</div>
                    <div style='color: #888;'>
                        Importance: {task.get('importance', 3)}/5, 
                        Urgency: {task.get('urgency', 3)}/5
                    </div>
                    {f"<div>Due: {datetime.fromisoformat(task['due_date']).strftime('%Y-%m-%d')}</div>" if task.get('due_date') else ""}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No task recommendations available.")
    else:
        st.info("Add some tasks to get AI recommendations.")
