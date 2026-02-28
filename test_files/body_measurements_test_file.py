"""
========================================
  FitterGem — Body Measurements Test
========================================

Tests the /predict endpoint.

BEFORE RUNNING:
  1. Make sure body_measurements.py server is running:
       python body_measurements.py
  2. Have a JPG image of a person standing upright (full body visible)
  3. Make sure your OpenAI API key is set as an environment variable:
       Windows:  set api_key=your_openai_key_here
       Mac/Linux: export api_key=your_openai_key_here
  4. Run this script:
       python test_body_measurements.py

The test will return the estimated age, gender, height, and weight.
"""

import requests
import sys
import os

SERVER_URL = "http://localhost:8080/predict"

# ─── COLORS FOR TERMINAL OUTPUT ───────────────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BLUE   = "\033[94m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def print_banner():
    print(f"\n{BLUE}{BOLD}{'='*50}{RESET}")
    print(f"{BLUE}{BOLD}   FitterGem — Body Measurements Test{RESET}")
    print(f"{BLUE}{BOLD}{'='*50}{RESET}\n")

def print_measurements(data):
    age        = data.get("age", "N/A")
    gender     = data.get("gender", "N/A").capitalize()
    height_cm  = data.get("height_cm", "N/A")
    weight_kg  = data.get("weight", "N/A")

    # convert height to feet/inches as well
    try:
        total_inches = height_cm / 2.54
        feet = int(total_inches // 12)
        inches = round(total_inches % 12, 1)
        height_imperial = f"{feet}ft {inches}in"
    except:
        height_imperial = ""

    print(f"{GREEN}{BOLD}✅ Analysis Complete!{RESET}\n")
    print(f"{BOLD}{'─'*30}{RESET}")
    print(f"{CYAN}{BOLD}  👤 Gender    : {RESET}{gender}")
    print(f"{CYAN}{BOLD}  🎂 Age       : {RESET}{age} years")
    print(f"{CYAN}{BOLD}  📏 Height    : {RESET}{height_cm} cm  ({height_imperial})")
    print(f"{CYAN}{BOLD}  ⚖️  Weight    : {RESET}{weight_kg} kg  ({round(weight_kg * 2.205, 1)} lbs)")
    print(f"{BOLD}{'─'*30}{RESET}")

def run_test(image_path, user_id="test_user_001", warning=""):
    print_banner()

    # check file exists
    if not os.path.exists(image_path):
        print(f"{RED}❌ File not found: {image_path}{RESET}")
        print(f"{YELLOW}   Make sure the image path is correct.\n{RESET}")
        sys.exit(1)

    # check it's a JPG
    if not image_path.lower().endswith((".jpg", ".jpeg")):
        print(f"{YELLOW}⚠️  Warning: This test is designed for JPG images.{RESET}")
        print(f"{YELLOW}   Other formats may work but are not guaranteed.\n{RESET}")

    print(f"{BOLD}📸 Image     : {image_path}{RESET}")
    print(f"{BOLD}🆔 User ID   : {user_id}{RESET}")
    print(f"{BOLD}🌐 Server    : {SERVER_URL}{RESET}")
    if warning:
        print(f"{YELLOW}{BOLD}⚠️  Warning   : {warning}{RESET}")
    print()
    print("Sending image for analysis... (this may take a few seconds)")
    print("-" * 50)

    try:
        with open(image_path, "rb") as img:
            response = requests.post(
                SERVER_URL,
                files={"image": (os.path.basename(image_path), img, "image/jpeg")},
                data={
                    "user_id": user_id,
                    "warning": warning
                }
            )

        if response.status_code == 200:
            data = response.json()

            # check if it returned an error inside a 200 response
            if data.get("status") == "error":
                print(f"{RED}❌ Analysis failed:{RESET}")
                print(f"   {data.get('message', 'Unknown error')}")
                print(f"\n{BOLD}📋 Tips for a good photo:{RESET}")
                print("   • Stand upright against a plain background")
                print("   • Make sure your full body is visible (head to feet)")
                print("   • Face the camera directly")
                print("   • Good lighting — not too dark or bright")
                print("   • Run test_verification.py first to check your image\n")
            else:
                print_measurements(data)
                print(f"\n{BOLD}ℹ️  Note:{RESET}")
                print("   These are AI-estimated values based on computer vision.")
                print("   Results are approximate and may vary based on image quality.")

        elif response.status_code == 400:
            data = response.json()
            print(f"{RED}❌ Bad request: {data.get('message', response.text)}{RESET}")
            print(f"{YELLOW}   Make sure both image and user_id are provided correctly.{RESET}\n")

        elif response.status_code == 500:
            print(f"{RED}❌ Server error (500) — this is likely an OpenAI API issue.{RESET}")
            print(f"{YELLOW}   Check that your api_key environment variable is set correctly:{RESET}")
            print(f"{YELLOW}   Windows:   set api_key=your_key_here{RESET}")
            print(f"{YELLOW}   Mac/Linux: export api_key=your_key_here{RESET}\n")

        else:
            print(f"{RED}❌ Unexpected HTTP {response.status_code}{RESET}")
            print(f"   Response: {response.text}\n")

    except requests.exceptions.ConnectionError:
        print(f"{RED}❌ Could not connect to the server at {SERVER_URL}{RESET}")
        print(f"{YELLOW}   Make sure body_measurements.py is running first:{RESET}")
        print(f"{YELLOW}   → python body_measurements.py{RESET}\n")
        sys.exit(1)

    except Exception as e:
        print(f"{RED}❌ Unexpected error: {str(e)}{RESET}\n")
        sys.exit(1)

    print(f"\n{BLUE}{'='*50}{RESET}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"\n{BOLD}Usage:{RESET}")
        print(f"   python test_body_measurements.py <path_to_image.jpg> [user_id] [warning]")
        print(f"\n{BOLD}Examples:{RESET}")
        print(f"   python test_body_measurements.py sample.jpg")
        print(f"   python test_body_measurements.py sample.jpg user_123")
        print(f"   python test_body_measurements.py sample.jpg user_123 'slightly bent posture'")
        print(f"\n{BOLD}Tips for best results:{RESET}")
        print("   • Use a JPG image of a person standing upright")
        print("   • Full body must be visible (head to feet)")
        print("   • Good lighting, plain background")
        print("   • Run test_verification.py first to make sure your image passes\n")
        sys.exit(0)

    image_path = sys.argv[1]
    user_id    = sys.argv[2] if len(sys.argv) > 2 else "test_user_001"
    warning    = sys.argv[3] if len(sys.argv) > 3 else ""

    run_test(image_path, user_id, warning)