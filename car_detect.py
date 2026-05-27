from ultralytics import YOLO
import cv2
import os

# ====== CONFIG ======
RTSP_URL = "rtsp://192.168.1.35"  # <-- ajusta si falta usuario/pass o path
LINE_P1 = (0, 50)
LINE_P2 = (1300, 700)

# ====== INIT ======
model = YOLO("yolov8n.pt")

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

cap = cv2.VideoCapture(RTSP_URL, cv2.CAP_FFMPEG)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

# Contadores
total_cars = 0
total_people = 0
total_bikes = 0

# Tracking estado
prev_positions = {}
counted_ids = set()

# ====== FUNC ======
def side_of_line(px, py, x1, y1, x2, y2):
    return (px - x1) * (y2 - y1) - (py - y1) * (x2 - x1)

# ====== LOOP ======
while True:
    ret, frame = cap.read()
    if not ret:
        continue

    # Inferencia + tracking
    results = model.track(frame, persist=True, conf=0.25, verbose=False)

    for r in results:
        if r.boxes is None:
            continue

        boxes = r.boxes.xyxy.cpu().numpy()
        classes = r.boxes.cls.cpu().numpy()
        ids = r.boxes.id

        if ids is None:
            continue

        ids = ids.cpu().numpy()

        for box, cls, obj_id in zip(boxes, classes, ids):

            cls = int(cls)
            obj_id = int(obj_id)

            # Solo persona, carro, moto
            if cls not in [0, 2, 3]:
                continue

            x1, y1, x2, y2 = map(int, box)
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2

            # lado actual
            current_side = side_of_line(cx, cy, *LINE_P1, *LINE_P2)

            if obj_id in prev_positions:
                prev_side = prev_positions[obj_id]

                # Cruce de línea
                if current_side * prev_side < 0 and obj_id not in counted_ids:
                    counted_ids.add(obj_id)

                    if cls == 2:
                        total_cars += 1
                    elif cls == 0:
                        total_people += 1
                    elif cls == 3:
                        total_bikes += 1

            prev_positions[obj_id] = current_side

            # ====== DIBUJAR ======
            if cls == 2:
                label = "car"
                color = (0, 255, 0)
            elif cls == 0:
                label = "person"
                color = (255, 255, 0)
            else:
                label = "motorcycle"
                color = (0, 255, 255)

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)

            cv2.putText(frame, f"{label} ID:{obj_id}", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    # ====== UI ======
    cv2.line(frame, LINE_P1, LINE_P2, (255, 0, 0), 3)

    cv2.putText(frame, f"Cars: {total_cars}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    cv2.putText(frame, f"People: {total_people}", (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

    cv2.putText(frame, f"Bikes: {total_bikes}", (20, 120),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

    cv2.imshow("Conteo Multiclase", frame)

    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()
