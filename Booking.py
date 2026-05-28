import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import random

# ---------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------
st.set_page_config(
    page_title="Booking – Europe & Worldwide",
    layout="wide",
    initial_sidebar_state="collapsed"
)

from components.navbar import navbar
navbar()

# ---------------------------------------------------
# GLOBAL STYLE DEFINITIONS (CSS)
# ---------------------------------------------------
# These classes define the visual style of metric boxes, titles, and values
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
# DATA LOADING FUNCTION
# ---------------------------------------------------
@st.cache_data
def load_data():
    """
    Loads the travel dataset, parses dates, and computes
    estimated flight and train travel times.
    """
    df = pd.read_excel("traveldata-export.xlsx")
    df["date"] = pd.to_datetime(df["date"])
    df["route"] = df["departure_iata"] + " → " + df["arrival_iata"]

    # Estimated flight time: distance / 850 km/h + 0.5h buffer
    df["flight_time_h"] = ((df["km"] / 850) + 0.5).round(1)

    # Estimated train time: distance / 120 km/h
    df["train_time_h"] = (df["km"] / 120).round(1)

    return df

df = load_data()


# ---------------------------------------------------
# HEADER + CALL TO ACTION
# ---------------------------------------------------
st.markdown("<h1>Book your next trip</h1>", unsafe_allow_html=True)

# CTA box encouraging sustainable travel
st.markdown("""
<div style='padding:18px; background:#F5F2EB; border-radius:8px;
            font-family: 'Inter', sans-serif; font-size:18px; font-weight:400;
            color:#111111; margin-bottom:1.5rem; letter-spacing:0.01em;'>
    🌍 Choose the greener option – earn points & reduce CO₂
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ---------------------------------------------------
# MAIN LAYOUT: LEFT = BOOKING FORM, RIGHT = INSIGHTS
# ---------------------------------------------------
left, right = st.columns([1.2, 1], vertical_alignment="top")

with left:

    # Basic traveler information
    name_ma = st.text_input("Traveler name & 4-digit ID", "")

    # Departure and arrival selection
    col_dep, col_arr = st.columns(2)

    departure_options = sorted(df["departure_city"].dropna().unique())
    departure_options_with_other = departure_options + ["Other"]

    # Departure city selection
    with col_dep:
        selected_departure = st.selectbox("Departure city", departure_options_with_other)
        if selected_departure == "Other":
            selected_departure = st.text_input("Enter custom departure city")

    # Arrival city options depend on selected departure
    arrival_options = sorted(
        df[df["departure_city"] == selected_departure]["arrival_city"].dropna().unique()
    )
    arrival_options_with_other = arrival_options + ["Other"]

    # Arrival city selection
    with col_arr:
        selected_arrival = st.selectbox("Arrival city", arrival_options_with_other)
        if selected_arrival == "Other":
            selected_arrival = st.text_input("Enter custom arrival city")

    # Trip type and dates
    col_trip, col_dates = st.columns(2)

    with col_trip:
        trip_type = st.radio("Trip type", ["One-way", "Round-trip"])

    with col_dates:
        departure_date = st.date_input("Departure date")
        return_date = st.date_input("Return date") if trip_type == "Round-trip" else None

    # Determine if a train alternative exists for the selected route
    row = df[
        (df["departure_city"] == selected_departure) &
        (df["arrival_city"] == selected_arrival)
    ]

    train_possible = False
    if not row.empty:
        train_possible = bool(row.iloc[0]["train_alternative_available"])

    # Travel mode selection (Train only shown if available)
    travel_modes = ["Flight"]
    if train_possible:
        travel_modes.append("Train")

    booking_choice = st.radio("Preferred travel mode", travel_modes)

    # Optional notes
    optional_note = st.text_area("Optional note (special requests, comments)", "")


# ---------------------------------------------------
# RIGHT SIDE – TRIP INSIGHTS PANEL
# ---------------------------------------------------
with right:

    st.markdown("<div class='section-title'>📊 Trip Insights</div>", unsafe_allow_html=True)

    if not row.empty:
        r = row.iloc[0]

        # Extract CO₂ values
        co2_flight = float(r["CO2e RFI2.7 (t)"])
        train_possible = bool(r["train_alternative_available"])
        co2_train = co2_flight * 0.05 if train_possible else None

        # ---------------------------------------------------
        # 1) CO₂ BAR CHART (always shown)
        # ---------------------------------------------------
        fig = go.Figure()

        # Flight CO₂ bar
        fig.add_trace(go.Bar(
            x=["Flight"],
            y=[co2_flight],
            marker_color="#DCC9B6",
            name="Flight CO₂"
        ))

        # Train CO₂ bar only if train exists
        if train_possible:
            fig.add_trace(go.Bar(
                x=["Train"],
                y=[co2_train],
                marker_color="#83781B",
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
        # 2) CO₂ Flight | CO₂ Train | Gamification Points
        # ---------------------------------------------------
        if train_possible:
            col_c1, col_c2, col_c3 = st.columns(3)

            # CO₂ Flight
            with col_c1:
                st.markdown(f"""
                <div class='metric-box'>
                    <div class='metric-title'>CO₂ Flight</div>
                    <div class='metric-value'>{co2_flight:.4f} t</div>
                </div>
                """, unsafe_allow_html=True)

            # CO₂ Train
            with col_c2:
                st.markdown(f"""
                <div class='metric-box'>
                    <div class='metric-title'>CO₂ Train</div>
                    <div class='metric-value'>{co2_train:.4f} t</div>
                </div>
                """, unsafe_allow_html=True)

            # Gamification points (only if train selected)
            with col_c3:
                if booking_choice == "Train":
                    st.markdown(f"""
                    <div class='metric-box'>
                        <div class='metric-title'>Gamification Points</div>
                        <div class='metric-value'>+50 🌟</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class='metric-box'>
                        <div class='metric-title'>Gamification Points</div>
                        <div class='metric-value'>–</div>
                    </div>
                    """, unsafe_allow_html=True)

        else:
            # Only show CO₂ Flight if no train option exists
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

            # Flight time
            with col_t1:
                st.markdown(f"""
                <div class='metric-box'>
                    <div class='metric-title'>Flight time</div>
                    <div class='metric-value'>{r['flight_time_h']:.1f} h</div>
                </div>
                """, unsafe_allow_html=True)

            # Train time
            with col_t2:
                st.markdown(f"""
                <div class='metric-box'>
                    <div class='metric-title'>Train time</div>
                    <div class='metric-value'>{r['train_time_h']:.1f} h</div>
                </div>
                """, unsafe_allow_html=True)

            # Train efficiency rating
            with col_t3:
                eff = "Good ✅" if r["train_time_h"] < 10 else "Poor ❌"
                st.markdown(f"""
                <div class='metric-box'>
                    <div class='metric-title'>Train Efficiency</div>
                    <div class='metric-value'>{eff}</div>
                </div>
                """, unsafe_allow_html=True)

        else:
            # Only show flight time if no train option exists
            st.markdown(f"""
            <div class='metric-box'>
                <div class='metric-title'>Flight time</div>
                <div class='metric-value'>{r['flight_time_h']:.1f} h</div>
            </div>
            """, unsafe_allow_html=True)


# ---------------------------------------------------
# BOOKING EMAIL + SCOREBOARD
# ---------------------------------------------------
secretary_email = "secretariat@company.com"

# Build email body dynamically
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

# When user clicks the booking button
if st.button("📧 Generate booking email"):
    st.code(email_body)
    st.success(f"Email successfully sent to – {secretary_email}.")

    # Show gamification success message if train chosen
    if train_possible and booking_choice == "Train":
        st.markdown("""
        ### 🌟 Good job!
        You made the planet a bit greener 🌱
        """)

    # ---------------------------------------------------
    # TEAM SCOREBOARD (shown after booking)
    # ---------------------------------------------------
    scoreboard = pd.DataFrame({
        "Team": ["Sales & Customer Markets", "Operations & Delivery", "Technology & Innovation", "Corporate Services"],
        "Points": [140, 135, 110, 90]
    })

    # Sort teams by points and assign ranking
    scoreboard = scoreboard.sort_values(by="Points", ascending=False).reset_index(drop=True)
    scoreboard.insert(0, "Rank", range(1, len(scoreboard) + 1))

    max_pts = scoreboard["Points"].max()

    # Styles for rank badges and progress bars
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

    # Build HTML table rows
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

    # Final scoreboard table
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