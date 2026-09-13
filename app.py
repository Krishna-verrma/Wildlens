import os
import time
import tempfile
from pathlib import Path
import cv2
import numpy as np
import streamlit as st
from PIL import Image
from dotenv import load_dotenv

# Load local environment variables if present
load_dotenv()

# Streamlit Page Config
st.set_page_config(
    page_title="Wildlens - Elephant Detection & Alerts",
    page_icon="🐘",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.3rem;
        font-weight: 800;
        background: -webkit-linear-gradient(45deg, #10B981, #059669);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #9CA3AF;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
    }
    .alert-banner {
        background: linear-gradient(90deg, #DC2626 0%, #991B1B 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        font-size: 1.2rem;
        font-weight: bold;
        text-align: center;
        animation: pulse 1.5s infinite;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to load YOLO model with caching
@st.cache_resource
def load_model(model_name="yolov8s.pt"):
    from ultralytics import YOLO
    return YOLO(model_name)

@st.cache_resource
def load_class_list():
    coco_file = Path("coco.txt")
    if coco_file.exists():
        with open(coco_file, "r") as f:
            return [c.strip() for c in f.read().split("\n") if c.strip()]
    return None

def get_twilio_client():
    account_sid = os.getenv("TWILIO_ACCOUNT_SID") or st.session_state.get("twilio_sid", "")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN") or st.session_state.get("twilio_token", "")
    if account_sid and auth_token and not "YOUR_" in account_sid:
        try:
            from twilio.rest import Client
            return Client(account_sid, auth_token)
        except Exception as e:
            st.sidebar.error(f"Twilio error: {e}")
            return None
    return None

def send_whatsapp(client, to_number, message_text="🚨 ALERT: Elephant Detected near perimeter!"):
    from_number = os.getenv("FROM_WHATSAPP") or st.session_state.get("from_whatsapp", "whatsapp:+14155238886")
    if not client:
        return False, "Twilio credentials not configured."
    try:
        msg = client.messages.create(body=message_text, from_=from_number, to=to_number)
        return True, msg.sid
    except Exception as e:
        return False, str(e)

# Sidebar Configuration
st.sidebar.image("https://images.unsplash.com/photo-1557050543-4d5f4e07ef46?auto=format&fit=crop&w=400&q=80", use_container_width=True)
st.sidebar.markdown("## ⚙️ Demo Controls")

# Input Source
source_option = st.sidebar.selectbox(
    "Select Input Source",
    ["🐘 Demo Video (ele.mp4)", "📤 Upload Video / Image", "📸 Webcam Snapshot"]
)

# Detection Sensitivity
conf_threshold = st.sidebar.slider("Detection Confidence", min_value=0.20, max_value=0.95, value=0.45, step=0.05)
alert_cooldown = st.sidebar.slider("Alert Cooldown (seconds)", min_value=10, max_value=120, value=45, step=5)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📲 WhatsApp Alert Settings")

default_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
default_token = os.getenv("TWILIO_AUTH_TOKEN", "")
default_from = os.getenv("FROM_WHATSAPP", "whatsapp:+14155238886")
default_to = os.getenv("TO_WHATSAPP", "")

# In Streamlit Cloud, secrets can also be configured
if "TWILIO_ACCOUNT_SID" in st.secrets:
    default_sid = st.secrets["TWILIO_ACCOUNT_SID"]
if "TWILIO_AUTH_TOKEN" in st.secrets:
    default_token = st.secrets["TWILIO_AUTH_TOKEN"]
if "TO_WHATSAPP" in st.secrets:
    default_to = st.secrets["TO_WHATSAPP"]

target_whatsapp = st.sidebar.text_input(
    "Recipient WhatsApp Number",
    value=default_to,
    help="e.g. whatsapp:+919876543210 (must have joined Twilio sandbox)"
)
st.session_state["target_whatsapp"] = target_whatsapp

# Manual Test Button
if st.sidebar.button("🔔 Send Test WhatsApp Alert"):
    client = get_twilio_client()
    if client and target_whatsapp:
        success, msg = send_whatsapp(client, target_whatsapp, "🐘 Wildlens Test: WhatsApp integration is working perfectly!")
        if success:
            st.sidebar.success(f"Alert Sent! (SID: {msg[:8]}...)")
        else:
            st.sidebar.error(f"Failed: {msg}")
    else:
        st.sidebar.warning("Please configure Twilio credentials & recipient number in .env or secrets.")

st.sidebar.markdown("""
> **Note for Hackathon Judges**:
> Send `join <sandbox-code>` to **+1 415 523 8886** on WhatsApp to receive live alerts on your phone.
""")

# Main Screen
st.markdown('<div class="main-title">🐘 Wildlens: Autonomous Elephant Detection</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">AI-Powered Perimeter Surveillance & Instant WhatsApp Community Warning System</div>', unsafe_allow_html=True)

# Metrics Bar
col1, col2, col3 = st.columns(3)
metric_status = col1.empty()
metric_count = col2.empty()
metric_alert = col3.empty()

metric_status.metric("System Status", "🟢 Ready / Active")
metric_count.metric("Elephants Detected", "0")
metric_alert.metric("Last Alert Status", "Standby")

# Session state initialization
if "last_alert_time" not in st.session_state:
    st.session_state.last_alert_time = 0
if "alert_log" not in st.session_state:
    st.session_state.alert_log = []

# Load model
model = load_model("yolov8s.pt")
class_list = load_class_list()
twilio_client = get_twilio_client()

alert_placeholder = st.empty()
video_placeholder = st.empty()

# Processing Loop
if source_option == "🐘 Demo Video (ele.mp4)":
    video_path = "ele.mp4"
    if not os.path.exists(video_path):
        st.error("Demo video ele.mp4 not found in project root.")
    else:
        start_btn = st.button("▶️ Start Live Detection Stream", type="primary")
        stop_btn = st.button("⏹️ Stop Stream")

        if start_btn:
            cap = cv2.VideoCapture(video_path)
            while cap.isOpened() and not stop_btn:
                ret, frame = cap.read()
                if not ret:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue

                # Inference
                results = model.predict(frame, conf=conf_threshold, verbose=False)
                elephant_count = 0
                max_conf = 0.0

                for r in results:
                    for box in r.boxes:
                        cls_id = int(box.cls[0])
                        label = class_list[cls_id] if class_list and cls_id < len(class_list) else model.names.get(cls_id, "")
                        if label == "elephant":
                            elephant_count += 1
                            conf = float(box.conf[0])
                            if conf > max_conf:
                                max_conf = conf

                # Trigger Alert
                current_time = time.time()
                if elephant_count > 0:
                    alert_placeholder.markdown(
                        f'<div class="alert-banner">🚨 ALERT: {elephant_count} Elephant(s) Detected! (Confidence: {max_conf*100:.1f}%)</div>',
                        unsafe_allow_html=True
                    )
                    metric_status.metric("System Status", "🔴 ELEPHANT DETECTED")
                    metric_count.metric("Elephants in Frame", f"{elephant_count}")

                    if (current_time - st.session_state.last_alert_time) > alert_cooldown:
                        if twilio_client and target_whatsapp:
                            success, sid = send_whatsapp(
                                twilio_client,
                                target_whatsapp,
                                f"🚨 WILDLENS ALERT: Elephant detected near perimeter! Confidence: {max_conf*100:.1f}%. Take safety precautions."
                            )
                            if success:
                                metric_alert.metric("Last Alert", "✅ Sent via WhatsApp")
                                st.session_state.alert_log.append(f"Sent WhatsApp alert at {time.strftime('%H:%M:%S')}")
                            else:
                                metric_alert.metric("Last Alert", "❌ Send Failed")
                        else:
                            metric_alert.metric("Last Alert", "⚠️ Triggered (Simulated)")
                        st.session_state.last_alert_time = current_time
                else:
                    alert_placeholder.empty()
                    metric_status.metric("System Status", "🟢 Monitoring (Clear)")
                    metric_count.metric("Elephants in Frame", "0")

                # Display annotated frame
                annotated_frame = results[0].plot()
                annotated_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                video_placeholder.image(annotated_rgb, channels="RGB", use_container_width=True)
                time.sleep(0.03)
            cap.release()

elif source_option == "📤 Upload Video / Image":
    uploaded_file = st.file_uploader("Upload Image or Video", type=["jpg", "jpeg", "png", "mp4", "mov", "avi"])
    if uploaded_file is not None:
        file_ext = uploaded_file.name.split(".")[-1].lower()
        if file_ext in ["jpg", "jpeg", "png"]:
            image = Image.open(uploaded_file)
            img_array = np.array(image)
            results = model.predict(img_array, conf=conf_threshold)
            annotated = results[0].plot()
            st.image(annotated, caption="Detection Result", use_container_width=True)

            elephant_detected = any(
                (class_list[int(b.cls[0])] if class_list else model.names.get(int(b.cls[0]))) == "elephant"
                for r in results for b in r.boxes
            )
            if elephant_detected:
                st.error("🚨 Elephant Detected in Uploaded Image!")
                if twilio_client and target_whatsapp:
                    send_whatsapp(twilio_client, target_whatsapp, "🚨 Wildlens Alert: Elephant detected in analyzed image!")
            else:
                st.success("✅ No elephants detected in this image.")
        else:
            tfile = tempfile.NamedTemporaryFile(delete=False)
            tfile.write(uploaded_file.read())
            cap = cv2.VideoCapture(tfile.name)
            ret, frame = cap.read()
            if ret:
                results = model.predict(frame, conf=conf_threshold)
                st.image(results[0].plot(), caption="First Frame Detection", use_container_width=True)
            cap.release()

elif source_option == "📸 Webcam Snapshot":
    cam_img = st.camera_input("Capture Live Webcam Frame")
    if cam_img is not None:
        img = Image.open(cam_img)
        img_array = np.array(img)
        results = model.predict(img_array, conf=conf_threshold)
        st.image(results[0].plot(), caption="Webcam Detection", use_container_width=True)

# Alert History Log
if st.session_state.alert_log:
    st.markdown("### 📋 Recent Alert Activity")
    for log_entry in reversed(st.session_state.alert_log[-5:]):
        st.info(log_entry)
