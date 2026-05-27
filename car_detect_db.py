from ultralytics import YOLO
import cv2
import os
import psycopg2
from psycopg2.extras import execute_values
import argparse
import time

# ========= CLI =========
parser = argparse.ArgumentParser(description="Conteo YOLO (RTSP o video) + PostgreSQL")
parser.add_argument("source", help="rtsp://...  o  /ruta/video.mp4")
parser.add_argument("--show", action="store_true", help="Mostrar ventana")
parser.add_argument("--skip", type=int, default=1, help="Procesar 1 de cada N frames (solo archivo)")
args = parser.parse_args()

SOURCE = args.source
SHOW = args.show
SKIP = max(1, args.skip)

# ========= CONFIG =========
LINE_P1 = (800, 0)
LINE_P2 = (0, 700)
#LINE_P1 = (0, 50)
#LINE_P2 = (1300, 700)

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "bodegas_balam",
    "user": "postgres",
    "password": "password"
}

BATCH_SIZE = 5
MODEL_NAME = "yolov8n.pt"
#MODEL_NAME = "yolov8s.pt"

# ========= INIT =========
model = YOLO(MODEL_NAME)

is_rtsp = SOURCE.lower().startswith("rtsp://")

if is_rtsp:
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
    cap = cv2.VideoCapture(SOURCE, cv2.CAP_FFMPEG)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
else:
    cap = cv2.VideoCapture(SOURCE)

if not cap.isOpened():
    raise RuntimeError(f"No se pudo abrir la fuente: {SOURCE}")

# DB
conn = psycopg2.connect(**DB_CONFIG)
conn.autocommit = True
cur = conn.cursor()

# Contadores
total_cars = 0
total_people = 0
total_bikes = 0

# Tracking
prev_positions = {}
counted_ids = set()

# Buffer DB
buffer = []

# ========= FUNC =========
def side_of_line(px, py, x1, y1, x2, y2):
    return (px - x1) * (y2 - y1) - (py - y1) * (x2 - x1)

def save_batch(rows):
    if not rows:
        return
    query = """
        INSERT INTO detections (object_type, object_id)
        VALUES %s
        ON CONFLICT DO NOTHING
    """
    execute_values(cur, query, rows)

# ========= LOOP =========
frame_idx = 0
t0 = time.time()

while True:
    ret, frame = cap.read()
    if frame is not None and frame.any():
        frame = cv2.resize(frame, (960, 540))

    if not ret or frame is None:
        if is_rtsp:
            continue
        else:
            break

    frame_idx += 1

    # 🚀 MODO RÁPIDO
    if frame_idx % SKIP != 0:
        continue

    results = model.track(
        frame,
        tracker="bytetrack.yaml",
        classes=[0, 2, 3],  # person, car, motorcycle
        persist=True,
        conf=0.3,
        verbose=False
    )
    #results = model(frame, verbose=False)

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

            #if cls not in [0, 2, 3]:
            #    continue

            x1, y1, x2, y2 = map(int, box)
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2

            current_side = side_of_line(cx, cy, *LINE_P1, *LINE_P2)

            if obj_id in prev_positions:
                prev_side = prev_positions[obj_id]

                if current_side * prev_side < 0 and obj_id not in counted_ids:
                    counted_ids.add(obj_id)

                    if cls == 2:
                        total_cars += 1
                        buffer.append(("car", obj_id))
                    elif cls == 0:
                        total_people += 1
                        buffer.append(("person", obj_id))
                    elif cls == 3:
                        total_bikes += 1
                        buffer.append(("motorcycle", obj_id))

                    if len(buffer) >= BATCH_SIZE:
                        save_batch(buffer)
                        buffer.clear()

            prev_positions[obj_id] = current_side

            # Dibujar solo si SHOW
            if SHOW:
                if cls == 2:
                    label, color = "car", (0,255,0)
                elif cls == 0:
                    label, color = "person", (255,255,0)
                else:
                    label, color = "motorcycle", (0,255,255)

                cv2.rectangle(frame, (x1,y1), (x2,y2), color, 2)
                cv2.circle(frame, (cx,cy), 4, (0,0,255), -1)
                cv2.putText(frame, f"{label} ID:{obj_id}", (x1, y1-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    # UI solo si SHOW
    if SHOW:
        cv2.line(frame, LINE_P1, LINE_P2, (255,0,0), 3)

        cv2.putText(frame, f"Cars: {total_cars}", (20,40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)

        cv2.putText(frame, f"People: {total_people}", (20,80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,0), 2)

        cv2.putText(frame, f"Bikes: {total_bikes}", (20,120),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)

        cv2.imshow("Conteo Multiclase", frame)

        if cv2.waitKey(1) == 27:
            break

# flush final
save_batch(buffer)

cap.release()
cv2.destroyAllWindows()
cur.close()
conn.close()

elapsed = time.time() - t0
print(f"Tiempo total: {elapsed:.2f}s")
print("Cars:", total_cars)
print("People:", total_people)
print("Bikes:", total_bikes)
