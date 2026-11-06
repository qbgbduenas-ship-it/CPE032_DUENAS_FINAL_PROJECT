import os
from io import BytesIO
from html import escape

import pandas as pd
import streamlit as st
import plotly.express as px
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Air Quality Monitoring Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE = os.getenv("MONGODB_DATABASE", "air_quality_db")
COLLECTION = os.getenv("MONGODB_COLLECTION", "measurements")


# =========================================================
# GLOBAL CSS
# =========================================================

st.html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    --bg: #0b1320;
    --panel: #101b2b;
    --panel2: #121f31;
    --border: #24334a;
    --text: #e8eef7;
    --muted: #91a0b6;
    --blue: #35b8ff;
    --green: #36d98b;
    --red: #ff5f72;
    --yellow: #f5c451;
}

html,
body,
[class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: #0b1320;
    color: #e8eef7;
}

[data-testid="stHeader"] {
    background: transparent;
}

[data-testid="stToolbar"] {
    visibility: hidden;
}

[data-testid="stSidebar"] {
    background: #0d1726;
    border-right: 1px solid #1e2b3d;
}

[data-testid="stSidebar"] > div:first-child {
    padding-top: 1.2rem;
}

.block-container {
    max-width: 1500px;
    padding: 28px 34px 42px 34px;
}

/* SIDEBAR */

.sidebar-brand {
    padding: 0 5px 20px 5px;
}

.sidebar-brand-row {
    display: flex;
    align-items: center;
    gap: 9px;
}

.sidebar-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: linear-gradient(135deg, #2ec5ff, #3be18c);
    box-shadow: 0 0 12px rgba(53,184,255,.45);
}

.sidebar-name {
    color: #eef5ff;
    font-weight: 700;
    font-size: 14px;
}

.sidebar-description {
    color: #71839b;
    font-size: 10px;
    line-height: 1.5;
    margin-top: 8px;
}

.sidebar-section {
    color: #71839b;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: .08em;
    text-transform: uppercase;
    margin-top: 20px;
    margin-bottom: 8px;
}

.sidebar-info {
    color: #d5dfec;
    font-size: 11px;
    margin-top: 3px;
}

.sidebar-footer {
    color: #596c85;
    font-size: 9px;
    text-align: center;
    margin-top: 30px;
}

/* RADIO */

[data-testid="stSidebar"] .stRadio > label {
    color: #71839b !important;
    font-size: 9px !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: .08em;
}

[data-testid="stSidebar"] .stRadio div[role="radiogroup"] {
    gap: 4px;
}

[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
    background: transparent;
    border-radius: 8px;
    padding: 8px 9px;
    color: #aab8cb !important;
}

[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover {
    background: #142238;
}

/* HEADER */

.dashboard-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;
}

.brand {
    display: flex;
    align-items: center;
    gap: 11px;
}

.brand-icon {
    width: 34px;
    height: 34px;
    border-radius: 50%;
    background: linear-gradient(135deg, #2ec5ff, #3be18c);
    display: flex;
    align-items: center;
    justify-content: center;
    color: #06111d;
    font-size: 17px;
    font-weight: 800;
    box-shadow: 0 0 18px rgba(53,184,255,.18);
}

.brand-title {
    font-size: 21px;
    font-weight: 700;
    color: #eef5ff;
    letter-spacing: -.02em;
}

.live-pill {
    border: 1px solid #1d704d;
    background: #0e2c25;
    color: #49db96;
    border-radius: 999px;
    padding: 5px 10px;
    font-size: 10px;
    font-weight: 700;
}

.subtitle {
    color: #71839b;
    font-size: 10px;
    margin-bottom: 20px;
}

/* METRIC CARDS */

.metric-card {
    background: linear-gradient(
        180deg,
        #121f31 0%,
        #0f1a2a 100%
    );

    border: 1px solid #24334a;
    border-radius: 10px;

    padding: 15px 17px;

    min-height: 88px;

    box-shadow: 0 8px 24px rgba(0,0,0,.12);
}

.metric-label {
    color: #91a0b6;
    font-size: 10px;
    font-weight: 500;
    margin-bottom: 7px;
}

.metric-value {
    color: #f4f8ff;
    font-size: 25px;
    font-weight: 700;
    line-height: 1;
}

.metric-note {
    color: #5f7895;
    font-size: 9px;
    margin-top: 7px;
}

/* PANELS */

.panel {
    background: #101b2b;
    border: 1px solid #24334a;
    border-radius: 10px;
    padding: 16px;
    box-shadow: 0 8px 24px rgba(0,0,0,.10);
}

.panel-title {
    color: #e9eff8;
    font-size: 13px;
    font-weight: 700;
    margin-bottom: 2px;
}

.panel-subtitle {
    color: #75869d;
    font-size: 9px;
    margin-bottom: 8px;
}

.section-title {
    color: #eef4fb;
    font-size: 13px;
    font-weight: 700;
    margin: 20px 0 8px 2px;
}

.small-muted {
    color: #71839b;
    font-size: 9px;
}

/* BUTTONS */

.stButton > button,
.stDownloadButton > button {
    background: #16283f;
    border: 1px solid #29415e;
    color: #dbe8f8;
    border-radius: 7px;
    font-weight: 600;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
    border-color: #35b8ff;
    color: white;
}

/* SELECTBOX */

div[data-baseweb="select"] > div {
    background: #111f32;
    border-color: #2a3d56;
}

div[data-baseweb="select"] span {
    color: #dce7f5;
}

/* DATAFRAME */

[data-testid="stDataFrame"] {
    border: 1px solid #24334a;
    border-radius: 9px;
    overflow: hidden;
}

/* EXPANDER */

[data-testid="stExpander"] {
    background: #101b2b;
    border: 1px solid #24334a;
    border-radius: 9px;
}

/* ALERTS */

[data-testid="stAlert"] {
    border-radius: 8px;
}

/* MAP */

.map-wrapper {
    background: #101b2b;
    border: 1px solid #24334a;
    border-radius: 10px;
    padding: 10px;
}

/* STATUS */

.status-good {
    color: #49db96;
}

.status-warning {
    color: #f5c451;
}

.status-danger {
    color: #ff5f72;
}
</style>
""")


# =========================================================
# MONGODB
# =========================================================

@st.cache_resource
def get_collection():

    if not MONGODB_URI:
        raise ValueError(
            "MONGODB_URI is missing from your .env file."
        )

    client = MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=5000
    )

    client.admin.command("ping")

    return client[DATABASE][COLLECTION]


# =========================================================
# LOAD DATA
# =========================================================

@st.cache_data(ttl=10)
def load_data():

    collection = get_collection()

    documents = list(
        collection.find(
            {},
            {"_id": 0}
        )
    )

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

    df["parameter"] = (
        df["parameter"]
        .fillna("Not provided")
        .astype(str)
        .str.strip()
    )

    df["unit"] = (
        df["unit"]
        .fillna("Unit not provided")
        .astype(str)
        .str.strip()
    )

    df["location_name"] = (
        df["location_name"]
        .fillna("Unknown location")
        .astype(str)
        .str.strip()
    )

    df["sensor_id"] = (
        df["sensor_id"]
        .fillna("Unknown")
        .astype(str)
        .str.strip()
    )

    df["value"] = pd.to_numeric(
        df["value"],
        errors="coerce"
    )

    df["latitude"] = pd.to_numeric(
        df["latitude"],
        errors="coerce"
    )

    df["longitude"] = pd.to_numeric(
        df["longitude"],
        errors="coerce"
    )

    df["datetime_utc"] = pd.to_datetime(
        df["datetime_utc"],
        errors="coerce",
        utc=True
    )

    return df


# =========================================================
# EXPORT FUNCTIONS
# =========================================================

def create_excel(data):

    excel_df = data.copy()

    if "datetime_utc" in excel_df.columns:

        excel_df["datetime_utc"] = (
            pd.to_datetime(
                excel_df["datetime_utc"],
                errors="coerce",
                utc=True
            )
            .dt
            .tz_localize(None)
        )

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        excel_df.to_excel(
            writer,
            index=False,
            sheet_name="Air Quality Data"
        )

    return output.getvalue()


def create_pdf(data):

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.platypus import (
        SimpleDocTemplate,
        Table,
        TableStyle,
        Paragraph,
        Spacer
    )
    from reportlab.lib.styles import getSampleStyleSheet

    output = BytesIO()

    document = SimpleDocTemplate(
        output,
        pagesize=landscape(letter)
    )

    styles = getSampleStyleSheet()

    elements = [
        Paragraph(
            "Air Quality Measurement History",
            styles["Title"]
        ),
        Spacer(1, 12)
    ]

    pdf_df = data.copy()

    columns = [
        "location_name",
        "parameter",
        "value",
        "unit",
        "datetime_utc"
    ]

    for column in columns:

        if column not in pdf_df.columns:
            pdf_df[column] = ""

    pdf_df["datetime_utc"] = (
        pdf_df["datetime_utc"]
        .astype(str)
    )

    table_data = (
        [columns]
        +
        pdf_df[
            columns
        ]
        .fillna("")
        .astype(str)
        .values
        .tolist()
    )

    table = Table(
        table_data,
        repeatRows=1
    )

    table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#16283f")
            ),

            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.HexColor("#b8c1cc")
            ),

            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                7
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    colors.white,
                    colors.HexColor("#f2f5f8")
                ]
            )
        ])
    )

    elements.append(table)

    document.build(elements)

    return output.getvalue()


# =========================================================
# SIDEBAR
# =========================================================

def show_sidebar():

    st.sidebar.html("""
    <div class="sidebar-brand">

        <div class="sidebar-brand-row">

            <div class="sidebar-dot"></div>

            <div class="sidebar-name">
                Air Quality Monitoring
            </div>

        </div>

        <div class="sidebar-description">
            Real-time environmental monitoring dashboard
        </div>

    </div>
    """)

    page = st.sidebar.radio(
        "Navigation",
        [
            "Live Dashboard",
            "Measurement History",
            "Analytics",
            "About"
        ]
    )

    st.sidebar.html("""
    <div class="sidebar-section">
        Data Source
    </div>

    <div class="sidebar-info">
        OpenAQ
    </div>

    <div class="sidebar-section">
        Pipeline
    </div>

    <div class="sidebar-info">
        Kafka → Spark → MongoDB
    </div>

    <div class="sidebar-footer">
        Air Quality Monitoring System
    </div>
    """)

    return page


# =========================================================
# HEADER
# =========================================================

def show_header():

    st.html("""
    <div class="dashboard-header">

        <div class="brand">

            <div class="brand-icon">
                ◉
            </div>

            <div class="brand-title">
                Air Quality Monitoring Dashboard
            </div>

        </div>

        <div class="live-pill">
            ● LIVE
        </div>

    </div>

    <div class="subtitle">
        Real-time environmental measurements collected through
        OpenAQ and processed using Kafka and Spark.
    </div>
    """)


# =========================================================
# METRIC CARD
# =========================================================

def metric_card(
    label,
    value,
    note
):

    st.html(f"""
    <div class="metric-card">

        <div class="metric-label">
            {escape(str(label))}
        </div>

        <div class="metric-value">
            {escape(str(value))}
        </div>

        <div class="metric-note">
            {escape(str(note))}
        </div>

    </div>
    """)


# =========================================================
# UNIT GUIDE
# =========================================================

def show_unit_guide():

    unit_guide = pd.DataFrame({
        "Unit": [
            "µg/m³",
            "mg/m³",
            "ppm",
            "ppb"
        ],

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

    st.dataframe(
        unit_guide,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# INTERACTIVE MOVING MAP
# =========================================================

def show_map(data):

    map_data = data.dropna(
        subset=[
            "latitude",
            "longitude"
        ]
    ).copy()

    if map_data.empty:

        st.html("""
        <div class="panel">

            <div class="panel-title">
                Monitoring Locations
            </div>

            <div class="panel-subtitle">
                No coordinate data available
            </div>

        </div>
        """)

        return

    map_data = map_data.sort_values(
        "datetime_utc",
        ascending=False
    )

    map_data = map_data.drop_duplicates(
        subset=[
            "location_name"
        ],
        keep="first"
    )

    map_data["Display Value"] = (
        map_data["value"]
        .round(2)
        .astype(str)
    )

    fig = px.scatter_mapbox(
        map_data,
        lat="latitude",
        lon="longitude",
        hover_name="location_name",
        hover_data={
            "parameter": True,
            "Display Value": True,
            "unit": True,
            "sensor_id": True,
            "latitude": False,
            "longitude": False,
            "value": False
        },
        zoom=4.8,
        height=330
    )

    fig.update_traces(
        marker=dict(
            size=13,
            opacity=0.9
        )
    )

    center_lat = map_data["latitude"].mean()
    center_lon = map_data["longitude"].mean()

    fig.update_layout(

        mapbox=dict(
            style="open-street-map",

            center=dict(
                lat=center_lat,
                lon=center_lon
            ),

            zoom=4.8
        ),

        margin=dict(
            l=0,
            r=0,
            t=0,
            b=0
        ),

        paper_bgcolor="#101b2b",
        plot_bgcolor="#101b2b",

        font=dict(
            color="#dce7f5"
        ),

        showlegend=False
    )

    st.html("""
    <div class="panel">

        <div class="panel-title">
            Monitoring Locations
        </div>

        <div class="panel-subtitle">
            Drag to move · Scroll to zoom · Hover for sensor details
        </div>

    </div>
    """)

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": True,
            "scrollZoom": True,
            "doubleClick": "reset",
            "displaylogo": False,
            "responsive": True
        },
        key="air_quality_map"
    )


# =========================================================
# LATEST MEASUREMENTS
# =========================================================

def show_latest_table(data):

    latest = (
        data
        .sort_values(
            "datetime_utc",
            ascending=False
        )
        .drop_duplicates(
            subset=[
                "location_name",
                "sensor_id"
            ],
            keep="first"
        )
        .head(15)
        .copy()
    )

    latest["Status"] = latest["value"].apply(
        lambda x: "Recorded"
        if pd.notna(x)
        else "Unknown"
    )

    latest = latest.rename(
        columns={
            "location_name": "Location",
            "parameter": "Pollutant",
            "value": "Measurement",
            "unit": "Unit",
            "datetime_utc": "Date and Time (UTC)"
        }
    )

    latest["Date and Time (UTC)"] = (
        latest["Date and Time (UTC)"]
        .dt
        .strftime("%Y-%m-%d %H:%M:%S")
        .fillna("N/A")
    )

    columns = [
        "Location",
        "Pollutant",
        "Measurement",
        "Unit",
        "Status",
        "Date and Time (UTC)"
    ]

    st.dataframe(
        latest[columns],
        use_container_width=True,
        hide_index=True,
        height=280
    )


# =========================================================
# LIVE DASHBOARD
# =========================================================

def show_live_dashboard(data):

    col1, col2, col3 = st.columns(3)

    with col1:

        metric_card(
            "Total Measurements",
            len(data),
            "Records stored"
        )

    with col2:

        metric_card(
            "Monitoring Locations",
            data["location_name"].nunique(),
            "Active locations"
        )

    with col3:

        metric_card(
            "Unique Sensors",
            data["sensor_id"].nunique(),
            "Detected sensors"
        )

    st.write("")

    left, right = st.columns(
        [1.55, 1],
        gap="medium"
    )

    # =====================================================
    # TREND CHART
    # =====================================================

    with left:

        st.html("""
        <div class="panel">

            <div class="panel-title">
                Air Pollutant Trends
            </div>

            <div class="panel-subtitle">
                Latest measurements over time
            </div>

        </div>
        """)

        chart_data = data.dropna(
            subset=[
                "value",
                "datetime_utc"
            ]
        ).copy()

        if not chart_data.empty:

            parameter_counts = (
                chart_data[
                    "parameter"
                ]
                .value_counts()
                .head(4)
                .index
            )

            chart_data = chart_data[
                chart_data["parameter"].isin(
                    parameter_counts
                )
            ]

            fig = px.line(
                chart_data.sort_values(
                    "datetime_utc"
                ),
                x="datetime_utc",
                y="value",
                color="parameter"
            )

            fig.update_layout(
                height=330,

                margin=dict(
                    l=8,
                    r=8,
                    t=20,
                    b=8
                ),

                paper_bgcolor="#101b2b",
                plot_bgcolor="#101b2b",

                font=dict(
                    color="#91a0b6",
                    size=9
                ),

                legend=dict(
                    orientation="h",
                    y=1.08,
                    x=0
                ),

                xaxis=dict(
                    gridcolor="#203049",
                    title=""
                ),

                yaxis=dict(
                    gridcolor="#203049",
                    title=""
                )
            )

            fig.update_traces(
                line=dict(
                    width=2
                )
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
                config={
                    "displayModeBar": False
                }
            )

        else:

            st.info(
                "No numeric measurements are available."
            )

    # =====================================================
    # MAP
    # =====================================================

    with right:

        show_map(data)

    # =====================================================
    # TABLE
    # =====================================================

    st.html("""
    <div class="section-title">
        Latest Measurements
    </div>
    """)

    show_latest_table(data)

    latest_time = data["datetime_utc"].max()

    if pd.notna(latest_time):

        latest_text = latest_time.strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        )

    else:

        latest_text = "No timestamp available"

    st.html(f"""
    <div class="small-muted">
        Last measurement: {escape(latest_text)}
        · Data refreshes automatically every 15 seconds.
    </div>
    """)

    st.write("")

    if st.button(
        "↻ Refresh Dashboard",
        key="manual_refresh"
    ):

        st.cache_data.clear()
        st.rerun()

    with st.expander(
        "Measurement Unit Guide"
    ):

        show_unit_guide()


# =========================================================
# MEASUREMENT HISTORY
# =========================================================

def show_measurement_history(data):

    st.html("""
    <div class="section-title">
        Measurement History
    </div>
    """)

    col1, col2 = st.columns(2)

    locations = (
        ["All Locations"]
        +
        sorted(
            data[
                "location_name"
            ]
            .dropna()
            .unique()
            .tolist()
        )
    )

    parameters = (
        ["All Pollutants"]
        +
        sorted(
            data[
                "parameter"
            ]
            .dropna()
            .unique()
            .tolist()
        )
    )

    with col1:

        selected_location = st.selectbox(
            "Location",
            locations
        )

    with col2:

        selected_parameter = st.selectbox(
            "Pollutant",
            parameters
        )

    filtered = data.copy()

    if selected_location != "All Locations":

        filtered = filtered[
            filtered[
                "location_name"
            ] == selected_location
        ]

    if selected_parameter != "All Pollutants":

        filtered = filtered[
            filtered[
                "parameter"
            ] == selected_parameter
        ]

    metric_card(
        "Records Found",
        len(filtered),
        "Current filter result"
    )

    st.write("")

    display = filtered.copy()

    display = display.rename(
        columns={
            "location_name": "Location",
            "parameter": "Pollutant",
            "value": "Measurement",
            "unit": "Unit",
            "datetime_utc": "Date and Time (UTC)"
        }
    )

    display["Date and Time (UTC)"] = (
        display[
            "Date and Time (UTC)"
        ]
        .dt
        .strftime("%Y-%m-%d %H:%M:%S")
        .fillna("N/A")
    )

    columns = [
        "Location",
        "Pollutant",
        "Measurement",
        "Unit",
        "Date and Time (UTC)"
    ]

    st.dataframe(
        display[
            columns
        ],
        use_container_width=True,
        hide_index=True,
        height=430
    )

    st.html("""
    <div class="section-title">
        Export Measurement History
    </div>
    """)

    csv_data = filtered.to_csv(
        index=False
    ).encode("utf-8")

    col1, col2, col3 = st.columns(3)

    with col1:

        st.download_button(
            "Download CSV",
            data=csv_data,
            file_name="air_quality_history.csv",
            mime="text/csv"
        )

    with col2:

        st.download_button(
            "Download Excel",
            data=create_excel(filtered),
            file_name="air_quality_history.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    with col3:

        st.download_button(
            "Download PDF",
            data=create_pdf(filtered),
            file_name="air_quality_history.pdf",
            mime="application/pdf"
        )

    with st.expander(
        "Measurement Unit Guide"
    ):

        show_unit_guide()


# =========================================================
# ANALYTICS
# =========================================================

def show_analytics(data):

    st.html("""
    <div class="section-title">
        Air Quality Analytics
    </div>
    """)

    chart_data = data.dropna(
        subset=[
            "value"
        ]
    ).copy()

    if chart_data.empty:

        st.info(
            "No numeric measurements are available for analytics."
        )

        return

    left, right = st.columns(2)

    # =====================================================
    # AVERAGE POLLUTANT
    # =====================================================

    with left:

        average_data = (
            chart_data
            .groupby(
                [
                    "parameter",
                    "unit"
                ],
                as_index=False
            )["value"]
            .mean()
        )

        average_data["Pollutant"] = (
            average_data[
                "parameter"
            ]
            +
            " ("
            +
            average_data[
                "unit"
            ]
            +
            ")"
        )

        fig = px.bar(
            average_data,
            x="Pollutant",
            y="value"
        )

        fig.update_layout(
            height=330,

            margin=dict(
                l=8,
                r=8,
                t=20,
                b=8
            ),

            paper_bgcolor="#101b2b",
            plot_bgcolor="#101b2b",

            font=dict(
                color="#91a0b6",
                size=9
            ),

            xaxis=dict(
                gridcolor="#203049",
                title=""
            ),

            yaxis=dict(
                gridcolor="#203049",
                title=""
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                "displayModeBar": False
            }
        )

    # =====================================================
    # LOCATION AVERAGE
    # =====================================================

    with right:

        location_data = (
            chart_data
            .groupby(
                "location_name",
                as_index=False
            )["value"]
            .mean()
            .sort_values(
                "value",
                ascending=False
            )
            .head(15)
        )

        fig = px.bar(
            location_data,
            x="location_name",
            y="value"
        )

        fig.update_layout(
            height=330,

            margin=dict(
                l=8,
                r=8,
                t=20,
                b=8
            ),

            paper_bgcolor="#101b2b",
            plot_bgcolor="#101b2b",

            font=dict(
                color="#91a0b6",
                size=9
            ),

            xaxis=dict(
                gridcolor="#203049",
                title=""
            ),

            yaxis=dict(
                gridcolor="#203049",
                title=""
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                "displayModeBar": False
            }
        )

    # =====================================================
    # TREND
    # =====================================================

    trend_data = (
        chart_data
        .dropna(
            subset=[
                "datetime_utc"
            ]
        )
        .sort_values(
            "datetime_utc"
        )
    )

    if not trend_data.empty:

        fig = px.line(
            trend_data,
            x="datetime_utc",
            y="value",
            color="parameter"
        )

        fig.update_layout(
            height=360,

            margin=dict(
                l=8,
                r=8,
                t=20,
                b=8
            ),

            paper_bgcolor="#101b2b",
            plot_bgcolor="#101b2b",

            font=dict(
                color="#91a0b6",
                size=9
            ),

            xaxis=dict(
                gridcolor="#203049",
                title=""
            ),

            yaxis=dict(
                gridcolor="#203049",
                title=""
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                "displayModeBar": False
            }
        )

    with st.expander(
        "Measurement Unit Guide"
    ):

        show_unit_guide()


# =========================================================
# ABOUT
# =========================================================

def show_about(data):

    st.html("""
    <div class="section-title">
        About the System
    </div>

    <div class="panel">

        <div class="panel-title">
            Air Quality Monitoring System
        </div>

        <div class="panel-subtitle">
            Real-time environmental measurements collected through
            OpenAQ and processed using Kafka, Spark, and MongoDB.
        </div>

        <p style="
            color:#b4c1d2;
            font-size:12px;
            line-height:1.7;
        ">
            The system collects monitoring-station measurements,
            streams the records through Kafka, processes incoming
            data through Spark, stores the results in MongoDB,
            and presents the processed measurements through this
            Streamlit dashboard.
        </p>

    </div>
    """)

    st.html("""
    <div class="section-title">
        System Pipeline
    </div>
    """)

    pipeline = pd.DataFrame({
        "Component": [
            "OpenAQ API",
            "Python Producer",
            "Apache Kafka",
            "Apache Spark",
            "MongoDB",
            "Streamlit"
        ],

        "Role": [
            "Provides air quality measurements",
            "Retrieves and sends measurements",
            "Handles real-time message streaming",
            "Consumes and processes incoming data",
            "Stores processed measurements",
            "Displays readings, history, and analytics"
        ]
    })

    st.dataframe(
        pipeline,
        use_container_width=True,
        hide_index=True
    )

    st.html("""
    <div class="section-title">
        Database Information
    </div>
    """)

    st.html(f"""
    <div class="panel">

        <div style="
            display:flex;
            gap:40px;
            flex-wrap:wrap;
        ">

            <div>

                <div class="small-muted">
                    Database
                </div>

                <div style="
                    color:#e9f0fa;
                    font-size:12px;
                    margin-top:4px;
                ">
                    {escape(DATABASE)}
                </div>

            </div>

            <div>

                <div class="small-muted">
                    Collection
                </div>

                <div style="
                    color:#e9f0fa;
                    font-size:12px;
                    margin-top:4px;
                ">
                    {escape(COLLECTION)}
                </div>

            </div>

            <div>

                <div class="small-muted">
                    Stored Measurements
                </div>

                <div style="
                    color:#e9f0fa;
                    font-size:12px;
                    margin-top:4px;
                ">
                    {len(data)}
                </div>

            </div>

        </div>

    </div>
    """)

    with st.expander(
        "Measurement Unit Guide"
    ):

        show_unit_guide()


# =========================================================
# MAIN
# =========================================================

page = show_sidebar()

try:

    data = load_data()

except Exception as error:

    show_header()

    st.error(
        f"Database connection error: {error}"
    )

    st.stop()


show_header()


if data.empty:

    st.warning(
        "No measurements are stored yet. "
        "Start Kafka, the Producer, and Spark Consumer."
    )

    st.stop()


# =========================================================
# PAGE ROUTING
# =========================================================

if page == "Live Dashboard":

    # Automatically reruns this section every 15 seconds.
    # The map will therefore receive newly inserted
    # MongoDB locations/measurements automatically.

    @st.fragment(run_every="15s")
    def live_page():

        current_data = load_data()

        show_live_dashboard(
            current_data
        )

    live_page()


elif page == "Measurement History":

    show_measurement_history(
        data
    )


elif page == "Analytics":

    show_analytics(
        data
    )


elif page == "About":

    show_about(
        data
    )