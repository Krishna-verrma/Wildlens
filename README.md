# 🐘 Wildlens: Real-Time Elephant Detection with WhatsApp Alerts

Wildlens is an AI-powered surveillance pipeline using **YOLOv8** for real-time elephant detection and **Twilio WhatsApp API** for automated security alerts.

Built for forest reserves, border fences, and farm perimeters to prevent human-wildlife conflict.

---

## 🚀 Features
- 🎯 **YOLOv8 Detection**: High-accuracy object detection with configurable confidence threshold.
- 📹 **Flexible Video Sources**: Ingest from **Webcam**, **RTSP CCTV stream**, **Video File (`ele.mp4`)**, or **Screen Capture**.
- 📲 **Instant WhatsApp Alerts**: Automatically triggers WhatsApp notifications when an elephant enters the frame.
- ⏱️ **Smart Alert Cooldown**: Configurable cooldown period (default: 60s) to prevent notification flooding.
- 🖥️ **Headless & Production-Ready**: Auto-switches to headless mode on cloud servers/Docker without crashing GUI calls.
- 🐳 **Docker & Systemd Support**: 1-command containerized deployment or Linux 24/7 background service.

---

## 🛠️ Tech Stack
- **AI/CV**: Ultralytics YOLOv8, OpenCV, NumPy
- **Alerts**: Twilio WhatsApp Messaging API
- **Screen Capture**: MSS
- **Deployment**: Docker, Docker Compose, Linux Systemd

---

## ⚡ Quick Start (Local Run)

### 1. Clone & Setup Virtual Environment
```bash
git clone git@github.com:Krishna-verrma/Wildlens.git
cd Wildlens
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure Environment (`.env`)
Copy the example configuration:
```bash
cp .env.example .env
```

Open `.env` and fill in your Twilio credentials and phone numbers:
```ini
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
FROM_WHATSAPP=whatsapp:+14155238886
TO_WHATSAPP=whatsapp:+91XXXXXXXXXX
SOURCE=ele.mp4
ALERT_COOLDOWN=60
```

### 3. Run Detection
```bash
# Run with settings from .env (defaults to sample video ele.mp4)
python main.py

# Or override source via command line:
python main.py --source 0               # Use default webcam
python main.py --source rtsp://ip:port  # Use RTSP IP camera
python main.py --source screen          # Monitor PC screen
python main.py --headless               # Run without GUI window
```

---

## 🐳 Deployment Option 1: Docker (Fastest)

Run the entire pipeline in an isolated container:

```bash
# 1. Edit .env with your credentials
nano .env

# 2. Start container in background
docker compose up -d

# 3. View live logs
docker compose logs -f
```

To stop:
```bash
docker compose down
```

---

## 🐧 Deployment Option 2: Linux Cloud Server or Edge Device (24/7 Service)

For deployment on **Ubuntu VPS (AWS EC2 / DigitalOcean)** or **Raspberry Pi / Jetson Nano**:

1. Install dependencies:
   ```bash
   sudo apt update && sudo apt install -y python3-pip python3-venv git ffmpeg libsm6 libxext6
   ```
2. Clone repository and setup venv:
   ```bash
   git clone git@github.com:Krishna-verrma/Wildlens.git
   cd Wildlens
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your credentials
   ```
3. Install the Systemd Service:
   ```bash
   sudo cp systemd/wildlens.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable wildlens
   sudo systemctl start wildlens
   ```
4. Check service status:
   ```bash
   sudo systemctl status wildlens
   journalctl -u wildlens -f
   ```

---

## 📲 Twilio WhatsApp Setup Checklist
1. Create a free account at [Twilio](https://console.twilio.com/).
2. Navigate to **Messaging > Try it out > Send a WhatsApp message**.
3. Follow the instructions to join your sandbox by sending the keyword (e.g. `join <code-name>`) to `+1 415 523 8886` from your WhatsApp.
4. Copy your **Account SID** and **Auth Token** to `.env`.

---

## 📁 Repository Structure
```
Wildlens/
├── main.py                  # Production entrypoint with multi-source & headless support
├── test2.py                 # Original screen capture prototype
├── requirements.txt         # Pinned production dependencies
├── .env.example             # Configuration template
├── .env                     # Local configuration (ignored by git)
├── Dockerfile               # Production Docker container definition
├── docker-compose.yml       # 1-command container deployment
├── systemd/
│   └── wildlens.service     # Linux 24/7 background service definition
├── coco.txt                 # COCO dataset classes
├── ele.mp4                  # Sample video for verification
└── README.md                # Documentation
```

---

## 📜 License
This project is open-source under the MIT License.

👨‍💻 **Author**: Krishna Verma
