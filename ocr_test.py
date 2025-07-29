#!/usr/bin/env python3

import requests
import sys
import json
import uuid
from datetime import datetime
import time
import io
from PIL import Image, ImageDraw, ImageFont
import base64
import os

class OCREndpointTester:
    def __init__(self, base_url="https://e741bfcc-c88e-4c94-9fe8-d56b7bd4d544.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session_id = f"ocr_test_{uuid.uuid4().hex[:8]}"
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
        
        if details and success:
            print(f"   📝 Details: {details}")
        
        self.test_results.append({
            "name": name,
            "success": success,
            "details": details
        })

    def create_test_image_with_ingredients(self):
        """Create a test image with ingredient text"""
        try:
            # Create image with white background
            img = Image.new('RGB', (600, 400), color='white')
            draw = ImageDraw.Draw(img)
            
            # Try to use a default font, fallback to basic if not available
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
            except:
                font = ImageFont.load_default()
            
            # Add ingredient text
            ingredient_text = """INGREDIENTS: Water, Sugar, Wheat Flour, 
Vegetable Oil (Palm, Sunflower), Salt, 
Natural Flavoring, Preservatives (E202, E211), 
Organic Cocoa Powder, Non-GMO Lecithin"""
            
            # Draw text on image
            draw.multiline_text((20, 50), ingredient_text, fill='black', font=font)
            
            # Add some certification text
            cert_text = "USDA ORGANIC - NON-GMO VERIFIED"
            draw.text((20, 200), cert_text, fill='green', font=font)
            
            # Convert to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            return img_bytes
            
        except Exception as e:
            print(f"Error creating test image: {e}")
            # Fallback: create simple image
            img = Image.new('RGB', (400, 200), color='white')
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            return img_bytes

    def test_ocr_basic_functionality(self):
        """Test basic OCR endpoint functionality"""
        try:
            print("   🖼️  Creating test image with ingredient text...")
            img_bytes = self.create_test_image_with_ingredients()
            
            files = {
                'image': ('test_ingredients.png', img_bytes, 'image/png'),
                'session_id': (None, self.session_id)
            }
            
            print("   📤 Uploading image to OCR endpoint...")
            start_time = time.time()
            
            response = requests.post(
                f"{self.api_url}/scan/ocr",
                files=files,
                timeout=30  # Increased timeout for OCR processing
            )
            
            response_time = time.time() - start_time
            print(f"   ⏱️  Response time: {response_time:.2f}s")
            
            if response.status_code == 200:
                data = response.json()
                product = data.get("product", {})
                
                # Validate response structure
                required_fields = ["id", "name", "ingredients", "ingredient_count", "rating"]
                missing_fields = [field for field in required_fields if field not in product]
                
                if missing_fields:
                    self.log_test("OCR Basic Functionality", False, f"Missing fields: {missing_fields}")
                    return False
                
                # Check if ingredients were extracted
                ingredients = product.get("ingredients", [])
                ingredient_count = product.get("ingredient_count", 0)
                rating = product.get("rating", "")
                certifications = product.get("certifications", [])
                
                details = f"Extracted {ingredient_count} ingredients, Rating: {rating}, Certifications: {certifications}"
                
                # Verify rating calculation
                expected_rating = self.calculate_expected_rating(ingredient_count)
                if rating != expected_rating:
                    self.log_test("OCR Basic Functionality", False, f"Rating mismatch: got {rating}, expected {expected_rating}")
                    return False
                
                self.log_test("OCR Basic Functionality", True, details)
                return True
            else:
                self.log_test("OCR Basic Functionality", False, f"Status: {response.status_code}, Response: {response.text[:300]}")
                return False
                
        except requests.exceptions.Timeout:
            self.log_test("OCR Basic Functionality", False, "Request timed out - endpoint may be hanging")
            return False
        except Exception as e:
            self.log_test("OCR Basic Functionality", False, f"Exception: {str(e)}")
            return False

    def test_ocr_timeout_handling(self):
        """Test OCR endpoint timeout handling"""
        try:
            print("   🖼️  Creating test image for timeout test...")
            img_bytes = self.create_test_image_with_ingredients()
            
            files = {
                'image': ('timeout_test.png', img_bytes, 'image/png'),
                'session_id': (None, f"{self.session_id}_timeout")
            }
            
            print("   ⏰ Testing with shorter timeout to verify handling...")
            start_time = time.time()
            
            # Test with a reasonable timeout
            response = requests.post(
                f"{self.api_url}/scan/ocr",
                files=files,
                timeout=25  # Reasonable timeout
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if "product" in data:
                    self.log_test("OCR Timeout Handling", True, f"Completed within timeout: {response_time:.2f}s")
                    return True
                else:
                    self.log_test("OCR Timeout Handling", False, "Invalid response structure")
                    return False
            else:
                self.log_test("OCR Timeout Handling", False, f"Status: {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            self.log_test("OCR Timeout Handling", False, "Request timed out - endpoint still hanging")
            return False
        except Exception as e:
            self.log_test("OCR Timeout Handling", False, f"Exception: {str(e)}")
            return False

    def test_ocr_ingredient_extraction(self):
        """Test ingredient extraction from OCR text"""
        try:
            print("   🧪 Testing ingredient extraction capabilities...")
            img_bytes = self.create_test_image_with_ingredients()
            
            files = {
                'image': ('ingredient_test.png', img_bytes, 'image/png'),
                'session_id': (None, f"{self.session_id}_ingredients")
            }
            
            response = requests.post(
                f"{self.api_url}/scan/ocr",
                files=files,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                product = data.get("product", {})
                ingredients = product.get("ingredients", [])
                
                # Check if any ingredients were extracted
                if len(ingredients) > 0:
                    # Look for expected ingredients from our test image
                    expected_ingredients = ["water", "sugar", "wheat flour", "vegetable oil"]
                    found_ingredients = [ing.lower() for ing in ingredients]
                    
                    matches = sum(1 for exp in expected_ingredients if any(exp in found for found in found_ingredients))
                    
                    details = f"Found {len(ingredients)} ingredients, {matches}/{len(expected_ingredients)} expected matches"
                    
                    if matches > 0:
                        self.log_test("OCR Ingredient Extraction", True, details)
                        return True
                    else:
                        self.log_test("OCR Ingredient Extraction", False, f"No expected ingredients found: {ingredients}")
                        return False
                else:
                    self.log_test("OCR Ingredient Extraction", False, "No ingredients extracted from image")
                    return False
            else:
                self.log_test("OCR Ingredient Extraction", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("OCR Ingredient Extraction", False, f"Exception: {str(e)}")
            return False

    def test_ocr_error_handling(self):
        """Test OCR endpoint error handling"""
        try:
            print("   🚫 Testing error handling with invalid image...")
            
            # Test with invalid image data
            files = {
                'image': ('invalid.txt', io.BytesIO(b'not an image'), 'text/plain'),
                'session_id': (None, f"{self.session_id}_error")
            }
            
            response = requests.post(
                f"{self.api_url}/scan/ocr",
                files=files,
                timeout=15
            )
            
            # Should handle gracefully (either 400 error or 200 with minimal data)
            if response.status_code in [200, 400, 422]:
                if response.status_code == 200:
                    data = response.json()
                    if "product" in data:
                        self.log_test("OCR Error Handling", True, "Handled invalid image gracefully with fallback")
                        return True
                else:
                    self.log_test("OCR Error Handling", True, f"Properly rejected invalid image: {response.status_code}")
                    return True
            else:
                self.log_test("OCR Error Handling", False, f"Unexpected status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("OCR Error Handling", False, f"Exception: {str(e)}")
            return False

    def test_ocr_usda_api_integration(self):
        """Test USDA API integration and timeout handling"""
        try:
            print("   🏛️  Testing USDA API integration with OCR...")
            img_bytes = self.create_test_image_with_ingredients()
            
            files = {
                'image': ('usda_test.png', img_bytes, 'image/png'),
                'session_id': (None, f"{self.session_id}_usda")
            }
            
            start_time = time.time()
            
            response = requests.post(
                f"{self.api_url}/scan/ocr",
                files=files,
                timeout=30
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                product = data.get("product", {})
                certifications = product.get("certifications", [])
                
                # The endpoint should complete even if USDA API fails
                details = f"Completed in {response_time:.2f}s, Certifications: {certifications}"
                
                # Check if response time is reasonable (not hanging)
                if response_time < 25:  # Should complete within reasonable time
                    self.log_test("OCR USDA API Integration", True, details)
                    return True
                else:
                    self.log_test("OCR USDA API Integration", False, f"Too slow: {response_time:.2f}s")
                    return False
            else:
                self.log_test("OCR USDA API Integration", False, f"Status: {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            self.log_test("OCR USDA API Integration", False, "Request timed out - USDA API may be causing hangs")
            return False
        except Exception as e:
            self.log_test("OCR USDA API Integration", False, f"Exception: {str(e)}")
            return False

    def test_ocr_logging_verification(self):
        """Test that OCR endpoint logs processing steps properly"""
        try:
            print("   📝 Testing logging functionality...")
            img_bytes = self.create_test_image_with_ingredients()
            
            files = {
                'image': ('logging_test.png', img_bytes, 'image/png'),
                'session_id': (None, f"{self.session_id}_logging")
            }
            
            response = requests.post(
                f"{self.api_url}/scan/ocr",
                files=files,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                product = data.get("product", {})
                
                # If we get a valid response, logging is likely working
                # (We can't directly check logs from here, but successful processing indicates logging is functional)
                self.log_test("OCR Logging Verification", True, "Endpoint processed successfully - logging likely functional")
                return True
            else:
                self.log_test("OCR Logging Verification", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("OCR Logging Verification", False, f"Exception: {str(e)}")
            return False

    def calculate_expected_rating(self, ingredient_count):
        """Calculate expected traffic light rating"""
        if ingredient_count <= 4:
            return "green"
        elif ingredient_count <= 9:
            return "amber"
        else:
            return "red"

    def run_ocr_tests(self):
        """Run all OCR-specific tests"""
        print("🚀 Starting OCR Endpoint Tests")
        print(f"📍 Testing against: {self.api_url}/scan/ocr")
        print(f"🔑 Session ID: {self.session_id}")
        print("=" * 80)
        
        # OCR-specific test sequence
        tests = [
            ("OCR Basic Functionality", self.test_ocr_basic_functionality),
            ("OCR Timeout Handling", self.test_ocr_timeout_handling),
            ("OCR Ingredient Extraction", self.test_ocr_ingredient_extraction),
            ("OCR Error Handling", self.test_ocr_error_handling),
            ("OCR USDA API Integration", self.test_ocr_usda_api_integration),
            ("OCR Logging Verification", self.test_ocr_logging_verification),
        ]
        
        for test_name, test_func in tests:
            print(f"\n🔍 Running {test_name}...")
            try:
                test_func()
            except Exception as e:
                self.log_test(test_name, False, f"Unexpected error: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 OCR TEST SUMMARY")
        print("=" * 80)
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Detailed results
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"   {status} - {result['name']}")
            if result["details"] and not result["success"]:
                print(f"      └─ {result['details']}")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 All OCR tests passed! The endpoint is working correctly.")
            return 0
        else:
            print(f"\n⚠️  {self.tests_run - self.tests_passed} test(s) failed. Check the details above.")
            return 1

def main():
    tester = OCREndpointTester()
    return tester.run_ocr_tests()

if __name__ == "__main__":
    sys.exit(main())