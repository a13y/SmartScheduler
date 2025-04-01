import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import uuid
from utils.data_manager import (
    initialize_session_state,
    save_user_data,
    add_goal,
    update_goal,
    delete_goal,
    complete_goal
)
from utils.visualization import goal_progress_chart
from assets.icons import get_icon

# Initialize session state
initialize_session_state()

# Page configuration
st.set_page_config(
    page_title="Goals | AI Planner",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Goal Tracking")
st.write("Set and track your long-term goals, break them down into milestones, and monitor your progress.")

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
    status_options = ["All Goals", "In Progress", "Completed"]
    selected_status = st.selectbox(
        "Status",
        options=status_options,
        index=0
    )
    
    # Timeframe filter
    timeframe_options = ["All Time", "This Month", "This Quarter", "This Year"]
    selected_timeframe = st.selectbox(
        "Timeframe",
        options=timeframe_options,
        index=0
    )

# Main content
tab1, tab2, tab3 = st.tabs(["Active Goals", "Add New Goal", "Goal Analytics"])

# Active Goals tab
with tab1:
    # Get and filter goals
    goals = st.session_state.get("goals", [])
    
    # Apply filters
    if selected_category != "All Categories":
        category_id = next((c["id"] for c in categories if c["name"] == selected_category), None)
        if category_id:
            goals = [goal for goal in goals if goal.get("category_id") == category_id]
    
    if selected_status != "All Goals":
        is_completed = selected_status == "Completed"
        goals = [goal for goal in goals if goal.get("completed", False) == is_completed]
    
    if selected_timeframe != "All Time":
        today = datetime.now().date()
        
        if selected_timeframe == "This Month":
            start_date = datetime(today.year, today.month, 1).date()
            if today.month == 12:
                end_date = datetime(today.year + 1, 1, 1).date() - timedelta(days=1)
            else:
                end_date = datetime(today.year, today.month + 1, 1).date() - timedelta(days=1)
        elif selected_timeframe == "This Quarter":
            quarter = (today.month - 1) // 3 + 1
            start_date = datetime(today.year, (quarter - 1) * 3 + 1, 1).date()
            if quarter == 4:
                end_date = datetime(today.year + 1, 1, 1).date() - timedelta(days=1)
            else:
                end_date = datetime(today.year, quarter * 3 + 1, 1).date() - timedelta(days=1)
        elif selected_timeframe == "This Year":
            start_date = datetime(today.year, 1, 1).date()
            end_date = datetime(today.year + 1, 1, 1).date() - timedelta(days=1)
        
        goals = [
            goal for goal in goals if goal.get("target_date") and 
            start_date <= datetime.fromisoformat(goal["target_date"]).date() <= end_date
        ]
    
    # Display goals
    if goals:
        # Sort by target date and then progress
        sorted_goals = sorted(
            goals, 
            key=lambda x: (
                x.get("completed", False),  # Incomplete goals first
                x.get("target_date", "9999-12-31"),  # Then by target date
                -x.get("progress", 0)  # Then by progress (highest first)
            )
        )
        
        for goal in sorted_goals:
            with st.container():
                # Check if goal is completed
                completed = goal.get("completed", False)
                
                # Get category info
                category = next((c for c in categories if c["id"] == goal.get("category_id")), None)
                category_color = category["color"] if category else "#808080"
                category_name = category["name"] if category else "Uncategorized"
                
                # Goal container
                col1, col2 = st.columns([0.7, 0.3])
                
                with col1:
                    # Title and description
                    title_style = "text-decoration: line-through;" if completed else ""
                    
                    st.markdown(f"""
                    <div style='padding-left: 5px; border-left: 5px solid {category_color};'>
                        <span style='font-weight: bold; font-size: 1.2em; {title_style}'>{goal['title']}</span>
                        <div style='display: flex; gap: 10px; margin-top: 5px;'>
                            <span style='font-size: 0.8em; color: #888;'>{category_name}</span>
                            {f"<span style='font-size: 0.8em; color: #888;'>Target: {datetime.fromisoformat(goal['target_date']).strftime('%Y-%m-%d')}</span>" if goal.get('target_date') else ""}
                            <span style='font-size: 0.8em; color: #888;'>Progress: {goal.get('progress', 0)}%</span>
                        </div>
                        {f"<div style='margin-top: 5px; font-size: 0.9em;'>{goal['description']}</div>" if goal.get('description') else ""}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Milestones
                    if goal.get("milestones"):
                        st.markdown("#### Milestones")
                        
                        for i, milestone in enumerate(goal["milestones"]):
                            milestone_completed = milestone.get("completed", False)
                            milestone_style = "text-decoration: line-through;" if milestone_completed else ""
                            
                            col_m1, col_m2 = st.columns([0.05, 0.95])
                            
                            with col_m1:
                                milestone_status = st.checkbox("", value=milestone_completed, key=f"milestone_{goal['id']}_{i}")
                                
                                # Update milestone status if changed
                                if milestone_status != milestone_completed:
                                    goal["milestones"][i]["completed"] = milestone_status
                                    
                                    # Update progress based on completed milestones
                                    total_milestones = len(goal["milestones"])
                                    completed_milestones = sum(1 for m in goal["milestones"] if m.get("completed", False))
                                    
                                    if total_milestones > 0:
                                        progress = int((completed_milestones / total_milestones) * 100)
                                        update_goal(goal["id"], progress=progress)
                                        
                                        # If all milestones are completed, mark goal as completed
                                        if completed_milestones == total_milestones:
                                            complete_goal(goal["id"])
                                    
                                    st.rerun()
                            
                            with col_m2:
                                st.markdown(f"""
                                <span style='{milestone_style}'>{milestone["title"]}</span>
                                {f"<div style='font-size: 0.8em; color: #888;'>{milestone.get('description', '')}</div>" if milestone.get('description') else ""}
                                """, unsafe_allow_html=True)
                
                with col2:
                    # Progress bar
                    progress = goal.get("progress", 0)
                    st.progress(progress / 100)
                    
                    # Actions
                    col_a1, col_a2, col_a3 = st.columns(3)
                    
                    with col_a1:
                        # Complete goal button
                        if not completed:
                            if st.button("Complete", key=f"complete_{goal['id']}"):
                                complete_goal(goal["id"])
                                st.success("Goal marked as completed!")
                                st.rerun()
                    
                    with col_a2:
                        # Edit goal button
                        if st.button("Edit", key=f"edit_{goal['id']}"):
                            st.session_state["edit_goal_id"] = goal["id"]
                            st.session_state["edit_goal_title"] = goal["title"]
                            st.session_state["edit_goal_description"] = goal.get("description", "")
                            st.session_state["edit_goal_category"] = goal.get("category_id", "")
                            st.session_state["edit_goal_target_date"] = datetime.fromisoformat(goal["target_date"]).date() if goal.get("target_date") else None
                            st.session_state["edit_goal_milestones"] = goal.get("milestones", [])
                            st.rerun()
                    
                    with col_a3:
                        # Delete goal button
                        if st.button("Delete", key=f"delete_{goal['id']}"):
                            delete_goal(goal["id"])
                            st.success("Goal deleted!")
                            st.rerun()
            
            st.markdown("---")
    else:
        st.info("No goals found matching your filters. Add some goals to get started!")

# Add New Goal tab
with tab2:
    goal_id = st.session_state.get("edit_goal_id")
    
    if goal_id:
        st.subheader("Edit Goal")
    else:
        st.subheader("Add New Goal")
    
    with st.form(key="goal_form"):
        title = st.text_input(
            "Goal Title",
            value=st.session_state.get("edit_goal_title", "")
        )
        
        description = st.text_area(
            "Description",
            value=st.session_state.get("edit_goal_description", "")
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            category_id = st.selectbox(
                "Category",
                options=[c["id"] for c in categories],
                format_func=lambda x: next((c["name"] for c in categories if c["id"] == x), ""),
                index=0 if not st.session_state.get("edit_goal_category") else 
                    [i for i, c in enumerate(categories) if c["id"] == st.session_state.get("edit_goal_category")][0]
                    if any(c["id"] == st.session_state.get("edit_goal_category") for c in categories) else 0
            )
        
        with col2:
            target_date = st.date_input(
                "Target Completion Date",
                value=st.session_state.get("edit_goal_target_date")
            )
        
        # Milestones
        st.subheader("Milestones")
        st.write("Break down your goal into smaller, actionable steps")
        
        milestones = st.session_state.get("edit_goal_milestones", [])
        
        # Display existing milestones with option to edit
        for i in range(len(milestones)):
            col_m1, col_m2, col_m3 = st.columns([0.45, 0.45, 0.1])
            
            with col_m1:
                milestones[i]["title"] = st.text_input(
                    f"Milestone {i+1} Title",
                    value=milestones[i].get("title", ""),
                    key=f"milestone_title_{i}"
                )
            
            with col_m2:
                milestones[i]["description"] = st.text_input(
                    f"Description (optional)",
                    value=milestones[i].get("description", ""),
                    key=f"milestone_desc_{i}"
                )
            
            with col_m3:
                if st.button("X", key=f"remove_milestone_{i}"):
                    milestones.pop(i)
                    st.rerun()
        
        # Add new milestone
        if st.button("+ Add Milestone"):
            milestones.append({"title": "", "description": "", "completed": False})
            st.rerun()
        
        # Submit button
        submit_label = "Update Goal" if goal_id else "Add Goal"
        submit = st.form_submit_button(submit_label)
        
        if submit:
            if not title:
                st.error("Goal title is required.")
            else:
                # Filter out empty milestones
                valid_milestones = [m for m in milestones if m.get("title")]
                
                # Calculate initial progress for existing milestones
                if valid_milestones:
                    completed_milestones = sum(1 for m in valid_milestones if m.get("completed", False))
                    progress = int((completed_milestones / len(valid_milestones)) * 100) if valid_milestones else 0
                else:
                    progress = 0
                
                if goal_id:
                    # Update existing goal
                    update_goal(
                        goal_id,
                        title=title,
                        description=description,
                        category_id=category_id,
                        target_date=target_date.isoformat() if target_date else None,
                        milestones=valid_milestones,
                        progress=progress
                    )
                    
                    # Clear edit state
                    for key in ["edit_goal_id", "edit_goal_title", "edit_goal_description", 
                               "edit_goal_category", "edit_goal_target_date", "edit_goal_milestones"]:
                        if key in st.session_state:
                            del st.session_state[key]
                    
                    st.success("Goal updated successfully!")
                else:
                    # Add new goal
                    add_goal(
                        title=title,
                        description=description,
                        target_date=target_date if target_date else None,
                        category_id=category_id,
                        milestones=valid_milestones
                    )
                    
                    st.success("Goal added successfully!")
                
                # Clear the form and milestones
                st.rerun()
    
    # Cancel button for edit mode
    if goal_id:
        if st.button("Cancel Editing"):
            # Clear edit state
            for key in ["edit_goal_id", "edit_goal_title", "edit_goal_description", 
                       "edit_goal_category", "edit_goal_target_date", "edit_goal_milestones"]:
                if key in st.session_state:
                    del st.session_state[key]
            
            st.rerun()

# Goal Analytics tab
with tab3:
    st.subheader("Goal Progress Overview")
    
    # Goal progress chart
    active_goals = [goal for goal in st.session_state.get("goals", []) 
                   if not goal.get("completed", False)]
    
    if active_goals:
        progress_chart = goal_progress_chart(active_goals)
        
        if progress_chart:
            st.plotly_chart(progress_chart, use_container_width=True)
        else:
            st.info("Not enough data to generate the progress chart.")
        
        # Display completion statistics
        all_goals = st.session_state.get("goals", [])
        completed_goals = [goal for goal in all_goals if goal.get("completed", False)]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Goals", len(all_goals))
        
        with col2:
            st.metric("Completed Goals", len(completed_goals))
        
        with col3:
            completion_rate = int((len(completed_goals) / len(all_goals)) * 100) if all_goals else 0
            st.metric("Completion Rate", f"{completion_rate}%")
        
        # Display goal completion time statistics
        if completed_goals:
            st.subheader("Goal Completion Time")
            
            completion_times = []
            for goal in completed_goals:
                if goal.get("completed_at") and goal.get("created_at"):
                    created = datetime.fromisoformat(goal["created_at"])
                    completed = datetime.fromisoformat(goal["completed_at"])
                    days_to_complete = (completed - created).days
                    
                    completion_times.append({
                        "goal": goal["title"],
                        "days": days_to_complete
                    })
            
            if completion_times:
                df = pd.DataFrame(completion_times)
                df = df.sort_values("days")
                
                # Calculate statistics
                avg_days = df["days"].mean()
                min_days = df["days"].min()
                max_days = df["days"].max()
                
                st.write(f"On average, you complete goals in **{avg_days:.1f} days**.")
                st.write(f"Your fastest goal completion was **{min_days} days**, and your longest was **{max_days} days**.")
                
                # Create a bar chart for goal completion times
                import altair as alt
                
                chart = alt.Chart(df).mark_bar().encode(
                    x=alt.X('goal:N', title='Goal', sort='-y'),
                    y=alt.Y('days:Q', title='Days to Complete')
                ).properties(
                    title='Days to Complete Each Goal',
                    height=300
                )
                
                st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No active goals found. Add some goals to see analytics.")
    
    # Category distribution
    st.subheader("Goals by Category")
    
    all_goals = st.session_state.get("goals", [])
    if all_goals and categories:
        category_counts = {}
        
        for goal in all_goals:
            category_id = goal.get("category_id")
            if category_id:
                category = next((c for c in categories if c["id"] == category_id), None)
                if category:
                    category_name = category["name"]
                    if category_name not in category_counts:
                        category_counts[category_name] = {"total": 0, "completed": 0}
                    
                    category_counts[category_name]["total"] += 1
                    if goal.get("completed", False):
                        category_counts[category_name]["completed"] += 1
        
        if category_counts:
            df = pd.DataFrame([
                {
                    "category": category,
                    "total": stats["total"],
                    "completed": stats["completed"]
                }
                for category, stats in category_counts.items()
            ])
            
            import plotly.express as px
            
            fig = px.bar(
                df,
                x="category",
                y=["completed", "total"],
                title="Goals by Category",
                labels={"value": "Number of Goals", "category": "Category"},
                height=400,
                barmode="group"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No categorized goals found.")
    else:
        st.info("No goals or categories found. Add some to see analytics.")
