# 🐘 Real-Time Elephant Detection with WhatsApp Alerts

This project uses **YOLOv8 (Ultralytics)** for real-time object detection and integrates **Twilio WhatsApp API** to send instant alerts when an elephant is detected on screen.

---

## 🚀 Features
- 🎯 Real-time object detection using YOLOv8  
- 🖥️ Live screen capture using MSS  
- 📲 Automatic WhatsApp alerts via Twilio  
- ⏱️ Cooldown system to prevent message spam  
- 🧠 Detects "elephant" class from COCO dataset  

---

## 🛠️ Tech Stack
- Python  
- OpenCV (`cv2`)  
- NumPy  
- Ultralytics YOLOv8  
- Twilio API  
- MSS (screen capture)  

---

## ⚙️ How It Works
1. Captures your screen continuously using MSS  
2. Runs YOLOv8 object detection on each frame  
3. Checks if an **elephant** is detected  
4. Sends a WhatsApp alert using Twilio  
5. Applies a cooldown (default: 60 seconds) to avoid spam alerts  

---

## 📦 Setup Instructions

### 1️⃣ Install Dependencies
```bash
pip install opencv-python numpy ultralytics mss twilio
2️⃣ Add Twilio Credentials
Python


Run
account_sid = "YOUR_ACCOUNT_SID"
auth_token = "YOUR_AUTH_TOKEN"
3️⃣ Configure WhatsApp Numbers
Python


Run
FROM_WHATSAPP = "whatsapp:+14155238886"
TO_WHATSAPP = "whatsapp:+91XXXXXXXXXX"
4️⃣ Add COCO Class File
Make sure coco.txt is present in the project directory.

5️⃣ Run the Project
Bash

python main.py
📌 Use Cases
🌲 Wildlife monitoring systems

🚨 Forest safety alerts

🛡️ Smart surveillance systems

🤖 AI-based event detection

⚠️ Notes
Requires active internet connection for WhatsApp alerts

Twilio sandbox must be configured before use

Detection accuracy depends on YOLO model (yolov8s.pt)

💡 Future Improvements
🔊 Add sound alert system

🐅 Detect multiple animal classes

📱 Deploy on edge devices (Raspberry Pi / Jetson Nano)

🌐 Build a web dashboard

📷 Demo
Add screenshots or GIFs here

📜 License
This project is open-source and available under the MIT License.

👨‍💻 Author
Krishna Verma
