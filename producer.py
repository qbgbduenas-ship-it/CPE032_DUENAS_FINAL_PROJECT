import os
from io import BytesIO

import pandas as pd
import streamlit as st
import plotly.express as px
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Air Quality Monitoring Dashboard",
    page_icon="🌍",
    layout="wide"
)

# Dark theme custom CSS injection
st.markdown("""
<style>
    /* Dark Theme Core Backgrounds */
    .stApp {
        background-color: #0b0f19;
        color: #e2e8f0;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid #1f2937;
    }

    /* Metric Cards Styling */
    div[data-testid="metric-container"] {
        background-color: #111827;
        border: 1px solid #1f2937;
        border-radius: 10px;
        padding: 15px 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }

    div[data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 700;
        color: #ffffff;
    }

    div[data-testid="stMetricLabel"] {
        color: #9ca3af !important;
        font-size: 0.875rem !important;
    }

    /* Streamlit DataFrame Styling */
    div[data-testid="stDataFrame"] {
        background-color: #111827;
        border-radius: 8px;
        border: 1px solid #1f2937;
    }
</style>
""", unsafe_allow_html=True)


MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE = os.getenv("MONGODB_DATABASE", "air_quality_db")
COLLECTION = os.getenv("MONGODB_COLLECTION", "measurements")


# --------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------

@st.cache_resource
def get_collection():
    if not MONGODB_URI:
        raise ValueError("MONGODB_URI is missing from your .env file.")

    client = MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=5000
    )
    client.admin.command("ping")

    return client[DATABASE][COLLECTION]


# --------------------------------------------------
# LOAD MEASUREMENTS
# --------------------------------------------------

@st.cache_data(ttl=15)
def load_data():
    collection = get_collection()
    documents = list(collection.find({}, {"_id": 0}))

    if not documents:
        return pd.DataFrame()

    df = pd.DataFrame(documents)

    defaults = {
        "parameter": "Not provided",
        "unit": "Unit not provided",
        "location_name": "Unknown location",
        "sensor_id": "Unknown",
        "country": "Unknown",
        "value": None,
        "datetime_utc": None,
        "latitude": None,
        "longitude": None
    }

    for column, default in defaults.items():
        if column not in df.columns:
            df[column] = default

    df["unit"] = df["unit"].fillna("Unit not provided").astype(str).str.strip()
    df.loc[df["unit"].isin(["", "nan", "None"]), "unit"] = "Unit not provided"

    df["parameter"] = df["parameter"].fillna("Not provided").astype(str).str.strip()
    df.loc[df["parameter"].isin(["", "nan", "None"]), "parameter"] = "Not provided"

    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

    df["datetime_utc"] = pd.to_datetime(
        df["datetime_utc"],
        errors="coerce",
        utc=True
    )

    return df


# Helper function for Air Quality Assessment Status
def get_aqi_status(row):
    param = str(row.get("parameter", "")).lower()
    val = row.get("value")
    
    if pd.isna(val):
        return "N/A"
    
    if "pm25" in param or "pm2.5" in param:
        if val <= 12:
            return "Good"
        elif val <= 35.4:
            return "Moderate"
        else:
            return "Unhealthy"
    elif "pm10" in param or "pm1" in param:
        if val <= 54:
            return "Good"
        elif val <= 154:
            return "Moderate"
        else:
            return "Unhealthy"
    else:
        return "Good" if val < 50 else "Moderate"


# --------------------------------------------------
# EXPORT FUNCTIONS
# --------------------------------------------------

def create_excel(data):
    excel_df = data.copy()
    if "datetime_utc" in excel_df.columns:
        excel_df["datetime_utc"] = (
            pd.to_datetime(excel_df["datetime_utc"], errors="coerce", utc=True)
            .dt.tz_localize(None)
        )

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        excel_df.to_excel(writer, index=False, sheet_name="Air Quality Data")
    return output.getvalue()


def create_pdf(data):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet

    output = BytesIO()
    document = SimpleDocTemplate(output, pagesize=landscape(letter))
    styles = getSampleStyleSheet()

    elements = [
        Paragraph("Air Quality Measurement History", styles["Title"]),
        Spacer(1, 12)
    ]

    pdf_df = data.copy()
    pdf_df["datetime_utc"] = pdf_df["datetime_utc"].astype(str)

    columns = ["location_name", "parameter", "value", "unit", "datetime_utc"]
    for column in columns:
        if column not in pdf_df.columns:
            pdf_df[column] = ""

    table_data = [columns] + pdf_df[columns].fillna("").astype(str).values.tolist()
    table = Table(table_data, repeatRows=1)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightgrey])
    ]))

    elements.append(table)
    document.build(elements)
    return output.getvalue()


# --------------------------------------------------
# MEASUREMENT UNIT GUIDE
# --------------------------------------------------

def show_unit_guide():
    st.subheader("📖 Measurement Unit Guide")
    st.write("Measurement units explain the scale used to report the concentration of air pollutants.")

    unit_guide = pd.DataFrame({
        "Unit": ["µg/m³", "mg/m³", "ppm", "ppb"],
        "Full Meaning": [
            "Micrograms per cubic meter",
            "Milligrams per cubic meter",
            "Parts per million",
            "Parts per billion"
        ],
        "Description": [
            "Mass of pollutant in one cubic meter of air.",
            "A larger mass-based concentration unit.",
            "One part of a substance per one million parts.",
            "One part of a substance per one billion parts."
        ]
    })

    st.dataframe(unit_guide, use_container_width=True, hide_index=True)


# --------------------------------------------------
# SIDEBAR NAVIGATION
# --------------------------------------------------

st.sidebar.title("🌍 Air Quality Monitoring")

page = st.sidebar.radio(
    "Navigation",
    ["Live Dashboard", "Measurement History", "Analytics", "About"]
)

st.sidebar.caption("Data Source: OpenAQ")
st.sidebar.caption("Pipeline: Kafka → Spark → MongoDB")


# --------------------------------------------------
# MAIN HEADER
# --------------------------------------------------

st.title("🌍 Air Quality Monitoring Dashboard")
st.caption("Real-time environmental measurements collected through OpenAQ and processed using Kafka and Spark.")

# Load Data
try:
    df = load_data()
except Exception as error:
    st.error(f"Database connection error: {error}")
    st.stop()

if df.empty:
    st.warning("No measurements are stored yet. Start Kafka, the Producer, and Spark Consumer.")
    st.stop()


# --------------------------------------------------
# LIVE DASHBOARD
# --------------------------------------------------

if page == "Live Dashboard":

    # Metric Cards
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Measurements", f"{len(df):,}")
    col2.metric("Monitoring Locations", df["location_name"].nunique())
    col3.metric("Unique Sensors", df["sensor_id"].nunique())

    st.markdown("<br>", unsafe_allow_html=True)

    # Visualizations Row (Trends & Map)
    viz_col1, viz_col2 = st.columns([1.4, 1.0])

    with viz_col1:
        st.markdown("##### Air Pollutant Trends")
        trend_df = df.dropna(subset=["datetime_utc", "value"]).sort_values("datetime_utc")
        
        if not trend_df.empty:
            fig_trend = px.line(
                trend_df,
                x="datetime_utc",
                y="value",
                color="parameter",
                color_discrete_sequence=["#ef4444", "#10b981", "#3b82f6", "#f59e0b"]
            )
            fig_trend.update_layout(
                paper_bgcolor="rgba(17, 24, 39, 1)",
                plot_bgcolor="rgba(17, 24, 39, 1)",
                font_color="#9ca3af",
                margin=dict(l=20, r=20, t=10, b=20),
                height=280,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            fig_trend.update_xaxes(showgrid=True, gridwidth=1, gridcolor="#1f2937")
            fig_trend.update_yaxes(showgrid=True, gridwidth=1, gridcolor="#1f2937")
            st.plotly_chart(fig_trend, use_container_width=True)

    with viz_col2:
        st.markdown("##### Active Stations Map")
        map_df = df.dropna(subset=["latitude", "longitude"]).drop_duplicates(subset=["location_name"])
        if not map_df.empty:
            fig_map = px.scatter_mapbox(
                map_df,
                lat="latitude",
                lon="longitude",
                hover_name="location_name",
                zoom=5,
                color_discrete_sequence=["#10b981"]
            )
            fig_map.update_layout(
                mapbox_style="carto-darkmatter",
                paper_bgcolor="rgba(17, 24, 39, 1)",
                margin=dict(l=0, r=0, t=0, b=0),
                height=280
            )
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.info("Map coordinates currently unavailable.")

    # Latest Air Quality Readings Table
    latest = (
        df.sort_values("datetime_utc", ascending=False)
        .drop_duplicates(subset=["location_name", "sensor_id"], keep="first")
        .copy()
    )

    latest["Status"] = latest.apply(get_aqi_status, axis=1)

    display_columns = [
        "location_name",
        "parameter",
        "value",
        "unit",
        "Status",
        "datetime_utc"
    ]

    table_data = latest[display_columns].rename(columns={
        "location_name": "Location",
        "parameter": "Pollutant",
        "value": "Measurement Value",
        "unit": "Unit",
        "datetime_utc": "Date and Time (UTC)"
    })

    st.dataframe(
        table_data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Status": st.column_config.SelectboxColumn(
                "Status",
                help="Air Quality Standard Assessment",
                options=["Good", "Moderate", "Unhealthy"]
            )
        }
    )

    with st.expander("📖 What do the measurement units mean?"):
        show_unit_guide()

    st.caption("Dashboard auto-refreshes every 75 seconds.")
    if st.button("Refresh Dashboard"):
        st.cache_data.clear()
        st.rerun()

    st.markdown("""<meta http-equiv="refresh" content="75">""", unsafe_allow_html=True)


# --------------------------------------------------
# MEASUREMENT HISTORY
# --------------------------------------------------

elif page == "Measurement History":
    st.subheader("Measurement History")

    locations = ["All Locations"] + sorted(df["location_name"].dropna().unique().tolist())
    parameters = ["All Pollutants"] + sorted(df["parameter"].dropna().unique().tolist())

    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        selected_location = st.selectbox("Filter by Location", locations)
    with col_filter2:
        selected_parameter = st.selectbox("Filter by Pollutant", parameters)

    filtered = df.copy()
    if selected_location != "All Locations":
        filtered = filtered[filtered["location_name"] == selected_location]
    if selected_parameter != "All Pollutants":
        filtered = filtered[filtered["parameter"] == selected_parameter]

    st.write(f"Records found: **{len(filtered)}**")

    history_columns = ["location_name", "parameter", "value", "unit", "datetime_utc"]
    st.dataframe(
        filtered[history_columns].rename(columns={
            "location_name": "Location",
            "parameter": "Pollutant",
            "value": "Measurement Value",
            "unit": "Unit",
            "datetime_utc": "Date and Time (UTC)"
        }),
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    show_unit_guide()

    st.divider()

    st.subheader("Export Measurement History")
    csv_data = filtered.to_csv(index=False).encode("utf-8")

    col_e1, col_e2, col_e3 = st.columns(3)
    with col_e1:
        st.download_button("Download CSV", data=csv_data, file_name="air_quality_history.csv", mime="text/csv")
    with col_e2:
        st.download_button("Download Excel", data=create_excel(filtered), file_name="air_quality_history.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with col_e3:
        st.download_button("Download PDF", data=create_pdf(filtered), file_name="air_quality_history.pdf", mime="application/pdf")


# --------------------------------------------------
# ANALYTICS
# --------------------------------------------------

elif page == "Analytics":
    st.subheader("Air Quality Analytics")

    chart_data = df.dropna(subset=["value"]).copy()

    if not chart_data.empty:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Average Measurement by Pollutant")
            avg_data = chart_data.groupby(["parameter", "unit"], as_index=False)["value"].mean()
            avg_data["Pollutant and Unit"] = avg_data["parameter"] + " (" + avg_data["unit"] + ")"
            
            fig1 = px.bar(avg_data, x="Pollutant and Unit", y="value", template="plotly_dark")
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            st.markdown("#### Measurements by Location")
            loc_data = chart_data.groupby("location_name", as_index=False)["value"].mean()
            fig2 = px.bar(loc_data, x="location_name", y="value", template="plotly_dark")
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("#### Measurement Trend Over Time")
        trend_data = chart_data.dropna(subset=["datetime_utc"]).sort_values("datetime_utc")

        if not trend_data.empty:
            fig3 = px.line(
                trend_data,
                x="datetime_utc",
                y="value",
                color="parameter",
                title="Air Quality Measurement Trend",
                template="plotly_dark"
            )
            st.plotly_chart(fig3, use_container_width=True)


# --------------------------------------------------
# ABOUT
# --------------------------------------------------

elif page == "About":
    st.subheader("About the System")
    st.markdown("""
    The Air Quality Monitoring System collects environmental measurements from the OpenAQ API and processes them through a real-time data pipeline.

    ### System Architecture
    1. **OpenAQ API** – Provides air quality measurements.
    2. **Python Producer** – Retrieves and sends measurements.
    3. **Apache Kafka** – Handles real-time message streaming.
    4. **Apache Spark** – Consumes and processes incoming data.
    5. **MongoDB** – Stores processed measurements.
    6. **Streamlit** – Displays readings, history, and analytics.
    """)

    st.divider()

    show_unit_guide()

    st.divider()

    st.subheader("Database Information")
    st.write(f"Database: `{DATABASE}`")
    st.write(f"Collection: `{COLLECTION}`")
    st.write(f"Stored measurements: **{len(df)}**")