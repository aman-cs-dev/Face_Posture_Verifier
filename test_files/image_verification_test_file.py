"""
========================================
  FitterGem — Image Verification Test
========================================

Tests the /Verification endpoint.

BEFORE RUNNING:
  1. Make sure verification.py server is running:
       python verification.py
  2. Have a JPG image of a person standing upright (full body visible)
  3. Run this script:
       python test_verification.py

The test will tell you exactly what the server thinks of your image.
"""

import requests
import sys
import os

SERVER_URL = "http://localhost:8080/Verification"

# ─── COLORS FOR TERMINAL OUTPUT ───────────────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BLUE   = "\033[94m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def print_banner():
    print(f"\n{BLUE}{BOLD}{'='*50}{RESET}")
    print(f"{BLUE}{BOLD}   FitterGem — Image Verification Test{RESET}")
    print(f"{BLUE}{BOLD}{'='*50}{RESET}\n")

def print_result(status, reason, retry):
    if status == "success":
        color = GREEN
        icon = "✅"
    elif status == "note":
        color = BLUE
        icon = "ℹ️ "
    elif status == "warning":
        color = YELLOW
        icon = "⚠️ "
    else:
        color = RED
        icon = "❌"

    print(f"{color}{BOLD}{icon}  Status  : {status.upper()}{RESET}")
    print(f"{color}   Reason  : {reason}{RESET}")
    print(f"{color}   Retry?  : {retry}{RESET}")

def run_test(image_path):
    print_banner()

    # check file exists
    if not os.path.exists(image_path):
        print(f"{RED}❌ File not found: {image_path}{RESET}")
        print(f"{YELLOW}   Make sure the image path is correct and the file exists.{RESET}\n")
        sys.exit(1)

    # check it's a JPG
    if not image_path.lower().endswith((".jpg", ".jpeg")):
        print(f"{YELLOW}⚠️  Warning: This test is designed for JPG images.{RESET}")
        print(f"{YELLOW}   Other formats may work but are not guaranteed.\n{RESET}")

    print(f"{BOLD}📸 Image   : {image_path}{RESET}")
    print(f"{BOLD}🌐 Server  : {SERVER_URL}{RESET}\n")
    print("Sending image to verification server...")
    print("-" * 50)

    try:
        with open(image_path, "rb") as img:
            response = requests.post(
                SERVER_URL,
                files={"image": (os.path.basename(image_path), img, "image/jpeg")}
            )

        if response.status_code == 200:
            data = response.json()
            status = data.get("status", "unknown")
            reason = data.get("reason", "No reason provided")
            retry  = data.get("retry", "unknown")
            print_result(status, reason, retry)

            print(f"\n{BOLD}What this means:{RESET}")
            if status == "success":
                print(f"{GREEN}   Your image passed all checks and is ready for body analysis.{RESET}")
            elif status == "note":
                print(f"{BLUE}   Minor issue detected. You can still proceed but results may vary slightly.{RESET}")
            elif status == "warning":
                print(f"{YELLOW}   Significant issue detected. Consider retaking the photo for better accuracy.{RESET}")
            else:
                print(f"{RED}   Image did not pass verification. Please retake the photo following the tips below.{RESET}")
                print(f"\n{BOLD}📋 Tips for a good photo:{RESET}")
                print("   • Stand upright against a plain background")
                print("   • Make sure your full body is visible (head to feet)")
                print("   • Face the camera directly")
                print("   • Make sure the image is well lit (not too dark or bright)")
                print("   • Don't bend or slouch")

        else:
            print(f"{RED}❌ Server returned error: HTTP {response.status_code}{RESET}")
            print(f"   Response: {response.text}")

    except requests.exceptions.ConnectionError:
        print(f"{RED}❌ Could not connect to the server at {SERVER_URL}{RESET}")
        print(f"{YELLOW}   Make sure verification.py is running first:{RESET}")
        print(f"{YELLOW}   → python verification.py{RESET}\n")
        sys.exit(1)

    except Exception as e:
        print(f"{RED}❌ Unexpected error: {str(e)}{RESET}\n")
        sys.exit(1)

    print(f"\n{BLUE}{'='*50}{RESET}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"\n{BOLD}Usage:{RESET}")
        print(f"   python test_verification.py <path_to_image.jpg>")
        print(f"\n{BOLD}Example:{RESET}")
        print(f"   python test_verification.py sample.jpg")
        print(f"\n{BOLD}Tips for best results:{RESET}")
        print("   • Use a JPG image of a person standing upright")
        print("   • Full body must be visible (head to feet)")
        print("   • Good lighting, plain background\n")
        sys.exit(0)

    run_test(sys.argv[1])