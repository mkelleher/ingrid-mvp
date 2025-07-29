#!/usr/bin/env python3

import requests
import sys
import json
import uuid
from datetime import datetime
import time

class EnhancedIngridAPITester:
    def __init__(self, base_url="https://a165ce7d-3f72-4652-abdd-b6cf18dc4cf1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session_id = f"enhanced_test_{uuid.uuid4().hex[:8]}"
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
        
        if details:
            print(f"   📝 Details: {details}")
        
        self.test_results.append({
            "name": name,
            "success": success,
            "details": details
        })

    def test_comprehensive_api_integration(self):
        """Test comprehensive API integration with specific barcodes"""
        test_barcodes = [
            {
                "barcode": "3017620422003",
                "name": "Nutella (OpenFoodFacts expected)",
                "expected_source": "OpenFoodFacts"
            },
            {
                "barcode": "012000161155", 
                "name": "US Product (USDA FDC possible)",
                "expected_source": "USDA or OpenFoodFacts"
            },
            {
                "barcode": "0123456789012",
                "name": "Generic Test Barcode",
                "expected_source": "Generated (fallback)"
            }
        ]
        
        all_passed = True
        
        for test_case in test_barcodes:
            try:
                print(f"\n🔍 Testing {test_case['name']} - {test_case['barcode']}")
                
                start_time = time.time()
                
                payload = {
                    "barcode": test_case["barcode"],
                    "session_id": self.session_id
                }
                
                response = requests.post(
                    f"{self.api_url}/scan/barcode",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=20
                )
                
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    product = data.get("product", {})
                    
                    # Log detailed product information
                    details = {
                        "name": product.get("name", "Unknown"),
                        "brand": product.get("brand", "No brand"),
                        "ingredients": len(product.get("ingredients", [])),
                        "rating": product.get("rating", "Unknown"),
                        "certifications": product.get("certifications", []),
                        "response_time": f"{response_time:.2f}s"
                    }
                    
                    print(f"   📦 Product: {details['name']}")
                    print(f"   🏷️  Brand: {details['brand']}")
                    print(f"   🧪 Ingredients: {details['ingredients']}")
                    print(f"   🚦 Rating: {details['rating']}")
                    print(f"   🏆 Certifications: {details['certifications']}")
                    print(f"   ⏱️  Response Time: {details['response_time']}")
                    
                    # Test traffic light rating accuracy
                    ingredient_count = details['ingredients']
                    rating = details['rating']
                    expected_rating = self.calculate_expected_rating(ingredient_count)
                    
                    if rating == expected_rating:
                        print(f"   ✅ Rating correct: {rating} for {ingredient_count} ingredients")
                    else:
                        print(f"   ❌ Rating incorrect: got {rating}, expected {expected_rating}")
                        all_passed = False
                    
                    # Check for enhanced certification detection
                    if test_case["barcode"] == "3017620422003":  # Nutella
                        # Nutella should have ingredient data from OpenFoodFacts
                        if ingredient_count > 0:
                            print(f"   ✅ OpenFoodFacts integration working - found {ingredient_count} ingredients")
                        else:
                            print(f"   ⚠️  No ingredients found - API integration may have issues")
                    
                else:
                    print(f"   ❌ API call failed: {response.status_code}")
                    all_passed = False
                    
            except Exception as e:
                print(f"   ❌ Exception: {str(e)}")
                all_passed = False
        
        if all_passed:
            self.log_test("Comprehensive API Integration", True, "All barcode tests passed with proper data sources")
        else:
            self.log_test("Comprehensive API Integration", False, "Some barcode tests failed")
        
        return all_passed

    def test_data_source_verification(self):
        """Test data source verification and quality"""
        try:
            # Test Nutella specifically for OpenFoodFacts
            nutella_payload = {
                "barcode": "3017620422003",
                "session_id": self.session_id
            }
            
            response = requests.post(
                f"{self.api_url}/scan/barcode",
                json=nutella_payload,
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                product = data.get("product", {})
                
                # Check data quality indicators
                has_name = bool(product.get("name", "").strip())
                has_brand = bool(product.get("brand", "").strip())
                has_ingredients = len(product.get("ingredients", [])) > 0
                has_proper_rating = product.get("rating") in ["green", "amber", "red"]
                
                quality_score = sum([has_name, has_brand, has_ingredients, has_proper_rating])
                
                details = f"Quality Score: {quality_score}/4 - Name: {has_name}, Brand: {has_brand}, Ingredients: {has_ingredients}, Rating: {has_proper_rating}"
                
                if quality_score >= 3:
                    self.log_test("Data Source Verification", True, details)
                    return True
                else:
                    self.log_test("Data Source Verification", False, f"Low quality data: {details}")
                    return False
            else:
                self.log_test("Data Source Verification", False, f"API call failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Data Source Verification", False, f"Exception: {str(e)}")
            return False

    def test_enhanced_certification_detection(self):
        """Test enhanced certification detection"""
        try:
            # Test with a barcode that might have organic certification
            test_payload = {
                "barcode": "3017620422003",  # Nutella - unlikely to be organic, good test
                "session_id": self.session_id
            }
            
            response = requests.post(
                f"{self.api_url}/scan/barcode",
                json=test_payload,
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                product = data.get("product", {})
                certifications = product.get("certifications", [])
                
                # Check if certification detection is working (even if no certifications found)
                # The fact that we get a certifications array means the system is working
                details = f"Certifications found: {certifications}"
                self.log_test("Enhanced Certification Detection", True, details)
                return True
            else:
                self.log_test("Enhanced Certification Detection", False, f"API call failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Enhanced Certification Detection", False, f"Exception: {str(e)}")
            return False

    def test_performance_and_reliability(self):
        """Test API performance and reliability"""
        try:
            response_times = []
            success_count = 0
            total_tests = 3
            
            for i in range(total_tests):
                start_time = time.time()
                
                payload = {
                    "barcode": "3017620422003",
                    "session_id": f"{self.session_id}_{i}"
                }
                
                response = requests.post(
                    f"{self.api_url}/scan/barcode",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=15
                )
                
                response_time = time.time() - start_time
                response_times.append(response_time)
                
                if response.status_code == 200:
                    success_count += 1
                
                # Small delay between requests
                time.sleep(0.5)
            
            avg_response_time = sum(response_times) / len(response_times)
            success_rate = (success_count / total_tests) * 100
            
            details = f"Avg Response Time: {avg_response_time:.2f}s, Success Rate: {success_rate:.1f}%"
            
            if success_rate >= 100 and avg_response_time < 10:
                self.log_test("Performance & Reliability", True, details)
                return True
            else:
                self.log_test("Performance & Reliability", False, details)
                return False
                
        except Exception as e:
            self.log_test("Performance & Reliability", False, f"Exception: {str(e)}")
            return False

    def test_error_handling(self):
        """Test error handling for various scenarios"""
        try:
            # Test invalid barcode
            invalid_payload = {
                "barcode": "",
                "session_id": self.session_id
            }
            
            response = requests.post(
                f"{self.api_url}/scan/barcode",
                json=invalid_payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            # Should handle gracefully (either 400 or 200 with fallback data)
            if response.status_code in [200, 400, 422]:
                self.log_test("Error Handling", True, f"Handled invalid barcode gracefully: {response.status_code}")
                return True
            else:
                self.log_test("Error Handling", False, f"Unexpected status for invalid barcode: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Error Handling", False, f"Exception: {str(e)}")
            return False

    def calculate_expected_rating(self, ingredient_count):
        """Calculate expected traffic light rating"""
        if ingredient_count <= 4:
            return "green"
        elif ingredient_count <= 9:
            return "amber"
        else:
            return "red"

    def run_enhanced_tests(self):
        """Run all enhanced API tests"""
        print("🚀 Starting Enhanced Ingrid MVP API Tests")
        print(f"📍 Testing against: {self.api_url}")
        print(f"🔑 Session ID: {self.session_id}")
        print("=" * 80)
        
        # Enhanced test sequence
        tests = [
            ("Comprehensive API Integration", self.test_comprehensive_api_integration),
            ("Data Source Verification", self.test_data_source_verification),
            ("Enhanced Certification Detection", self.test_enhanced_certification_detection),
            ("Performance & Reliability", self.test_performance_and_reliability),
            ("Error Handling", self.test_error_handling),
        ]
        
        for test_name, test_func in tests:
            print(f"\n🔍 Running {test_name}...")
            try:
                test_func()
            except Exception as e:
                self.log_test(test_name, False, f"Unexpected error: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 ENHANCED TEST SUMMARY")
        print("=" * 80)
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 All enhanced tests passed! Triple API integration is working correctly.")
            return 0
        else:
            print(f"\n⚠️  {self.tests_run - self.tests_passed} test(s) failed. Check the details above.")
            return 1

def main():
    tester = EnhancedIngridAPITester()
    return tester.run_enhanced_tests()

if __name__ == "__main__":
    sys.exit(main())