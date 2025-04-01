import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import altair as alt
import pandas as pd
from datetime import datetime, timedelta

def task_completion_chart(tasks):
    """Generate a chart showing task completion rates over time"""
    if not tasks:
        return None
    
    # Prepare the data
    completed_tasks = [task for task in tasks if task.get("completed", False)]
    
    if not completed_tasks:
        return None
    
    # Group by completion date
    completion_dates = {}
    for task in completed_tasks:
        completion_date = datetime.fromisoformat(task.get("completed_at", task.get("created_at"))).date()
        completion_dates[completion_date] = completion_dates.get(completion_date, 0) + 1
    
    # Create a pandas dataframe
    df = pd.DataFrame([
        {"date": date, "completed_tasks": count}
        for date, count in completion_dates.items()
    ])
    
    # Sort by date
    df = df.sort_values("date")
    
    # Create a cumulative sum column
    df["cumulative_completed"] = df["completed_tasks"].cumsum()
    
    # Create the chart
    chart = alt.Chart(df).mark_line(point=True).encode(
        x=alt.X('date:T', title='Date'),
        y=alt.Y('completed_tasks:Q', title='Tasks Completed'),
        tooltip=['date:T', 'completed_tasks:Q']
    ).properties(
        title='Tasks Completed Over Time',
        width=600,
        height=300
    )
    
    return chart

def task_completion_by_category(tasks, categories):
    """Generate a chart showing task completion by category"""
    if not tasks or not categories:
        return None
    
    # Create a map of category_id to name
    category_map = {c["id"]: c["name"] for c in categories}
    
    # Group tasks by category
    category_stats = {}
    for task in tasks:
        category_id = task.get("category_id")
        if not category_id or category_id not in category_map:
            continue
            
        category_name = category_map[category_id]
        
        if category_name not in category_stats:
            category_stats[category_name] = {"completed": 0, "total": 0}
        
        category_stats[category_name]["total"] += 1
        if task.get("completed", False):
            category_stats[category_name]["completed"] += 1
    
    # Create a pandas dataframe
    df = pd.DataFrame([
        {
            "category": category,
            "completed": stats["completed"],
            "incomplete": stats["total"] - stats["completed"],
            "completion_rate": round(stats["completed"] / stats["total"] * 100, 1) if stats["total"] > 0 else 0
        }
        for category, stats in category_stats.items()
    ])
    
    if df.empty:
        return None
    
    # Create the chart
    fig = px.bar(
        df,
        x="category",
        y=["completed", "incomplete"],
        title="Task Completion by Category",
        labels={"value": "Number of Tasks", "category": "Category", "variable": "Status"},
        height=400,
        barmode="stack"
    )
    
    return fig

def priority_matrix_chart(tasks):
    """Generate a quadrant chart showing tasks by importance and urgency (Eisenhower matrix)"""
    if not tasks:
        return None
    
    # Filter for incomplete tasks
    incomplete_tasks = [task for task in tasks if not task.get("completed", False)]
    
    if not incomplete_tasks:
        return None
    
    # Create a pandas dataframe
    df = pd.DataFrame([
        {
            "title": task["title"],
            "importance": task.get("importance", 3),
            "urgency": task.get("urgency", 3),
            "id": task["id"]
        }
        for task in incomplete_tasks
    ])
    
    # Create a scatter plot
    fig = px.scatter(
        df,
        x="urgency",
        y="importance",
        text="title",
        custom_data=["id"],
        title="Priority Matrix (Eisenhower Matrix)",
        labels={"urgency": "Urgency", "importance": "Importance"},
        height=500
    )
    
    # Add quadrant lines
    fig.add_hline(y=3, line_dash="dash", line_color="gray")
    fig.add_vline(x=3, line_dash="dash", line_color="gray")
    
    # Add quadrant labels
    fig.add_annotation(x=4.5, y=4.5, text="Important & Urgent<br>DO", showarrow=False, font=dict(size=12))
    fig.add_annotation(x=1.5, y=4.5, text="Important & Not Urgent<br>SCHEDULE", showarrow=False, font=dict(size=12))
    fig.add_annotation(x=4.5, y=1.5, text="Not Important & Urgent<br>DELEGATE", showarrow=False, font=dict(size=12))
    fig.add_annotation(x=1.5, y=1.5, text="Not Important & Not Urgent<br>ELIMINATE", showarrow=False, font=dict(size=12))
    
    # Set axis ranges
    fig.update_layout(
        xaxis=dict(range=[0, 6], tickvals=[1, 2, 3, 4, 5]),
        yaxis=dict(range=[0, 6], tickvals=[1, 2, 3, 4, 5])
    )
    
    return fig

def habit_streak_chart(habits):
    """Generate a chart showing habit streaks"""
    if not habits:
        return None
    
    # Create a pandas dataframe
    df = pd.DataFrame([
        {
            "habit": habit["title"],
            "current_streak": habit.get("current_streak", 0),
            "best_streak": habit.get("best_streak", 0)
        }
        for habit in habits
    ])
    
    if df.empty:
        return None
    
    # Create the chart
    fig = px.bar(
        df,
        x="habit",
        y=["current_streak", "best_streak"],
        title="Habit Streaks",
        labels={"value": "Days", "habit": "Habit", "variable": "Streak Type"},
        height=400,
        barmode="group"
    )
    
    return fig

def habit_heatmap(habit, start_date=None, end_date=None):
    """Generate a heatmap showing habit check-ins for a specific habit"""
    if not habit or "check_ins" not in habit or not habit["check_ins"]:
        return None
    
    # Set default date range if not specified
    if not end_date:
        end_date = datetime.now().date()
    if not start_date:
        start_date = end_date - timedelta(days=60)  # Show ~2 months by default
    
    # Parse check-in dates
    check_in_dates = [datetime.fromisoformat(date_str).date() for date_str in habit["check_ins"]]
    
    # Create a date range
    date_range = pd.date_range(start=start_date, end=end_date)
    
    # Create a dataframe with all dates in range
    df = pd.DataFrame(date_range, columns=["date"])
    df["date"] = df["date"].dt.date
    
    # Add a column indicating if habit was checked on each date
    df["checked"] = df["date"].isin(check_in_dates)
    df["checked_numeric"] = df["checked"].astype(int)
    
    # Add columns for week and weekday
    df["weekday"] = df["date"].apply(lambda d: d.strftime("%a"))
    df["week"] = df["date"].apply(lambda d: d.isocalendar()[1])
    
    # Create the heatmap
    fig = go.Figure(data=go.Heatmap(
        z=df["checked_numeric"],
        x=df["date"],
        y=df["weekday"],
        colorscale=[[0, 'lightgray'], [1, 'green']],
        showscale=False
    ))
    
    fig.update_layout(
        title=f"Habit Tracking: {habit['title']}",
        xaxis_title="Date",
        yaxis_title="Day of Week",
        height=300
    )
    
    return fig

def goal_progress_chart(goals):
    """Generate a chart showing progress towards goals"""
    if not goals:
        return None
    
    # Create a pandas dataframe
    df = pd.DataFrame([
        {
            "goal": goal["title"],
            "progress": goal.get("progress", 0),
            "remaining": 100 - goal.get("progress", 0)
        }
        for goal in goals
        if not goal.get("completed", False)  # Only include incomplete goals
    ])
    
    if df.empty:
        return None
    
    # Create the chart
    fig = px.bar(
        df,
        x="goal",
        y=["progress", "remaining"],
        title="Goal Progress",
        labels={"value": "Percentage", "goal": "Goal", "variable": "Status"},
        height=400,
        barmode="stack",
        color_discrete_map={"progress": "green", "remaining": "lightgray"}
    )
    
    # Add a line at 100%
    fig.add_hline(y=100, line_dash="dash", line_color="gray")
    
    return fig

def time_distribution_chart(calendar_events, categories):
    """Generate a chart showing time distribution across categories"""
    if not calendar_events or not categories:
        return None
    
    # Create a map of category_id to name and color
    category_map = {c["id"]: {"name": c["name"], "color": c["color"]} for c in categories}
    
    # Group events by category
    category_durations = {}
    for event in calendar_events:
        category_id = event.get("category_id")
        if not category_id or category_id not in category_map:
            continue
            
        category_name = category_map[category_id]["name"]
        
        # Calculate event duration in hours
        try:
            start_time = datetime.fromisoformat(event["start_time"])
            end_time = datetime.fromisoformat(event["end_time"])
            duration = (end_time - start_time).total_seconds() / 3600  # Convert to hours
        except (ValueError, TypeError, KeyError):
            continue
        
        if category_name not in category_durations:
            category_durations[category_name] = 0
        
        category_durations[category_name] += duration
    
    # Create a pandas dataframe
    df = pd.DataFrame([
        {"category": category, "hours": duration}
        for category, duration in category_durations.items()
    ])
    
    if df.empty:
        return None
    
    # Create the chart
    fig = px.pie(
        df,
        values="hours",
        names="category",
        title="Time Distribution by Category",
        height=400
    )
    
    # Update colors based on category colors
    category_colors = {
        category_map[cat_id]["name"]: category_map[cat_id]["color"]
        for cat_id in category_map
        if category_map[cat_id]["name"] in df["category"].values
    }
    
    fig.update_traces(marker=dict(colors=[category_colors.get(cat, "#808080") for cat in df["category"]]))
    
    return fig

def productivity_by_hour_chart(tasks):
    """Generate a chart showing task completion by hour of day"""
    if not tasks:
        return None
    
    # Filter for completed tasks with completion timestamp
    completed_tasks = [
        task for task in tasks 
        if task.get("completed", False) and "completed_at" in task
    ]
    
    if not completed_tasks:
        return None
    
    # Group by hour of completion
    hour_counts = {}
    for task in completed_tasks:
        try:
            completion_time = datetime.fromisoformat(task["completed_at"])
            hour = completion_time.hour
            
            if hour not in hour_counts:
                hour_counts[hour] = 0
            
            hour_counts[hour] += 1
        except (ValueError, TypeError):
            continue
    
    # Create a pandas dataframe with all hours
    df = pd.DataFrame([
        {"hour": hour, "completed_tasks": hour_counts.get(hour, 0)}
        for hour in range(24)
    ])
    
    # Create the chart
    fig = px.bar(
        df,
        x="hour",
        y="completed_tasks",
        title="Task Completion by Hour of Day",
        labels={"hour": "Hour of Day", "completed_tasks": "Tasks Completed"},
        height=400
    )
    
    # Format x-axis to show hours in 12-hour format
    fig.update_xaxes(
        tickvals=list(range(24)),
        ticktext=[f"{h%12 if h%12 else 12} {'AM' if h<12 else 'PM'}" for h in range(24)]
    )
    
    return fig
