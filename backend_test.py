#!/usr/bin/env python3

import requests
import sys
import json
import uuid
from datetime import datetime
import io
from PIL import Image
import base64

class IngridAPITester:
    def __init__(self, base_url="https://a165ce7d-3f72-4652-abdd-b6cf18dc4cf1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session_id = f"test_session_{uuid.uuid4().hex[:8]}"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "name": name,
            "success": success,
            "details": details
        })

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            success = response.status_code == 200
            data = response.json() if success else {}
            
            if success and "message" in data:
                self.log_test("Root Endpoint", True, f"Message: {data['message']}")
            else:
                self.log_test("Root Endpoint", False, f"Status: {response.status_code}, Response: {response.text[:200]}")
            
            return success
        except Exception as e:
            self.log_test("Root Endpoint", False, f"Exception: {str(e)}")
            return False

    def test_barcode_scan(self, barcode="3017620422003"):
        """Test barcode scanning endpoint"""
        try:
            payload = {
                "barcode": barcode,
                "session_id": self.session_id
            }
            
            response = requests.post(
                f"{self.api_url}/scan/barcode",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            
            success = response.status_code == 200
            
            if success:
                data = response.json()
                product = data.get("product", {})
                
                # Validate response structure
                required_fields = ["id", "name", "ingredients", "ingredient_count", "rating"]
                missing_fields = [field for field in required_fields if field not in product]
                
                if missing_fields:
                    self.log_test("Barcode Scan", False, f"Missing fields: {missing_fields}")
                    return False
                
                # Test traffic light rating logic
                ingredient_count = product["ingredient_count"]
                rating = product["rating"]
                expected_rating = self.calculate_expected_rating(ingredient_count)
                
                if rating != expected_rating:
                    self.log_test("Barcode Scan", False, f"Rating mismatch: got {rating}, expected {expected_rating} for {ingredient_count} ingredients")
                    return False
                
                details = f"Product: {product['name']}, Ingredients: {ingredient_count}, Rating: {rating}"
                self.log_test("Barcode Scan", True, details)
                
                # Store product ID for bookmark testing
                self.test_product_id = product["id"]
                return True
            else:
                self.log_test("Barcode Scan", False, f"Status: {response.status_code}, Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log_test("Barcode Scan", False, f"Exception: {str(e)}")
            return False

    def test_bookmark_toggle(self):
        """Test bookmark toggle functionality"""
        if not hasattr(self, 'test_product_id'):
            self.log_test("Bookmark Toggle", False, "No product ID available from previous test")
            return False
        
        try:
            # Test adding bookmark
            response = requests.post(
                f"{self.api_url}/bookmarks/toggle",
                params={
                    "session_id": self.session_id,
                    "product_id": self.test_product_id
                },
                timeout=10
            )
            
            if response.status_code != 200:
                self.log_test("Bookmark Toggle", False, f"Add bookmark failed: {response.status_code}")
                return False
            
            data = response.json()
            if not data.get("bookmarked"):
                self.log_test("Bookmark Toggle", False, "Expected bookmarked=True after first toggle")
                return False
            
            # Test removing bookmark
            response = requests.post(
                f"{self.api_url}/bookmarks/toggle",
                params={
                    "session_id": self.session_id,
                    "product_id": self.test_product_id
                },
                timeout=10
            )
            
            if response.status_code != 200:
                self.log_test("Bookmark Toggle", False, f"Remove bookmark failed: {response.status_code}")
                return False
            
            data = response.json()
            if data.get("bookmarked"):
                self.log_test("Bookmark Toggle", False, "Expected bookmarked=False after second toggle")
                return False
            
            self.log_test("Bookmark Toggle", True, "Add and remove bookmark successful")
            return True
            
        except Exception as e:
            self.log_test("Bookmark Toggle", False, f"Exception: {str(e)}")
            return False

    def test_scan_history(self):
        """Test scan history retrieval"""
        try:
            response = requests.get(
                f"{self.api_url}/history/{self.session_id}",
                timeout=10
            )
            
            success = response.status_code == 200
            
            if success:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("Scan History", True, f"Retrieved {len(data)} history items")
                    return True
                else:
                    self.log_test("Scan History", False, "Response is not a list")
                    return False
            else:
                self.log_test("Scan History", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Scan History", False, f"Exception: {str(e)}")
            return False

    def test_bookmarks_list(self):
        """Test bookmarks list retrieval"""
        try:
            response = requests.get(
                f"{self.api_url}/bookmarks/{self.session_id}",
                timeout=10
            )
            
            success = response.status_code == 200
            
            if success:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("Bookmarks List", True, f"Retrieved {len(data)} bookmarked items")
                    return True
                else:
                    self.log_test("Bookmarks List", False, "Response is not a list")
                    return False
            else:
                self.log_test("Bookmarks List", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Bookmarks List", False, f"Exception: {str(e)}")
            return False

    def test_ocr_scan(self):
        """Test OCR scanning endpoint with a simple test image"""
        try:
            # Create a simple test image with text
            img = Image.new('RGB', (400, 200), color='white')
            
            # Save to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            files = {
                'image': ('test_image.png', img_bytes, 'image/png'),
                'session_id': (None, self.session_id)
            }
            
            response = requests.post(
                f"{self.api_url}/scan/ocr",
                files=files,
                timeout=20
            )
            
            success = response.status_code == 200
            
            if success:
                data = response.json()
                product = data.get("product", {})
                
                if "id" in product and "name" in product:
                    self.log_test("OCR Scan", True, f"OCR processed successfully: {product['name']}")
                    return True
                else:
                    self.log_test("OCR Scan", False, "Invalid product structure in response")
                    return False
            else:
                self.log_test("OCR Scan", False, f"Status: {response.status_code}, Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log_test("OCR Scan", False, f"Exception: {str(e)}")
            return False

    def calculate_expected_rating(self, ingredient_count):
        """Calculate expected traffic light rating"""
        if ingredient_count <= 4:
            return "green"
        elif ingredient_count <= 9:
            return "amber"
        else:
            return "red"

    def test_rating_logic(self):
        """Test traffic light rating logic with different ingredient counts"""
        test_cases = [
            (2, "green"),
            (4, "green"),
            (5, "amber"),
            (9, "amber"),
            (10, "red"),
            (15, "red")
        ]
        
        all_passed = True
        for count, expected in test_cases:
            actual = self.calculate_expected_rating(count)
            if actual != expected:
                self.log_test("Rating Logic", False, f"Count {count}: expected {expected}, got {actual}")
                all_passed = False
        
        if all_passed:
            self.log_test("Rating Logic", True, "All rating calculations correct")
        
        return all_passed

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Ingrid MVP API Tests")
        print(f"📍 Testing against: {self.api_url}")
        print(f"🔑 Session ID: {self.session_id}")
        print("=" * 60)
        
        # Test sequence
        tests = [
            ("Root Endpoint", self.test_root_endpoint),
            ("Rating Logic", self.test_rating_logic),
            ("Barcode Scan", self.test_barcode_scan),
            ("Bookmark Toggle", self.test_bookmark_toggle),
            ("Scan History", self.test_scan_history),
            ("Bookmarks List", self.test_bookmarks_list),
            ("OCR Scan", self.test_ocr_scan),
        ]
        
        for test_name, test_func in tests:
            print(f"\n🔍 Running {test_name}...")
            try:
                test_func()
            except Exception as e:
                self.log_test(test_name, False, f"Unexpected error: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 All tests passed! API is working correctly.")
            return 0
        else:
            print(f"\n⚠️  {self.tests_run - self.tests_passed} test(s) failed. Check the details above.")
            return 1

def main():
    tester = IngridAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())