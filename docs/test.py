"""
Geschäftsreisen & CO₂-Emissionen – Unternehmensübersicht
Streamlit Dashboard basierend auf traveldata-export.xlsx
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── Seitenkonfiguration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Geschäftsreisen & CO₂",
    page_icon="✈️",
    layout="wide",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #f0f4f8; }
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    h1 { color: #1a3a5c; font-size: 1.6rem; text-align: center; }

    /* KPI-Karten */
    .kpi-card {
        background: white;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.5rem;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    }
    .kpi-label { color: #6b7280; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.2rem; }
    .kpi-value { color: #1a3a5c; font-size: 2rem; font-weight: 700; line-height: 1.1; }
    .kpi-sub   { color: #6b7280; font-size: 0.75rem; margin-top: 0.2rem; }
    .kpi-icon  { font-size: 1.4rem; margin-bottom: 0.3rem; }

    /* Tabelle */
    .route-table th { background: #1a3a5c; color: white; padding: 6px 10px; font-size: 0.78rem; }
    .route-table td { padding: 5px 10px; font-size: 0.8rem; border-bottom: 1px solid #e5e7eb; }
    .tag-ja  { color: #16a34a; font-weight: 700; }
    .tag-nein { color: #dc2626; font-weight: 700; }
</style>
""", unsafe_allow_html=True)


# ── Daten laden ────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_excel("traveldata-export.xlsx", sheet_name="travel_data")
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["route"] = df["departure_iata"] + " → " + df["arrival_iata"]
    return df

df = load_data()

# ── Filter-Leiste ──────────────────────────────────────────────────────────────
st.markdown("<h1>✈️ Geschäftsreisen & CO₂-Emissionen – Unternehmensübersicht</h1>", unsafe_allow_html=True)

col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    years = sorted(df["year"].unique())
    selected_year = st.selectbox("📅 Zeitraum", years, index=years.index(2024) if 2024 in years else len(years)-1)
with col_f2:
    bus_units = ["Alle"] + sorted(df["business_unit"].unique().tolist())
    selected_bu = st.selectbox("🏢 Business Unit", bus_units)
with col_f3:
    transport_opts = ["Alle"] + sorted(df["transport_mode"].unique().tolist())
    selected_transport = st.selectbox("🚌 Transport", transport_opts)

# ── Daten filtern ──────────────────────────────────────────────────────────────
mask = df["year"] == selected_year
if selected_bu != "Alle":
    mask &= df["business_unit"] == selected_bu
if selected_transport != "Alle":
    mask &= df["transport_mode"] == selected_transport

filtered = df[mask].copy()

# ── KPI-Berechnungen ───────────────────────────────────────────────────────────
total_trips     = len(filtered)
total_co2       = filtered["CO2e RFI2.7 (t)"].sum()
total_km        = filtered["km"].sum()
train_possible  = filtered["train_alternative_available"].sum() if "train_alternative_available" in filtered.columns else 0
train_pct       = (train_possible / total_trips * 100) if total_trips > 0 else 0
savings_possible = filtered.loc[filtered["train_alternative_available"] == True, "CO2e RFI2.7 (t)"].sum() * 0.85

# Top-Route
if not filtered.empty:
    top_route_series = filtered.groupby("route")["CO2e RFI2.7 (t)"].sum()
    top_route = top_route_series.idxmax() if not top_route_series.empty else "–"
    top_route_co2 = top_route_series.max() if not top_route_series.empty else 0
else:
    top_route, top_route_co2 = "–", 0

# ── Layout: KPIs | Karte | Rechte Spalte ──────────────────────────────────────
left, center, right = st.columns([1.2, 2.5, 1.5])

# ── Linke KPI-Spalte ──────────────────────────────────────────────────────────
with left:
    transport_icon = {"flight": "✈️", "train": "🚂", "bus": "🚌", "rental_car": "🚗"}.get(selected_transport, "🌍")

    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-icon">{transport_icon}</div>
        <div class="kpi-label">Reisen gesamt</div>
        <div class="kpi-value">{total_trips:,}</div>
        <div class="kpi-sub">{total_km:,.0f} km total</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-icon">🌫️</div>
        <div class="kpi-label">CO₂ gesamt</div>
        <div class="kpi-value">{total_co2:.0f} t</div>
        <div class="kpi-sub">RFI 2.7 Faktor</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-icon">✈️</div>
        <div class="kpi-label">Top-Route</div>
        <div class="kpi-value" style="font-size:1.1rem;">{top_route}</div>
        <div class="kpi-sub">{top_route_co2:.1f} t CO₂</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-icon">🚂</div>
        <div class="kpi-label">Bahn-Alternative</div>
        <div class="kpi-value">{train_pct:.0f}%</div>
        <div class="kpi-sub">der Strecken möglich</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-icon">🌿</div>
        <div class="kpi-label">Einsparung möglich</div>
        <div class="kpi-value">{savings_possible:.0f} t</div>
        <div class="kpi-sub">bei Bahn-Umstieg</div>
    </div>
    """, unsafe_allow_html=True)

# ── Karte ──────────────────────────────────────────────────────────────────────
with center:
    if not filtered.empty:
        # Routen aggregieren
        routes_agg = (
            filtered.groupby(["departure_lat","departure_lon","arrival_lat","arrival_lon","route"])
            .agg(trips=("CO2e RFI2.7 (t)","count"), co2=("CO2e RFI2.7 (t)","sum"))
            .reset_index()
        )

        fig_map = go.Figure()

        # Verbindungslinien
        for _, row in routes_agg.iterrows():
            intensity = min(row["co2"] / routes_agg["co2"].max(), 1.0)
            r = int(50 + 205 * intensity)
            g = int(200 - 180 * intensity)
            b = int(50)
            color = f"rgba({r},{g},{b},0.6)"
            width = 1 + intensity * 5

            fig_map.add_trace(go.Scattergeo(
                lon=[row["departure_lon"], row["arrival_lon"]],
                lat=[row["departure_lat"], row["arrival_lat"]],
                mode="lines",
                line=dict(width=width, color=color),
                hoverinfo="skip",
                showlegend=False,
            ))

        # Abflugpunkte
        dep = filtered.groupby(["departure_city","departure_lat","departure_lon"])["CO2e RFI2.7 (t)"].sum().reset_index()
        fig_map.add_trace(go.Scattergeo(
            lon=dep["departure_lon"],
            lat=dep["departure_lat"],
            mode="markers",
            marker=dict(size=7, color="white", line=dict(color="#1a3a5c", width=1.5)),
            text=dep["departure_city"],
            hovertemplate="<b>%{text}</b><br>CO₂: %{customdata:.1f} t<extra></extra>",
            customdata=dep["CO2e RFI2.7 (t)"],
            name="Abflug",
        ))

        fig_map.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            height=420,
            paper_bgcolor="rgba(0,0,0,0)",
            geo=dict(
                showland=True, landcolor="#e8f0f8",
                showocean=True, oceancolor="#b8d4e8",
                showcoastlines=True, coastlinecolor="#94b8c8",
                showcountries=True, countrycolor="#c0cfe0",
                showframe=False,
                projection_type="natural earth",

                        # 👉 Europa-Zoom
                lonaxis=dict(range=[-15, 35]),
                lataxis=dict(range=[35, 70]),
            ),
        )
        st.plotly_chart(fig_map, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Keine Daten für diese Filterauswahl.")

# ── Rechte Spalte: Charts + Tabelle ───────────────────────────────────────────
with right:
    # Emissionen nach Business Unit
    bu_co2 = filtered.groupby("business_unit")["CO2e RFI2.7 (t)"].sum().reset_index().sort_values("CO2e RFI2.7 (t)")
    colors = ["#4CAF50","#7B1FA2","#F44336","#FF9800"]
    fig_bu = px.bar(bu_co2, x="CO2e RFI2.7 (t)", y="business_unit", orientation="h",
                    color="business_unit", color_discrete_sequence=colors,
                    labels={"CO2e RFI2.7 (t)":"CO₂ (t)", "business_unit":""},
                    title="Emissionen nach Business Unit")
    fig_bu.update_layout(
        height=220, showlegend=False, margin=dict(l=0, r=10, t=30, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(size=11), title_font_size=13,
    )
    fig_bu.update_xaxes(showgrid=False, showticklabels=False)
    fig_bu.update_yaxes(showgrid=False)
    st.plotly_chart(fig_bu, use_container_width=True, config={"displayModeBar": False})

    # CO₂ & Reisen pro Monat
    monthly = filtered.groupby("month").agg(
        co2=("CO2e RFI2.7 (t)","sum"),
        trips=("CO2e RFI2.7 (t)","count")
    ).reset_index()
    MONTH_LABELS = {1:"Jan",2:"Feb",3:"Mär",4:"Apr",5:"Mai",6:"Jun",
                    7:"Jul",8:"Aug",9:"Sep",10:"Okt",11:"Nov",12:"Dez"}
    monthly["month_name"] = monthly["month"].map(MONTH_LABELS)

    fig_monthly = go.Figure()
    fig_monthly.add_trace(go.Bar(
        x=monthly["month_name"], y=monthly["co2"],
        name="CO₂ (t)", marker_color="#F06030", opacity=0.8,
        yaxis="y1"
    ))
    fig_monthly.add_trace(go.Scatter(
        x=monthly["month_name"], y=monthly["trips"],
        name="Reisen", mode="lines+markers",
        line=dict(color="#1a6e3c", width=2.5),
        marker=dict(size=5),
        yaxis="y2"
    ))
    fig_monthly.update_layout(
        title="CO₂ & Reisen pro Monat",
        height=200, margin=dict(l=0, r=0, t=30, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(x=0, y=1.15, orientation="h", font=dict(size=10)),
        yaxis=dict(showgrid=False, showticklabels=False),
        yaxis2=dict(overlaying="y", side="right", showgrid=False, showticklabels=False),
        font=dict(size=11), title_font_size=13,
        xaxis=dict(showgrid=False),
    )
    st.plotly_chart(fig_monthly, use_container_width=True, config={"displayModeBar": False})

    # Top-Routen-Tabelle
    st.markdown("**🗺️ Top-Routen**")
    top_routes = (
        filtered.groupby(["departure_iata","arrival_iata","train_alternative_available"])
        .agg(co2=("CO2e RFI2.7 (t)","sum"), km=("km","mean"))
        .reset_index()
        .sort_values("co2", ascending=False)
        .head(5)
    )
    top_routes["Route"] = top_routes["departure_iata"] + " → " + top_routes["arrival_iata"]
    top_routes["Bahn"] = top_routes["train_alternative_available"].map({True:"Ja", False:"Nein"})

    rows_html = ""
    for _, r in top_routes.iterrows():
        bahn_class = "tag-ja" if r["Bahn"] == "Ja" else "tag-nein"
        rows_html += f"""<tr>
            <td>{r['Route']}</td>
            <td>{r['co2']:.0f} t</td>
            <td>{r['km']:,.0f} km</td>
            <td class="{bahn_class}">{r['Bahn']}</td>
        </tr>"""

    st.markdown(f"""
    <table class="route-table" width="100%">
        <thead><tr><th>Route</th><th>CO₂</th><th>Distanz</th><th>Bahn-Alt.</th></tr></thead>
        <tbody>{rows_html}</tbody>
    </table>
    """, unsafe_allow_html=True)