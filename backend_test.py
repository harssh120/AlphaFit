import requests
import sys
import json
from datetime import datetime

class FitnessTrackerAPITester:
    def __init__(self, base_url="https://dev-requirements.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.food_items = []
        self.exercises = []

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_user_registration(self):
        """Test user registration with sample data"""
        timestamp = datetime.now().strftime("%H%M%S")
        test_user_data = {
            "username": f"testuser_{timestamp}",
            "email": f"test_{timestamp}@example.com",
            "password": "TestPass123!",
            "full_name": "Test User",
            "age": 25,
            "height": 175.0,
            "weight": 70.0,
            "goal_type": "maintenance",
            "activity_level": "moderately_active"
        }
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data=test_user_data
        )
        
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response['user']['id']
            self.username = test_user_data['username']  # Store for login test
            print(f"   ✅ Token received and stored")
            print(f"   ✅ User ID: {self.user_id}")
            print(f"   ✅ BMI calculated: {response['user']['bmi']}")
            print(f"   ✅ Daily calories: {response['user']['daily_calories']}")
            return True
        return False

    def test_user_login(self):
        """Test user login"""
        login_data = {
            "username": self.username,
            "password": "TestPass123!"
        }
        
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        if success and 'token' in response:
            self.token = response['token']
            print(f"   ✅ Login successful, token updated")
            return True
        return False

    def test_user_profile(self):
        """Test getting user profile"""
        success, response = self.run_test(
            "Get User Profile",
            "GET",
            "auth/profile",
            200
        )
        
        if success:
            print(f"   ✅ Profile retrieved successfully")
            print(f"   ✅ Username: {response.get('username')}")
            print(f"   ✅ BMI: {response.get('bmi')}")
            print(f"   ✅ Daily Calories: {response.get('daily_calories')}")
            return True
        return False

    def test_get_food_items(self):
        """Test getting food items (should have seeded data)"""
        success, response = self.run_test(
            "Get Food Items",
            "GET",
            "food/items",
            200
        )
        
        if success and isinstance(response, list):
            self.food_items = response
            print(f"   ✅ Found {len(self.food_items)} food items")
            for food in self.food_items[:3]:  # Show first 3
                print(f"   - {food['name']}: {food['calories_per_100g']} cal/100g")
            return True
        return False

    def test_log_meals(self):
        """Test logging multiple meals"""
        if not self.food_items:
            print("❌ No food items available for meal logging")
            return False
        
        # Log breakfast
        breakfast_data = {
            "food_item_id": self.food_items[0]['id'],  # First food item
            "quantity": 150.0,
            "meal_type": "breakfast"
        }
        
        success1, response1 = self.run_test(
            "Log Breakfast Meal",
            "POST",
            "food/log",
            200,
            data=breakfast_data
        )
        
        # Log lunch
        lunch_data = {
            "food_item_id": self.food_items[1]['id'] if len(self.food_items) > 1 else self.food_items[0]['id'],
            "quantity": 200.0,
            "meal_type": "lunch"
        }
        
        success2, response2 = self.run_test(
            "Log Lunch Meal",
            "POST",
            "food/log",
            200,
            data=lunch_data
        )
        
        if success1 and success2:
            print(f"   ✅ Breakfast logged: {response1.get('calories', 0)} calories")
            print(f"   ✅ Lunch logged: {response2.get('calories', 0)} calories")
            return True
        return False

    def test_get_meal_log(self):
        """Test getting today's meal log"""
        success, response = self.run_test(
            "Get Today's Meal Log",
            "GET",
            "food/log",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   ✅ Found {len(response)} meals logged today")
            total_calories = sum(meal.get('calories', 0) for meal in response)
            print(f"   ✅ Total calories from meals: {total_calories}")
            return True
        return False

    def test_nutrition_summary(self):
        """Test getting daily nutrition summary"""
        success, response = self.run_test(
            "Get Daily Nutrition Summary",
            "GET",
            "food/log/summary",
            200
        )
        
        if success:
            print(f"   ✅ Total calories: {response.get('total_calories', 0)}")
            print(f"   ✅ Total protein: {response.get('total_protein', 0)}g")
            print(f"   ✅ Total carbs: {response.get('total_carbs', 0)}g")
            print(f"   ✅ Total fat: {response.get('total_fat', 0)}g")
            print(f"   ✅ Meal count: {response.get('meal_count', 0)}")
            return True
        return False

    def test_get_exercises(self):
        """Test getting exercises (should have seeded data)"""
        success, response = self.run_test(
            "Get Exercises",
            "GET",
            "exercises",
            200
        )
        
        if success and isinstance(response, list):
            self.exercises = response
            print(f"   ✅ Found {len(self.exercises)} exercises")
            for exercise in self.exercises[:3]:  # Show first 3
                print(f"   - {exercise['name']}: {exercise['calories_per_minute']} cal/min")
            return True
        return False

    def test_log_workouts(self):
        """Test logging multiple workouts"""
        if not self.exercises:
            print("❌ No exercises available for workout logging")
            return False
        
        # Log first workout
        workout1_data = {
            "exercise_id": self.exercises[0]['id'],
            "duration": 30,
            "sets": 3,
            "reps": 15,
            "notes": "Morning workout session"
        }
        
        success1, response1 = self.run_test(
            "Log First Workout",
            "POST",
            "workouts/log",
            200,
            data=workout1_data
        )
        
        # Log second workout
        workout2_data = {
            "exercise_id": self.exercises[1]['id'] if len(self.exercises) > 1 else self.exercises[0]['id'],
            "duration": 45,
            "weight": 50.0,
            "notes": "Evening cardio session"
        }
        
        success2, response2 = self.run_test(
            "Log Second Workout",
            "POST",
            "workouts/log",
            200,
            data=workout2_data
        )
        
        if success1 and success2:
            print(f"   ✅ First workout logged: {response1.get('calories_burned', 0)} calories burned")
            print(f"   ✅ Second workout logged: {response2.get('calories_burned', 0)} calories burned")
            return True
        return False

    def test_get_workout_log(self):
        """Test getting today's workout log"""
        success, response = self.run_test(
            "Get Today's Workout Log",
            "GET",
            "workouts/log",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   ✅ Found {len(response)} workouts logged today")
            total_calories_burned = sum(workout.get('calories_burned', 0) for workout in response)
            print(f"   ✅ Total calories burned: {total_calories_burned}")
            return True
        return False

    def test_dashboard_stats(self):
        """Test getting dashboard statistics"""
        success, response = self.run_test(
            "Get Dashboard Stats",
            "GET",
            "dashboard/stats",
            200
        )
        
        if success:
            nutrition = response.get('nutrition', {})
            workouts = response.get('workouts', {})
            
            print(f"   ✅ Nutrition stats:")
            print(f"      - Total calories: {nutrition.get('total_calories', 0)}")
            print(f"      - Meal count: {nutrition.get('meal_count', 0)}")
            
            print(f"   ✅ Workout stats:")
            print(f"      - Calories burned: {workouts.get('total_calories_burned', 0)}")
            print(f"      - Workout time: {workouts.get('total_workout_time', 0)} min")
            print(f"      - Workout count: {workouts.get('workout_count', 0)}")
            
            print(f"   ✅ Active goals: {response.get('active_goals_count', 0)}")
            return True
        return False

    def run_all_tests(self):
        """Run all API tests in sequence"""
        print("🚀 Starting FitTracker Pro API Tests")
        print(f"🌐 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Authentication Tests
        print("\n📋 AUTHENTICATION TESTS")
        if not self.test_user_registration():
            print("❌ Registration failed, stopping tests")
            return False
        
        if not self.test_user_login():
            print("❌ Login failed, stopping tests")
            return False
            
        if not self.test_user_profile():
            print("❌ Profile retrieval failed")
            return False
        
        # Food Management Tests
        print("\n🍎 FOOD MANAGEMENT TESTS")
        if not self.test_get_food_items():
            print("❌ Food items retrieval failed")
            return False
            
        if not self.test_log_meals():
            print("❌ Meal logging failed")
            return False
            
        if not self.test_get_meal_log():
            print("❌ Meal log retrieval failed")
            return False
            
        if not self.test_nutrition_summary():
            print("❌ Nutrition summary failed")
            return False
        
        # Exercise Management Tests
        print("\n💪 EXERCISE MANAGEMENT TESTS")
        if not self.test_get_exercises():
            print("❌ Exercise retrieval failed")
            return False
            
        if not self.test_log_workouts():
            print("❌ Workout logging failed")
            return False
            
        if not self.test_get_workout_log():
            print("❌ Workout log retrieval failed")
            return False
        
        # Dashboard Tests
        print("\n📊 DASHBOARD TESTS")
        if not self.test_dashboard_stats():
            print("❌ Dashboard stats failed")
            return False
        
        # Print final results
        print("\n" + "=" * 60)
        print(f"📊 FINAL RESULTS: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED! Backend API is working correctly.")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed. Check the issues above.")
            return False

def main():
    tester = FitnessTrackerAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())