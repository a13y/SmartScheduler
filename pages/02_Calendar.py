import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import uuid
import calendar
from utils.data_manager import (
    initialize_session_state,
    save_user_data,
    add_calendar_event,
    update_calendar_event,
    delete_calendar_event
)
from utils.calendar_integration import (
    generate_month_view,
    generate_week_view,
    generate_day_view,
    import_ics_calendar,
    export_to_ics_calendar,
    get_google_auth_url,
    handle_google_auth_callback,
    sync_events_from_google
)
from utils.task_classifier import suggest_time_slot
from assets.icons import get_icon

# Initialize session state
initialize_session_state()

# Page configuration
st.set_page_config(
    page_title="Calendar | AI Planner",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Calendar")

# Sidebar filters and actions
with st.sidebar:
    st.header("Calendar Options")
    
    # View type
    view_options = ["Month", "Week", "Day", "Agenda"]
    selected_view = st.radio("View", options=view_options)
    
    # Date picker
    today = datetime.now().date()
    selected_date = st.date_input("Select Date", value=today)
    
    # Quick navigation
    st.write("---")
    st.subheader("Quick Navigation")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Today"):
            selected_date = today
            st.rerun()
    
    with col2:
        if st.button("Previous"):
            if selected_view == "Month":
                # Previous month
                if selected_date.month == 1:
                    selected_date = selected_date.replace(year=selected_date.year - 1, month=12, day=1)
                else:
                    selected_date = selected_date.replace(month=selected_date.month - 1, day=1)
            elif selected_view == "Week":
                # Previous week
                selected_date = selected_date - timedelta(days=7)
            else:
                # Previous day
                selected_date = selected_date - timedelta(days=1)
            st.rerun()
    
    with col3:
        if st.button("Next"):
            if selected_view == "Month":
                # Next month
                if selected_date.month == 12:
                    selected_date = selected_date.replace(year=selected_date.year + 1, month=1, day=1)
                else:
                    selected_date = selected_date.replace(month=selected_date.month + 1, day=1)
            elif selected_view == "Week":
                # Next week
                selected_date = selected_date + timedelta(days=7)
            else:
                # Next day
                selected_date = selected_date + timedelta(days=1)
            st.rerun()
    
    # Calendar integrations
    st.write("---")
    st.subheader("Import/Export")
    
    if st.button("Export Calendar (ICS)"):
        events = st.session_state.get("calendar_events", [])
        if events:
            ics_content = export_to_ics_calendar(events)
            st.download_button(
                label="Download ICS File",
                data=ics_content,
                file_name="ai_planner_calendar.ics",
                mime="text/calendar"
            )
        else:
            st.error("No events to export.")
    
    uploaded_file = st.file_uploader("Import ICS File", type=["ics"])
    if uploaded_file is not None:
        ics_content = uploaded_file.read().decode()
        imported_events = import_ics_calendar(ics_content)
        
        if imported_events:
            st.success(f"Successfully imported {len(imported_events)} events.")
            
            # Add imported events to session state
            for event in imported_events:
                if "id" in event and "title" in event and "start_time" in event and "end_time" in event:
                    # Check if event already exists
                    existing_events = st.session_state.get("calendar_events", [])
                    if not any(e.get("id") == event["id"] for e in existing_events):
                        add_calendar_event(
                            title=event["title"],
                            start_time=event["start_time"],
                            end_time=event["end_time"],
                            description=event.get("description", ""),
                            location=event.get("location", ""),
                            category_id=event.get("category_id")
                        )
            
            st.rerun()
        else:
            st.error("Failed to import events or no events found in the file.")
    
    # Google Calendar integration
    st.write("---")
    st.subheader("Google Calendar")
    
    # Check if already authenticated
    if st.session_state.get("google_calendar_token"):
        st.success("Connected to Google Calendar")
        
        if st.button("Sync with Google Calendar"):
            # Sync events
            access_token = st.session_state["google_calendar_token"].get("access_token")
            if access_token:
                synced_events = sync_events_from_google(access_token)
                
                if synced_events:
                    st.success(f"Synced {len(synced_events)} events from Google Calendar.")
                    
                    # Add synced events to session state
                    for event in synced_events:
                        if "id" in event and "title" in event and "start_time" in event and "end_time" in event:
                            # Check if event already exists
                            existing_events = st.session_state.get("calendar_events", [])
                            if not any(e.get("id") == event["id"] for e in existing_events):
                                add_calendar_event(
                                    title=event["title"],
                                    start_time=event["start_time"],
                                    end_time=event["end_time"],
                                    description=event.get("description", ""),
                                    location=event.get("location", ""),
                                    category_id=event.get("category_id")
                                )
                    
                    st.rerun()
                else:
                    st.error("Failed to sync events or no events found.")
        
        if st.button("Disconnect Google Calendar"):
            # Remove token
            if "google_calendar_token" in st.session_state:
                del st.session_state["google_calendar_token"]
            st.success("Disconnected from Google Calendar.")
            st.rerun()
    else:
        if st.button("Connect Google Calendar"):
            # Get auth URL
            auth_url = get_google_auth_url()
            st.markdown(f"[Click here to connect to Google Calendar]({auth_url})")
            st.session_state["awaiting_google_auth"] = True
        
        # Handle auth callback
        if st.session_state.get("awaiting_google_auth", False):
            auth_code = st.text_input("Enter the authorization code from Google")
            if auth_code:
                token = handle_google_auth_callback(auth_code)
                if token:
                    st.session_state["google_calendar_token"] = token
                    st.session_state["awaiting_google_auth"] = False
                    st.success("Successfully connected to Google Calendar!")
                    st.rerun()
                else:
                    st.error("Failed to authenticate with Google. Please try again.")

# Main content
tab1, tab2 = st.tabs(["View Calendar", "Add Event"])

# View Calendar tab
with tab1:
    # Get all calendar events
    all_events = st.session_state.get("calendar_events", [])
    
    # Month View
    if selected_view == "Month":
        st.subheader(f"{calendar.month_name[selected_date.month]} {selected_date.year}")
        
        # Generate month view data
        month_data = generate_month_view(selected_date.year, selected_date.month, all_events)
        
        # Create a table for the month view
        month_table = "<table style='width: 100%; border-collapse: collapse;'>"
        
        # Add weekday headers
        month_table += "<tr>"
        for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
            month_table += f"<th style='border: 1px solid #ddd; padding: 8px; text-align: center;'>{day}</th>"
        month_table += "</tr>"
        
        # Add weeks
        for week in month_data["weeks"]:
            month_table += "<tr>"
            
            for day_data in week:
                day = day_data["day"]
                events = day_data["events"]
                
                # Set cell style
                cell_style = "border: 1px solid #ddd; vertical-align: top; height: 100px; padding: 5px;"
                
                # Add cell for the day
                if day is None:
                    # Empty cell
                    month_table += f"<td style='{cell_style} background-color: #f9f9f9;'></td>"
                else:
                    # Check if this day is today
                    today_style = ""
                    if today.year == selected_date.year and today.month == selected_date.month and today.day == day:
                        today_style = "background-color: #e6f7ff; font-weight: bold;"
                    
                    month_table += f"<td style='{cell_style} {today_style}'>"
                    
                    # Add day number
                    month_table += f"<div style='text-align: right;'>{day}</div>"
                    
                    # Add events for this day (limited to top 3 for space)
                    max_visible_events = 3
                    visible_events = events[:max_visible_events]
                    
                    for event in visible_events:
                        # Get category color
                        category_id = event.get("category_id")
                        category = next((c for c in st.session_state.get("categories", []) if c["id"] == category_id), None)
                        category_color = category["color"] if category else "#808080"
                        
                        # Format time
                        try:
                            start_time = datetime.fromisoformat(event["start_time"]).strftime("%H:%M")
                        except (ValueError, TypeError):
                            start_time = "All day"
                        
                        month_table += f"""
                        <div style='
                            margin-top: 2px;
                            padding: 2px;
                            background-color: {category_color}20;
                            border-left: 3px solid {category_color};
                            font-size: 0.8em;
                            white-space: nowrap;
                            overflow: hidden;
                            text-overflow: ellipsis;
                        '>
                            <span>{start_time}</span> {event["title"]}
                        </div>
                        """
                    
                    # Show count of additional events
                    if len(events) > max_visible_events:
                        additional_count = len(events) - max_visible_events
                        month_table += f"<div style='text-align: right; font-size: 0.8em; color: #888;'>+{additional_count} more</div>"
                    
                    month_table += "</td>"
            
            month_table += "</tr>"
        
        month_table += "</table>"
        
        st.markdown(month_table, unsafe_allow_html=True)
    
    # Week View
    elif selected_view == "Week":
        # Get the year and week number
        year, week_num, _ = selected_date.isocalendar()
        
        st.subheader(f"Week {week_num}, {year}")
        
        # Generate week view data
        week_data = generate_week_view(year, week_num, all_events)
        
        # Create a table for the week view
        week_table = "<table style='width: 100%; border-collapse: collapse;'>"
        
        # Add header row with dates
        week_table += "<tr><th style='width: 10%; border: 1px solid #ddd; padding: 8px;'>Time</th>"
        
        for day_data in week_data["days"]:
            day = day_data["date"]
            day_name = day.strftime("%a")
            day_date = day.strftime("%d")
            
            # Check if this day is today
            today_style = ""
            if day == today:
                today_style = "background-color: #e6f7ff; font-weight: bold;"
            
            week_table += f"<th style='border: 1px solid #ddd; padding: 8px; {today_style}'>{day_name} {day_date}</th>"
        
        week_table += "</tr>"
        
        # Add time slots
        for hour in range(7, 22):  # 7 AM to 9 PM
            week_table += f"<tr><td style='border: 1px solid #ddd; padding: 8px;'>{hour}:00</td>"
            
            for day_data in week_data["days"]:
                day = day_data["date"]
                events = day_data["events"]
                
                # Filter events for this hour
                hour_events = []
                for event in events:
                    try:
                        start_time = datetime.fromisoformat(event["start_time"])
                        end_time = datetime.fromisoformat(event["end_time"])
                        
                        # Check if event is active during this hour
                        hour_start = datetime.combine(day, datetime.min.time()) + timedelta(hours=hour)
                        hour_end = hour_start + timedelta(hours=1)
                        
                        if (hour_start <= start_time < hour_end) or \
                           (start_time <= hour_start and end_time > hour_start):
                            hour_events.append(event)
                    except (ValueError, TypeError):
                        continue
                
                # Cell styling
                cell_style = "border: 1px solid #ddd; padding: 4px; vertical-align: top; height: 60px;"
                
                # Check if this day and hour is current
                current_style = ""
                if day == today and hour == datetime.now().hour:
                    current_style = "background-color: #e6f7ff;"
                
                week_table += f"<td style='{cell_style} {current_style}'>"
                
                # Add events for this hour
                for event in hour_events:
                    # Get category color
                    category_id = event.get("category_id")
                    category = next((c for c in st.session_state.get("categories", []) if c["id"] == category_id), None)
                    category_color = category["color"] if category else "#808080"
                    
                    # Format time
                    try:
                        start_time = datetime.fromisoformat(event["start_time"]).strftime("%H:%M")
                        end_time = datetime.fromisoformat(event["end_time"]).strftime("%H:%M")
                        time_str = f"{start_time}-{end_time}"
                    except (ValueError, TypeError):
                        time_str = "All day"
                    
                    week_table += f"""
                    <div style='
                        margin-bottom: 2px;
                        padding: 2px;
                        background-color: {category_color}20;
                        border-left: 3px solid {category_color};
                        font-size: 0.8em;
                        white-space: nowrap;
                        overflow: hidden;
                        text-overflow: ellipsis;
                    '>
                        <div>{time_str}</div>
                        <div>{event["title"]}</div>
                    </div>
                    """
                
                week_table += "</td>"
            
            week_table += "</tr>"
        
        week_table += "</table>"
        
        st.markdown(week_table, unsafe_allow_html=True)
    
    # Day View
    elif selected_view == "Day":
        st.subheader(f"{selected_date.strftime('%A, %B %d, %Y')}")
        
        # Generate day view data
        day_data = generate_day_view(selected_date, all_events)
        
        # Create a table for the day view
        day_table = "<table style='width: 100%; border-collapse: collapse;'>"
        
        # Add header
        day_table += "<tr><th style='width: 10%; border: 1px solid #ddd; padding: 8px;'>Time</th><th style='border: 1px solid #ddd; padding: 8px;'>Events</th></tr>"
        
        # Add time slots
        for hour_data in day_data["hours"]:
            hour = hour_data["hour"]
            events = hour_data["events"]
            
            # Only show hours from 6 AM to 10 PM
            if 6 <= hour <= 22:
                # Format the hour
                hour_str = f"{hour}:00"
                
                # Check if this is the current hour
                current_hour = ""
                if selected_date == today and hour == datetime.now().hour:
                    current_hour = "background-color: #e6f7ff;"
                
                day_table += f"<tr><td style='border: 1px solid #ddd; padding: 8px; {current_hour}'>{hour_str}</td>"
                
                # Add events for this hour
                day_table += f"<td style='border: 1px solid #ddd; padding: 8px; {current_hour}'>"
                
                for event in events:
                    # Get category color
                    category_id = event.get("category_id")
                    category = next((c for c in st.session_state.get("categories", []) if c["id"] == category_id), None)
                    category_color = category["color"] if category else "#808080"
                    category_name = category["name"] if category else "Uncategorized"
                    
                    # Format time
                    try:
                        start_time = datetime.fromisoformat(event["start_time"]).strftime("%H:%M")
                        end_time = datetime.fromisoformat(event["end_time"]).strftime("%H:%M")
                        time_str = f"{start_time} - {end_time}"
                    except (ValueError, TypeError):
                        time_str = "All day"
                    
                    day_table += f"""
                    <div style='
                        margin-bottom: 10px;
                        padding: 8px;
                        background-color: {category_color}20;
                        border-left: 5px solid {category_color};
                    '>
                        <div style='font-weight: bold;'>{event["title"]}</div>
                        <div style='font-size: 0.9em;'>{time_str}</div>
                        <div style='font-size: 0.8em; color: #888;'>{category_name}</div>
                        {f"<div style='margin-top: 5px;'>{event['description']}</div>" if event.get('description') else ""}
                        {f"<div style='font-size: 0.9em;'><b>Location:</b> {event['location']}</div>" if event.get('location') else ""}
                    </div>
                    """
                
                if not events:
                    day_table += "<em style='color: #888;'>No events</em>"
                
                day_table += "</td></tr>"
        
        day_table += "</table>"
        
        st.markdown(day_table, unsafe_allow_html=True)
    
    # Agenda View
    else:  # Agenda View
        st.subheader("Upcoming Events")
        
        # Filter future events
        now = datetime.now()
        future_events = []
        
        for event in all_events:
            try:
                start_time = datetime.fromisoformat(event["start_time"])
                if start_time >= now:
                    future_events.append(event)
            except (ValueError, TypeError):
                continue
        
        # Sort by start time
        future_events.sort(key=lambda x: x["start_time"])
        
        # Group by date
        date_grouped_events = {}
        for event in future_events:
            start_time = datetime.fromisoformat(event["start_time"])
            date_str = start_time.strftime("%Y-%m-%d")
            
            if date_str not in date_grouped_events:
                date_grouped_events[date_str] = []
            
            date_grouped_events[date_str].append(event)
        
        # Display events by date
        for date_str, events in date_grouped_events.items():
            event_date = datetime.strptime(date_str, "%Y-%m-%d")
            st.write(f"#### {event_date.strftime('%A, %B %d, %Y')}")
            
            for event in events:
                # Get category color
                category_id = event.get("category_id")
                category = next((c for c in st.session_state.get("categories", []) if c["id"] == category_id), None)
                category_color = category["color"] if category else "#808080"
                category_name = category["name"] if category else "Uncategorized"
                
                # Format time
                try:
                    start_time = datetime.fromisoformat(event["start_time"]).strftime("%H:%M")
                    end_time = datetime.fromisoformat(event["end_time"]).strftime("%H:%M")
                    time_str = f"{start_time} - {end_time}"
                except (ValueError, TypeError):
                    time_str = "All day"
                
                with st.container():
                    col1, col2 = st.columns([0.2, 0.8])
                    
                    with col1:
                        st.write(time_str)
                    
                    with col2:
                        st.markdown(f"""
                        <div style='
                            padding: 8px;
                            background-color: {category_color}20;
                            border-left: 5px solid {category_color};
                        '>
                            <div style='font-weight: bold;'>{event["title"]}</div>
                            <div style='font-size: 0.8em; color: #888;'>{category_name}</div>
                            {f"<div style='margin-top: 5px;'>{event['description']}</div>" if event.get('description') else ""}
                            {f"<div style='font-size: 0.9em;'><b>Location:</b> {event['location']}</div>" if event.get('location') else ""}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Add edit/delete buttons
                    edit_col, delete_col = st.columns(2)
                    
                    with edit_col:
                        if st.button("Edit", key=f"edit_event_{event['id']}"):
                            # Store event details in session state for editing
                            st.session_state["edit_event_id"] = event["id"]
                            st.session_state["edit_event_title"] = event["title"]
                            st.session_state["edit_event_description"] = event.get("description", "")
                            st.session_state["edit_event_location"] = event.get("location", "")
                            st.session_state["edit_event_category"] = event.get("category_id", "")
                            
                            start_dt = datetime.fromisoformat(event["start_time"])
                            end_dt = datetime.fromisoformat(event["end_time"])
                            
                            st.session_state["edit_event_date"] = start_dt.date()
                            st.session_state["edit_event_start_time"] = start_dt.time()
                            st.session_state["edit_event_end_time"] = end_dt.time()
                            
                            # Switch to the Add Event tab
                            st.session_state["active_tab"] = "Add Event"
                            st.rerun()
                    
                    with delete_col:
                        if st.button("Delete", key=f"delete_event_{event['id']}"):
                            delete_calendar_event(event["id"])
                            st.success("Event deleted!")
                            st.rerun()
                
                st.write("---")
        
        if not future_events:
            st.info("No upcoming events.")

# Add Event tab
with tab2:
    event_id = st.session_state.get("edit_event_id")
    
    if event_id:
        st.subheader("Edit Event")
    else:
        st.subheader("Add New Event")
    
    # Get tasks that could be scheduled
    tasks = st.session_state.get("tasks", [])
    incomplete_tasks = [task for task in tasks if not task.get("completed", False)]
    
    # Form for adding or editing an event
    with st.form(key="event_form"):
        title = st.text_input(
            "Event Title",
            value=st.session_state.get("edit_event_title", "")
        )
        
        description = st.text_area(
            "Description",
            value=st.session_state.get("edit_event_description", "")
        )
        
        location = st.text_input(
            "Location",
            value=st.session_state.get("edit_event_location", "")
        )
        
        # Date and time selection
        col1, col2, col3 = st.columns(3)
        
        with col1:
            event_date = st.date_input(
                "Date",
                value=st.session_state.get("edit_event_date", selected_date)
            )
        
        with col2:
            default_start = st.session_state.get("edit_event_start_time", datetime.now().replace(hour=9, minute=0).time())
            start_time = st.time_input("Start Time", value=default_start)
        
        with col3:
            default_end = st.session_state.get("edit_event_end_time", 
                                             (datetime.combine(datetime.today(), default_start) + timedelta(hours=1)).time())
            end_time = st.time_input("End Time", value=default_end)
        
        # Category selection
        categories = st.session_state.get("categories", [])
        category_id = st.selectbox(
            "Category",
            options=[c["id"] for c in categories],
            format_func=lambda x: next((c["name"] for c in categories if c["id"] == x), ""),
            index=0 if not st.session_state.get("edit_event_category") else 
                [i for i, c in enumerate(categories) if c["id"] == st.session_state.get("edit_event_category")][0]
                if any(c["id"] == st.session_state.get("edit_event_category") for c in categories) else 0
        )
        
        # Option to create event from a task
        if incomplete_tasks and not event_id:
            st.write("---")
            st.write("Or create event from an existing task:")
            
            task_options = ["None"] + [task["title"] for task in incomplete_tasks]
            selected_task_index = st.selectbox(
                "Select Task",
                options=range(len(task_options)),
                format_func=lambda i: task_options[i]
            )
            
            if selected_task_index > 0:
                selected_task = incomplete_tasks[selected_task_index - 1]
                
                # Suggest time slot based on task
                suggested_start, duration = suggest_time_slot(
                    selected_task, 
                    st.session_state.get("user_profile", {}),
                    st.session_state.get("calendar_events", [])
                )
                
                suggested_end = suggested_start + timedelta(minutes=duration)
                
                st.info(f"""
                Suggested time slot: 
                {suggested_start.strftime('%Y-%m-%d %H:%M')} - {suggested_end.strftime('%H:%M')}
                ({duration} minutes)
                """)
                
                if st.checkbox("Use suggested time"):
                    event_date = suggested_start.date()
                    start_time = suggested_start.time()
                    end_time = suggested_end.time()
                    
                # Use task details for the event
                if not title:
                    title = selected_task["title"]
                
                if not description:
                    description = selected_task.get("description", "")
                
                if not category_id:
                    category_id = selected_task.get("category_id", categories[0]["id"] if categories else None)
        
        submit_label = "Update Event" if event_id else "Add Event"
        submit = st.form_submit_button(submit_label)
        
        if submit:
            if not title:
                st.error("Event title is required.")
            elif end_time <= start_time:
                st.error("End time must be after start time.")
            else:
                # Combine date and time
                start_datetime = datetime.combine(event_date, start_time)
                end_datetime = datetime.combine(event_date, end_time)
                
                if event_id:
                    # Update existing event
                    update_calendar_event(
                        event_id,
                        title=title,
                        description=description,
                        location=location,
                        category_id=category_id,
                        start_time=start_datetime.isoformat(),
                        end_time=end_datetime.isoformat()
                    )
                    
                    # Clear edit state
                    for key in ["edit_event_id", "edit_event_title", "edit_event_description", 
                               "edit_event_location", "edit_event_category", 
                               "edit_event_date", "edit_event_start_time", "edit_event_end_time"]:
                        if key in st.session_state:
                            del st.session_state[key]
                    
                    st.success("Event updated successfully!")
                else:
                    # Add new event
                    add_calendar_event(
                        title=title,
                        start_time=start_datetime,
                        end_time=end_datetime,
                        description=description,
                        location=location,
                        category_id=category_id
                    )
                    
                    st.success("Event added successfully!")
                    
                    # Mark linked task as completed if selected
                    if incomplete_tasks and selected_task_index > 0:
                        if st.checkbox("Mark task as completed", value=False):
                            task_id = incomplete_tasks[selected_task_index - 1]["id"]
                            update_task(task_id, completed=True, completed_at=datetime.now().isoformat())
                
                # Clear form
                st.rerun()
    
    # Cancel button for edit mode
    if event_id:
        if st.button("Cancel Editing"):
            # Clear edit state
            for key in ["edit_event_id", "edit_event_title", "edit_event_description", 
                       "edit_event_location", "edit_event_category", 
                       "edit_event_date", "edit_event_start_time", "edit_event_end_time"]:
                if key in st.session_state:
                    del st.session_state[key]
            
            st.rerun()
