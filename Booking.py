import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import random

st.set_page_config(
    page_title="Booking – Europe & Worldwide",
    layout="wide",
    initial_sidebar_state="collapsed"
)

from components.navbar import navbar
navbar()

# ---------------------------------------------------
# STYLE
# ---------------------------------------------------
st.markdown("""
<style>

.metric-box {
    background: #FFFFFF;
    padding: 14px 18px;
    border-radius: 8px;
    margin-bottom: 10px;
    border: 1px solid #E6E6E6;
}

.metric-title {
    font-family: 'Inter', sans-serif;
    font-size: 14px;
    font-weight: 600;
    color: #444444;
    letter-spacing: 0.02em;
}

.metric-value {
    font-family: 'Inter', sans-serif;
    font-size: 20px;
    font-weight: 700;
    color: #111111;
    margin-top: 2px;
}

.section-title {
    font-family: 'Inter', sans-serif;
    font-size: 18px;
    font-weight: 700;
    color: #111111;
    margin-bottom: 12px;
}

</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------
# DATA LOADING
# ---------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_excel("traveldata-export.xlsx")
    df["date"] = pd.to_datetime(df["date"])
    df["route"] = df["departure_iata"] + " → " + df["arrival_iata"]

    df["flight_time_h"] = ((df["km"] / 850) + 0.5).round(1)
    df["train_time_h"] = (df["km"] / 120).round(1)

    return df

df = load_data()


# ---------------------------------------------------
# HEADER
# ---------------------------------------------------
st.markdown("<h1>Book your next trip</h1>", unsafe_allow_html=True)

st.markdown("""
<div style='padding:18px; background:#F5F2EB; border-radius:8px;
            font-family:Inter; font-size:16px; font-weight:600;
            color:#4A3F2A; margin-bottom:1.5rem'>
    🌍 Choose the greener option – earn points & reduce CO₂
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------
# LAYOUT
# ---------------------------------------------------
left, right = st.columns([1.2, 1], vertical_alignment="top")

with left:

    name_ma = st.text_input("Traveler name & 4-digit ID", "")

    col_dep, col_arr = st.columns(2)

    departure_options = sorted(df["departure_city"].dropna().unique())
    departure_options_with_other = departure_options + ["Other"]

    with col_dep:
        selected_departure = st.selectbox("Departure city", departure_options_with_other)
        if selected_departure == "Other":
            selected_departure = st.text_input("Enter custom departure city")

    arrival_options = sorted(
        df[df["departure_city"] == selected_departure]["arrival_city"].dropna().unique()
    )
    arrival_options_with_other = arrival_options + ["Other"]

    with col_arr:
        selected_arrival = st.selectbox("Arrival city", arrival_options_with_other)
        if selected_arrival == "Other":
            selected_arrival = st.text_input("Enter custom arrival city")

    # Trip type + dates
    col_trip, col_dates = st.columns(2)

    with col_trip:
        trip_type = st.radio("Trip type", ["One-way", "Round-trip"])

    with col_dates:
        departure_date = st.date_input("Departure date")
        return_date = st.date_input("Return date") if trip_type == "Round-trip" else None

    # Preferred travel mode – only show Train if available
    row = df[
        (df["departure_city"] == selected_departure) &
        (df["arrival_city"] == selected_arrival)
    ]

    train_possible = False
    if not row.empty:
        train_possible = bool(row.iloc[0]["train_alternative_available"])

    travel_modes = ["Flight"]
    if train_possible:
        travel_modes.append("Train")

    booking_choice = st.radio("Preferred travel mode", travel_modes)

    optional_note = st.text_area("Optional note (special requests, comments)", "")

# ---------------------------------------------------
# RIGHT SIDE – TRIP INSIGHTS
# ---------------------------------------------------
with right:

    st.markdown("<div class='section-title'>📊 Trip Insights</div>", unsafe_allow_html=True)

    if not row.empty:
        r = row.iloc[0]

        co2_flight = float(r["CO2e RFI2.7 (t)"])
        train_possible = bool(r["train_alternative_available"])
        co2_train = co2_flight * 0.05 if train_possible else None

        # ---------------------------------------------------
        # 1) CO₂ BAR CHART (ALWAYS SHOWN)
        # ---------------------------------------------------
        fig = go.Figure()

        # Flight bar always shown
        fig.add_trace(go.Bar(
            x=["Flight"],
            y=[co2_flight],
            marker_color="#C65D3A",
            name="Flight CO₂"
        ))

        # Train bar only if train alternative exists
        if train_possible:
            fig.add_trace(go.Bar(
                x=["Train"],
                y=[co2_train],
                marker_color="#7BAF7B",
                name="Train CO₂"
            ))

        fig.update_layout(
            height=260,
            margin=dict(l=0, r=0, t=10, b=0),
            showlegend=False,
            yaxis_title="CO₂ (t)"
        )

        st.plotly_chart(fig, use_container_width=True)

        # ---------------------------------------------------
        # 2) CO₂ Flight | CO₂ Train (SIDE BY SIDE)
        # ---------------------------------------------------
        if train_possible:
            col_c1, col_c2 = st.columns(2)

            with col_c1:
                st.markdown(f"""
                <div class='metric-box'>
                    <div class='metric-title'>CO₂ Flight</div>
                    <div class='metric-value'>{co2_flight:.4f} t</div>
                </div>
                """, unsafe_allow_html=True)

            with col_c2:
                st.markdown(f"""
                <div class='metric-box'>
                    <div class='metric-title'>CO₂ Train</div>
                    <div class='metric-value'>{co2_train:.4f} t</div>
                </div>
                """, unsafe_allow_html=True)

        else:
            # Only Flight CO₂ if no train alternative
            st.markdown(f"""
            <div class='metric-box'>
                <div class='metric-title'>CO₂ Flight</div>
                <div class='metric-value'>{co2_flight:.4f} t</div>
            </div>
            """, unsafe_allow_html=True)

        # ---------------------------------------------------
        # 3) Flight time | Train time | Train Efficiency
        # ---------------------------------------------------
        if train_possible:

            col_t1, col_t2, col_t3 = st.columns(3)

            with col_t1:
                st.markdown(f"""
                <div class='metric-box'>
                    <div class='metric-title'>Flight time</div>
                    <div class='metric-value'>{r['flight_time_h']:.1f} h</div>
                </div>
                """, unsafe_allow_html=True)

            with col_t2:
                st.markdown(f"""
                <div class='metric-box'>
                    <div class='metric-title'>Train time</div>
                    <div class='metric-value'>{r['train_time_h']:.1f} h</div>
                </div>
                """, unsafe_allow_html=True)

            with col_t3:
                eff = "Good ✅" if r["train_time_h"] < 10 else "Poor ❌"
                st.markdown(f"""
                <div class='metric-box'>
                    <div class='metric-title'>Train Efficiency</div>
                    <div class='metric-value'>{eff}</div>
                </div>
                """, unsafe_allow_html=True)

        else:
            # Only Flight time if no train alternative
            st.markdown(f"""
            <div class='metric-box'>
                <div class='metric-title'>Flight time</div>
                <div class='metric-value'>{r['flight_time_h']:.1f} h</div>
            </div>
            """, unsafe_allow_html=True)


# ---------------------------------------------------
# BOOKING EMAIL + SCOREBOARD (unverändert)
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
- Note: {optional_note if optional_note else '-'}
"""

if trip_type == "Round-trip":
    email_body += f"- Return date: {return_date}\n"

email_body += "\nThank you."

if st.button("📧 Generate booking email"):
    st.code(email_body)
    st.success(f"Email successfully sent to – {secretary_email}.")
