import streamlit as st
import pandas as pd
import plotly
import plotly.graph_objects as go
import math

st.set_page_config(page_title="Booking – Europe & Worldwide", layout="wide", initial_sidebar_state="collapsed")

# ---------------------------------------------------
# DATA LOADING
# ---------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_excel("traveldata-export.xlsx")
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["route"] = df["departure_iata"] + " → " + df["arrival_iata"]

    # Flight time estimation (distance / 850 km/h + 0.5h buffer)
    df["flight_time_h"] = (df["km"] / 850) + 0.5
    df["flight_time_h"] = df["flight_time_h"].round(1)

    # Train time estimation (distance / 120 km/h)
    df["train_time_h"] = df["km"] / 120
    df["train_time_h"] = df["train_time_h"].round(1)

    return df

df = load_data()

# ---------------------------------------------------
# EUROPE FILTER (always active)
# ---------------------------------------------------
@st.cache_data
def filter_europe(df):
    return df[
        (df["departure_lat"].between(35, 70)) &
        (df["departure_lon"].between(-15, 35)) &
        (df["arrival_lat"].between(35, 70)) &
        (df["arrival_lon"].between(-15, 35))
    ].copy()

df_active = filter_europe(df)
filtered = df_active.copy()

# ---------------------------------------------------
# MAP FUNCTION (SHOW ONLY SELECTED ROUTE)
# ---------------------------------------------------
@st.cache_data
def build_map(selected_departure, selected_arrival, df):
    fig = go.Figure()

    route_df = df[
        (df["departure_city"] == selected_departure) &
        (df["arrival_city"] == selected_arrival)
    ]

    if route_df.empty:
        return fig

    r = route_df.iloc[0]
    if r["train_alternative_available"] == 1:
        line_color = "#83781B"   # train alternative
    else:
        line_color = "#DCC9B6"   # flight

    fig.add_trace(go.Scattergeo(
        lon=[r["departure_lon"], r["arrival_lon"]],
        lat=[r["departure_lat"], r["arrival_lat"]],
        mode="lines+markers",
        line=dict(width=3, color=line_color),
        marker=dict(size=6, color="black"),
        hovertext=(
            f"{r['route']}<br>"
            f"CO₂: {r['CO2e RFI2.7 (t)']:.1f} t<br>"
            f"Distance: {r['km']:.0f} km<br>"
            f"Flight time: {r['flight_time_h']:.1f} h<br>"
            f"Train time: {r['train_time_h']:.1f} h<br>"
            f"Train alternative: {'Yes' if r['train_alternative_available'] else 'No'}"
        ),
        hoverinfo="text"
    ))

    fig.update_layout(
        height=450,
        geo=dict(
            projection_type="natural earth",
            lonaxis=dict(range=[-15, 35]),
            lataxis=dict(range=[35, 70]),
            showland=True,
            landcolor="#e8f0f8",
            showocean=True,
            oceancolor="#b8d4e8",
            showcountries=True,
            countrycolor="#c0cfe0",
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False
    )
    return fig

# ---------------------------------------------------
# HEADER: BOOKING TITLE + ROUTE MAP TITLE SIDE BY SIDE
# ---------------------------------------------------
col_title, col_map_title = st.columns([1.2, 1])
with col_title:
    st.markdown("<h1 style='margin-bottom:0;'>✈️ Book your next trip</h1>", unsafe_allow_html=True)
with col_map_title:
    st.markdown("<h1 style='margin-bottom:0;'></h1>", unsafe_allow_html=True)

# ---------------------------------------------------
# TWO-COLUMN LAYOUT: LEFT = BOOKING, RIGHT = MAP
# ---------------------------------------------------
left, right = st.columns([1.2, 1], vertical_alignment="top")

with left:

    name_ma = st.text_input("Traveler name & 4-digit ID", "")

    # --- ROW: Departure (left) + Arrival (right) ---
    col_dep, col_arr = st.columns(2)

    # Departure dropdown + "Other"
    departure_options = sorted(df["departure_city"].dropna().unique())
    departure_options_with_other = departure_options + ["Other"]

    with col_dep:
        selected_departure = st.selectbox("Departure city", departure_options_with_other)
        if selected_departure == "Other":
            selected_departure = st.text_input("Enter custom departure city")

    # Arrival dropdown + "Other"
    arrival_options = sorted(
        df[df["departure_city"] == selected_departure]["arrival_city"].dropna().unique()
    )
    arrival_options_with_other = arrival_options + ["Other"]

    with col_arr:
        selected_arrival = st.selectbox("Arrival city", arrival_options_with_other)
        if selected_arrival == "Other":
            selected_arrival = st.text_input("Enter custom arrival city")

    # --- ROW: Trip type (left) + Dates (right) ---
    col_trip, col_dates = st.columns(2)

    with col_trip:
        trip_type = st.radio("Trip type", ["One-way", "Round-trip"])

    with col_dates:
        departure_date = st.date_input("Departure date")
        return_date = (
            st.date_input("Return date") if trip_type == "Round-trip" else None
        )

    booking_choice = st.radio("Preferred travel mode", ["Flight", "Train"])
    optional_note = st.text_area("Optional note (special requests, comments)", "")

# --- MISSING BLOCK (now restored) ---
with right:
    fig_map = build_map(selected_departure, selected_arrival, df)
    st.plotly_chart(fig_map, use_container_width=True)

# ---------------------------------------------------
# FULL-WIDTH TRAVEL TIME COMPARISON
# ---------------------------------------------------

st.markdown("<div style='margin-top:-2rem'></div>", unsafe_allow_html=True)

st.subheader("⏱ Travel Time per way")

row = df[
    (df["departure_city"] == selected_departure) &
    (df["arrival_city"] == selected_arrival)
]

if not row.empty:
    train_possible = bool(row.iloc[0]["train_alternative_available"])
    train_time_h = row.iloc[0]["train_time_h"]
    flight_time_h = row.iloc[0]["flight_time_h"]

    def h_to_hm(hours):
        h = int(hours)
        m = int((hours - h) * 60)
        return f"{h}h {m:02d}m"

    train_hm = h_to_hm(train_time_h)
    flight_hm = h_to_hm(flight_time_h)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Train alternative", "Yes 🚆" if train_possible else "No ❌")
    col2.metric("Flight time", flight_hm)
    col3.metric("Train time", train_hm if train_possible else " --")
    col4.metric("Efficiency", "Good ✅" if train_time_h < 10 else "Poor ❌")
    col5.metric("Gamification points", "Yes" if booking_choice == "Train" else "No")



# ---------------------------------------------------
# FULL-WIDTH BOOKING + SCOREBOARD
# ---------------------------------------------------
secretary_email = "secretariat@company.com"

email_body = f"""
Hi,

Please book the following trip for me:

- Traveler: {name_ma}
- From: {selected_departure}
- To: {selected_arrival}
- Departure date: {departure_date}
- Travel mode: {booking_choice}
- Note: {optional_note if optional_note else 'N/A'}
"""

if trip_type == "Round-trip":
    email_body += f"- Return date: {return_date}\n"

email_body += "\nThank you."

if st.button("📧 Generate booking email"):
    st.code(email_body)
    st.success(f"Email successfully sent to – {secretary_email}.")

    if booking_choice == "Train":
        st.markdown("""
        ### 🌟 Great job!
        You earned points for your team and made the world a bit greener 🌱
        """)

    # --- Show scoreboard only after booking ---
    scoreboard = pd.DataFrame({
        "Team": ["Sales & Customer Markets", "Operations & Delivery", "Technology & Innovation", "Corporate Services"],
        "Points": [140, 135, 110, 90]
    })

    # Sort by points descending and add rank column
    scoreboard = scoreboard.sort_values(by="Points", ascending=False).reset_index(drop=True)
    scoreboard.insert(0, "Rank", range(1, len(scoreboard) + 1))

    # Style: remove index + improve design
    styled_scoreboard = scoreboard.style.set_table_styles([
        {"selector": "th", "props": [("background-color", "#f0f4f8"), ("color", "#333"), ("font-weight", "bold"), ("text-align", "center")]},
        {"selector": "td", "props": [("text-align", "center"), ("padding", "6px 12px")]},
        {"selector": "tr:nth-child(even)", "props": [("background-color", "#fafafa")]},
        {"selector": "tr:hover", "props": [("background-color", "#e8f0fe")]}
    ]).hide(axis="index")

    st.subheader("🏆 Team Scoreboard")
    
    max_pts = scoreboard["Points"].max()
 
    rank_styles = {
        1: "background:#FAEEDA;color:#633806",
        2: "background:#F1EFE8;color:#444441",
        3: "background:#FAECE7;color:#712B13",
    }
    bar_colors = {
        1: "#F09920",
        2: "#9DD8D1",
        3: "#D85A30",
        4: "#636361",
    }
 
    rows_html = ""
    for _, row in scoreboard.iterrows():
        r = int(row["Rank"])
        badge_style = rank_styles.get(r, "background:#f0f0f0;color:#888888")
        bar_color = bar_colors.get(r, "#C8C6BE")
        bar_pct = int(row["Points"] / max_pts * 100)
        rows_html += f"""
        <tr style="border-bottom:0.5px solid #e8e8e8;">
          <td style="padding:12px 16px;vertical-align:middle;width:56px">
            <span style="display:inline-flex;align-items:center;justify-content:center;
              width:28px;height:28px;border-radius:50%;font-size:13px;font-weight:600;
              {badge_style}">{r}</span>
          </td>
          <td style="padding:12px 16px;vertical-align:middle">
            <div style="font-weight:600;font-size:14px;color:#1a1a1a;margin-bottom:5px">{row['Team']}</div>
            <div style="background:#eeeeee;border-radius:3px;height:5px;width:100%">
              <div style="width:{bar_pct}%;height:5px;background:{bar_color};border-radius:3px"></div>
            </div>
          </td>
          <td style="padding:12px 16px;text-align:right;font-weight:600;font-size:16px;
            color:#1a1a1a;vertical-align:middle;width:80px">
            {int(row['Points'])}
          </td>
        </tr>"""
 
    table_html = f"""
    <table style="width:100%;border-collapse:collapse;font-family:sans-serif;
      border:0.5px solid #e0e0e0;border-radius:10px;overflow:hidden">
      <thead>
        <tr style="background:#f7f7f7;border-bottom:1px solid #e0e0e0">
          <th style="padding:10px 16px;text-align:left;font-size:11px;color:#999999;
            font-weight:600;letter-spacing:0.06em;width:56px">RANK</th>
          <th style="padding:10px 16px;text-align:left;font-size:11px;color:#999999;
            font-weight:600;letter-spacing:0.06em">TEAM</th>
          <th style="padding:10px 16px;text-align:right;font-size:11px;color:#999999;
            font-weight:600;letter-spacing:0.06em;width:80px">POINTS</th>
        </tr>
      </thead>
      <tbody>{rows_html}</tbody>
    </table>"""
 
    st.markdown(table_html, unsafe_allow_html=True)