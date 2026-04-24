import cv2
import numpy as np
from ultralytics import YOLO
import mss
from twilio.rest import Client
import time

# ---------------- TWILIO CONFIG ----------------
account_sid = "YOUR_ACCOUNT_SID"
auth_token = "YOUR_AUTH_TOKEN"

client = Client(account_sid, auth_token)

FROM_WHATSAPP = "whatsapp:+14155238886"   # Twilio sandbox number
TO_WHATSAPP = "whatsapp:+91XXXXXXXXXX"    # Your number

# ---------------- YOLO MODEL ----------------
model = YOLO('yolov8s.pt')

# Load COCO class names
with open("coco.txt", "r") as f:
    class_list = f.read().split("\n")

# ---------------- SCREEN CAPTURE ----------------
sct = mss.mss()
monitor = sct.monitors[1]

cv2.namedWindow("Detection")

# ---------------- CONTROL VARIABLES ----------------
alert_sent = False
last_alert_time = 0
cooldown = 60   # seconds (avoid spam)

try:
    while True:
        # Capture screen
        sct_img = sct.grab(monitor)
        frame = np.array(sct_img)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

        # YOLO Prediction
        results = model.predict(frame, verbose=False)

        detected_elephant = False

        # Check detections
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                label = class_list[cls_id]

                if label == "elephant":
                    detected_elephant = True

        # ---------------- WHATSAPP ALERT ----------------
        current_time = time.time()

        if detected_elephant:
            if (not alert_sent) or (current_time - last_alert_time > cooldown):
                try:
                    message = client.messages.create(
                        body="🚨 ALERT: Elephant Detected!",
                        from_=FROM_WHATSAPP,
                        to=TO_WHATSAPP
                    )
                    print("✅ WhatsApp Alert Sent!")
                    alert_sent = True
                    last_alert_time = current_time
                except Exception as e:
                    print("❌ Error sending WhatsApp:", e)

        else:
            alert_sent = False

        # ---------------- DISPLAY ----------------
        annotated_frame = results[0].plot()
        cv2.imshow("Detection", annotated_frame)

        # Exit on ESC
        if cv2.waitKey(1) & 0xFF == 27:
            break

finally:
    cv2.destroyAllWindows()