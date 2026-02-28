from flask import Flask, request, jsonify
import mediapipe as mp
import os
import imghdr
from PIL import Image
from pillow_heif import read_heif
import math
from io import BytesIO
import numpy as np
import cv2



app = Flask(__name__)

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["MEDIAPIPE_DISABLE_GPU"] = "true"

# activates the mediapipe
pose = mp.solutions.pose.Pose(mp.solutions.pose.Pose(
    static_image_mode=True,
    model_complexity=1,
    enable_segmentation=False,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
))

# landmark indices
nose_pixels = mp.solutions.pose.PoseLandmark.NOSE.value
ankle_pixels = mp.solutions.pose.PoseLandmark.LEFT_ANKLE.value
ankle_right_pixels = mp.solutions.pose.PoseLandmark.RIGHT_ANKLE.value
shoulder_pixels = mp.solutions.pose.PoseLandmark.LEFT_SHOULDER.value
shoulder_right_pixels = mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER.value
hip_pixels = mp.solutions.pose.PoseLandmark.LEFT_HIP.value
hip_right_pixels = mp.solutions.pose.PoseLandmark.RIGHT_HIP.value
knee_pixels = mp.solutions.pose.PoseLandmark.LEFT_KNEE.value
knee_right_pixels = mp.solutions.pose.PoseLandmark.RIGHT_KNEE.value
wrist_pixels = mp.solutions.pose.PoseLandmark.RIGHT_WRIST.value
elbow_pixels = mp.solutions.pose.PoseLandmark.LEFT_ELBOW.value

nose = mp.solutions.pose.PoseLandmark.NOSE.value
ankle_Left = mp.solutions.pose.PoseLandmark.LEFT_ANKLE.value
ankle_Right = mp.solutions.pose.PoseLandmark.RIGHT_ANKLE.value
shoulder_Right = mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER.value
shoulder_Left = mp.solutions.pose.PoseLandmark.LEFT_SHOULDER.value
knee_Left = mp.solutions.pose.PoseLandmark.LEFT_KNEE.value
wrist_Left = mp.solutions.pose.PoseLandmark.LEFT_WRIST.value
wrist_Right = mp.solutions.pose.PoseLandmark.RIGHT_WRIST.value
Hip_Left = mp.solutions.pose.PoseLandmark.LEFT_HIP.value
ANKLE_LEFT = mp.solutions.pose.PoseLandmark.LEFT_ANKLE.value
NOSE = mp.solutions.pose.PoseLandmark.NOSE.value
SHOULDER_LEFT = mp.solutions.pose.PoseLandmark.LEFT_SHOULDER.value


@app.route("/Verification", methods=['POST'])
def image_processing():

    file = request.files["image"]
    if file is None or file.filename == '':
        return jsonify(status="error", reason="the image seems corrupted", retry="yes"), 400
    raw = file.read()

    file_type = imghdr.what(None, h=raw)
    file_ext = file.filename.lower()

    try:
        if file_type in ["heic", "heif"]:
            heif_file = read_heif(raw)
            image_pil = Image.frombytes(
                heif_file.mode, heif_file.size, heif_file.data, "raw"
            )
            buffer = BytesIO()
            image_pil.save(buffer, format="JPEG")
            buffer.seek(0)
            file_bytes = np.asarray(bytearray(buffer.read()), dtype=np.uint8)
            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        else:
            file_bytes = np.frombuffer(raw, np.uint8)
            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    except Exception as e:
        return jsonify(status="error", reason=f"Invalid image format or corrupt image. Error: {str(e)}", retry="yes")

    # resize if resolution too high
    MAX_DIM = 1280
    height, width = image.shape[:2]
    if max(height, width) > MAX_DIM:
        scale = MAX_DIM / max(height, width)
        new_size = (int(width * scale), int(height * scale))
        image = cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)

    image_converted = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    result = pose.process(image_converted)

    if image is None:
        return jsonify(status="error", reason="Could not load the image!", retry="yes")

    if result is None:
        return jsonify(status="error", reason="could not convert the image to the required format!", retry="yes")

    try:
        landmarks = result.pose_landmarks.landmark
    except Exception:
        return jsonify(status="error", reason="could not find a face!", retry="yes")

    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    Brightness = np.mean(gray_image)

    if Brightness < 50 or Brightness > 200:
        return jsonify(status="note", reason="The image is either too bright or less bright!", retry="optional")

    A = landmarks[shoulder_Left]
    B = landmarks[Hip_Left]
    C = landmarks[knee_Left]

    NOSE_Y = landmarks[NOSE].y
    ANKLE_LEFT_Y = landmarks[ANKLE_LEFT].y
    SHOULDER_LEFT_Y = landmarks[SHOULDER_LEFT].y

    hip_vis = (landmarks[Hip_Left].visibility + landmarks[hip_right_pixels].visibility) / 2
    shoulder_vis = (landmarks[shoulder_Left].visibility + landmarks[shoulder_Right].visibility) / 2

    BODY_RATIO = (ANKLE_LEFT_Y - NOSE_Y) / (SHOULDER_LEFT_Y - NOSE_Y)

    if hip_vis < 0.3 and shoulder_vis > 0.5:
        return jsonify(status="error", reason="please upload full body image!", retry="yes")

    if BODY_RATIO > 9.1:
        return jsonify(status="warning", reason="The image seems to be a little too close!", retry="optional")

    a = np.array([A.x, A.y])
    b = np.array([B.x, B.y])
    c = np.array([C.x, C.y])

    v1 = a - b
    v2 = c - b
    cos_theta = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
    cos_theta = np.clip(cos_theta, -1.0, 1.0)
    angle = math.degrees(math.acos(cos_theta))

    if angle < 171 and angle >= 150:
        return jsonify(status="note", reason="You seem a little bent, this could maybe lead to minor inaccuracy in prediction of height!", retry="optional")
    elif angle < 150 and angle >= 130:
        return jsonify(status="warning", reason="You seem a slightly bent, this could possibly lead to inaccurate prediction of height!", retry="optional")
    elif angle < 130:
        return jsonify(status="error", reason="You seem a too bent, this could maybe lead to inaccurate prediction of height!", retry="yes")

    if landmarks is not None:
        if landmarks[nose].visibility < 0.45:
            return jsonify(status="error", reason="the image seems incomplete!", retry="yes")
        elif landmarks[shoulder_Left].visibility < 0.45:
            return jsonify(status="error", reason="the image seems incomplete!", retry="yes")
        elif landmarks[ankle_Left].visibility < 0.45:
            return jsonify(status="error", reason="the image seems incomplete!", retry="yes")
        elif landmarks[ankle_Right].visibility < 0.45:
            return jsonify(status="error", reason="the image seems incomplete!", retry="yes")
        elif landmarks[shoulder_Right].visibility < 0.5:
            return jsonify(status="error", reason="the image seems incomplete!", retry="yes")
        elif landmarks[wrist_Right].visibility < 0.5:
            return jsonify(status="error", reason="the image seems incomplete!", retry="yes")

        shoulder_Right_Y = landmarks[shoulder_Right].y
        shoulder_Left_Y = landmarks[shoulder_Left].y
        knee_Left_Y = landmarks[knee_Left].y
        ankle_Left_Y = landmarks[ankle_Left].y

        if shoulder_Left_Y > knee_Left_Y or shoulder_Left_Y > ankle_Left_Y:
            return jsonify(status="error", reason="you seem to have a sitting position. This could lead to inaccurate results!", retry="yes")

        if abs(shoulder_Left_Y - shoulder_Right_Y) > 0.05:
            return jsonify(status="error", reason="you seem to have a little bend position. This could lead to inaccurate results!", retry="yes")

        return jsonify(status="success", reason="Image satisfies all the requirements")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))