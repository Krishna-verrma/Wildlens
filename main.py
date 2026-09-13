import os
import sys
import time
import signal
import logging
import argparse
from pathlib import Path
import numpy as np
import cv2
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("Wildlens")

# Load environment variables
load_dotenv()

# Optional Twilio import
try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    logger.warning("Twilio library not found. WhatsApp alerts will be disabled.")

# Optional MSS import for screen capture
try:
    import mss
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False


def parse_args():
    parser = argparse.ArgumentParser(description="Wildlens: Real-Time Elephant Detection & Alert System")
    parser.add_argument(
        "--source",
        type=str,
        default=os.getenv("SOURCE", "ele.mp4"),
        help="Input source: '0' for webcam, 'screen' for screen capture, or path/URL to video file or RTSP stream (default: ele.mp4)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=os.getenv("MODEL_NAME", "yolov8s.pt"),
        help="YOLO model path or name (default: yolov8s.pt)"
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=float(os.getenv("CONFIDENCE", "0.45")),
        help="Confidence threshold for detection (default: 0.45)"
    )
    parser.add_argument(
        "--cooldown",
        type=int,
        default=int(os.getenv("ALERT_COOLDOWN", "60")),
        help="Cooldown between alerts in seconds (default: 60)"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=os.getenv("HEADLESS", "false").lower() in ("true", "1", "yes"),
        help="Run without displaying a GUI window (default: false)"
    )
    return parser.parse_args()


class WhatsAppNotifier:
    def __init__(self, account_sid: str, auth_token: str, from_num: str, to_num: str, cooldown: int):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_num = from_num
        self.to_num = to_num
        self.cooldown = cooldown
        self.last_alert_time = 0
        self.client = None

        if not TWILIO_AVAILABLE:
            logger.warning("Twilio is not installed. Alerts disabled.")
            return

        is_placeholder = (
            not account_sid
            or "YOUR_" in account_sid
            or not auth_token
            or "YOUR_" in auth_token
            or not to_num
            or "XXXX" in to_num
        )

        if is_placeholder:
            logger.warning("Twilio credentials not configured in .env. Detection will run in visual/log-only mode.")
        else:
            try:
                self.client = Client(account_sid, auth_token)
                logger.info(f"Twilio client initialized. Alerts will be sent to {self.to_num}")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")

    def send_alert(self, message_text: str = "🚨 ALERT: Elephant Detected by Wildlens!"):
        current_time = time.time()
        if (current_time - self.last_alert_time) < self.cooldown:
            return False

        if not self.client:
            logger.info(f"[SIMULATED ALERT] {message_text} (Configure .env with real Twilio credentials to send)")
            self.last_alert_time = current_time
            return False

        try:
            msg = self.client.messages.create(
                body=message_text,
                from_=self.from_num,
                to=self.to_num
            )
            logger.info(f"✅ WhatsApp alert sent successfully! SID: {msg.sid}")
            self.last_alert_time = current_time
            return True
        except Exception as e:
            logger.error(f"❌ Failed to send WhatsApp alert: {e}")
            return False


class DetectionPipeline:
    def __init__(self, args):
        self.args = args
        self.running = True

        # Load YOLO model
        logger.info(f"Loading YOLO model: {args.model} ...")
        from ultralytics import YOLO
        self.model = YOLO(args.model)

        # Load class list
        coco_file = Path("coco.txt")
        if coco_file.exists():
            with open(coco_file, "r") as f:
                self.class_list = [c.strip() for c in f.read().split("\n") if c.strip()]
        else:
            # Fallback to model names directly
            self.class_list = list(self.model.names.values())

        # Initialize notifier
        self.notifier = WhatsAppNotifier(
            account_sid=os.getenv("TWILIO_ACCOUNT_SID", ""),
            auth_token=os.getenv("TWILIO_AUTH_TOKEN", ""),
            from_num=os.getenv("FROM_WHATSAPP", "whatsapp:+14155238886"),
            to_num=os.getenv("TO_WHATSAPP", ""),
            cooldown=args.cooldown
        )

        # Handle screen capture vs video stream
        self.is_screen = (str(args.source).lower() == "screen")
        if self.is_screen:
            if not MSS_AVAILABLE:
                raise RuntimeError("MSS is required for screen capture. Install with `pip install mss`.")
            self.sct = mss.mss()
            self.monitor = self.sct.monitors[1]
            self.cap = None
            logger.info("Initialized screen capture pipeline.")
        else:
            # Check if source is an integer (camera index)
            source_val = int(args.source) if args.source.isdigit() else args.source
            self.cap = cv2.VideoCapture(source_val)
            if not self.cap.isOpened():
                raise RuntimeError(f"Unable to open video source: {args.source}")
            logger.info(f"Opened video stream: {args.source}")

        # Headless check
        self.headless = args.headless
        if not self.headless:
            # Check if display is available (especially on Linux / macOS SSH)
            if sys.platform.startswith("linux") and not os.getenv("DISPLAY"):
                logger.warning("No DISPLAY environment variable detected. Switching to headless mode.")
                self.headless = True

    def get_frame(self):
        if self.is_screen:
            sct_img = self.sct.grab(self.monitor)
            frame = np.array(sct_img)
            return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        else:
            ret, frame = self.cap.read()
            if not ret:
                # Loop video if source is a file
                if isinstance(self.args.source, str) and Path(self.args.source).exists():
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = self.cap.read()
            return frame if ret else None

    def run(self):
        logger.info("Starting detection loop. Press Ctrl+C or ESC in the window to stop.")
        if not self.headless:
            cv2.namedWindow("Wildlens - Elephant Detection", cv2.WINDOW_NORMAL)

        frame_count = 0
        fps_start_time = time.time()

        try:
            while self.running:
                frame = self.get_frame()
                if frame is None:
                    logger.info("End of video stream reached.")
                    break

                frame_count += 1

                # YOLO Inference
                results = self.model.predict(frame, conf=self.args.conf, verbose=False)

                detected_elephant = False
                for r in results:
                    for box in r.boxes:
                        cls_id = int(box.cls[0])
                        # Check label
                        label = self.class_list[cls_id] if cls_id < len(self.class_list) else self.model.names.get(cls_id, "")
                        if label == "elephant":
                            detected_elephant = True
                            conf_score = float(box.conf[0])
                            logger.info(f"🐘 Elephant detected! (Confidence: {conf_score:.2f})")

                if detected_elephant:
                    self.notifier.send_alert()

                # Visual feedback
                if not self.headless:
                    annotated_frame = results[0].plot()

                    # Calculate and display FPS
                    elapsed = time.time() - fps_start_time
                    if elapsed > 0:
                        fps = frame_count / elapsed
                        cv2.putText(
                            annotated_frame,
                            f"FPS: {fps:.1f}",
                            (20, 40),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1,
                            (0, 255, 0),
                            2
                        )

                    cv2.imshow("Wildlens - Elephant Detection", annotated_frame)
                    if cv2.waitKey(1) & 0xFF == 27:  # ESC to quit
                        break

        finally:
            self.cleanup()

    def cleanup(self):
        logger.info("Cleaning up resources...")
        self.running = False
        if self.cap:
            self.cap.release()
        if not self.headless:
            cv2.destroyAllWindows()
        logger.info("Wildlens shutdown complete.")


def main():
    args = parse_args()
    pipeline = DetectionPipeline(args)

    # Handle graceful signals
    def handle_signal(sig, frame):
        logger.info(f"Received exit signal ({sig}). Stopping...")
        pipeline.running = False

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    pipeline.run()


if __name__ == "__main__":
    main()
