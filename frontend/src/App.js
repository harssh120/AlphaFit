import React, { useState, useEffect } from 'react';
import './App.css';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Set up axios defaults
axios.defaults.headers.common['Content-Type'] = 'application/json';

// Auth Context
const AuthContext = React.createContext();

const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUserProfile();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchUserProfile = async () => {
    try {
      const response = await axios.get(`${API}/auth/profile`);
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user profile:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { username, password });
      const { token: newToken, user: userData } = response.data;
      
      localStorage.setItem('token', newToken);
      setToken(newToken);
      setUser(userData);
      axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
      
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Login failed' };
    }
  };

  const register = async (userData) => {
    try {
      const response = await axios.post(`${API}/auth/register`, userData);
      const { token: newToken, user: userProfile } = response.data;
      
      localStorage.setItem('token', newToken);
      setToken(newToken);
      setUser(userProfile);
      axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
      
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Registration failed' };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    delete axios.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

// Components
const LoginForm = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    email: '',
    full_name: '',
    age: '',
    height: '',
    weight: '',
    goal_type: 'maintenance',
    activity_level: 'moderately_active'
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    let result;
    if (isLogin) {
      result = await login(formData.username, formData.password);
    } else {
      const registerData = {
        ...formData,
        age: parseInt(formData.age),
        height: parseFloat(formData.height),
        weight: parseFloat(formData.weight)
      };
      result = await register(registerData);
    }

    if (!result.success) {
      setError(result.error);
    }
    setLoading(false);
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-cyan-900 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">FitTracker Pro</h1>
          <p className="text-gray-600">Your comprehensive fitness companion</p>
        </div>

        <div className="flex mb-6">
          <button
            type="button"
            onClick={() => setIsLogin(true)}
            className={`flex-1 py-2 text-center rounded-l-lg font-medium transition-colors ${
              isLogin ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'
            }`}
          >
            Login
          </button>
          <button
            type="button"
            onClick={() => setIsLogin(false)}
            className={`flex-1 py-2 text-center rounded-r-lg font-medium transition-colors ${
              !isLogin ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'
            }`}
          >
            Register
          </button>
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
            <input
              type="text"
              name="username"
              value={formData.username}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {!isLogin && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                <input
                  type="text"
                  name="full_name"
                  value={formData.full_name}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Age</label>
                  <input
                    type="number"
                    name="age"
                    value={formData.age}
                    onChange={handleChange}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Height (cm)</label>
                  <input
                    type="number"
                    name="height"
                    value={formData.height}
                    onChange={handleChange}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Weight (kg)</label>
                  <input
                    type="number"
                    name="weight"
                    value={formData.weight}
                    onChange={handleChange}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Fitness Goal</label>
                <select
                  name="goal_type"
                  value={formData.goal_type}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="weight_loss">Weight Loss</option>
                  <option value="muscle_gain">Muscle Gain</option>
                  <option value="maintenance">Maintenance</option>
                  <option value="endurance">Endurance</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Activity Level</label>
                <select
                  name="activity_level"
                  value={formData.activity_level}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="sedentary">Sedentary</option>
                  <option value="lightly_active">Lightly Active</option>
                  <option value="moderately_active">Moderately Active</option>
                  <option value="very_active">Very Active</option>
                  <option value="extremely_active">Extremely Active</option>
                </select>
              </div>
            </>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            {loading ? 'Processing...' : (isLogin ? 'Login' : 'Register')}
          </button>
        </form>
      </div>
    </div>
  );
};

const Dashboard = () => {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [dashboardStats, setDashboardStats] = useState(null);
  const [foodItems, setFoodItems] = useState([]);
  const [exercises, setExercises] = useState([]);
  const [mealLog, setMealLog] = useState([]);
  const [workoutLog, setWorkoutLog] = useState([]);

  useEffect(() => {
    fetchDashboardStats();
    fetchFoodItems();
    fetchExercises();
    fetchMealLog();
    fetchWorkoutLog();
  }, []);

  const fetchDashboardStats = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/stats`);
      setDashboardStats(response.data);
    } catch (error) {
      console.error('Failed to fetch dashboard stats:', error);
    }
  };

  const fetchFoodItems = async () => {
    try {
      const response = await axios.get(`${API}/food/items`);
      setFoodItems(response.data);
    } catch (error) {
      console.error('Failed to fetch food items:', error);
    }
  };

  const fetchExercises = async () => {
    try {
      const response = await axios.get(`${API}/exercises`);
      setExercises(response.data);
    } catch (error) {
      console.error('Failed to fetch exercises:', error);
    }
  };

  const fetchMealLog = async () => {
    try {
      const response = await axios.get(`${API}/food/log`);
      setMealLog(response.data);
    } catch (error) {
      console.error('Failed to fetch meal log:', error);
    }
  };

  const fetchWorkoutLog = async () => {
    try {
      const response = await axios.get(`${API}/workouts/log`);
      setWorkoutLog(response.data);
    } catch (error) {
      console.error('Failed to fetch workout log:', error);
    }
  };

  const logMeal = async (foodItemId, quantity, mealType) => {
    try {
      const response = await axios.post(`${API}/food/log`, {
        food_item_id: foodItemId,
        quantity: parseFloat(quantity),
        meal_type: mealType
      });
      console.log('Meal logged successfully:', response.data);
      // Refresh data after successful logging
      await Promise.all([fetchMealLog(), fetchDashboardStats()]);
      return { success: true };
    } catch (error) {
      console.error('Failed to log meal:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to log meal' };
    }
  };

  const logWorkout = async (exerciseId, duration, sets, reps, weight, notes) => {
    try {
      const response = await axios.post(`${API}/workouts/log`, {
        exercise_id: exerciseId,
        duration: parseInt(duration),
        sets: sets ? parseInt(sets) : null,
        reps: reps ? parseInt(reps) : null,
        weight: weight ? parseFloat(weight) : null,
        notes: notes || null
      });
      console.log('Workout logged successfully:', response.data);
      // Refresh data after successful logging
      await Promise.all([fetchWorkoutLog(), fetchDashboardStats()]);
      return { success: true };
    } catch (error) {
      console.error('Failed to log workout:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to log workout' };
    }
  };

  const DashboardView = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">Welcome back, {user?.full_name}!</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-blue-50 p-4 rounded-lg">
            <h3 className="font-semibold text-blue-800">BMI</h3>
            <p className="text-2xl font-bold text-blue-600">{user?.bmi}</p>
          </div>
          <div className="bg-green-50 p-4 rounded-lg">
            <h3 className="font-semibold text-green-800">Daily Calories Target</h3>
            <p className="text-2xl font-bold text-green-600">{user?.daily_calories}</p>
          </div>
          <div className="bg-purple-50 p-4 rounded-lg">
            <h3 className="font-semibold text-purple-800">Goal</h3>
            <p className="text-lg font-bold text-purple-600 capitalize">{user?.goal_type?.replace('_', ' ')}</p>
          </div>
        </div>
      </div>

      {dashboardStats && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-bold text-gray-800 mb-4">Today's Nutrition</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span>Calories:</span>
                <span className="font-semibold">{dashboardStats.nutrition.total_calories || 0}</span>
              </div>
              <div className="flex justify-between">
                <span>Protein:</span>
                <span className="font-semibold">{dashboardStats.nutrition.total_protein || 0}g</span>
              </div>
              <div className="flex justify-between">
                <span>Carbs:</span>
                <span className="font-semibold">{dashboardStats.nutrition.total_carbs || 0}g</span>
              </div>
              <div className="flex justify-between">
                <span>Fat:</span>
                <span className="font-semibold">{dashboardStats.nutrition.total_fat || 0}g</span>
              </div>
              <div className="flex justify-between">
                <span>Meals Logged:</span>
                <span className="font-semibold">{dashboardStats.nutrition.meal_count || 0}</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-bold text-gray-800 mb-4">Today's Workouts</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span>Calories Burned:</span>
                <span className="font-semibold">{dashboardStats.workouts.total_calories_burned || 0}</span>
              </div>
              <div className="flex justify-between">
                <span>Workout Time:</span>
                <span className="font-semibold">{dashboardStats.workouts.total_workout_time || 0} min</span>
              </div>
              <div className="flex justify-between">
                <span>Workouts:</span>
                <span className="font-semibold">{dashboardStats.workouts.workout_count || 0}</span>
              </div>
              <div className="flex justify-between">
                <span>Active Goals:</span>
                <span className="font-semibold">{dashboardStats.active_goals_count || 0}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const NutritionView = () => {
    const [selectedFood, setSelectedFood] = useState('');
    const [quantity, setQuantity] = useState('');
    const [mealType, setMealType] = useState('breakfast');
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState({ type: '', text: '' });

    const handleLogMeal = async (e) => {
      e.preventDefault();
      if (selectedFood && quantity) {
        setLoading(true);
        setMessage({ type: '', text: '' });
        
        const result = await logMeal(selectedFood, quantity, mealType);
        
        if (result.success) {
          setMessage({ type: 'success', text: 'Meal logged successfully!' });
          setSelectedFood('');
          setQuantity('');
        } else {
          setMessage({ type: 'error', text: result.error || 'Failed to log meal' });
        }
        setLoading(false);
        
        // Clear message after 3 seconds
        setTimeout(() => setMessage({ type: '', text: '' }), 3000);
      }
    };

    return (
      <div className="space-y-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">Log Your Meal</h2>
          <form onSubmit={handleLogMeal} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Food Item</label>
                <select
                  value={selectedFood}
                  onChange={(e) => setSelectedFood(e.target.value)}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select food</option>
                  {foodItems.map(food => (
                    <option key={food.id} value={food.id}>{food.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Quantity (g)</label>
                <input
                  type="number"
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Meal Type</label>
                <select
                  value={mealType}
                  onChange={(e) => setMealType(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="breakfast">Breakfast</option>
                  <option value="lunch">Lunch</option>
                  <option value="dinner">Dinner</option>
                  <option value="snack">Snack</option>
                </select>
              </div>
              <div className="flex items-end">
                <button
                  type="submit"
                  className="w-full bg-green-600 text-white py-2 rounded-lg font-medium hover:bg-green-700 transition-colors"
                >
                  Log Meal
                </button>
              </div>
            </div>
          </form>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-xl font-bold text-gray-800 mb-4">Today's Meals</h3>
          <div className="space-y-3">
            {mealLog.length === 0 ? (
              <p className="text-gray-500">No meals logged today</p>
            ) : (
              mealLog.map(meal => (
                <div key={meal.id} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <div>
                    <span className="font-medium">{meal.food_name}</span>
                    <span className="text-sm text-gray-600 ml-2">({meal.quantity}g)</span>
                    <span className="text-xs text-gray-500 ml-2 capitalize">{meal.meal_type}</span>
                  </div>
                  <div className="text-right">
                    <div className="font-medium">{meal.calories} cal</div>
                    <div className="text-sm text-gray-600">P:{meal.protein}g C:{meal.carbs}g F:{meal.fat}g</div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    );
  };

  const WorkoutView = () => {
    const [selectedExercise, setSelectedExercise] = useState('');
    const [duration, setDuration] = useState('');
    const [sets, setSets] = useState('');
    const [reps, setReps] = useState('');
    const [weight, setWeight] = useState('');
    const [notes, setNotes] = useState('');

    const handleLogWorkout = async (e) => {
      e.preventDefault();
      if (selectedExercise && duration) {
        await logWorkout(selectedExercise, duration, sets, reps, weight, notes);
        setSelectedExercise('');
        setDuration('');
        setSets('');
        setReps('');
        setWeight('');
        setNotes('');
      }
    };

    return (
      <div className="space-y-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">Log Your Workout</h2>
          <form onSubmit={handleLogWorkout} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Exercise</label>
                <select
                  value={selectedExercise}
                  onChange={(e) => setSelectedExercise(e.target.value)}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select exercise</option>
                  {exercises.map(exercise => (
                    <option key={exercise.id} value={exercise.id}>{exercise.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Duration (minutes)</label>
                <input
                  type="number"
                  value={duration}
                  onChange={(e) => setDuration(e.target.value)}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Sets (optional)</label>
                <input
                  type="number"
                  value={sets}
                  onChange={(e) => setSets(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Reps (optional)</label>
                <input
                  type="number"
                  value={reps}
                  onChange={(e) => setReps(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Weight (kg, optional)</label>
                <input
                  type="number"
                  step="0.1"
                  value={weight}
                  onChange={(e) => setWeight(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes (optional)</label>
                <input
                  type="text"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            <button
              type="submit"
              className="bg-blue-600 text-white py-2 px-6 rounded-lg font-medium hover:bg-blue-700 transition-colors"
            >
              Log Workout
            </button>
          </form>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-xl font-bold text-gray-800 mb-4">Today's Workouts</h3>
          <div className="space-y-3">
            {workoutLog.length === 0 ? (
              <p className="text-gray-500">No workouts logged today</p>
            ) : (
              workoutLog.map(workout => (
                <div key={workout.id} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <div>
                    <span className="font-medium">{workout.exercise_name}</span>
                    <div className="text-sm text-gray-600">
                      {workout.duration} min
                      {workout.sets && ` • ${workout.sets} sets`}
                      {workout.reps && ` • ${workout.reps} reps`}
                      {workout.weight && ` • ${workout.weight}kg`}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-medium">{workout.calories_burned} cal</div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    );
  };

  const TabButton = ({ tab, label, isActive, onClick }) => (
    <button
      onClick={() => onClick(tab)}
      className={`px-6 py-3 rounded-lg font-medium transition-colors ${
        isActive
          ? 'bg-blue-600 text-white shadow-md'
          : 'bg-white text-gray-700 hover:bg-gray-50'
      }`}
    >
      {label}
    </button>
  );

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-blue-600">FitTracker Pro</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-gray-700">Hello, {user?.username}</span>
              <button
                onClick={logout}
                className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Navigation Tabs */}
        <div className="flex space-x-4 mb-8">
          <TabButton tab="dashboard" label="Dashboard" isActive={activeTab === 'dashboard'} onClick={setActiveTab} />
          <TabButton tab="nutrition" label="Nutrition" isActive={activeTab === 'nutrition'} onClick={setActiveTab} />
          <TabButton tab="workouts" label="Workouts" isActive={activeTab === 'workouts'} onClick={setActiveTab} />
        </div>

        {/* Content */}
        {activeTab === 'dashboard' && <DashboardView />}
        {activeTab === 'nutrition' && <NutritionView />}
        {activeTab === 'workouts' && <WorkoutView />}
      </div>
    </div>
  );
};

const AppContent = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return user ? <Dashboard /> : <LoginForm />;
};

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/" element={<AppContent />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

export default App;