#!/usr/bin/env python3
import requests
import json
import base64
import time
import uuid
import os
import sys
from dotenv import load_dotenv
import random
from pathlib import Path

# Load environment variables from frontend/.env
load_dotenv(Path(__file__).parent / "frontend" / ".env")

# Get the backend URL from environment variables
BACKEND_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BACKEND_URL:
    print("Error: REACT_APP_BACKEND_URL not found in environment variables")
    sys.exit(1)

# Ensure the URL has the /api prefix
API_URL = f"{BACKEND_URL}/api"
print(f"Using API URL: {API_URL}")

# Test data
TEST_USER = {
    "name": f"Test User {uuid.uuid4().hex[:8]}",
    "email": f"test.user.{uuid.uuid4().hex[:8]}@example.com",
    "password": "Password123!"
}

TEST_WEBSITE = {
    "business_name": "Elegant Boutique",
    "business_description": "A premium fashion boutique offering the latest trends in clothing and accessories.",
    "industry": "fashion",
    "contact_email": "contact@elegantboutique.com",
    "contact_phone": "+1 (555) 123-4567",
    "address": "123 Fashion Avenue, Style District, NY 10001",
    "logo_base64": None,  # Will be populated with a sample base64 image
    "hero_image_base64": None,  # Will be populated with a sample base64 image
    "products": [
        {
            "name": "Designer Handbag",
            "description": "Luxury leather handbag with gold accents",
            "price": "299.99",
            "image_base64": None  # Will be populated with a sample base64 image
        },
        {
            "name": "Silk Scarf",
            "description": "Premium silk scarf with unique pattern",
            "price": "89.99",
            "image_base64": None  # Will be populated with a sample base64 image
        }
    ],
    "colors": {
        "primary": "#4A90E2",
        "secondary": "#50E3C2",
        "accent": "#F5A623"
    },
    "social_links": {
        "facebook": "https://facebook.com/elegantboutique",
        "instagram": "https://instagram.com/elegant_boutique",
        "twitter": "https://twitter.com/elegantboutique"
    }
}

# Generate a simple colored image as base64
def generate_base64_image(width=100, height=100, color=None):
    if color is None:
        # Generate a random color
        color = (
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255)
        )
    
    # Create a simple colored image
    image_data = bytearray([color[0], color[1], color[2]] * width * height)
    
    # Convert to base64
    base64_image = base64.b64encode(image_data).decode('utf-8')
    return base64_image

# Generate sample images
def generate_sample_images():
    global TEST_WEBSITE
    TEST_WEBSITE["logo_base64"] = generate_base64_image(200, 200, (66, 133, 244))
    TEST_WEBSITE["hero_image_base64"] = generate_base64_image(800, 400, (219, 68, 55))
    
    for product in TEST_WEBSITE["products"]:
        product["image_base64"] = generate_base64_image(300, 300)

# Test results tracking
test_results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "tests": []
}

def record_test_result(test_name, passed, message="", response=None):
    test_results["total"] += 1
    if passed:
        test_results["passed"] += 1
        status = "PASSED"
    else:
        test_results["failed"] += 1
        status = "FAILED"
    
    response_info = ""
    if response:
        try:
            response_info = f"Status: {response.status_code}, Response: {response.json()}"
        except:
            response_info = f"Status: {response.status_code}, Response: {response.text[:100]}"
    
    test_results["tests"].append({
        "name": test_name,
        "status": status,
        "message": message,
        "response": response_info
    })
    
    print(f"{status}: {test_name} - {message}")

def print_test_summary():
    print("\n" + "="*80)
    print(f"TEST SUMMARY: {test_results['passed']}/{test_results['total']} tests passed")
    print("="*80)
    
    for test in test_results["tests"]:
        status_symbol = "✅" if test["status"] == "PASSED" else "❌"
        print(f"{status_symbol} {test['name']}")
        if test["status"] == "FAILED":
            print(f"   Message: {test['message']}")
            print(f"   Response: {test['response']}")
    
    print("="*80)
    if test_results["failed"] == 0:
        print("All tests passed successfully!")
    else:
        print(f"{test_results['failed']} tests failed.")
    print("="*80)

# Main test function
def run_tests():
    access_token = None
    user_id = None
    website_id = None
    website_slug = None
    
    # Generate sample images
    generate_sample_images()
    
    print("\n" + "="*80)
    print("STARTING BACKEND API TESTS")
    print("="*80)
    
    # 1. Test User Registration
    print("\n1. Testing User Authentication System")
    print("-"*80)
    
    try:
        response = requests.post(
            f"{API_URL}/auth/register",
            json=TEST_USER
        )
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get("access_token")
            record_test_result(
                "User Registration",
                True,
                f"Successfully registered user: {TEST_USER['email']}",
                response
            )
        else:
            record_test_result(
                "User Registration",
                False,
                f"Failed to register user: {response.status_code}",
                response
            )
    except Exception as e:
        record_test_result(
            "User Registration",
            False,
            f"Exception: {str(e)}"
        )
    
    # 2. Test User Login
    try:
        response = requests.post(
            f"{API_URL}/auth/login",
            json={
                "email": TEST_USER["email"],
                "password": TEST_USER["password"]
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get("access_token")
            record_test_result(
                "User Login",
                True,
                f"Successfully logged in as: {TEST_USER['email']}",
                response
            )
        else:
            record_test_result(
                "User Login",
                False,
                f"Failed to login: {response.status_code}",
                response
            )
    except Exception as e:
        record_test_result(
            "User Login",
            False,
            f"Exception: {str(e)}"
        )
    
    # Skip remaining tests if we don't have an access token
    if not access_token:
        record_test_result(
            "Authentication Tests",
            False,
            "Skipping remaining tests due to authentication failure"
        )
        print_test_summary()
        return
    
    # Set up headers for authenticated requests
    auth_headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    # 3. Test Protected Route Access
    try:
        response = requests.get(
            f"{API_URL}/auth/me",
            headers=auth_headers
        )
        
        if response.status_code == 200:
            data = response.json()
            user_id = data.get("id")
            record_test_result(
                "Protected Route Access",
                True,
                f"Successfully accessed protected route. User ID: {user_id}",
                response
            )
        else:
            record_test_result(
                "Protected Route Access",
                False,
                f"Failed to access protected route: {response.status_code}",
                response
            )
    except Exception as e:
        record_test_result(
            "Protected Route Access",
            False,
            f"Exception: {str(e)}"
        )
    
    # 4. Test Website Creation
    print("\n2. Testing Website Management")
    print("-"*80)
    
    try:
        response = requests.post(
            f"{API_URL}/websites",
            json=TEST_WEBSITE,
            headers=auth_headers
        )
        
        if response.status_code == 200:
            data = response.json()
            website_id = data.get("id")
            website_slug = data.get("slug")
            record_test_result(
                "Website Creation",
                True,
                f"Successfully created website. ID: {website_id}, Slug: {website_slug}",
                response
            )
        else:
            record_test_result(
                "Website Creation",
                False,
                f"Failed to create website: {response.status_code}",
                response
            )
    except Exception as e:
        record_test_result(
            "Website Creation",
            False,
            f"Exception: {str(e)}"
        )
    
    # Skip remaining website tests if we don't have a website ID
    if not website_id:
        record_test_result(
            "Website Tests",
            False,
            "Skipping remaining website tests due to website creation failure"
        )
        print_test_summary()
        return
    
    # 5. Test Website Listing
    try:
        response = requests.get(
            f"{API_URL}/websites",
            headers=auth_headers
        )
        
        if response.status_code == 200:
            data = response.json()
            websites_count = len(data)
            record_test_result(
                "Website Listing",
                True,
                f"Successfully listed websites. Count: {websites_count}",
                response
            )
        else:
            record_test_result(
                "Website Listing",
                False,
                f"Failed to list websites: {response.status_code}",
                response
            )
    except Exception as e:
        record_test_result(
            "Website Listing",
            False,
            f"Exception: {str(e)}"
        )
    
    # 6. Test Website Retrieval
    try:
        response = requests.get(
            f"{API_URL}/websites/{website_id}",
            headers=auth_headers
        )
        
        if response.status_code == 200:
            data = response.json()
            retrieved_name = data.get("business_name")
            record_test_result(
                "Website Retrieval",
                True,
                f"Successfully retrieved website. Name: {retrieved_name}",
                response
            )
        else:
            record_test_result(
                "Website Retrieval",
                False,
                f"Failed to retrieve website: {response.status_code}",
                response
            )
    except Exception as e:
        record_test_result(
            "Website Retrieval",
            False,
            f"Exception: {str(e)}"
        )
    
    # 7. Test Website Update
    try:
        update_data = {
            "business_name": "Updated Boutique Name",
            "business_description": "Updated description with new information",
            "colors": {
                "primary": "#3498DB",
                "secondary": "#2ECC71",
                "accent": "#E74C3C"
            }
        }
        
        response = requests.put(
            f"{API_URL}/websites/{website_id}",
            json=update_data,
            headers=auth_headers
        )
        
        if response.status_code == 200:
            data = response.json()
            updated_name = data.get("business_name")
            record_test_result(
                "Website Update",
                True,
                f"Successfully updated website. New name: {updated_name}",
                response
            )
        else:
            record_test_result(
                "Website Update",
                False,
                f"Failed to update website: {response.status_code}",
                response
            )
    except Exception as e:
        record_test_result(
            "Website Update",
            False,
            f"Exception: {str(e)}"
        )
    
    # 8. Test Website Preview
    print("\n3. Testing Website Hosting")
    print("-"*80)
    
    try:
        response = requests.get(
            f"{API_URL}/websites/{website_id}/preview",
            headers=auth_headers
        )
        
        if response.status_code == 200 and "<!DOCTYPE html>" in response.text:
            record_test_result(
                "Website Preview",
                True,
                f"Successfully previewed website. HTML length: {len(response.text)} characters",
                response
            )
        else:
            record_test_result(
                "Website Preview",
                False,
                f"Failed to preview website: {response.status_code}",
                response
            )
    except Exception as e:
        record_test_result(
            "Website Preview",
            False,
            f"Exception: {str(e)}"
        )
    
    # 9. Test Public Website Hosting
    try:
        response = requests.get(
            f"{API_URL}/sites/{TEST_USER['email']}/{website_slug}"
        )
        
        if response.status_code == 200 and "<!DOCTYPE html>" in response.text:
            record_test_result(
                "Public Website Hosting",
                True,
                f"Successfully accessed public website. HTML length: {len(response.text)} characters",
                response
            )
        else:
            record_test_result(
                "Public Website Hosting",
                False,
                f"Failed to access public website: {response.status_code}",
                response
            )
    except Exception as e:
        record_test_result(
            "Public Website Hosting",
            False,
            f"Exception: {str(e)}"
        )
    
    # 10. Test Website Deletion
    try:
        response = requests.delete(
            f"{API_URL}/websites/{website_id}",
            headers=auth_headers
        )
        
        if response.status_code == 200:
            record_test_result(
                "Website Deletion",
                True,
                "Successfully deleted website",
                response
            )
        else:
            record_test_result(
                "Website Deletion",
                False,
                f"Failed to delete website: {response.status_code}",
                response
            )
    except Exception as e:
        record_test_result(
            "Website Deletion",
            False,
            f"Exception: {str(e)}"
        )
    
    # 11. Test Data Validation
    print("\n4. Testing Data Validation")
    print("-"*80)
    
    # Test invalid registration (missing required fields)
    try:
        response = requests.post(
            f"{API_URL}/auth/register",
            json={"email": f"invalid.{uuid.uuid4().hex[:8]}@example.com"}
        )
        
        if response.status_code >= 400:
            record_test_result(
                "Invalid Registration Validation",
                True,
                f"Correctly rejected invalid registration with status: {response.status_code}",
                response
            )
        else:
            record_test_result(
                "Invalid Registration Validation",
                False,
                "Failed to reject invalid registration",
                response
            )
    except Exception as e:
        record_test_result(
            "Invalid Registration Validation",
            False,
            f"Exception: {str(e)}"
        )
    
    # Test invalid website creation (missing required fields)
    try:
        response = requests.post(
            f"{API_URL}/websites",
            json={"business_name": "Incomplete Website"},
            headers=auth_headers
        )
        
        if response.status_code >= 400:
            record_test_result(
                "Invalid Website Creation Validation",
                True,
                f"Correctly rejected invalid website creation with status: {response.status_code}",
                response
            )
        else:
            record_test_result(
                "Invalid Website Creation Validation",
                False,
                "Failed to reject invalid website creation",
                response
            )
    except Exception as e:
        record_test_result(
            "Invalid Website Creation Validation",
            False,
            f"Exception: {str(e)}"
        )
    
    # Test non-existent website access
    try:
        fake_id = str(uuid.uuid4())
        response = requests.get(
            f"{API_URL}/websites/{fake_id}",
            headers=auth_headers
        )
        
        if response.status_code == 404:
            record_test_result(
                "Non-existent Website Access",
                True,
                "Correctly returned 404 for non-existent website",
                response
            )
        else:
            record_test_result(
                "Non-existent Website Access",
                False,
                f"Failed to return 404 for non-existent website: {response.status_code}",
                response
            )
    except Exception as e:
        record_test_result(
            "Non-existent Website Access",
            False,
            f"Exception: {str(e)}"
        )
    
    # Print test summary
    print_test_summary()

if __name__ == "__main__":
    run_tests()