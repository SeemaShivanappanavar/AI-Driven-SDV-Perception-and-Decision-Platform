import json
import os
import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# ==HTML-CLEAN-FIX==
from streamlit.delta_generator import DeltaGenerator as _DG
if not getattr(_DG.markdown, "_html_clean", False):
    _orig_md = _DG.markdown
    def _clean_md(self, body, *args, **kwargs):
        wants_html = kwargs.get("unsafe_allow_html", False) or (args and args[0] is True)
        if wants_html and isinstance(body, str):
            body = "\n".join(l.strip() for l in body.splitlines() if l.strip())
        return _orig_md(self, body, *args, **kwargs)
    _clean_md._html_clean = True
    _DG.markdown = _clean_md
    st.markdown = lambda body, *a, **k: _DG.markdown(st._main, body, *a, **k)
# ==END-HTML-CLEAN-FIX==


from kuksa_client.grpc import VSSClient, Datapoint


# ============================================================
# PATHS AND CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = BASE_DIR / "dashboard" / "data" / "sdv_history.db"
CAMERA_PATH = BASE_DIR / "dashboard" / "static" / "latest_frame.jpg"

EVALUATION_PATH = BASE_DIR / "evaluation" / "evaluation_results_corrected.csv"
LOGS_PATH = BASE_DIR / "logs"

KUKSA_HOST = "127.0.0.1"
KUKSA_PORT = 55555
VIDEO_STREAM_URL = os.getenv(
    "VIDEO_STREAM_URL",
    "http://127.0.0.1:5002/video_feed"
)

DISTANCE_SIGNAL = "Vehicle.Simulation.ObstacleDistance"

SIGNALS = [
    "Vehicle.Perception.FrameData",
    "Vehicle.Perception.IntegrityStatus",
    "Vehicle.Decision.Status",
    DISTANCE_SIGNAL
]


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="SDV Intelligence Platform",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# GLOBAL CSS
# ============================================================

st.markdown("""
<style>

/* =========================================================
   GLOBAL THEME
========================================================= */

:root {
    color-scheme: light;

    --background: #F3F6FA;
    --surface: #FFFFFF;
    --sidebar: #101D32;
    --primary: #2563EB;
    --heading: #172B4D;
    --text: #344054;
    --muted: #667085;
    --border: #E2E8F0;
    --success: #15803D;
    --danger: #DC2626;
    --warning: #D97706;
}

html, body, [class*="css"] {
    font-family: Arial, Helvetica, sans-serif !important;
    font-size: 14px !important;
}

/* MAIN BACKGROUND */

.stApp {
    background-color: var(--background) !important;
    color: var(--text) !important;
}

[data-testid="stAppViewContainer"] {
    background-color: var(--background) !important;
}

[data-testid="stMain"] {
    background-color: var(--background) !important;
}

[data-testid="stHeader"] {
    background-color: var(--background) !important;
}

/* MAIN CONTENT WIDTH */

.main .block-container {
    max-width: 1450px !important;
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
    padding-left: 2.2rem !important;
    padding-right: 2.2rem !important;
}

/* =========================================================
   MAIN TEXT
========================================================= */

.stApp p,
.stApp li,
.stApp label,
.stApp .stMarkdown {
    color: var(--text) !important;
    font-size: 14px !important;
    line-height: 1.55 !important;
}

.stApp h1 {
    color: var(--heading) !important;
    font-size: 29px !important;
    font-weight: 750 !important;
}

.stApp h2 {
    color: var(--heading) !important;
    font-size: 23px !important;
    font-weight: 700 !important;
}

.stApp h3 {
    color: var(--heading) !important;
    font-size: 18px !important;
    font-weight: 700 !important;
}

.stApp h4 {
    color: var(--heading) !important;
    font-size: 16px !important;
    font-weight: 650 !important;
}

.stCaption,
[data-testid="stCaptionContainer"] {
    color: var(--muted) !important;
    font-size: 12px !important;
}

/* =========================================================
   SIDEBAR
========================================================= */

[data-testid="stSidebar"] {
    background-color: var(--sidebar) !important;
    min-width: 260px !important;
    max-width: 280px !important;
}

[data-testid="stSidebar"] > div {
    background-color: var(--sidebar) !important;
}

[data-testid="stSidebarContent"] {
    background-color: var(--sidebar) !important;
}

[data-testid="stSidebar"] * {
    color: #F8FAFC !important;
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #FFFFFF !important;
}

[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label {
    color: #DCE6F3 !important;
    font-size: 13px !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label {
    background-color: transparent !important;
    border-radius: 8px !important;
    padding: 9px 10px !important;
    margin-bottom: 4px !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background-color: #263B59 !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
    background-color: #244D91 !important;
}

[data-testid="stSidebar"] hr {
    border-color: #34445B !important;
}

/* Sidebar collapsed/expanded button */

[data-testid="stSidebarCollapseButton"] button,
[data-testid="stSidebarNavCollapseButton"] button {
    color: #FFFFFF !important;
}

/* =========================================================
   HERO SECTION
========================================================= */

.hero {
    background: linear-gradient(
        110deg,
        #142B4C,
        #1D4778
    );

    padding: 27px 30px;
    border-radius: 14px;
    margin-bottom: 24px;
    border: 1px solid #294C78;
}

.hero h1 {
    color: #FFFFFF !important;
    font-size: 29px !important;
    margin-bottom: 7px !important;
}

.hero p {
    color: #DCE8F7 !important;
    font-size: 14px !important;
    margin-bottom: 0 !important;
}

/* =========================================================
   METRIC CARDS
========================================================= */

[data-testid="stMetric"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E1E7EF !important;
    border-radius: 11px !important;
    padding: 15px 17px !important;
    box-shadow: 0 2px 5px rgba(16, 29, 50, 0.04);
}

[data-testid="stMetricLabel"] {
    color: #667085 !important;
    font-size: 12px !important;
}

[data-testid="stMetricValue"] {
    color: #172B4D !important;
    font-size: 25px !important;
    font-weight: 750 !important;
}

[data-testid="stMetricDelta"] {
    font-size: 12px !important;
}

/* =========================================================
   CARDS AND CONTAINERS
========================================================= */

[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E1E7EF !important;
    border-radius: 12px !important;
}

[data-testid="stExpander"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E1E7EF !important;
    border-radius: 9px !important;
}

[data-testid="stExpander"] summary {
    color: #172B4D !important;
}

/* =========================================================
   BUTTONS
========================================================= */

.stButton > button {
    background-color: #2563EB !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 7px !important;
    padding: 8px 17px !important;
    font-size: 13px !important;
    font-weight: 600 !important;
}

.stButton > button:hover {
    background-color: #1D4ED8 !important;
    color: #FFFFFF !important;
    border: none !important;
}

/* =========================================================
   SELECT BOX AND INPUTS
========================================================= */

[data-baseweb="select"] > div {
    background-color: #FFFFFF !important;
    border-color: #CBD5E1 !important;
    color: #172B4D !important;
}

[data-baseweb="select"] span {
    color: #172B4D !important;
}

[data-baseweb="popover"] {
    background-color: #FFFFFF !important;
}

[data-baseweb="menu"] {
    background-color: #FFFFFF !important;
}

[data-baseweb="menu"] * {
    color: #172B4D !important;
}

.stTextInput input,
.stNumberInput input,
.stTextArea textarea {
    background-color: #FFFFFF !important;
    color: #172B4D !important;
    border: 1px solid #CBD5E1 !important;
}

/* =========================================================
   DATA TABLES
========================================================= */

[data-testid="stDataFrame"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E1E7EF !important;
    border-radius: 9px !important;
}

[data-testid="stTable"] {
    background-color: #FFFFFF !important;
}

/* =========================================================
   ALERTS
========================================================= */

[data-testid="stAlert"] {
    border-radius: 9px !important;
}

/* =========================================================
   STATUS LABELS
========================================================= */

.status-valid {
    color: #15803D !important;
    font-weight: 700;
}

.status-fault {
    color: #DC2626 !important;
    font-weight: 700;
}

.status-warning {
    color: #D97706 !important;
    font-weight: 700;
}

/* =========================================================
   FOOTER
========================================================= */

.footer {
    text-align: center;
    padding: 18px;
    color: #667085;
    font-size: 12px;
}

hr {
    border-color: #E2E8F0 !important;
}

/* ==READABILITY-FIX-START== */
html { font-size: clamp(15px, 0.55vw + 9px, 18px) !important; }

html body .stApp,
html body [data-testid="stAppViewContainer"],
html body [data-testid="stMain"],
html body [data-testid="stHeader"] { background-color:#0b1120 !important; color:#e5e7eb !important; }
html body [data-testid="stHeader"] * { color:#e2e8f0 !important; }
.stApp .block-container { padding:2rem 2.5rem 3rem 2.5rem !important; max-width:100% !important; }

.stApp h1,.stApp h2,.stApp h3,.stApp h4,.stApp h5 { color:#ffffff !important; }
.stApp h1 { font-size:2.1rem !important; }
.stApp h2 { font-size:1.7rem !important; }
.stApp h3 { font-size:1.35rem !important; }
.stApp h4 { font-size:1.15rem !important; }
.stApp p,.stApp li,.stApp label,.stApp span,
.stApp [data-testid="stMarkdownContainer"] { color:#e2e8f0 !important; }
.stApp p,.stApp li { font-size:1rem !important; line-height:1.55 !important; }
.stApp hr { border-color:#334155 !important; }

.stApp .status-valid { color:#22c55e !important; font-weight:700; }
.stApp .status-fault { color:#ef4444 !important; font-weight:700; }
.stApp .status-alert { color:#f97316 !important; font-weight:700; }
.stApp .small-note { color:#94a3b8 !important; font-size:0.9rem !important; }

.stApp [data-testid="stCaptionContainer"],
.stApp [data-testid="stCaptionContainer"] *,
.stApp [data-testid="stImageCaption"] { color:#94a3b8 !important; font-size:0.9rem !important; }

.stApp .hero { background:linear-gradient(120deg,#172554,#172033) !important; padding:1.6rem 1.8rem !important; border:1px solid #334155; border-radius:16px; margin-bottom:1.5rem; }
.stApp .hero h1 { font-size:2.1rem !important; margin:0 0 .4rem 0; }
.stApp .hero p { color:#cbd5e1 !important; font-size:1.05rem !important; }
.stApp .section-card { background:#172033 !important; border:1px solid #334155; border-radius:12px; padding:1.2rem 1.4rem; }
.stApp .section-card h3 { font-size:1.2rem !important; margin:.5rem 0 .1rem 0; }
.stApp .section-card p { color:#cbd5e1 !important; margin:0 0 .3rem 0; }

.stApp [data-testid="stMetric"] { background:#172033 !important; border:1px solid #334155; border-radius:12px; padding:1rem 1.1rem; }
.stApp [data-testid="stMetricLabel"],
.stApp [data-testid="stMetricLabel"] * { color:#cbd5e1 !important; font-size:0.95rem !important; }
.stApp [data-testid="stMetricValue"],
.stApp [data-testid="stMetricValue"] * { color:#ffffff !important; font-size:1.9rem !important; font-weight:700; }

.stApp [data-testid="stAlert"],
.stApp [data-testid="stAlertContainer"],
.stApp div[data-baseweb="notification"] { background:#1e293b !important; border:1px solid #475569 !important; border-radius:10px !important; }
.stApp [data-testid="stAlert"] *,
.stApp [data-testid="stAlert"] p { color:#f8fafc !important; font-size:1rem !important; }
.stApp [data-testid="stAlert"]:has([data-testid="stAlertContentSuccess"]) { border-left:6px solid #22c55e !important; }
.stApp [data-testid="stAlert"]:has([data-testid="stAlertContentError"]) { border-left:6px solid #ef4444 !important; }
.stApp [data-testid="stAlert"]:has([data-testid="stAlertContentWarning"]) { border-left:6px solid #f59e0b !important; }
.stApp [data-testid="stAlert"]:has([data-testid="stAlertContentInfo"]) { border-left:6px solid #38bdf8 !important; }

.stApp [data-testid="stSidebar"],
.stApp [data-testid="stSidebar"] > div:first-child,
.stApp [data-testid="stSidebarContent"] { background:#111827 !important; }
.stApp [data-testid="stSidebar"] { min-width:280px !important; }
.stApp [data-testid="stSidebar"] * { color:#f1f5f9 !important; }
.stApp [data-testid="stSidebar"] [data-testid="stRadio"] label p { font-size:1.05rem !important; }

.stApp div[data-baseweb="select"] > div,
.stApp div[data-baseweb="input"] > div,
.stApp .stTextInput input { background:#172033 !important; border:1px solid #475569 !important; color:#f1f5f9 !important; }
.stApp div[data-baseweb="select"] *,
.stApp div[data-baseweb="select"] input { color:#f1f5f9 !important; -webkit-text-fill-color:#f1f5f9 !important; }
.stApp div[data-baseweb="select"] svg { fill:#cbd5e1 !important; }

html body div[data-baseweb="popover"],
html body div[data-baseweb="popover"] > div,
html body div[data-baseweb="menu"],
html body ul[role="listbox"] { background:#1e293b !important; }
html body li[role="option"] { background:#1e293b !important; color:#f1f5f9 !important; font-size:1rem !important; }
html body li[role="option"] * { color:#f1f5f9 !important; }
html body li[role="option"]:hover,
html body li[aria-selected="true"] { background:#1d4ed8 !important; }

.stApp [data-testid="stDataFrame"] { border:1px solid #334155; border-radius:8px; overflow:hidden; }

.stApp [data-testid="stExpander"] { background:#111827 !important; border:1px solid #334155 !important; border-radius:10px; }
.stApp [data-testid="stExpander"] details { background:#111827 !important; }
.stApp [data-testid="stExpander"] summary,
.stApp [data-testid="stExpander"] summary * { color:#f1f5f9 !important; font-size:1.05rem !important; }

.stApp [data-testid="stCodeBlock"],
.stApp [data-testid="stCodeBlock"] pre { background:#0f172a !important; }
.stApp [data-testid="stCodeBlock"] code,
.stApp [data-testid="stCodeBlock"] code * { color:#e2e8f0 !important; font-size:0.95rem !important; }
.stApp :not(pre) > code { background:#0f172a !important; color:#7dd3fc !important; }

.stApp [data-testid="stJson"] { background:#0f172a !important; border:1px solid #334155; border-radius:8px; padding:.6rem; }
.stApp [data-testid="stJson"] * { color:#e2e8f0 !important; background-color:transparent !important; }
.stApp [data-testid="stJson"] .object-key,
.stApp [data-testid="stJson"] .object-key * { color:#7dd3fc !important; }
.stApp [data-testid="stJson"] .string-value,
.stApp [data-testid="stJson"] .string-value * { color:#86efac !important; }

.stApp .stButton button { background:#2563eb !important; color:#ffffff !important; border:none; border-radius:8px; font-size:1rem !important; }
.stApp .stButton button * { color:#ffffff !important; }
.stApp .stButton button:hover { background:#1d4ed8 !important; }
/* ==READABILITY-FIX-END== */

</style>
""", unsafe_allow_html=True)


# ============================================================
# SHARED KUKSA STATE
# ============================================================

@st.cache_resource
def get_shared_state():

    return {
        "perception": None,
        "integrity": None,
        "decision": None,
        "simulation_distance": None,
        "connected": False,
        "last_update": None,
        "error": None,
        "lock": threading.Lock(),
        "started": False
    }


STATE = get_shared_state()


# ============================================================
# JSON PARSER
# ============================================================

def parse_payload(value):

    if value is None:
        return None

    if isinstance(value, dict):
        return value

    try:
        return json.loads(value)

    except (json.JSONDecodeError, TypeError):
        return None


# ============================================================
# KUKSA LISTENER
# ============================================================

def kuksa_listener():

    while True:

        try:

            with VSSClient(KUKSA_HOST, KUKSA_PORT) as client:

                with STATE["lock"]:
                    STATE["connected"] = True
                    STATE["error"] = None

                for updates in client.subscribe_current_values(SIGNALS):

                    for path, datapoint in updates.items():

                        if path == DISTANCE_SIGNAL:
                            data = datapoint.value
                        else:
                            data = parse_payload(datapoint.value)

                        if data is None:
                            continue

                        with STATE["lock"]:

                            if path == "Vehicle.Perception.FrameData":
                                STATE["perception"] = data

                            elif path == "Vehicle.Perception.IntegrityStatus":
                                STATE["integrity"] = data

                            elif path == "Vehicle.Decision.Status":
                                STATE["decision"] = data

                            elif path == DISTANCE_SIGNAL:
                                STATE["simulation_distance"] = float(data)

                            STATE["last_update"] = time.time()

        except Exception as error:

            with STATE["lock"]:
                STATE["connected"] = False
                STATE["error"] = str(error)

            time.sleep(3)


def start_kuksa_listener():

    if STATE["started"]:
        return

    STATE["started"] = True

    thread = threading.Thread(
        target=kuksa_listener,
        daemon=True
    )

    thread.start()


start_kuksa_listener()


# ============================================================
# DATABASE FUNCTIONS
# ============================================================

def get_db_connection():

    if not DB_PATH.exists():
        return None

    return sqlite3.connect(
        str(DB_PATH),
        timeout=10
    )


def get_database_statistics():

    connection = get_db_connection()

    if connection is None:
        return {}

    try:

        result = pd.read_sql_query(
            """
            SELECT signal, COUNT(*)
            FROM events
            GROUP BY signal
            """,
            connection
        )

        return dict(zip(result.iloc[:, 0], result.iloc[:, 1]))

    finally:
        connection.close()


def get_sessions():

    connection = get_db_connection()

    if connection is None:
        return []

    try:

        result = pd.read_sql_query(
            """
            SELECT DISTINCT session_id
            FROM events
            WHERE session_id IS NOT NULL
            ORDER BY session_id DESC
            """,
            connection
        )

        return result["session_id"].tolist()

    finally:
        connection.close()


def get_history(session_id=None, signal=None, limit=1000):

    connection = get_db_connection()

    if connection is None:
        return pd.DataFrame()

    try:

        query = """
            SELECT
                id,
                signal,
                session_id,
                sequence_number,
                received_at_ms,
                payload
            FROM events
            WHERE 1=1
        """

        parameters = []

        if session_id:
            query += " AND session_id = ?"
            parameters.append(session_id)

        if signal and signal != "All":
            query += " AND signal = ?"
            parameters.append(signal)

        query += " ORDER BY id DESC LIMIT ?"
        parameters.append(limit)

        return pd.read_sql_query(
            query,
            connection,
            params=parameters
        )

    finally:
        connection.close()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div style="text-align:center;padding:18px 5px 10px 5px;">

            <div style="font-size:38px;">🚗</div>

            <div style="
                color:#FFFFFF;
                font-size:18px;
                font-weight:750;
                letter-spacing:0.5px;
            ">
                SDV INTELLIGENCE
            </div>

            <div style="
                color:#B8C9DF;
                font-size:11px;
                margin-top:5px;
            ">
                AI-Driven Vehicle Platform
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    st.markdown(
        """
        <div style="
            color:#93B4DC;
            font-size:11px;
            font-weight:700;
            letter-spacing:1px;
            margin-bottom:8px;
        ">
            MAIN MENU
        </div>
        """,
        unsafe_allow_html=True
    )

    page = st.radio(
        "Navigation",
        [
            "Live Vehicle View",
            "History Explorer",
            "Research Experiments",
            "System Architecture"
        ],
        index=0,
        label_visibility="collapsed"
    )

    st.divider()

    @st.fragment(run_every="1s")
    def sidebar_connection_status():
        with STATE["lock"]:
            connected = STATE["connected"]

        if connected:
            st.success("● KUKSA CONNECTED")
        else:
            st.error("● KUKSA DISCONNECTED")

    sidebar_connection_status()

    st.markdown(
        """
        <div style="
            background:#1A2D47;
            padding:12px;
            border-radius:8px;
            margin-top:18px;
        ">
            <div style="
                color:#93B4DC;
                font-size:10px;
                font-weight:700;
                letter-spacing:1px;
            ">
                RESEARCH PROJECT
            </div>

            <div style="
                color:#FFFFFF;
                font-size:12px;
                margin-top:7px;
                line-height:1.5;
            ">
                Data-Integrity-Aware
                Perception-to-Decision Framework
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# MAIN HERO
# ============================================================

st.markdown(
    """
    <div class="hero">

        <h1>Software-Defined Vehicle Platform</h1>

        <p>
            AI-driven perception | Vehicle data integrity |
            Fault-aware decision-making
        </p>

    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# PAGE 1: LIVE VEHICLE VIEW
# ============================================================

if page == "Live Vehicle View":

    @st.fragment(run_every="1s")
    def live_vehicle_view():

        with STATE["lock"]:

            perception = STATE["perception"]
            integrity = STATE["integrity"]
            decision = STATE["decision"]
            connected = STATE["connected"]
            last_update = STATE["last_update"]
            error = STATE["error"]

        st.subheader("Live Vehicle Monitoring")

        # SIMULATED OBSTACLE DISTANCE CONTROL
        st.markdown("### 📏 Obstacle Distance Simulation")
        st.caption(
            "SIMULATION INPUT — This distance is manually controlled "
            "and is NOT measured by the camera."
        )

        distance_col, publish_col = st.columns([3, 1])

        with distance_col:
            selected_distance = st.slider(
                "Simulated obstacle distance (metres)",
                min_value=0.0,
                max_value=50.0,
                value=25.0,
                step=0.5,
                key="simulated_obstacle_distance"
            )

        with publish_col:
            st.write("")
            st.write("")
            publish_distance = st.button(
                "Publish Distance",
                use_container_width=True,
                key="publish_simulated_distance"
            )

        if publish_distance:
            try:
                with VSSClient(KUKSA_HOST, KUKSA_PORT) as distance_client:
                    distance_client.set_current_values({
                        DISTANCE_SIGNAL: Datapoint(float(selected_distance))
                    })

                with STATE["lock"]:
                    STATE["simulation_distance"] = float(selected_distance)

                st.success(
                    f"Published simulated distance: {selected_distance:.1f} m"
                )

            except Exception as error:
                st.error(f"Could not publish distance to KUKSA: {error}")

        with STATE["lock"]:
            displayed_distance = STATE["simulation_distance"]

        if displayed_distance is None:
            st.info("No simulated distance has been published yet.")
        else:
            st.metric(
                "Current published simulated distance",
                f"{displayed_distance:.1f} m"
            )

        st.markdown("---")


        if connected:
            st.success("Connected to KUKSA Databroker")
        else:
            st.error("KUKSA connection unavailable")

        if error:
            st.caption(error)

        # CAMERA AND DECISION AREA

        left, right = st.columns([2.2, 1])

        with left:

            st.markdown("### 📷 Live Camera Feed")

            components.html(
                """
                <div style="width:100%; text-align:center;">
                    <img
                        src="__VIDEO_STREAM_URL__"
                        style="width:100%; height:auto; border-radius:10px;"
                        alt="Live YOLO annotated camera feed">
                </div>
                """.replace("__VIDEO_STREAM_URL__", VIDEO_STREAM_URL),
                height=650,
            )

            st.success("Live Raspberry Pi YOLO video stream")

        with right:

            st.markdown("### 🚘 Vehicle Status")

            if perception:

                st.metric(
                    "Detected Objects",
                    perception.get("detection_count", 0)
                )

                st.metric(
                    "Frame Number",
                    perception.get("sequence_number", "N/A")
                )

                st.metric(
                    "Perception Latency",
                    f"{perception.get('perception_latency_ms', 0):.2f} ms"
                )

            else:

                st.info("Waiting for perception data")

            st.divider()

            st.markdown("### 🧠 Decision Output")

            if decision:

                decision_value = decision.get(
                    "decision", "UNKNOWN"
                )

                reason = decision.get(
                    "reason", "No reason available"
                )

                if decision_value == "ALERT":
                    st.error(f"🚨 {decision_value}")

                elif decision_value == "CAUTION":
                    st.warning(f"⚠️ {decision_value}")

                else:
                    st.success(f"🟢 {decision_value}")

                st.write(reason)

            else:
                st.info("Waiting for decision data")

        st.divider()

        # DETECTIONS

        st.markdown("### Object Detection Details")

        if perception:

            detections = perception.get("detections", [])

            if detections:

                detection_df = pd.DataFrame(detections)

                st.dataframe(
                    detection_df,
                    use_container_width=True,
                    hide_index=True
                )

            else:

                st.info("No objects detected in this frame.")

        else:

            st.info("Perception information unavailable.")

        st.divider()

        # INTEGRITY

        st.markdown("### 🛡️ Data Integrity Monitoring")

        if integrity:

            integrity_status = integrity.get(
                "integrity_status", "UNKNOWN"
            )

            if integrity_status == "VALID":
                st.success("INTEGRITY STATUS: VALID")
            else:
                st.error(f"INTEGRITY STATUS: {integrity_status}")

            faults = integrity.get("faults", [])

            if faults:

                st.markdown("#### Detected Faults")

                for fault in faults:
                    st.write(f"• {fault}")

            statistics = integrity.get("statistics", {})

            if statistics:

                st.markdown("#### Cumulative Statistics")

                names = [
                    "messages_received",
                    "missing_messages",
                    "duplicate_messages",
                    "out_of_order_messages",
                    "stale_messages",
                    "invalid_messages"
                ]

                columns = st.columns(3)

                for index, name in enumerate(names):

                    with columns[index % 3]:

                        st.metric(
                            name.replace("_", " ").title(),
                            statistics.get(name, 0)
                        )

        else:

            st.info("Waiting for integrity information.")

        st.divider()

        # FRAME DETAILS

        st.markdown("### Frame Information")

        if perception:

            c1, c2, c3 = st.columns(3)

            with c1:
                st.caption("Session ID")
                st.code(perception.get("session_id", "N/A"))

            with c2:
                st.caption("Sequence Number")
                st.write(perception.get("sequence_number", "N/A"))

            with c3:
                st.caption("Detection Count")
                st.write(perception.get("detection_count", 0))

        if last_update:

            st.caption(
                "Last KUKSA update: "
                + datetime.fromtimestamp(last_update).strftime(
                    "%d-%m-%Y %H:%M:%S"
                )
            )

        st.caption(
            "Research prototype only. Not a certified vehicle safety system."
        )

    live_vehicle_view()


# ============================================================

# PAGE 2: HISTORY EXPLORER
# ============================================================

elif page == "History Explorer":

    st.subheader("Historical Vehicle Data")

    st.write(
        "Explore, filter and analyse previously recorded "
        "vehicle perception, integrity and decision messages."
    )

    statistics = get_database_statistics()

    if not statistics:
        st.warning("No historical data found.")
        st.stop()

    total = sum(statistics.values())

    # --------------------------------------------------------
    # DATABASE SUMMARY
    # --------------------------------------------------------

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric("Total Events", f"{total:,}")

    with c2:
        st.metric(
            "Perception",
            f"{statistics.get('Vehicle.Perception.FrameData', 0):,}"
        )

    with c3:
        st.metric(
            "Integrity",
            f"{statistics.get('Vehicle.Perception.IntegrityStatus', 0):,}"
        )

    with c4:
        st.metric(
            "Decisions",
            f"{statistics.get('Vehicle.Decision.Status', 0):,}"
        )

    st.divider()

    # --------------------------------------------------------
    # LOAD HISTORICAL RECORDS
    # --------------------------------------------------------

    history = get_history(limit=20000)

    if history.empty:
        st.info("No historical events are available.")
        st.stop()

    history["received_time"] = pd.to_datetime(
        history["received_at_ms"],
        unit="ms",
        errors="coerce"
    )

    # --------------------------------------------------------
    # EXTRACT JSON PAYLOAD FIELDS
    # --------------------------------------------------------

    extracted = []

    for _, row in history.iterrows():

        try:
            payload = json.loads(row["payload"])
            if not isinstance(payload, dict):
                payload = {}
        except (ValueError, TypeError):
            payload = {}

        detections = payload.get("detections", [])

        if not isinstance(detections, list):
            detections = []

        classes = []
        confidences = []

        for detection in detections:

            if not isinstance(detection, dict):
                continue

            object_class = detection.get("class")

            if object_class:
                classes.append(str(object_class))

            confidence = detection.get("confidence")

            if isinstance(confidence, (int, float)):
                confidences.append(float(confidence))

        faults = payload.get("faults", [])

        if isinstance(faults, list):
            fault_text = ", ".join(str(x) for x in faults)
        else:
            fault_text = str(faults) if faults else ""

        extracted.append({

            "decision": str(
                payload.get("decision", "N/A")
            ).upper(),

            "integrity": str(
                payload.get("integrity_status", "N/A")
            ).upper(),

            "faults": fault_text,

            "detection_count": payload.get(
                "detection_count",
                len(detections)
            ),

            "objects": ", ".join(classes) if classes else "None",

            "mean_confidence": (
                sum(confidences) / len(confidences)
                if confidences else None
            ),

            "perception_latency_ms": payload.get(
                "perception_latency_ms"
            ),

            "decision_latency_ms": payload.get(
                "decision_latency_ms"
            ),

            "payload": payload
        })

    details = pd.DataFrame(extracted)

    history = pd.concat(
        [
            history.reset_index(drop=True),
            details.drop(columns=["payload"]).reset_index(drop=True)
        ],
        axis=1
    )

    # --------------------------------------------------------
    # FILTERS
    # --------------------------------------------------------

    st.markdown("### Filter Historical Records")

    filter_col1, filter_col2 = st.columns(2)

    with filter_col1:

        sessions = get_sessions()

        selected_session = st.selectbox(
            "Recording Session",
            ["All Sessions"] + sessions,
            key="history_session_filter"
        )

    with filter_col2:

        signal_options = [
            "All",
            "Vehicle.Perception.FrameData",
            "Vehicle.Perception.IntegrityStatus",
            "Vehicle.Decision.Status"
        ]

        selected_signal = st.selectbox(
            "Vehicle Signal",
            signal_options,
            key="history_signal_filter"
        )

    filter_col3, filter_col4 = st.columns(2)

    with filter_col3:

        decision_options = ["All"] + sorted(
            x for x in history["decision"].unique()
            if x != "N/A"
        )

        selected_decision = st.selectbox(
            "Decision Status",
            decision_options,
            key="history_decision_filter"
        )

    with filter_col4:

        integrity_options = ["All"] + sorted(
            x for x in history["integrity"].unique()
            if x != "N/A"
        )

        selected_integrity = st.selectbox(
            "Integrity Status",
            integrity_options,
            key="history_integrity_filter"
        )

    # --------------------------------------------------------
    # DATE FILTER
    # --------------------------------------------------------

    valid_times = history["received_time"].dropna()

    if not valid_times.empty:

        min_date = valid_times.min().date()
        max_date = valid_times.max().date()

        selected_dates = st.date_input(
            "Recording Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key="history_date_filter"
        )

    else:
        selected_dates = None

    # --------------------------------------------------------
    # OBJECT FILTER
    # --------------------------------------------------------

    all_objects = set()

    for object_list in history["objects"].dropna():

        if object_list != "None":
            all_objects.update(
                item.strip()
                for item in object_list.split(",")
                if item.strip()
            )

    object_options = ["All Objects"] + sorted(all_objects)

    selected_object = st.selectbox(
        "Detected Object Class",
        object_options,
        key="history_object_filter"
    )

    # --------------------------------------------------------
    # APPLY FILTERS
    # --------------------------------------------------------

    filtered = history.copy()

    if selected_session != "All Sessions":

        filtered = filtered[
            filtered["session_id"] == selected_session
        ]

    if selected_signal != "All":

        filtered = filtered[
            filtered["signal"] == selected_signal
        ]

    if selected_decision != "All":

        filtered = filtered[
            filtered["decision"] == selected_decision
        ]

    if selected_integrity != "All":

        filtered = filtered[
            filtered["integrity"] == selected_integrity
        ]

    if selected_dates and len(selected_dates) == 2:

        start_date, end_date = selected_dates

        filtered = filtered[
            (filtered["received_time"].dt.date >= start_date)
            &
            (filtered["received_time"].dt.date <= end_date)
        ]

    if selected_object != "All Objects":

        filtered = filtered[
            filtered["objects"].str.contains(
                selected_object,
                regex=False,
                na=False
            )
        ]

    filtered = filtered.sort_values(
        "received_at_ms",
        ascending=False
    )

    st.divider()

    # --------------------------------------------------------
    # FILTERED SUMMARY
    # --------------------------------------------------------

    st.markdown("### Filtered Results")

    result_col1, result_col2, result_col3 = st.columns(3)

    with result_col1:
        st.metric("Matching Events", f"{len(filtered):,}")

    with result_col2:
        alerts = int(
            (filtered["decision"] == "ALERT").sum()
        )
        st.metric("Alert Decisions", alerts)

    with result_col3:
        faults_count = int(
            (filtered["integrity"] == "FAULT").sum()
        )
        st.metric("Fault Events", faults_count)

    if filtered.empty:

        st.info("No events match the selected filters.")

    else:

        # ----------------------------------------------------
        # HISTORICAL EVENT TABLE
        # ----------------------------------------------------

        st.markdown("### Recorded Events")

        display_columns = [
            "id",
            "signal",
            "sequence_number",
            "received_time",
            "decision",
            "integrity",
            "detection_count",
            "objects"
        ]

        st.dataframe(
            filtered[display_columns].head(1000),
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            f"Displaying up to 1,000 of {len(filtered):,} matching events."
        )


        # ----------------------------------------------------
        # EXPORT FILTERED RESEARCH DATA
        # ----------------------------------------------------

        st.markdown("### Export Research Data")

        export_col1, export_col2 = st.columns(2)

        with export_col1:

            csv_data = filtered.to_csv(
                index=False
            ).encode("utf-8")

            st.download_button(
                label="Download Filtered CSV",
                data=csv_data,
                file_name="sdv_filtered_history.csv",
                mime="text/csv",
                key="history_download_csv",
                use_container_width=True
            )

        with export_col2:

            json_records = json.loads(
                filtered.to_json(
                    orient="records",
                    date_format="iso"
                )
            )

            for record in json_records:
                if isinstance(record.get("payload"), str):
                    try:
                        record["payload"] = json.loads(
                            record["payload"]
                        )
                    except (ValueError, TypeError):
                        pass

            json_data = json.dumps(
                json_records,
                indent=2,
                ensure_ascii=False
            )

            st.download_button(
                label="Download Filtered JSON",
                data=json_data,
                file_name="sdv_filtered_history.json",
                mime="application/json",
                key="history_download_json",
                use_container_width=True
            )

        # ----------------------------------------------------
        # DECISION ANALYTICS
        # ----------------------------------------------------

        st.divider()
        st.markdown("### Decision Analytics")

        decision_data = filtered[
            filtered["decision"] != "N/A"
        ]

        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:

            st.markdown("#### Decision Distribution")

            if not decision_data.empty:

                decision_counts = (
                    decision_data["decision"]
                    .value_counts()
                )

                st.bar_chart(decision_counts)

            else:
                st.info("No decision records in this selection.")

        with chart_col2:

            st.markdown("#### Integrity Distribution")

            integrity_data = filtered[
                filtered["integrity"] != "N/A"
            ]

            if not integrity_data.empty:

                integrity_counts = (
                    integrity_data["integrity"]
                    .value_counts()
                )

                st.bar_chart(integrity_counts)

            else:
                st.info("No integrity records in this selection.")

        # ----------------------------------------------------
        # OBJECT DETECTION ANALYTICS
        # ----------------------------------------------------

        st.divider()
        st.markdown("### Perception Analytics")

        perception_data = filtered[
            filtered["signal"]
            == "Vehicle.Perception.FrameData"
        ].copy()

        if not perception_data.empty:

            p1, p2, p3 = st.columns(3)

            with p1:
                st.metric(
                    "Perception Frames",
                    f"{len(perception_data):,}"
                )

            with p2:
                st.metric(
                    "Total Detections",
                    int(
                        pd.to_numeric(
                            perception_data["detection_count"],
                            errors="coerce"
                        ).fillna(0).sum()
                    )
                )

            with p3:

                valid_confidence = pd.to_numeric(
                    perception_data["mean_confidence"],
                    errors="coerce"
                ).dropna()

                if not valid_confidence.empty:

                    st.metric(
                        "Average Confidence",
                        f"{valid_confidence.mean():.2%}"
                    )

                else:
                    st.metric("Average Confidence", "N/A")

            object_counts = {}

            for object_list in perception_data["objects"].dropna():

                if object_list == "None":
                    continue

                for object_class in object_list.split(","):

                    object_class = object_class.strip()

                    if object_class:
                        object_counts[object_class] = (
                            object_counts.get(object_class, 0) + 1
                        )

            object_col1, object_col2 = st.columns(2)

            with object_col1:

                st.markdown("#### Detected Object Classes")

                if object_counts:
                    st.bar_chart(
                        pd.Series(
                            object_counts,
                            name="Detection Count"
                        )
                    )
                else:
                    st.info("No object detections in this selection.")

            with object_col2:

                st.markdown("#### Perception Latency")

                latency_data = perception_data[
                    ["received_time", "perception_latency_ms"]
                ].copy()

                latency_data["perception_latency_ms"] = pd.to_numeric(
                    latency_data["perception_latency_ms"],
                    errors="coerce"
                )

                latency_data = latency_data.dropna()

                if not latency_data.empty:

                    st.metric(
                        "Average Inference Latency",
                        f"{latency_data['perception_latency_ms'].mean():.2f} ms"
                    )

                    latency_chart = latency_data.set_index(
                        "received_time"
                    )[["perception_latency_ms"]].sort_index()

                    st.line_chart(latency_chart)

                else:
                    st.info("No perception latency values available.")

        else:

            st.info(
                "No perception frames match the current filters."
            )

        # ----------------------------------------------------
        # FAULT ANALYTICS
        # ----------------------------------------------------

        st.divider()
        st.markdown("### Integrity Fault Analysis")

        integrity_records = filtered[
            filtered["signal"]
            == "Vehicle.Perception.IntegrityStatus"
        ]

        fault_counts = {}

        for fault_text in integrity_records["faults"].dropna():

            if not fault_text:
                continue

            for fault in fault_text.split(","):

                fault = fault.strip()

                if fault:
                    fault_counts[fault] = (
                        fault_counts.get(fault, 0) + 1
                    )

        if fault_counts:

            st.bar_chart(
                pd.Series(
                    fault_counts,
                    name="Fault Occurrences"
                )
            )

        else:

            st.success(
                "No explicitly recorded faults in the selected integrity records."
            )

        # ----------------------------------------------------
        # EVENT INSPECTOR
        # ----------------------------------------------------

        st.divider()
        st.markdown("### Individual Event Inspector")

        event_ids = filtered["id"].tolist()

        event_id = st.selectbox(
            "Select an event ID",
            event_ids,
            key="history_event_inspector"
        )

        selected_event = filtered[
            filtered["id"] == event_id
        ].iloc[0]

        info1, info2, info3 = st.columns(3)

        with info1:
            st.write("**Signal**")
            st.write(selected_event["signal"])

        with info2:
            st.write("**Sequence Number**")
            st.write(selected_event["sequence_number"])

        with info3:
            st.write("**Received At**")
            st.write(str(selected_event["received_time"]))

        st.markdown("#### Complete Message Payload")

        st.json(selected_event["payload"])

    # --------------------------------------------------------
    # DATABASE INFORMATION
    # --------------------------------------------------------

    st.divider()

    st.info(
        "Historical data is loaded from the local SQLite database. "
        "This database stores vehicle messages and JSON detection "
        "metadata, not camera video recordings. The History Explorer "
        "does not run YOLO or access the webcam."
    )


# ============================================================
# PAGE 3: RESEARCH EXPERIMENTS
# ============================================================

elif page == "Research Experiments":

    st.subheader("Research Experiments")

    st.write(
        "Evaluation of a baseline decision pipeline against the "
        "proposed integrity-aware decision pipeline."
    )

    if EVALUATION_PATH.exists():

        df = pd.read_csv(EVALUATION_PATH)

        required_columns = [
            "test_id",
            "scenario",
            "injected_fault",
            "integrity_status",
            "baseline_decision",
            "proposed_decision",
            "baseline_latency_ms",
            "proposed_latency_ms"
        ]

        missing_columns = [
            col for col in required_columns if col not in df.columns
        ]

        if missing_columns:

            st.error(
                "Evaluation dataset is missing required columns: "
                + ", ".join(missing_columns)
            )

        else:

            st.markdown("### Evaluation Dataset")

            st.caption(
                "Ground-truth labels come from the independently defined "
                "fault-injection scenarios."
            )

            st.metric("Total Evaluated Messages", len(df))

            # Independent ground truth from the corrected dataset
            df["ground_truth_fault"] = (
                df["injected_fault"]
                .astype(str)
                .str.strip()
                .str.lower()
                .isin(["true", "1", "yes"])
            )

            # Fault detection output from the integrity monitor
            df["detected_fault"] = (
                df["integrity_status"]
                .astype(str)
                .str.upper()
                == "FAULT"
            )

            tp = int(
                (df["ground_truth_fault"] & df["detected_fault"]).sum()
            )

            fp = int(
                (~df["ground_truth_fault"] & df["detected_fault"]).sum()
            )

            fn = int(
                (df["ground_truth_fault"] & ~df["detected_fault"]).sum()
            )

            tn = int(
                (~df["ground_truth_fault"] & ~df["detected_fault"]).sum()
            )

            total = tp + fp + fn + tn
            actual_faults = tp + fn
            actual_normal = tn + fp

            precision = tp / (tp + fp) * 100 if (tp + fp) else 0
            recall = tp / actual_faults * 100 if actual_faults else 0
            false_positive_rate = (
                fp / actual_normal * 100 if actual_normal else 0
            )
            accuracy = (
                (tp + tn) / total * 100 if total else 0
            )

            st.markdown("### Fault Detection Performance")

            c1, c2, c3, c4 = st.columns(4)

            with c1:
                st.metric("Accuracy", f"{accuracy:.1f}%")

            with c2:
                st.metric("Precision", f"{precision:.1f}%")

            with c3:
                st.metric("Recall / Detection Rate", f"{recall:.1f}%")

            with c4:
                st.metric("False Positive Rate", f"{false_positive_rate:.1f}%")

            c1, c2, c3, c4 = st.columns(4)

            with c1:
                st.metric("True Positives", tp)

            with c2:
                st.metric("False Positives", fp)

            with c3:
                st.metric("True Negatives", tn)

            with c4:
                st.metric("False Negatives", fn)

            st.caption(
                "These are preliminary results from a small, controlled "
                "fault-injection dataset. They do not establish "
                "general performance in real-world driving conditions."
            )

            st.divider()

            # Baseline vs proposed decisions
            st.markdown("### Baseline vs Proposed Decisions")

            comparison_columns = [
                "test_id",
                "scenario",
                "injected_fault",
                "integrity_status",
                "baseline_decision",
                "proposed_decision",
                "baseline_latency_ms",
                "proposed_latency_ms"
            ]

            st.dataframe(
                df[comparison_columns],
                use_container_width=True,
                hide_index=True
            )

            st.divider()

            # Latency comparison
            st.markdown("### Decision-Processing Latency")

            baseline_latency = pd.to_numeric(
                df["baseline_latency_ms"], errors="coerce"
            )

            proposed_latency = pd.to_numeric(
                df["proposed_latency_ms"], errors="coerce"
            )

            latency = pd.DataFrame({
                "Approach": ["Baseline", "Proposed"],
                "Mean Latency (ms)": [
                    baseline_latency.mean(),
                    proposed_latency.mean()
                ],
                "Median Latency (ms)": [
                    baseline_latency.median(),
                    proposed_latency.median()
                ]
            })

            st.dataframe(
                latency.round(5),
                use_container_width=True,
                hide_index=True
            )

            st.bar_chart(
                latency.set_index("Approach")[["Mean Latency (ms)"]]
            )

            st.caption(
                "Latency measures the decision-processing functions only. "
                "It excludes KUKSA communication, message pairing, "
                "database operations and dashboard rendering."
            )

            st.divider()

            # ==========================================
            # REPEATED LATENCY BENCHMARK
            # ==========================================

            st.markdown("### Repeated Latency Benchmark")

            st.write(
                "Repeated local measurements comparing baseline "
                "and integrity-aware decision processing."
            )

            BENCHMARK_SUMMARY_PATH = (
                BASE_DIR / "evaluation" / "latency_benchmark_summary.csv"
            )

            BENCHMARK_RAW_PATH = (
                BASE_DIR / "evaluation" / "latency_benchmark_raw.csv"
            )

            if BENCHMARK_SUMMARY_PATH.exists():

                benchmark_df = pd.read_csv(
                    BENCHMARK_SUMMARY_PATH
                )

                overall = benchmark_df[
                    benchmark_df["scenario"] == "OVERALL"
                ]

                if len(overall) == 2:

                    baseline_row = overall[
                        overall["pipeline"] == "baseline"
                    ].iloc[0]

                    proposed_row = overall[
                        overall["pipeline"] == "proposed"
                    ].iloc[0]

                    st.caption(
                        "30 measured repetitions per scenario, "
                        "after 5 warm-up repetitions. Paired scenarios "
                        "contain two messages per repetition."
                    )

                    b1, b2, b3, b4 = st.columns(4)

                    with b1:
                        st.metric(
                            "Baseline Mean",
                            f'{baseline_row["mean_ms"]:.6f} ms'
                        )

                    with b2:
                        st.metric(
                            "Proposed Mean",
                            f'{proposed_row["mean_ms"]:.6f} ms'
                        )

                    with b3:
                        st.metric(
                            "Baseline P95",
                            f'{baseline_row["p95_ms"]:.6f} ms'
                        )

                    with b4:
                        st.metric(
                            "Proposed P95",
                            f'{proposed_row["p95_ms"]:.6f} ms'
                        )

                    st.markdown("#### Overall Latency Statistics")

                    overall_display = overall[
                        [
                            "pipeline",
                            "sample_count",
                            "mean_ms",
                            "median_ms",
                            "minimum_ms",
                            "maximum_ms",
                            "standard_deviation_ms",
                            "p95_ms"
                        ]
                    ].copy()

                    overall_display = overall_display.rename(
                        columns={
                            "pipeline": "Pipeline",
                            "sample_count": "Samples",
                            "mean_ms": "Mean (ms)",
                            "median_ms": "Median (ms)",
                            "minimum_ms": "Minimum (ms)",
                            "maximum_ms": "Maximum (ms)",
                            "standard_deviation_ms": "Std. Deviation (ms)",
                            "p95_ms": "P95 (ms)"
                        }
                    )

                    st.dataframe(
                        overall_display.round(6),
                        use_container_width=True,
                        hide_index=True
                    )

                    st.markdown("#### Scenario-wise Mean Latency")

                    scenario_df = benchmark_df[
                        benchmark_df["scenario"] != "OVERALL"
                    ]

                    scenario_chart = scenario_df.pivot(
                        index="scenario",
                        columns="pipeline",
                        values="mean_ms"
                    )

                    scenario_chart = scenario_chart.rename(
                        columns={
                            "baseline": "Baseline",
                            "proposed": "Proposed"
                        }
                    )

                    st.bar_chart(
                        scenario_chart,
                        y_label="Mean decision-processing latency (ms)"
                    )

                    st.markdown("#### Detailed Scenario Statistics")

                    detail_columns = [
                        "scenario",
                        "pipeline",
                        "sample_count",
                        "mean_ms",
                        "median_ms",
                        "standard_deviation_ms",
                        "p95_ms"
                    ]

                    st.dataframe(
                        scenario_df[detail_columns].round(6),
                        use_container_width=True,
                        hide_index=True
                    )

                    st.download_button(
                        label="Download Latency Summary CSV",
                        data=benchmark_df.to_csv(index=False),
                        file_name="latency_benchmark_summary.csv",
                        mime="text/csv"
                    )

                    if BENCHMARK_RAW_PATH.exists():

                        raw_benchmark = pd.read_csv(
                            BENCHMARK_RAW_PATH
                        )

                        with st.expander(
                            "View Raw Repeated Latency Measurements"
                        ):

                            st.write(
                                f"Total measured records: "
                                f"{len(raw_benchmark)}"
                            )

                            st.dataframe(
                                raw_benchmark,
                                use_container_width=True,
                                hide_index=True
                            )

                            st.download_button(
                                label="Download Raw Measurements CSV",
                                data=raw_benchmark.to_csv(index=False),
                                file_name="latency_benchmark_raw.csv",
                                mime="text/csv"
                            )

                    st.info(
                        "The proposed pipeline performs additional "
                        "integrity validation, so its local processing "
                        "latency is higher. These measurements cover "
                        "Python decision-processing functions only; "
                        "they exclude KUKSA communication, message "
                        "pairing, publication, database operations "
                        "and dashboard rendering."
                    )

                else:

                    st.warning(
                        "Overall baseline/proposed benchmark records "
                        "are incomplete."
                    )

            else:

                st.warning(
                    "Repeated latency benchmark summary was not found."
                )

            st.divider()

            # Confusion matrix
            st.markdown("### Fault Classification Confusion Matrix")

            confusion = pd.DataFrame(
                [
                    [tp, fn],
                    [fp, tn]
                ],
                index=["Actual Fault", "Actual Normal"],
                columns=["Detected Fault", "Detected Normal"]
            )

            st.dataframe(
                confusion,
                use_container_width=True
            )

            st.divider()

            # Experiment logs
            st.markdown("### Experiment Logs")

            if LOGS_PATH.exists():

                for log_file in sorted(LOGS_PATH.glob("*.md")):

                    with st.expander(
                        log_file.stem.replace("_", " ").title()
                    ):

                        st.markdown(
                            log_file.read_text(encoding="utf-8")
                        )

            else:

                st.warning("Experiment logs not found.")

            st.caption(
                "Offline controlled evaluation using independently "
                "labelled fault-injection scenarios. These results are "
                "separate from the live camera feed."
            )

    else:

        st.error("Corrected evaluation dataset not found.")

        st.code("evaluation/evaluation_results_corrected.csv")


# ============================================================

# PAGE 4: SYSTEM ARCHITECTURE
# ============================================================

elif page == "System Architecture":

    st.subheader("System Architecture")

    st.write(
        "The proposed platform evaluates the effect of "
        "perception-message integrity on downstream vehicle decisions."
    )

    st.markdown("### Perception-to-Decision Pipeline")

    architecture = [
        (
            "01",
            "Camera Input",
            "Captures the vehicle's surrounding environment."
        ),
        (
            "02",
            "YOLO Perception",
            "Detects objects and creates structured perception messages."
        ),
        (
            "03",
            "Eclipse KUKSA Databroker",
            "Exchanges vehicle data using Vehicle Signal Specification."
        ),
        (
            "04",
            "Data Integrity Monitor",
            "Checks stale, missing, duplicate, out-of-order and invalid messages."
        ),
        (
            "05",
            "Fault-Aware Decision Module",
            "Combines perception and integrity information to generate decisions."
        ),
        (
            "06",
            "History and Dashboard",
            "Stores vehicle events and displays system information."
        )
    ]

    for number, title, description in architecture:

        st.markdown(
            f"""
            <div style="
                background:#FFFFFF;
                border:1px solid #E1E7EF;
                border-left:5px solid #2563EB;
                border-radius:9px;
                padding:14px 18px;
                margin-bottom:11px;
            ">

                <div style="
                    color:#2563EB;
                    font-size:11px;
                    font-weight:700;
                ">
                    MODULE {number}
                </div>

                <div style="
                    color:#172B4D;
                    font-size:17px;
                    font-weight:700;
                    margin-top:4px;
                ">
                    {title}
                </div>

                <div style="
                    color:#475467;
                    font-size:13px;
                    margin-top:5px;
                ">
                    {description}
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    st.divider()

    st.markdown("### Research Contribution")

    st.info(
        "An experimental integrity-aware perception-to-decision "
        "framework that evaluates how unreliable perception messages "
        "affect downstream vehicle decisions."
    )

    st.markdown("### Fault Injection Scenarios")

    scenarios = {
        "Stale": "Message exceeds the configured freshness limit.",
        "Missing": "A sequence gap is observed.",
        "Duplicate": "A previously received sequence number appears again.",
        "Out of order": "An older sequence arrives after a newer sequence.",
        "Invalid confidence": "A detection contains an invalid confidence value.",
        "Delay": "A perception message is intentionally delayed."
    }

    for name, description in scenarios.items():

        st.markdown(
            f"**{name}:** {description}"
        )

    st.divider()

    st.markdown("### Technology Stack")

    technologies = pd.DataFrame({
        "Layer": [
            "Perception",
            "Communication",
            "Integrity Monitoring",
            "Decision",
            "Database",
            "Dashboard"
        ],
        "Technology": [
            "Python, YOLO, OpenCV",
            "Eclipse KUKSA, VSS",
            "Python",
            "Python",
            "SQLite",
            "Streamlit"
        ]
    })

    st.dataframe(
        technologies,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    st.markdown("### Research Scope")

    st.write(
        "This is a software-based research prototype. "
        "It evaluates message integrity and decision behavior "
        "under controlled fault-injection scenarios. "
        "It is not a certified autonomous-driving or vehicle safety system."
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.markdown(
    """
    <div class="footer">

        <strong style="color:#344054;">
            SOFTWARE-DEFINED VEHICLE RESEARCH PLATFORM
        </strong>

        <br>

        AI-Driven Perception | Data Integrity |
        Fault-Aware Decision-Making

    </div>
    """,
    unsafe_allow_html=True
)
