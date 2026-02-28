# 👁️ Face & Posture Verifier — Computer Vision Body Analysis Pipeline

A two-stage computer vision backend that first **verifies image quality and posture**, then **estimates height, weight, age, and gender** from a single full-body photo — using MediaPipe, InsightFace, OpenCV, and GPT-4o.

Built as the computer vision backbone of **[FitterGem](https://github.com/aman-cs-dev/Fittergem)** — an AI-powered fitness platform.

---

## 💡 How It Works

```
User uploads full-body photo
        ↓
Stage 1 — Image Verification (/Verification)
  • Checks brightness
  • Detects posture (upright vs bent)
  • Verifies full body is visible
  • Checks face and landmark visibility
        ↓
Stage 2 — Body Measurements (/predict)
  • Detects age & gender via InsightFace
  • Estimates height using MediaPipe pose landmarks + geometric scaling
  • Estimates weight via shoulder/hip/ankle width ratios
  • Refines results using GPT-4o for accuracy
        ↓
Returns: age, gender, height (cm), weight (kg)
```

---

## ✨ Features

**🔍 Stage 1 — Image Verification**
- Brightness validation — rejects images that are too dark or overexposed
- Full-body detection — ensures head, shoulders, and ankles are all visible
- Posture analysis — calculates shoulder-hip-knee angle to detect bending
- Selfie detection — rejects close-up face photos automatically
- HEIC/HEIF support — handles iPhone photo formats
- Returns structured status: `success`, `note`, `warning`, or `error`

**📏 Stage 2 — Body Measurements**
- Age and gender estimation via InsightFace FaceAnalysis model
- Height estimation using nose-to-ankle pixel distance + head scaling
- Weight estimation using shoulder, hip, and ankle width ratios
- GPT-4o refinement for improved accuracy across body types
- Structured JSON fallback parsing if GPT response is malformed

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Pose Detection | MediaPipe (33 landmark model) |
| Face Analysis | InsightFace FaceAnalysis |
| Image Processing | OpenCV, Pillow |
| AI Refinement | OpenAI GPT-4o |
| Backend | Python, Flask |
| Deployment | Docker, Railway |

---

## 📁 Project Structure

```
Face_Posture_Verifier/
├── Image_Verification_Backend_Files/
│   └── verification.py          # /Verification endpoint
├── Age_Height_Gender_Prediction/
│   └── body_measurements.py     # /predict endpoint
├── test_files/
│   ├── test_verification.py     # User-friendly verification tester
│   └── test_body_measurements.py # User-friendly measurements tester
├── Dockerfile
├── Procfile
├── requirements.txt
└── .gitignore
```

---

## ⚙️ Getting Started

### Prerequisites
- Python 3.9+
- OpenAI API key
- Docker (optional, for containerized deployment)

### Installation

```bash
git clone https://github.com/aman-cs-dev/Face_Posture_Verifier.git
cd Face_Posture_Verifier
pip install -r requirements.txt
```

### Environment Variables

```bash
# Windows
set api_key=your_openai_api_key_here

# Mac/Linux
export api_key=your_openai_api_key_here
```

### Run the Servers

```bash
# Terminal 1 — Image Verification
python Image_Verification_Backend_Files/verification.py

# Terminal 2 — Body Measurements
python Age_Height_Gender_Prediction/body_measurements.py
```

Both servers run on `localhost:8080` by default.

---

## 🧪 Testing

Two user-friendly test scripts are included in `test_files/`.

### Step 1 — Verify your image first

```bash
python test_files/test_verification.py your_photo.jpg
```

Example output:
```
✅ Status  : SUCCESS
   Reason  : Image satisfies all the requirements
   Retry?  : no
```

### Step 2 — Get body measurements

```bash
python test_files/test_body_measurements.py your_photo.jpg
```

Example output:
```
✅ Analysis Complete!
──────────────────────────────
  👤 Gender  : Male
  🎂 Age     : 24 years
  📏 Height  : 178.5 cm  (5ft 10.3in)
  ⚖️  Weight  : 74.2 kg  (163.5 lbs)
──────────────────────────────
```

### Tips for best results
- Stand upright against a plain background
- Full body must be visible — head to feet
- Face the camera directly
- Good lighting — not too dark or too bright
- Use a JPG image

---

## 🐳 Docker Deployment

```bash
docker build -t face-posture-verifier .
docker run -e api_key=your_openai_key -p 8080:8080 face-posture-verifier
```

---

## 📡 API Reference

### POST `/Verification`

Validates image quality and posture before analysis.

**Request:** `multipart/form-data`
| Field | Type | Description |
|-------|------|-------------|
| `image` | file | Full-body JPG photo |

**Response:**
```json
{
  "status": "success",
  "reason": "Image satisfies all the requirements",
  "retry": "no"
}
```

| Status | Meaning |
|--------|---------|
| `success` | Image passed all checks |
| `note` | Minor issue, can proceed |
| `warning` | Consider retaking photo |
| `error` | Image failed, must retry |

---

### POST `/predict`

Estimates body measurements from a verified image.

**Request:** `multipart/form-data`
| Field | Type | Description |
|-------|------|-------------|
| `image` | file | Full-body JPG photo |
| `user_id` | string | Unique user identifier |
| `warning` | string | Optional warning from verification stage |

**Response:**
```json
{
  "age": 24,
  "gender": "male",
  "height_cm": 178.5,
  "weight": 74.2
}
```

---

## 👨‍💻 Developer

**Aman Sharma** — CS Student @ Western University
[LinkedIn](https://www.linkedin.com/in/aman-software-dev/) · [Portfolio](https://aman-portfolio-three-xi.vercel.app/) · [GitHub](https://github.com/aman-cs-dev)

*Built as the computer vision backend for FitterGem — an AI-powered fitness platform.*
