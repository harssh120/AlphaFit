from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import bcrypt
import jwt
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Fitness Tracker API", description="Comprehensive fitness and nutrition tracking system")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-here')
JWT_ALGORITHM = "HS256"

# Enums
class GoalType(str, Enum):
    WEIGHT_LOSS = "weight_loss"
    MUSCLE_GAIN = "muscle_gain"
    MAINTENANCE = "maintenance"
    ENDURANCE = "endurance"

class ActivityLevel(str, Enum):
    SEDENTARY = "sedentary"
    LIGHTLY_ACTIVE = "lightly_active"
    MODERATELY_ACTIVE = "moderately_active"
    VERY_ACTIVE = "very_active"
    EXTREMELY_ACTIVE = "extremely_active"

class ExerciseType(str, Enum):
    CARDIO = "cardio"
    STRENGTH = "strength"
    FLEXIBILITY = "flexibility"
    SPORTS = "sports"

# User Models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    age: int
    height: float  # in cm
    weight: float  # in kg
    goal_type: GoalType
    activity_level: ActivityLevel

class UserLogin(BaseModel):
    username: str
    password: str

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    full_name: str
    age: int
    height: float
    weight: float
    goal_type: GoalType
    activity_level: ActivityLevel
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class UserProfile(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    age: int
    height: float
    weight: float
    goal_type: GoalType
    activity_level: ActivityLevel
    bmi: float
    daily_calories: int

# Food and Nutrition Models
class FoodItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    calories_per_100g: float
    protein_per_100g: float
    carbs_per_100g: float
    fat_per_100g: float
    fiber_per_100g: Optional[float] = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

class FoodItemCreate(BaseModel):
    name: str
    calories_per_100g: float
    protein_per_100g: float
    carbs_per_100g: float
    fat_per_100g: float
    fiber_per_100g: Optional[float] = 0

class MealEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    food_item_id: str
    food_name: str
    quantity: float  # in grams
    calories: float
    protein: float
    carbs: float
    fat: float
    meal_type: str  # breakfast, lunch, dinner, snack
    logged_at: datetime = Field(default_factory=datetime.utcnow)

class MealEntryCreate(BaseModel):
    food_item_id: str
    quantity: float
    meal_type: str

# Workout Models
class Exercise(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: ExerciseType
    muscle_groups: List[str]
    description: str
    instructions: List[str]
    calories_per_minute: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ExerciseCreate(BaseModel):
    name: str
    type: ExerciseType
    muscle_groups: List[str]
    description: str
    instructions: List[str]
    calories_per_minute: float

class WorkoutEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    exercise_id: str
    exercise_name: str
    duration: int  # in minutes
    calories_burned: float
    sets: Optional[int] = None
    reps: Optional[int] = None
    weight: Optional[float] = None  # in kg
    notes: Optional[str] = None
    completed_at: datetime = Field(default_factory=datetime.utcnow)

class WorkoutEntryCreate(BaseModel):
    exercise_id: str
    duration: int
    sets: Optional[int] = None
    reps: Optional[int] = None
    weight: Optional[float] = None
    notes: Optional[str] = None

# Goal Models
class Goal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    goal_type: GoalType
    target_weight: Optional[float] = None
    target_date: Optional[datetime] = None
    current_progress: float = 0.0
    is_achieved: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class GoalCreate(BaseModel):
    goal_type: GoalType
    target_weight: Optional[float] = None
    target_date: Optional[datetime] = None

# Utility functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> str:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload["user_id"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token = credentials.credentials
    return verify_jwt_token(token)

def calculate_bmi(weight: float, height: float) -> float:
    return round(weight / ((height / 100) ** 2), 2)

def calculate_daily_calories(user: User) -> int:
    # Basic BMR calculation using Mifflin-St Jeor Equation
    if user.age and user.weight and user.height:
        # Assuming male for simplicity, can be enhanced later
        bmr = 10 * user.weight + 6.25 * user.height - 5 * user.age + 5
        
        activity_multiplier = {
            ActivityLevel.SEDENTARY: 1.2,
            ActivityLevel.LIGHTLY_ACTIVE: 1.375,
            ActivityLevel.MODERATELY_ACTIVE: 1.55,
            ActivityLevel.VERY_ACTIVE: 1.725,
            ActivityLevel.EXTREMELY_ACTIVE: 1.9
        }
        
        daily_calories = bmr * activity_multiplier.get(user.activity_level, 1.2)
        return int(daily_calories)
    return 2000  # default

# Authentication Routes
@api_router.post("/auth/register")
async def register_user(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"$or": [{"username": user_data.username}, {"email": user_data.email}]})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    # Hash password and create user
    hashed_password = hash_password(user_data.password)
    user_dict = user_data.dict()
    user_dict.pop('password')
    user_dict['password_hash'] = hashed_password
    
    user = User(**user_dict)
    # Insert user data with password_hash included
    user_data_with_hash = user.dict()
    user_data_with_hash['password_hash'] = hashed_password
    await db.users.insert_one(user_data_with_hash)
    
    # Create JWT token
    token = create_jwt_token(user.id)
    return {"token": token, "user": UserProfile(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        age=user.age,
        height=user.height,
        weight=user.weight,
        goal_type=user.goal_type,
        activity_level=user.activity_level,
        bmi=calculate_bmi(user.weight, user.height),
        daily_calories=calculate_daily_calories(user)
    )}

@api_router.post("/auth/login")
async def login_user(login_data: UserLogin):
    # Find user
    user_doc = await db.users.find_one({"username": login_data.username})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Verify password
    if not verify_password(login_data.password, user_doc['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create JWT token
    token = create_jwt_token(user_doc['id'])
    user = User(**user_doc)
    return {"token": token, "user": UserProfile(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        age=user.age,
        height=user.height,
        weight=user.weight,
        goal_type=user.goal_type,
        activity_level=user.activity_level,
        bmi=calculate_bmi(user.weight, user.height),
        daily_calories=calculate_daily_calories(user)
    )}

@api_router.get("/auth/profile")
async def get_user_profile(current_user_id: str = Depends(get_current_user)):
    user_doc = await db.users.find_one({"id": current_user_id})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = User(**user_doc)
    return UserProfile(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        age=user.age,
        height=user.height,
        weight=user.weight,
        goal_type=user.goal_type,
        activity_level=user.activity_level,
        bmi=calculate_bmi(user.weight, user.height),
        daily_calories=calculate_daily_calories(user)
    )

# Food Management Routes (Harsh Kumar's Database Expertise)
@api_router.post("/food/items", response_model=FoodItem)
async def create_food_item(food_data: FoodItemCreate, current_user_id: str = Depends(get_current_user)):
    food_item = FoodItem(**food_data.dict())
    await db.food_items.insert_one(food_item.dict())
    return food_item

@api_router.get("/food/items", response_model=List[FoodItem])
async def get_food_items(current_user_id: str = Depends(get_current_user)):
    food_items = await db.food_items.find().to_list(1000)
    return [FoodItem(**item) for item in food_items]

@api_router.post("/food/log", response_model=MealEntry)
async def log_meal(meal_data: MealEntryCreate, current_user_id: str = Depends(get_current_user)):
    # Get food item details
    food_item = await db.food_items.find_one({"id": meal_data.food_item_id})
    if not food_item:
        raise HTTPException(status_code=404, detail="Food item not found")
    
    # Calculate nutrition values based on quantity
    quantity_ratio = meal_data.quantity / 100  # food items are per 100g
    calories = food_item['calories_per_100g'] * quantity_ratio
    protein = food_item['protein_per_100g'] * quantity_ratio
    carbs = food_item['carbs_per_100g'] * quantity_ratio
    fat = food_item['fat_per_100g'] * quantity_ratio
    
    meal_entry = MealEntry(
        user_id=current_user_id,
        food_item_id=meal_data.food_item_id,
        food_name=food_item['name'],
        quantity=meal_data.quantity,
        calories=round(calories, 2),
        protein=round(protein, 2),
        carbs=round(carbs, 2),
        fat=round(fat, 2),
        meal_type=meal_data.meal_type
    )
    
    await db.meal_entries.insert_one(meal_entry.dict())
    return meal_entry

@api_router.get("/food/log", response_model=List[MealEntry])
async def get_meal_log(date: Optional[str] = None, current_user_id: str = Depends(get_current_user)):
    # If date provided, filter by date, otherwise return today's meals
    if date:
        start_date = datetime.fromisoformat(date)
    else:
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    end_date = start_date + timedelta(days=1)
    
    meal_entries = await db.meal_entries.find({
        "user_id": current_user_id,
        "logged_at": {"$gte": start_date, "$lt": end_date}
    }).to_list(1000)
    
    return [MealEntry(**entry) for entry in meal_entries]

@api_router.get("/food/log/summary")
async def get_daily_nutrition_summary(date: Optional[str] = None, current_user_id: str = Depends(get_current_user)):
    if date:
        start_date = datetime.fromisoformat(date)
    else:
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    end_date = start_date + timedelta(days=1)
    
    # Aggregate nutrition data for the day
    pipeline = [
        {
            "$match": {
                "user_id": current_user_id,
                "logged_at": {"$gte": start_date, "$lt": end_date}
            }
        },
        {
            "$group": {
                "_id": None,
                "total_calories": {"$sum": "$calories"},
                "total_protein": {"$sum": "$protein"},
                "total_carbs": {"$sum": "$carbs"},
                "total_fat": {"$sum": "$fat"},
                "meal_count": {"$sum": 1}
            }
        }
    ]
    
    result = await db.meal_entries.aggregate(pipeline).to_list(1)
    if result:
        summary = result[0]
        summary.pop('_id')
        return summary
    else:
        return {
            "total_calories": 0,
            "total_protein": 0,
            "total_carbs": 0,
            "total_fat": 0,
            "meal_count": 0
        }

# Exercise Management Routes
@api_router.post("/exercises", response_model=Exercise)
async def create_exercise(exercise_data: ExerciseCreate, current_user_id: str = Depends(get_current_user)):
    exercise = Exercise(**exercise_data.dict())
    await db.exercises.insert_one(exercise.dict())
    return exercise

@api_router.get("/exercises", response_model=List[Exercise])
async def get_exercises(exercise_type: Optional[ExerciseType] = None, current_user_id: str = Depends(get_current_user)):
    query = {}
    if exercise_type:
        query["type"] = exercise_type
    
    exercises = await db.exercises.find(query).to_list(1000)
    return [Exercise(**exercise) for exercise in exercises]

@api_router.post("/workouts/log", response_model=WorkoutEntry)
async def log_workout(workout_data: WorkoutEntryCreate, current_user_id: str = Depends(get_current_user)):
    # Get exercise details
    exercise = await db.exercises.find_one({"id": workout_data.exercise_id})
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    
    # Calculate calories burned
    calories_burned = exercise['calories_per_minute'] * workout_data.duration
    
    workout_entry = WorkoutEntry(
        user_id=current_user_id,
        exercise_id=workout_data.exercise_id,
        exercise_name=exercise['name'],
        duration=workout_data.duration,
        calories_burned=round(calories_burned, 2),
        sets=workout_data.sets,
        reps=workout_data.reps,
        weight=workout_data.weight,
        notes=workout_data.notes
    )
    
    await db.workout_entries.insert_one(workout_entry.dict())
    return workout_entry

@api_router.get("/workouts/log", response_model=List[WorkoutEntry])
async def get_workout_log(date: Optional[str] = None, current_user_id: str = Depends(get_current_user)):
    if date:
        start_date = datetime.fromisoformat(date)
    else:
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    end_date = start_date + timedelta(days=1)
    
    workout_entries = await db.workout_entries.find({
        "user_id": current_user_id,
        "completed_at": {"$gte": start_date, "$lt": end_date}
    }).to_list(1000)
    
    return [WorkoutEntry(**entry) for entry in workout_entries]

# Goal Management Routes (Harsh Kumar's Database Expertise)
@api_router.post("/goals", response_model=Goal)
async def create_goal(goal_data: GoalCreate, current_user_id: str = Depends(get_current_user)):
    goal = Goal(user_id=current_user_id, **goal_data.dict())
    await db.goals.insert_one(goal.dict())
    return goal

@api_router.get("/goals", response_model=List[Goal])
async def get_user_goals(current_user_id: str = Depends(get_current_user)):
    goals = await db.goals.find({"user_id": current_user_id}).to_list(1000)
    return [Goal(**goal) for goal in goals]

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user_id: str = Depends(get_current_user)):
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    
    # Get today's nutrition
    nutrition_summary = await get_daily_nutrition_summary(current_user_id=current_user_id)
    
    # Get today's workouts
    workout_entries = await db.workout_entries.find({
        "user_id": current_user_id,
        "completed_at": {"$gte": today, "$lt": tomorrow}
    }).to_list(1000)
    
    total_workout_calories = sum(entry['calories_burned'] for entry in workout_entries)
    workout_time = sum(entry['duration'] for entry in workout_entries)
    
    # Get active goals
    active_goals = await db.goals.find({
        "user_id": current_user_id,
        "is_achieved": False
    }).to_list(1000)
    
    return {
        "nutrition": nutrition_summary,
        "workouts": {
            "total_calories_burned": round(total_workout_calories, 2),
            "total_workout_time": workout_time,
            "workout_count": len(workout_entries)
        },
        "active_goals_count": len(active_goals)
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

# Seed data on startup
@app.on_event("startup")
async def create_seed_data():
    # Check if food items exist, if not create some sample data
    existing_foods = await db.food_items.count_documents({})
    if existing_foods == 0:
        sample_foods = [
            FoodItem(name="Chicken Breast", calories_per_100g=165, protein_per_100g=31, carbs_per_100g=0, fat_per_100g=3.6),
            FoodItem(name="Brown Rice", calories_per_100g=111, protein_per_100g=2.6, carbs_per_100g=23, fat_per_100g=0.9),
            FoodItem(name="Banana", calories_per_100g=89, protein_per_100g=1.1, carbs_per_100g=23, fat_per_100g=0.3),
            FoodItem(name="Oatmeal", calories_per_100g=68, protein_per_100g=2.4, carbs_per_100g=12, fat_per_100g=1.4),
            FoodItem(name="Salmon", calories_per_100g=208, protein_per_100g=20, carbs_per_100g=0, fat_per_100g=12),
            FoodItem(name="Sweet Potato", calories_per_100g=86, protein_per_100g=1.6, carbs_per_100g=20, fat_per_100g=0.1),
            FoodItem(name="Greek Yogurt", calories_per_100g=59, protein_per_100g=10, carbs_per_100g=3.6, fat_per_100g=0.4),
            FoodItem(name="Almonds", calories_per_100g=579, protein_per_100g=21, carbs_per_100g=22, fat_per_100g=50),
        ]
        
        for food in sample_foods:
            await db.food_items.insert_one(food.dict())
    
    # Check if exercises exist, if not create some sample data
    existing_exercises = await db.exercises.count_documents({})
    if existing_exercises == 0:
        sample_exercises = [
            Exercise(name="Push-ups", type=ExerciseType.STRENGTH, muscle_groups=["chest", "triceps", "shoulders"], 
                    description="Classic bodyweight exercise", instructions=["Start in plank position", "Lower body to ground", "Push back up"], calories_per_minute=8.0),
            Exercise(name="Running", type=ExerciseType.CARDIO, muscle_groups=["legs", "glutes", "core"], 
                    description="Cardiovascular running exercise", instructions=["Maintain steady pace", "Keep proper form", "Breathe rhythmically"], calories_per_minute=12.0),
            Exercise(name="Squats", type=ExerciseType.STRENGTH, muscle_groups=["legs", "glutes", "core"], 
                    description="Lower body strength exercise", instructions=["Stand with feet shoulder-width apart", "Lower hips back and down", "Return to standing"], calories_per_minute=6.0),
            Exercise(name="Plank", type=ExerciseType.STRENGTH, muscle_groups=["core", "shoulders"], 
                    description="Core strengthening exercise", instructions=["Hold plank position", "Keep body straight", "Engage core muscles"], calories_per_minute=4.0),
            Exercise(name="Cycling", type=ExerciseType.CARDIO, muscle_groups=["legs", "glutes"], 
                    description="Low-impact cardio exercise", instructions=["Maintain steady cadence", "Keep proper posture", "Adjust resistance as needed"], calories_per_minute=10.0),
        ]
        
        for exercise in sample_exercises:
            await db.exercises.insert_one(exercise.dict())