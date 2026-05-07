import streamlit as st
import pandas as pd
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
    line_color = "green" if r["train_alternative_available"] else "red"

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
    departure_options = sorted(df["departure_city"].dropna().unique())
    selected_departure = st.selectbox("Departure city", departure_options)
    arrival_options = sorted(
        df[df["departure_city"] == selected_departure]["arrival_city"].dropna().unique()
    )
    selected_arrival = st.selectbox("Arrival city", arrival_options)
    trip_type = st.radio("Trip type", ["One-way", "Round-trip"])
    departure_date = st.date_input("Departure date")
    return_date = st.date_input("Return date") if trip_type == "Round-trip" else None
    booking_choice = st.radio("Preferred travel mode", ["Flight", "Train"])

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
    col3.metric("Train time", train_hm)
    col4.metric("Efficiency", "Good ✅" if train_time_h < 10 else "Poor ❌")
    col5.metric("Gamification points", "50" if train_possible else "0")


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
"""

if trip_type == "Round-trip":
    email_body += f"- Return date: {return_date}\n"

email_body += "\nThank you."

if st.button("📧 Generate booking email"):
    st.code(email_body)
    st.success(f"Email succesfully sent to – {secretary_email}.")

    if booking_choice == "Train":
        st.markdown(f"""
        ### 🌟 Great job!
        You earned **{points} points** for your team and made the world a bit greener 🌱
        """)

    scoreboard = pd.DataFrame({
        "Team": ["Marketing", "Sales", "HR"],
        "Points": [120, 95, 140]
    })

    st.subheader("🏆 Team Scoreboard")
    st.table(scoreboard)
