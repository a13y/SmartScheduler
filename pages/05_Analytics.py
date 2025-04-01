import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import altair as alt
from datetime import datetime, timedelta
from utils.data_manager import initialize_session_state
from utils.visualization import (
    task_completion_chart,
    task_completion_by_category,
    priority_matrix_chart,
    habit_streak_chart,
    goal_progress_chart,
    time_distribution_chart,
    productivity_by_hour_chart
)
from assets.icons import get_icon

# Initialize session state
initialize_session_state()

# Page configuration
st.set_page_config(
    page_title="Analytics | AI Planner",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Analytics & Insights")
st.write("Gain insights into your productivity, habits, and goal progress with comprehensive analytics.")

# Sidebar for time range selection
with st.sidebar:
    st.header("Analytics Settings")
    
    # Time range selection
    time_range = st.selectbox(
        "Time Range",
        options=["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time", "Custom Range"],
        index=1
    )
    
    # Custom date range
    if time_range == "Custom Range":
        start_date = st.date_input(
            "Start Date",
            value=datetime.now().date() - timedelta(days=30)
        )
        end_date = st.date_input(
            "End Date",
            value=datetime.now().date()
        )
        
        if start_date > end_date:
            st.error("Start date must be before end date.")
    else:
        # Calculate date range based on selection
        end_date = datetime.now().date()
        
        if time_range == "Last 7 Days":
            start_date = end_date - timedelta(days=7)
        elif time_range == "Last 30 Days":
            start_date = end_date - timedelta(days=30)
        elif time_range == "Last 90 Days":
            start_date = end_date - timedelta(days=90)
        else:  # All Time
            # Use the earliest recorded data or default to 1 year
            all_dates = []
            
            # Extract dates from tasks
            for task in st.session_state.get("tasks", []):
                if "created_at" in task:
                    try:
                        all_dates.append(datetime.fromisoformat(task["created_at"]).date())
                    except (ValueError, TypeError):
                        pass
            
            # Extract dates from goals
            for goal in st.session_state.get("goals", []):
                if "created_at" in goal:
                    try:
                        all_dates.append(datetime.fromisoformat(goal["created_at"]).date())
                    except (ValueError, TypeError):
                        pass
            
            # Extract dates from habits
            for habit in st.session_state.get("habits", []):
                if "created_at" in habit:
                    try:
                        all_dates.append(datetime.fromisoformat(habit["created_at"]).date())
                    except (ValueError, TypeError):
                        pass
            
            if all_dates:
                start_date = min(all_dates)
            else:
                start_date = end_date - timedelta(days=365)
    
    # Data filters
    st.header("Filters")
    
    # Category filter
    categories = st.session_state.get("categories", [])
    category_options = ["All Categories"] + [c["name"] for c in categories]
    
    selected_category = st.multiselect(
        "Categories",
        options=category_options,
        default=["All Categories"]
    )
    
    if "All Categories" in selected_category:
        # If "All Categories" is selected, use all categories
        category_filter = [c["id"] for c in categories]
    else:
        # Otherwise, use selected categories
        category_filter = [
            c["id"] for c in categories 
            if c["name"] in selected_category
        ]

# Main content with dashboard sections
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Task Analysis", "Goals & Habits", "Time Management"])

# Overview tab
with tab1:
    st.subheader("Dashboard Overview")
    
    # Filter tasks, goals, habits, and events based on date range
    tasks = st.session_state.get("tasks", [])
    goals = st.session_state.get("goals", [])
    habits = st.session_state.get("habits", [])
    events = st.session_state.get("calendar_events", [])
    
    filtered_tasks = []
    for task in tasks:
        # Check if created_at is within date range
        if "created_at" in task:
            try:
                created_date = datetime.fromisoformat(task["created_at"]).date()
                if start_date <= created_date <= end_date:
                    # Apply category filter if available
                    if not category_filter or task.get("category_id") in category_filter:
                        filtered_tasks.append(task)
            except (ValueError, TypeError):
                pass
    
    filtered_goals = []
    for goal in goals:
        # Check if created_at is within date range
        if "created_at" in goal:
            try:
                created_date = datetime.fromisoformat(goal["created_at"]).date()
                if start_date <= created_date <= end_date:
                    # Apply category filter if available
                    if not category_filter or goal.get("category_id") in category_filter:
                        filtered_goals.append(goal)
            except (ValueError, TypeError):
                pass
    
    filtered_habits = []
    for habit in habits:
        # Include habits with check-ins within date range
        if "check_ins" in habit:
            habit_in_range = False
            for check_in in habit["check_ins"]:
                try:
                    check_date = datetime.fromisoformat(check_in).date()
                    if start_date <= check_date <= end_date:
                        habit_in_range = True
                        break
                except (ValueError, TypeError):
                    pass
            
            if habit_in_range:
                # Apply category filter if available
                if not category_filter or habit.get("category_id") in category_filter:
                    filtered_habits.append(habit)
    
    filtered_events = []
    for event in events:
        # Check if start_time is within date range
        if "start_time" in event:
            try:
                start_time = datetime.fromisoformat(event["start_time"]).date()
                if start_date <= start_time <= end_date:
                    # Apply category filter if available
                    if not category_filter or event.get("category_id") in category_filter:
                        filtered_events.append(event)
            except (ValueError, TypeError):
                pass
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        completed_tasks = sum(1 for task in filtered_tasks if task.get("completed", False))
        total_tasks = len(filtered_tasks)
        completion_rate = f"{int((completed_tasks / total_tasks) * 100)}%" if total_tasks > 0 else "0%"
        
        st.metric(
            "Task Completion",
            completion_rate,
            f"{completed_tasks}/{total_tasks} tasks"
        )
    
    with col2:
        completed_goals = sum(1 for goal in filtered_goals if goal.get("completed", False))
        total_goals = len(filtered_goals)
        goal_rate = f"{int((completed_goals / total_goals) * 100)}%" if total_goals > 0 else "0%"
        
        st.metric(
            "Goal Completion",
            goal_rate,
            f"{completed_goals}/{total_goals} goals"
        )
    
    with col3:
        if filtered_habits:
            avg_streak = sum(habit.get("current_streak", 0) for habit in filtered_habits) / len(filtered_habits)
            max_streak = max((habit.get("current_streak", 0) for habit in filtered_habits), default=0)
            
            st.metric(
                "Average Habit Streak",
                f"{avg_streak:.1f} days",
                f"Max: {max_streak} days"
            )
        else:
            st.metric("Average Habit Streak", "0 days")
    
    with col4:
        total_events = len(filtered_events)
        
        # Calculate events per day
        days_in_range = (end_date - start_date).days + 1
        events_per_day = total_events / days_in_range if days_in_range > 0 else 0
        
        st.metric(
            "Calendar Events",
            total_events,
            f"{events_per_day:.1f} per day"
        )
    
    # Summary charts
    st.markdown("---")
    
    # Task trend chart
    task_trend = task_completion_chart(filtered_tasks)
    if task_trend:
        st.subheader("Task Completion Trend")
        st.altair_chart(task_trend, use_container_width=True)
    
    # Time distribution chart
    col1, col2 = st.columns(2)
    
    with col1:
        time_dist = time_distribution_chart(filtered_events, categories)
        if time_dist:
            st.subheader("Time Distribution by Category")
            st.plotly_chart(time_dist, use_container_width=True)
    
    with col2:
        category_comp = task_completion_by_category(filtered_tasks, categories)
        if category_comp:
            st.subheader("Task Completion by Category")
            st.plotly_chart(category_comp, use_container_width=True)
    
    # AI Insights
    st.markdown("---")
    st.subheader("AI Insights")
    
    # Generate insights based on the data
    insights = []
    
    # Productivity insights
    if filtered_tasks:
        # Check productivity by day of week
        day_productivity = {}
        for task in filtered_tasks:
            if task.get("completed", False) and "completed_at" in task:
                try:
                    completed_date = datetime.fromisoformat(task["completed_at"])
                    day_of_week = completed_date.strftime("%A")
                    
                    if day_of_week not in day_productivity:
                        day_productivity[day_of_week] = 0
                    
                    day_productivity[day_of_week] += 1
                except (ValueError, TypeError):
                    pass
        
        if day_productivity:
            most_productive_day = max(day_productivity.items(), key=lambda x: x[1])
            insights.append(f"You're most productive on **{most_productive_day[0]}**, completing {most_productive_day[1]} tasks.")
    
    # Task completion rate trend
    if len(filtered_tasks) >= 10:
        # Get completion rate over time
        completion_dates = {}
        for task in filtered_tasks:
            if task.get("completed", False) and "completed_at" in task:
                try:
                    completed_date = datetime.fromisoformat(task["completed_at"]).date()
                    date_str = completed_date.isoformat()
                    
                    if date_str not in completion_dates:
                        completion_dates[date_str] = {"completed": 0, "total": 0}
                    
                    completion_dates[date_str]["completed"] += 1
                except (ValueError, TypeError):
                    pass
        
        # Count total tasks by created date
        for task in filtered_tasks:
            if "created_at" in task:
                try:
                    created_date = datetime.fromisoformat(task["created_at"]).date()
                    date_str = created_date.isoformat()
                    
                    if date_str not in completion_dates:
                        completion_dates[date_str] = {"completed": 0, "total": 0}
                    
                    completion_dates[date_str]["total"] += 1
                except (ValueError, TypeError):
                    pass
        
        # Calculate completion rates
        dates = sorted(completion_dates.keys())
        rates = []
        
        for date_str in dates:
            data = completion_dates[date_str]
            if data["total"] > 0:
                rate = (data["completed"] / data["total"]) * 100
                rates.append(rate)
        
        if len(rates) >= 3:
            # Check if completion rate is trending up or down
            trend = "increasing" if rates[-1] > rates[0] else "decreasing"
            insights.append(f"Your task completion rate is **{trend}** over time.")
    
    # Habit streak insights
    if filtered_habits:
        # Find habit with longest streak
        longest_streak_habit = max(filtered_habits, key=lambda x: x.get("current_streak", 0))
        if longest_streak_habit.get("current_streak", 0) > 0:
            insights.append(f"Your longest current habit streak is **{longest_streak_habit['current_streak']} days** for {longest_streak_habit['title']}.")
        
        # Find habits with broken streaks
        broken_streaks = []
        for habit in filtered_habits:
            if "check_ins" in habit and habit.get("current_streak", 0) < habit.get("best_streak", 0):
                broken_streaks.append(habit)
        
        if broken_streaks:
            habits_to_rebuild = min(3, len(broken_streaks))
            habit_names = [h["title"] for h in sorted(broken_streaks, key=lambda x: x.get("best_streak", 0) - x.get("current_streak", 0), reverse=True)[:habits_to_rebuild]]
            insights.append(f"Consider rebuilding your streak for: **{', '.join(habit_names)}**")
    
    # Category focus insights
    if filtered_tasks and categories:
        # Calculate time spent per category
        category_time = {}
        for task in filtered_tasks:
            category_id = task.get("category_id")
            if category_id:
                category = next((c for c in categories if c["id"] == category_id), None)
                if category:
                    category_name = category["name"]
                    if category_name not in category_time:
                        category_time[category_name] = 0
                    
                    # Estimate time based on importance/urgency
                    importance = task.get("importance", 3)
                    urgency = task.get("urgency", 3)
                    estimated_time = (importance + urgency) * 15  # minutes
                    
                    category_time[category_name] += estimated_time
        
        if category_time:
            # Find category with most time
            most_time_category = max(category_time.items(), key=lambda x: x[1])
            most_time_hours = most_time_category[1] / 60
            
            insights.append(f"You've spent the most time on **{most_time_category[0]}** tasks (approximately {most_time_hours:.1f} hours).")
    
    # Display insights
    if insights:
        for i, insight in enumerate(insights):
            st.markdown(f"#### Insight {i+1}: {insight}")
    else:
        st.info("Add more data to generate AI insights about your productivity patterns.")

# Task Analysis tab
with tab2:
    st.subheader("Task Analysis")
    
    # Filter tasks based on date range
    filtered_tasks = []
    for task in st.session_state.get("tasks", []):
        # Check if created_at is within date range
        if "created_at" in task:
            try:
                created_date = datetime.fromisoformat(task["created_at"]).date()
                if start_date <= created_date <= end_date:
                    # Apply category filter
                    if not category_filter or task.get("category_id") in category_filter:
                        filtered_tasks.append(task)
            except (ValueError, TypeError):
                pass
    
    # Task metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_tasks = len(filtered_tasks)
        completed_tasks = sum(1 for task in filtered_tasks if task.get("completed", False))
        completion_rate = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
        
        st.metric("Task Completion Rate", f"{completion_rate:.1f}%")
    
    with col2:
        # Calculate average time to complete tasks
        completion_times = []
        for task in filtered_tasks:
            if task.get("completed", False) and "created_at" in task and "completed_at" in task:
                try:
                    created = datetime.fromisoformat(task["created_at"])
                    completed = datetime.fromisoformat(task["completed_at"])
                    hours_to_complete = (completed - created).total_seconds() / 3600
                    completion_times.append(hours_to_complete)
                except (ValueError, TypeError):
                    pass
        
        avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else 0
        
        st.metric("Avg. Completion Time", f"{avg_completion_time:.1f} hours")
    
    with col3:
        # Calculate overdue tasks
        overdue_tasks = 0
        for task in filtered_tasks:
            if not task.get("completed", False) and "due_date" in task and task["due_date"]:
                try:
                    due_date = datetime.fromisoformat(task["due_date"]).date()
                    if due_date < datetime.now().date():
                        overdue_tasks += 1
                except (ValueError, TypeError):
                    pass
        
        st.metric("Overdue Tasks", overdue_tasks)
    
    # Priority matrix chart
    matrix_chart = priority_matrix_chart(filtered_tasks)
    if matrix_chart:
        st.subheader("Priority Matrix")
        st.plotly_chart(matrix_chart, use_container_width=True)
    
    # Task completion by hour
    hour_chart = productivity_by_hour_chart(filtered_tasks)
    if hour_chart:
        st.subheader("Task Completion by Hour of Day")
        st.plotly_chart(hour_chart, use_container_width=True)
    
    # Task creation vs completion over time
    st.subheader("Task Creation vs Completion Over Time")
    
    # Prepare data
    date_data = {}
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.isoformat()
        date_data[date_str] = {"created": 0, "completed": 0}
        current_date += timedelta(days=1)
    
    # Count created tasks by date
    for task in filtered_tasks:
        if "created_at" in task:
            try:
                created_date = datetime.fromisoformat(task["created_at"]).date()
                date_str = created_date.isoformat()
                if date_str in date_data:
                    date_data[date_str]["created"] += 1
            except (ValueError, TypeError):
                pass
    
    # Count completed tasks by date
    for task in filtered_tasks:
        if task.get("completed", False) and "completed_at" in task:
            try:
                completed_date = datetime.fromisoformat(task["completed_at"]).date()
                date_str = completed_date.isoformat()
                if date_str in date_data:
                    date_data[date_str]["completed"] += 1
            except (ValueError, TypeError):
                pass
    
    # Convert to dataframe
    df = pd.DataFrame([
        {"date": date, "metric": "Created", "count": data["created"]}
        for date, data in date_data.items()
    ] + [
        {"date": date, "metric": "Completed", "count": data["completed"]}
        for date, data in date_data.items()
    ])
    
    # Create chart
    if not df.empty:
        chart = alt.Chart(df).mark_line().encode(
            x=alt.X('date:T', title='Date'),
            y=alt.Y('count:Q', title='Number of Tasks'),
            color=alt.Color('metric:N', scale=alt.Scale(domain=['Created', 'Completed'], range=['#5470c6', '#91cc75']))
        ).properties(
            height=300
        )
        
        st.altair_chart(chart, use_container_width=True)
    
    # Task completion by category
    category_chart = task_completion_by_category(filtered_tasks, categories)
    if category_chart:
        st.subheader("Task Completion by Category")
        st.plotly_chart(category_chart, use_container_width=True)
    
    # Task distribution by importance and urgency
    st.subheader("Task Distribution by Importance and Urgency")
    
    # Prepare data
    importance_urgency_data = {}
    for i in range(1, 6):
        for j in range(1, 6):
            importance_urgency_data[(i, j)] = 0
    
    for task in filtered_tasks:
        importance = task.get("importance", 3)
        urgency = task.get("urgency", 3)
        importance_urgency_data[(importance, urgency)] += 1
    
    # Convert to dataframe
    df = pd.DataFrame([
        {"importance": imp, "urgency": urg, "count": count}
        for (imp, urg), count in importance_urgency_data.items()
    ])
    
    if not df.empty:
        fig = px.density_heatmap(
            df,
            x="urgency",
            y="importance",
            z="count",
            title="Task Distribution by Importance and Urgency",
            labels={"urgency": "Urgency", "importance": "Importance", "count": "Number of Tasks"},
            height=400
        )
        
        # Customize layout
        fig.update_layout(
            xaxis=dict(tickvals=[1, 2, 3, 4, 5]),
            yaxis=dict(tickvals=[1, 2, 3, 4, 5])
        )
        
        st.plotly_chart(fig, use_container_width=True)

# Goals & Habits tab
with tab3:
    st.subheader("Goals & Habits Analysis")
    
    # Filter goals and habits based on date range
    filtered_goals = []
    for goal in st.session_state.get("goals", []):
        # Check if created_at is within date range
        if "created_at" in goal:
            try:
                created_date = datetime.fromisoformat(goal["created_at"]).date()
                if start_date <= created_date <= end_date:
                    # Apply category filter
                    if not category_filter or goal.get("category_id") in category_filter:
                        filtered_goals.append(goal)
            except (ValueError, TypeError):
                pass
    
    filtered_habits = []
    for habit in st.session_state.get("habits", []):
        # Include habits with check-ins within date range
        if "check_ins" in habit:
            habit_in_range = False
            filtered_checkins = []
            
            for check_in in habit["check_ins"]:
                try:
                    check_date = datetime.fromisoformat(check_in).date()
                    if start_date <= check_date <= end_date:
                        habit_in_range = True
                        filtered_checkins.append(check_in)
                except (ValueError, TypeError):
                    pass
            
            if habit_in_range:
                # Apply category filter
                if not category_filter or habit.get("category_id") in category_filter:
                    habit_copy = habit.copy()
                    habit_copy["check_ins"] = filtered_checkins
                    filtered_habits.append(habit_copy)
    
    # Goals progress chart
    progress_chart = goal_progress_chart(filtered_goals)
    if progress_chart:
        st.subheader("Goal Progress")
        st.plotly_chart(progress_chart, use_container_width=True)
    
    # Habit streak chart
    streak_chart = habit_streak_chart(filtered_habits)
    if streak_chart:
        st.subheader("Habit Streaks")
        st.plotly_chart(streak_chart, use_container_width=True)
    
    # Habit consistency calendar
    st.subheader("Habit Consistency")
    
    # Create combined heatmap for all habits
    if filtered_habits:
        # Aggregate all check-ins
        all_checkins = []
        for habit in filtered_habits:
            all_checkins.extend(habit.get("check_ins", []))
        
        # Count check-ins per day
        checkin_counts = {}
        for checkin in all_checkins:
            try:
                check_date = datetime.fromisoformat(checkin).date()
                date_str = check_date.isoformat()
                if date_str not in checkin_counts:
                    checkin_counts[date_str] = 0
                checkin_counts[date_str] += 1
            except (ValueError, TypeError):
                pass
        
        # Create date range
        date_range = []
        current_date = start_date
        while current_date <= end_date:
            date_range.append(current_date)
            current_date += timedelta(days=1)
        
        # Create dataframe
        df = pd.DataFrame([
            {
                "date": date,
                "count": checkin_counts.get(date.isoformat(), 0),
                "weekday": date.strftime("%a"),
                "week": date.isocalendar()[1]
            }
            for date in date_range
        ])
        
        if not df.empty:
            fig = go.Figure(data=go.Heatmap(
                z=df["count"],
                x=df["date"],
                y=df["weekday"],
                colorscale="Greens",
                showscale=True
            ))
            
            fig.update_layout(
                title="Habit Check-ins Heatmap",
                height=300,
                yaxis=dict(categoryorder="array", categoryarray=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # Goals completion time analysis
    st.subheader("Goal Completion Time Analysis")
    
    completed_goals = [goal for goal in filtered_goals if goal.get("completed", False)]
    
    if completed_goals:
        completion_times = []
        for goal in completed_goals:
            if "created_at" in goal and "completed_at" in goal:
                try:
                    created = datetime.fromisoformat(goal["created_at"])
                    completed = datetime.fromisoformat(goal["completed_at"])
                    days_to_complete = (completed - created).days
                    
                    completion_times.append({
                        "goal": goal["title"],
                        "days": days_to_complete,
                        "category_id": goal.get("category_id")
                    })
                except (ValueError, TypeError):
                    pass
        
        if completion_times:
            df = pd.DataFrame(completion_times)
            
            # Add category information
            df["category"] = df["category_id"].apply(
                lambda x: next((c["name"] for c in categories if c["id"] == x), "Uncategorized")
            )
            
            # Create chart
            chart = alt.Chart(df).mark_bar().encode(
                x=alt.X('goal:N', title='Goal', sort='-y'),
                y=alt.Y('days:Q', title='Days to Complete'),
                color=alt.Color('category:N', title='Category')
            ).properties(
                height=300
            )
            
            st.altair_chart(chart, use_container_width=True)
            
            # Calculate and display statistics
            avg_completion_time = df["days"].mean()
            fastest_completion = df.loc[df["days"].idxmin()]
            slowest_completion = df.loc[df["days"].idxmax()]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Avg. Goal Completion Time", f"{avg_completion_time:.1f} days")
            
            with col2:
                st.metric("Fastest Completion", f"{fastest_completion['days']} days", 
                         fastest_completion["goal"])
            
            with col3:
                st.metric("Slowest Completion", f"{slowest_completion['days']} days",
                         slowest_completion["goal"])
    else:
        st.info("No completed goals in the selected time range.")

# Time Management tab
with tab4:
    st.subheader("Time Management Analysis")
    
    # Filter calendar events based on date range
    filtered_events = []
    for event in st.session_state.get("calendar_events", []):
        # Check if start_time is within date range
        if "start_time" in event and "end_time" in event:
            try:
                start_time = datetime.fromisoformat(event["start_time"])
                end_time = datetime.fromisoformat(event["end_time"])
                
                # Check if event falls within date range
                event_start_date = start_time.date()
                event_end_date = end_time.date()
                
                if (start_date <= event_start_date <= end_date) or \
                   (start_date <= event_end_date <= end_date) or \
                   (event_start_date <= start_date and event_end_date >= end_date):
                    # Apply category filter
                    if not category_filter or event.get("category_id") in category_filter:
                        filtered_events.append(event)
            except (ValueError, TypeError):
                pass
    
    # Time distribution by category
    dist_chart = time_distribution_chart(filtered_events, categories)
    if dist_chart:
        st.plotly_chart(dist_chart, use_container_width=True)
    
    # Calculate time spent per day
    st.subheader("Time Allocated Per Day")
    
    if filtered_events:
        # Calculate hours per day
        day_hours = {}
        for event in filtered_events:
            try:
                start_time = datetime.fromisoformat(event["start_time"])
                end_time = datetime.fromisoformat(event["end_time"])
                
                event_date = start_time.date()
                date_str = event_date.isoformat()
                
                if start_date <= event_date <= end_date:
                    if date_str not in day_hours:
                        day_hours[date_str] = 0
                    
                    # Calculate duration in hours
                    duration = (end_time - start_time).total_seconds() / 3600
                    day_hours[date_str] += duration
            except (ValueError, TypeError):
                pass
        
        if day_hours:
            # Create dataframe
            df = pd.DataFrame([
                {"date": date, "hours": hours}
                for date, hours in day_hours.items()
            ])
            
            # Sort by date
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date")
            
            # Create chart
            chart = alt.Chart(df).mark_bar().encode(
                x=alt.X('date:T', title='Date'),
                y=alt.Y('hours:Q', title='Hours')
            ).properties(
                height=300
            )
            
            st.altair_chart(chart, use_container_width=True)
            
            # Calculate statistics
            avg_hours = df["hours"].mean()
            max_hours = df["hours"].max()
            max_date = df.loc[df["hours"].idxmax(), "date"].strftime("%Y-%m-%d")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Avg. Hours Scheduled Per Day", f"{avg_hours:.1f} hours")
            
            with col2:
                st.metric("Max Hours in a Day", f"{max_hours:.1f} hours", f"on {max_date}")
    
    # Time allocation by hour of day
    st.subheader("Time Allocation by Hour of Day")
    
    if filtered_events:
        # Count events by hour of day
        hour_counts = {hour: 0 for hour in range(24)}
        
        for event in filtered_events:
            try:
                start_time = datetime.fromisoformat(event["start_time"])
                end_time = datetime.fromisoformat(event["end_time"])
                
                # Count all hours this event spans
                current_hour = start_time.replace(minute=0, second=0, microsecond=0)
                while current_hour < end_time:
                    hour_counts[current_hour.hour] += 1
                    current_hour += timedelta(hours=1)
            except (ValueError, TypeError):
                pass
        
        # Create dataframe
        df = pd.DataFrame([
            {"hour": hour, "count": count}
            for hour, count in hour_counts.items()
        ])
        
        # Create chart
        fig = px.bar(
            df,
            x="hour",
            y="count",
            title="Number of Events by Hour of Day",
            labels={"hour": "Hour of Day", "count": "Number of Events"},
            height=400
        )
        
        # Format x-axis to show hours in 12-hour format
        fig.update_xaxes(
            tickvals=list(range(24)),
            ticktext=[f"{h%12 if h%12 else 12} {'AM' if h<12 else 'PM'}" for h in range(24)]
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Find peak hours
        busy_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        quiet_hours = sorted(hour_counts.items(), key=lambda x: x[1])[:3]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Busiest Hours")
            for hour, count in busy_hours:
                am_pm = "AM" if hour < 12 else "PM"
                hour_12 = hour % 12
                if hour_12 == 0:
                    hour_12 = 12
                st.write(f"**{hour_12} {am_pm}**: {count} events")
        
        with col2:
            st.subheader("Quietest Hours")
            for hour, count in quiet_hours:
                am_pm = "AM" if hour < 12 else "PM"
                hour_12 = hour % 12
                if hour_12 == 0:
                    hour_12 = 12
                st.write(f"**{hour_12} {am_pm}**: {count} events")
    
    # Free time analysis
    st.subheader("Free Time Analysis")
    
    if filtered_events:
        # Calculate free time per day (assuming 8-hour work day, 8 AM to 5 PM)
        work_hours = 9  # 8 AM to 5 PM
        free_time_per_day = {}
        
        # Initialize with full work days
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.isoformat()
            # Skip weekends
            if current_date.weekday() < 5:  # Monday to Friday
                free_time_per_day[date_str] = work_hours
            else:
                free_time_per_day[date_str] = 0
            current_date += timedelta(days=1)
        
        # Subtract event times during work hours
        for event in filtered_events:
            try:
                start_time = datetime.fromisoformat(event["start_time"])
                end_time = datetime.fromisoformat(event["end_time"])
                
                event_date = start_time.date()
                date_str = event_date.isoformat()
                
                # Skip if outside work day or on weekend
                if event_date.weekday() >= 5 or date_str not in free_time_per_day:
                    continue
                
                # Limit to work hours (8 AM to 5 PM)
                work_start = datetime.combine(event_date, datetime.min.time()) + timedelta(hours=8)
                work_end = datetime.combine(event_date, datetime.min.time()) + timedelta(hours=17)
                
                if end_time <= work_start or start_time >= work_end:
                    continue
                
                # Clip to work hours
                overlap_start = max(start_time, work_start)
                overlap_end = min(end_time, work_end)
                
                # Calculate overlap duration in hours
                overlap_duration = (overlap_end - overlap_start).total_seconds() / 3600
                
                # Subtract from free time
                free_time_per_day[date_str] -= overlap_duration
            except (ValueError, TypeError):
                pass
        
        # Create dataframe
        df = pd.DataFrame([
            {"date": date, "free_hours": max(0, hours)}  # Ensure no negative free time
            for date, hours in free_time_per_day.items()
            if hours > 0  # Only include work days
        ])
        
        if not df.empty:
            # Sort by date
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date")
            
            # Create chart
            chart = alt.Chart(df).mark_bar().encode(
                x=alt.X('date:T', title='Date'),
                y=alt.Y('free_hours:Q', title='Free Hours')
            ).properties(
                height=300
            )
            
            st.altair_chart(chart, use_container_width=True)
            
            # Calculate statistics
            avg_free_hours = df["free_hours"].mean()
            min_free_day = df.loc[df["free_hours"].idxmin()]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Avg. Free Time Per Work Day", f"{avg_free_hours:.1f} hours")
            
            with col2:
                st.metric("Busiest Work Day", f"{min_free_day['free_hours']:.1f} free hours", 
                         min_free_day["date"].strftime("%Y-%m-%d"))
