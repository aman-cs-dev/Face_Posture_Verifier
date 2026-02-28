from flask import Flask, request, jsonify
from insightface.app import FaceAnalysis
import mediapipe as mp
from pydantic import BaseModel
import os

import numpy as np
import cv2
from typing import Literal
from openai import OpenAI
import json
import base64
import re

app = Flask(__name__)

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["MEDIAPIPE_DISABLE_GPU"] = "true"

# api key
api_key = os.getenv("api_key")
client = OpenAI(api_key=api_key)

# activates FaceAnalysis
model = FaceAnalysis()
model.prepare(ctx_id=-1)

# activates mediapipe
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


class bodymeasurements(BaseModel):
    height_cm: float
    weight_kg: float
    age: int
    gender: str


class bodymeasurementsTool(BaseModel):
    name: Literal["bodymeasurements"]
    measurements: list[bodymeasurements]


@app.route("/predict", methods=['POST'])
def find_image():

    print("✅ /predict endpoint called")

    if "image" not in request.files:
        return jsonify(status="error", message="The image is missing!"), 400

    if "user_id" not in request.form:
        return jsonify(status="error", message="The user-id is missing!"), 400

    image_file = request.files["image"]
    warning = request.form.get("warning", "").strip()
    print("got image!")
    image_save_path = f"/tmp/{request.form['user_id']}_upload.jpg"
    image_file.save(image_save_path)
    image = cv2.imread(image_save_path)

    # get age and gender from face
    face = model.get(image)
    age = int(face[0].age)
    gender = face[0].gender
    gender = "female" if gender == 0 else "male"

    # convert BGR to RGB for mediapipe
    image_converted = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    result = pose.process(image_converted)

    if result.pose_landmarks is not None:
        landmark = result.pose_landmarks.landmark

        hip_pixels_y = landmark[hip_pixels].y
        nose_y = landmark[nose_pixels].y
        ankle_y = landmark[ankle_pixels].y
        hip_pixels_x = landmark[hip_pixels].x
        hip_right_pixels_x = landmark[hip_right_pixels].x
        shoulder_pixels_x = landmark[shoulder_pixels].x
        shoulder_right_pixels_x = landmark[shoulder_right_pixels].x
        ankle_pixels_x = landmark[ankle_pixels].x
        ankle_right_pixels_x = landmark[ankle_right_pixels].x
        shoulder_pixels_y = landmark[shoulder_pixels].y

        image_height = image.shape[0]
        nose_y_pixels = image_height * nose_y
        ankle_y_pixels = image_height * ankle_y
        distance_pixels = ankle_y_pixels - nose_y_pixels

        # assume head length from nose to top
        head_cms = 20.5

        shoulder_y_pixels = image_height * shoulder_pixels_y
        head_pixel_height = shoulder_y_pixels - nose_y_pixels
        scale_cm_per_pixel = head_cms / head_pixel_height

        height_cm = distance_pixels * scale_cm_per_pixel
        height_m = height_cm / 100

        shoulder_width = abs(shoulder_pixels_x - shoulder_right_pixels_x) * height_m
        hip_width = abs(hip_pixels_x - hip_right_pixels_x) * height_m
        ankle_width = abs(ankle_pixels_x - ankle_right_pixels_x) * height_m

        extension = os.path.splitext(image_save_path)[1].lower().replace(",", "")
        if extension == ".jpg":
            extension = ".jpeg"
        extension = extension.replace(".", "")

        with open(image_save_path, "rb") as file:
            binary_data = file.read()

        Base64_String = base64.b64encode(binary_data).decode("utf-8")

        try:
            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    f"This person has the following body metrics derived from computer vision:\n"
                                    f"- Apparent age from face: {age} years\n"
                                    f"- Gender: {gender}\n"
                                    f"- Shoulder width: {shoulder_width:.4f} meters\n"
                                    f"- Hip width: {hip_width:.4f} meters\n"
                                    f"- Ankle width: {ankle_width:.4f} meters\n"
                                    f"- Vertical nose-to-ankle pixel distance: {distance_pixels:.2f}\n"
                                    f"- Full image height: {image_height} pixels\n\n"
                                    + (f"- ⚠️ Warning (based on image analysis): {warning}\n" if warning else "") +
                                    "Using this data, please estimate the user's:\n"
                                    "your height measurements are sometimes really off, like 140 cm for a 6ft person, so be as accurate as possible\n"
                                    "you need to return the height and weight no matter what nothing just strictly in the format mentioned\n"
                                    "Do NOT wrap it in triple backticks or say anything else.\n"
                                    "I just need the height and weight of the user nothing else at all\n"
                                    "1. Height (in centimeters)\n"
                                    "2. Weight (in kilograms)\n\n"
                                    "Return the result as strict JSON in this format:\n"
                                    "{\"height_cm\": 178.5, \"weight_kg\": 72.2}\n"
                                    "the result should be as accurate as possible.\n"
                                    "**Return ONLY the JSON. No explanation or extra text.**"
                                )
                            }
                        ]
                    }
                ]
            )

            gpt_reply = completion.choices[0].message.content.strip()

            try:
                reply_float = json.loads(gpt_reply)
                height_cm = reply_float["height_cm"]
                weight = reply_float["weight_kg"]
            except Exception as e:
                height_final = re.search(r'"height_cm"\s*:\s*([0-9.]+)', gpt_reply)
                weight_final = re.search(r'"weight_kg"\s*:\s*([0-9.]+)', gpt_reply)
                if height_final and weight_final:
                    height_cm = float(height_final.group(1))
                    weight = float(weight_final.group(1))
                else:
                    return jsonify(status="error", message="Failed to extract height/weight from GPT reply")

        except Exception as e:
            return jsonify(status="error", message="Weight estimation failed"), 500

        finally:
            if os.path.exists(image_save_path):
                os.remove(image_save_path)

        analysis = {
            "age": age,
            "gender": gender,
            "height_cm": round(height_cm, 2),
            "weight": round(weight, 2)
        }

        return jsonify(analysis)

    else:
        return jsonify(status="error", message="No landmarks found please try again!"), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))