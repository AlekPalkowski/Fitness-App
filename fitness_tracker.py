import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np

class FitnessTracker:
    def __init__(self, db_path="fitness_tracker.db"):
        """
        Initialize the FitnessTracker instance.

        Parameters:
        - db_path (str): Path to the SQLite database file.
        """
        try:
            self.db_path = db_path
            self.user_id = None
            self.create_tables()
        except sqlite3.Error as e:
            print(f'Error accessing the database: {e}')
            raise

    # Function to create tables if they don't exist
    def create_tables(self):
        """
        Create tables in the database if they don't exist.
        Tables include users, exercises, routines, calories, goals, and other_exercises.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    password TEXT,
                    age INTEGER NOT NULL,
                    gender TEXT NOT NULL,
                    weight REAL NOT NULL,
                    height REAL NOT NULL,
                    fitness_goal TEXT,
                    bmr REAL,
                    UNIQUE(username)
                )
            ''')
            # Exercises table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS exercises (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    name TEXT,
                    reps INTEGER,
                    weight REAL,
                    duration REAL,
                    distance REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            # Routines table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS routines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    routine_name TEXT,
                    exercise_name TEXT,
                    reps INTEGER,
                    weight REAL,
                    sets INTEGER,
                    duration REAL,
                    distance REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            # Calorie table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS calories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    calories_burned REAL,
                    calories_consumed REAL,
                    timestamp DATETIME,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            # Goals table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    daily_calorie_goal REAL,
                    exercise_name TEXT,
                    target_reps INTEGER,
                    target_weight REAL,
                    target_duration REAL,
                    target_distance REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')

            # Additional table for custom exercises
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS other_exercises (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    name TEXT UNIQUE NOT NULL,
                    light_intensity REAL NOT NULL,
                    moderate_intensity REAL NOT NULL,
                    intense_intensity REAL NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        except sqlite3.Error as e:
            print(f'Error creating the database table: {e}')
            raise

    # Function to get float input
    def get_float_input(self, prompt):
        """
        Get user input as a floating-point number.

        Parameters:
        - prompt (str): The prompt to display when requesting input.

        Returns:
        - float: The user-entered floating-point number.
        """
        while True:
            try:
                return float(input(prompt))
            except ValueError:
                print("Invalid input. Please enter a number.")
                
    # Function to log in
    def login(self):
        """
        Log in an existing user.

        Returns:
        - tuple or None: User information as a tuple (id, username, password, age, gender, weight, height, fitness_goal, bmr),
          or None if login is unsuccessful.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

            username = input("Enter your username: ")
            password = input("Enter your password: ")

            cursor.execute('''
                SELECT * FROM users
                WHERE username = ? AND password = ?
            ''', (username, password))

            user = cursor.fetchone()
            return user
        except sqlite3.Error as e:
            print(f'Error logging in user: {e}')
            raise

    # Function to register a new user
    def register(self):
        """
        Register a new user.

        Returns:
        - tuple: User information as a tuple (id, username, password, age, gender, weight, height, fitness_goal, bmr).
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                username = input("Enter a username: ")

                # Check if username already exists
                cursor.execute('''
                    SELECT * FROM users
                    WHERE username = ?
                ''', (username,))

                existing_user = cursor.fetchone()

                if existing_user:
                    print("Username already exists. Registration failed.")
                    return None

                # Get user details
                password = input("Enter a password: ")
                age = float(input("Enter your current age (years): "))
                # Get valid gender input
                while True:
                    gender = input("Enter your gender (male/female): ").lower()
                    if gender in ['male', 'female']:
                        break
                    else:
                        print("Invalid input. Please enter 'male' or 'female'.")

                weight = float(input("Enter your weight (kg): "))
                height = float(input("What is your height (cm): "))
                # Get valid fitness goal input
                while True:
                    fitness_goal = input("Is your fitness goal to lose/gain/maintain?: ").lower()
                    if fitness_goal in ['lose', 'gain', 'maintain']:
                        break
                    else:
                        print("Invalid input. Please enter 'lose', 'gain', or 'maintain'.")
                
                # BMR calculator
                bmr = self.calculate_bmr(gender, weight, height, age)
                
                # Calculate initial daily calorie goal based on fitness goal
                initial_calorie_goal = self.calculate_goal_calories(bmr, fitness_goal)
                
                # Register the new user into the database
                cursor.execute('''
                    INSERT INTO users (username, password, age, gender, weight, height, fitness_goal, bmr)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (username, password, age, gender, weight, height, fitness_goal, bmr))

                user_id = cursor.lastrowid
                
                # Insert the initial daily calorie goal into the goals table
                cursor.execute('''
                    INSERT INTO goals (user_id, daily_calorie_goal)
                    VALUES (?, ?)
                ''', (user_id, initial_calorie_goal))

            return user_id
        
        except sqlite3.Error as e:
            print(f'Error registering new user: {e}')
            conn.rollback()
            raise

    # Function to calculate BMR
    def calculate_bmr(self, gender, weight, height, age):
        """
        Calculate Basal Metabolic Rate (BMR) based on user details.

        Parameters:
        - gender (str): User's gender ('female' or 'male').
        - weight (float): User's weight in kilograms.
        - height (float): User's height in centimeters.
        - age (float): User's age in years.

        Returns:
        - float or None: Calculated BMR or None if an invalid gender is provided.
        """
        try:
            if gender.lower() == 'female':
                return float(655.1 + (9.563 * weight) + (1.850 * height) - (4.676 * age))
            elif gender.lower() == 'male':
                return float(66.47 + (13.75 * weight) + (5.003 * height) - (6.755 * age))
            else:
                print("Invalid gender. Please provide 'female' or 'male'.")
                return None
            
        except sqlite3.Error as e:
            print(f'Error calculating bmr: {e}')
            raise

    # Function to log exercise
    def log_exercise(self):
        """
        Log details of a user's exercise session into the database.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                print("--- Log Exercise ---\n")
                exercise_name = input("Enter Exercise Name: ")
                print(f"--- Enter the best set for {exercise_name}. Enter 0 for the unrelated attributes ---\n")

                # Log the most important set
                reps = self.get_float_input("Reps: ")
                weight = self.get_float_input("Weight (kg): ")
                duration = self.get_float_input("Duration (minutes): ")
                distance = self.get_float_input("Distance (km): ")

                # Log the exercise details
                cursor.execute('''
                    INSERT INTO exercises (user_id, name, reps, weight, duration, distance)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (self.user_id, exercise_name, reps, weight, duration, distance))
                
                input("--- Exercise logged successfully! Press enter to return to menu ---")
                conn.commit()

        except sqlite3.Error as e:
            print(f"Problem occurred while trying to log an exercise: {e}")
            conn.rollback()
            raise

        finally:
            if 'cursor' in locals() and cursor is not None:
                cursor.close()
                            
    # Function to log a workout
    def log_workout(self):
        """
        Log details of a user's workout session into the database.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                            
                print("--- Log Workout ---\n")
                option = input("1. Enter manually \n2. Select from listed exercises\n")

                if option == "1":
                    calories_burned = self.get_float_input("Enter calories burned: ")
                elif option == "2":
                    exercise_type = input("What type of exercise did you do (1. Weights, 2. Other): ")

                    if exercise_type == "1":
                        intensity = input("Select intensity (1. Light, 2. Moderate, 3. Intense): ")
                        duration = self.get_float_input("How long did you exercise for (minutes)?: ")
                        calories_burned = self.calculate_calories_burned_weightlifting(intensity, duration)
                    elif exercise_type == "2":
                        other_exercises = self.get_other_exercises(self.user_id)
                        exercise_names = list(other_exercises.keys())

                        # Display exercise names to the user
                        for index_other_exercises, exercise_name in enumerate(exercise_names, start=1):
                            print(f"{index_other_exercises}. {exercise_name}")

                        # Assuming the user selects an exercise by entering a number
                        selected_index_input = input("Enter the number corresponding to the exercise (or type 'custom' to add a custom exercise): ")

                        if selected_index_input.lower() == "custom":
                            self.add_custom_exercise()
                            input("Press enter to return to menu")
                            return
                        else:
                            # Assuming the user entered a number
                            selected_index = int(selected_index_input) - 1
                            selected_exercise = exercise_names[selected_index]

                            intensity = input("Select intensity (1. Light, 2. Moderate, 3. Intense): ")
                            duration = self.get_float_input("Enter duration (minutes): ")
                            calories_burned = self.calculate_calories_burned_other_exercises(self.user_id, selected_exercise, intensity, duration)
                    else:
                        input("--- Invalid option. Logging workout failed. Press enter to continue ---")
                        return
                else:
                    return

                # Log the workout details
                current_date = datetime.now().date()
                cursor.execute('''
                    INSERT INTO calories (user_id, calories_burned, timestamp)
                    VALUES (?, ?, ?)
                ''', (self.user_id, calories_burned, current_date))

                print(f"Workout logged successfully.")
                
                # Calculate the sum of calories burned for the current date
                cursor.execute('''
                    SELECT SUM(calories_burned) FROM calories
                    WHERE user_id = ? AND timestamp = ?
                    ''', (self.user_id, current_date))
                
                total_calories_burned = cursor.fetchone()[0]
                
                if total_calories_burned:
                    print(f"Calories burned today: {total_calories_burned}")
                else:
                    print("No calories burned today.")
                    
                input("--- Press enter to return to menu ---")
                conn.commit()

        except sqlite3.Error as e:
            print(f'Error logging a workout: {e}')
            conn.rollback()
            raise

        finally:
            if 'cursor' in locals() and cursor is not None:
                cursor.close()
            
    # Function to calculate calories burned for weightlifting
    def calculate_calories_burned_weightlifting(self, intensity, duration):
        """
        Calculates calories burned during a weightlifting session.

        Args:
        - intensity (str): The intensity level of the weightlifting session (1 for light, 2 for moderate, 3 for intense).
        - duration (float): The duration of the weightlifting session in minutes.

        Returns:
        - float: Calories burned during the weightlifting session.
        """
        try:
            if intensity == "1":
                return 4 * duration  # Light session: 4 cal/min
            elif intensity == "2":
                return 6 * duration  # Moderate session: 6 cal/min
            elif intensity == "3":
                return 10 * duration # Intense session: 10 cal/min
            else:
                print("Invalid intensity. Logging workout failed.")
                return 0
        
        except sqlite3.Error as e:
            print(f'Error calculating calories burned from weightlifting: {e}')
            raise
 
    # Function to add a custom exercise
    def add_custom_exercise(self):
        """
        Add a custom exercise to the database.

        Returns:
        - None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
            
                exercise_name = input("Enter the name of the exercise: ")
                light_intensity = self.get_float_input("Enter calories burned per minute for light intensity: ")
                moderate_intensity = self.get_float_input("Enter calories burned per minute for moderate intensity: ")
                intense_intensity = self.get_float_input("Enter calories burned per minute for intense intensity: ")

                # Add the custom exercise to the table
                cursor.execute('''
                    INSERT INTO other_exercises (user_id, name, light_intensity, moderate_intensity, intense_intensity)
                    VALUES (?, ?, ?, ?, ?)
                ''', (self.user_id, exercise_name, light_intensity, moderate_intensity, intense_intensity))

                print(f"--- Custom exercise '{exercise_name}' added successfully. ---")

        except sqlite3.Error as e:
            print(f'Error adding a custom exercise: {e}')
            conn.rollback()
            raise
            
    # Function to retrieve custom other exercises from the database
    def get_other_exercises(self, user_id):
        """
        Retrieve custom 'other' exercises from the database.

        Args:
        - user_id (int): The ID of the user.

        Returns:
        - dict: A dictionary containing exercise names and their corresponding calorie intensities.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Pregenerated exercise list with calories burned per minute per intensity level
                pregenerated_exercises = [
                    ("Running", 8, 11, 14),
                    ("Swimming", 11, 14, 17),
                    ("Padel", 5, 8, 11),
                    ("Climbing", 7, 10, 13)
                ]

                # Insert the pregenerated list of exercises into a table if not already present
                for exercise in pregenerated_exercises:
                    cursor.execute('''
                        INSERT OR IGNORE INTO other_exercises (user_id, name, light_intensity, moderate_intensity, intense_intensity)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (user_id,) + exercise)

                # Fetch all other exercises for the user
                cursor.execute('''
                    SELECT name, light_intensity, moderate_intensity, intense_intensity
                    FROM other_exercises
                    WHERE user_id = ? OR user_id IS NULL
                ''', (user_id,))

                fetch_other_exercises = {}

                for row in cursor.fetchall():
                    exercise_name, light_intensity, moderate_intensity, intense_intensity = row
                    fetch_other_exercises[exercise_name] = {
                        "light": light_intensity,
                        "moderate": moderate_intensity,
                        "intense": intense_intensity
                    }
            return fetch_other_exercises
        
        except sqlite3.Error as e:
            print(f'Error fetching other exercises: {e}')
            conn.rollback()
            raise
    
    # Function to add a custom exercise under 'other' category
    def add_custom_other_exercise(self):
        """
        Add a custom exercise under the 'other' category.

        Returns:
        - None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                exercise_name = input("Enter the name of the exercise: ")
                average_calories_burned = self.get_float_input("Enter average calories burned per minute: ")

                # Add the custom exercise to the 'other' exercises
                cursor.execute('''
                    INSERT INTO other_exercises (name, average_calories_burned)
                    VALUES (?, ?)
                ''', (exercise_name, average_calories_burned))

                print(f"Custom exercise '{exercise_name}' added successfully.")

        except sqlite3.Error as e:
            print(f'Error adding custom exercises to "other exercises": {e}')
            conn.rollback()
            raise
                
    # Function to calculate calories burned for other exercises
    def calculate_calories_burned_other_exercises(self, user_id, selected_exercise, intensity, duration):
        """
        Calculate calories burned during other exercises.

        Args:
        - user_id (int): The ID of the user.
        - selected_exercise (str): The name of the selected exercise.
        - intensity (str): The intensity level of the exercise (1 for light, 2 for moderate, 3 for intense).
        - duration (float): The duration of the exercise in minutes.

        Returns:
        - float: Calories burned during the exercise.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Retrieve custom exercises from the database
                exercises = self.get_other_exercises(user_id)

                if selected_exercise in exercises:
                    if intensity == "1":
                        return exercises[selected_exercise]["light"] * duration
                    elif intensity == "2":
                        return exercises[selected_exercise]["moderate"] * duration
                    elif intensity == "3":
                        return exercises[selected_exercise]["intense"] * duration
                    else:
                        print("Invalid intensity. Logging workout failed.")
                        return 0
                else:
                    print("Invalid exercise. Logging workout failed.")
                    return 0

        except sqlite3.Error as e:
            print(f'Error calculating calories burned from other exercises: {e}')
            raise
            
        finally:
            if 'cursor' in locals() and cursor is not None:
                cursor.close()
                
        User

    # Retrieve the last entry based off of the time stamp (done)
    def get_last_entry(self, cursor, table_name):
        """
        Retrieve the last entry from the specified table based on the timestamp.

        Args:
        - cursor: SQLite cursor.
        - table_name (str): Name of the table.

        Returns:
        - tuple or None: The last entry as a tuple or None if no entry is found.
        """
        try:
            cursor.execute(f'''
                SELECT * FROM {table_name}
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            ''', (self.user_id,))

            return cursor.fetchone()

        except sqlite3.Error as e:
            print(f'Error fetching last entry: {e}')
            raise
    
    # Function to log food entry
    def log_food(self):
        """
        Log details of a user's food consumption into the database.

        Returns:
        - None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                print("--- Log Food ---")
                calories_eaten = self.get_float_input("Enter calories eaten: ")

                # Ensure calories eaten is a valid number
                if calories_eaten is None or calories_eaten <= 0:
                    print("Invalid input for calories. Please enter a valid number greater than 0.")
                    return

                # Get the current date
                current_time = datetime.now().date()

                # Log the food details
                cursor.execute('''
                    INSERT INTO calories (user_id, calories_consumed, timestamp)
                    VALUES (?, ?, ?)
                ''', (self.user_id, calories_eaten, current_time))

                print(f"--- Food logged successfully! ---")

                # Calculate total calories eaten for the day
                cursor.execute('''
                    SELECT SUM(calories_consumed) FROM calories
                    WHERE user_id = ? AND timestamp = ?
                ''', (self.user_id, current_time))
                total_calories_eaten = cursor.fetchone()[0]
                print(f"Total calories eaten for the day: {total_calories_eaten}")

                # Retrieve daily calorie goal
                cursor.execute('''
                    SELECT daily_calorie_goal FROM goals
                    WHERE user_id = ?
                ''', (self.user_id,))
                result = cursor.fetchone()

                if result is not None:
                    daily_calorie_goal = result[0]
                    print(f"Daily calorie goal: {int(daily_calorie_goal)}")
                else:
                    print("No data found for the specified user and date.")

                input("--- Press enter to return to menu ---")
                conn.commit()

        except sqlite3.Error as e:
            print(f'Error for logging food into database: {e}')
            conn.rollback()
            raise
            
        finally:
            if 'cursor' in locals() and cursor is not None:
                cursor.close()
                
    # Function to create exercise routine
    def create_routine(self):
        """
        Create an exercise routine and add it to the database.

        Returns:
        - None
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            try:
                print("Create Exercise Routine\n")
                routine_name = input("Enter Routine Name: ")

                # Check if routine_name already exists for the user
                cursor.execute('''
                    SELECT * FROM routines
                    WHERE user_id = ? AND routine_name = ?
                ''', (self.user_id, routine_name))

                if cursor.fetchone():
                    input("Routine name already exists. Please choose a different name.")

                exercise_list = []

                while True:
                    exercise_name = input("Enter Exercise Name ('end' to finish or escape key to stop): ")

                    if exercise_name.lower() == 'end':
                        break
                    
                    print("--- For each entry add a number, else add 0 if not applicable ---")
                    
                    sets = self.get_float_input("Number of Sets: ")

                    if sets > 0:
                        for set_number in range(1, int(sets) + 1):
                            reps = self.get_float_input(f"Set {set_number} Reps: ")
                            weight = self.get_float_input(f"Set {set_number} Weight (kg): ")
                            duration = self.get_float_input(f"Set {set_number} Duration (minutes): ")
                            distance = self.get_float_input(f"Set {set_number} Distance (km): ")

                            exercise_list.append((self.user_id, routine_name, exercise_name, reps, weight, set_number, duration, distance))
                    else:
                        reps = self.get_float_input("Number of Reps: ")
                        weight = self.get_float_input("Weight (kg): ")
                        duration = self.get_float_input("Duration (minutes): ")
                        distance = self.get_float_input(f"Distance (km): ")

                        exercise_list.append((self.user_id, routine_name, exercise_name, reps, weight, 1, duration, distance))

                # Add exercises to the database
                for exercise in exercise_list:
                    cursor.execute('''
                        INSERT INTO routines
                        (user_id, routine_name, exercise_name, reps, weight, sets, duration, distance)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', exercise)

                input("--- Routine created successfully. Press enter to return to menu ---")
                conn.commit()

            except KeyboardInterrupt:
                # Handle KeyboardInterrupt (Escape button pressed)
                print("Operation aborted. No data entry added to the database.")
                conn.rollback()

            finally:
                if 'cursor' in locals() and cursor is not None:
                    cursor.close()
    
    # Function to view exercise routines
    def view_routines(self):
        """
        View and display exercise routines for the user.

        Returns:
        - None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                print("View Exercise Routines:")
                cursor.execute('''
                    SELECT DISTINCT routine_name FROM routines
                    WHERE user_id = ?
                ''', (self.user_id,))

                routines = cursor.fetchall()

                if not routines:
                    print("No routines available.")
                    return

                print("Select a routine:")
                for i, routine in enumerate(routines, start=1):
                    print(f"{i}. {routine[0]}")

                selected_routine = input("Enter the routine number or name: ")

                if selected_routine.isdigit():
                    selected_routine = int(selected_routine) - 1
                    if 0 <= selected_routine < len(routines):
                        selected_routine = routines[selected_routine][0]

                cursor.execute('''
                    SELECT exercise_name, reps, weight, sets, duration, distance
                    FROM routines
                    WHERE user_id = ? AND routine_name = ?
                    ORDER BY exercise_name, sets
                ''', (self.user_id, selected_routine))

                exercises = cursor.fetchall()

                if exercises:
                    print(f"Exercise routine: {selected_routine}")
                    current_exercise = None
                    for exercise in exercises:
                        exercise_name, reps, weight, set_number, duration, distance = exercise
                        if exercise_name != current_exercise:
                            print(f"\n{exercise_name}")
                            current_exercise = exercise_name

                        set_info = []
                        if reps > 0:
                            set_info.append(f"{reps} reps")
                        if weight > 0:
                            set_info.append(f"{weight} kg")
                        if duration > 0:
                            set_info.append(f"{duration} min")
                        if distance > 0:
                            set_info.append(f"{distance} km")

                        if set_info:
                            print(f"Set {set_number}: {', '.join(set_info)}")

                    input("--- Press enter to continue to menu ---")
                else:
                    input("-- No exercises found for the selected routine. Press enter to return to menu ---")
        except sqlite3.Error as e:
            print(f'Error occured while trying to view routines: {e}')
            raise

        finally:
            if 'cursor' in locals() and cursor is not None:
                cursor.close()
    
    # Short function to calculate total daily calories
    def calculate_daily_calories(self, calories_consumed, calories_burned):
        """
        Calculate the total daily calories by subtracting calories burned from calories consumed.

        Args:
        - calories_consumed (float): Calories consumed by the user.
        - calories_burned (float): Calories burned by the user through exercise.

        Returns:
        - float: Total daily calories.
        """
        return calories_consumed - calories_burned

    # Function to calculate goal calories based on BMR and fitness goal
    def calculate_goal_calories(self, bmr, fitness_goal):
        """
        Calculate the daily caloric goal based on the user's BMR and fitness goal.

        Args:
        - bmr (float): Basal Metabolic Rate (calories/day) calculated based on user's biometrics.
        - fitness_goal (str): User's fitness goal ("lose", "gain", or "maintain").

        Returns:
        - float: Daily caloric goal.
        """
        try:
            if fitness_goal == "lose":
                return float(bmr - 300)  # Caloric deficit for weight loss
            elif fitness_goal == "gain":
                return float(bmr + 300)  # Caloric surplus for weight gain
            else:
                return float(bmr)  # Maintain current weight
        
        except sqlite3.Error as e:
            print(f'Error occured while calculating calorie goals: {e}')
            raise
            
    # Function to view caloric progress
    def view_caloric_progress(self):
        """
        View and display the caloric progress of the user, plotting a graph.

        Returns:
        - None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

            # Retrieve user's BMR
            cursor.execute('''
                SELECT bmr
                FROM users
                WHERE id = ?
            ''', (self.user_id,))

            bmr = cursor.fetchone()[0]

            # Retrieve user's daily calorie goal
            cursor.execute('''
                SELECT daily_calorie_goal
                FROM goals
                WHERE user_id = ?
            ''', (self.user_id,))

            daily_calorie_goal = cursor.fetchone()[0]

            # Retrieve daily calorie intake and exercise calories burned
            cursor.execute('''
                SELECT timestamp, SUM(calories_consumed) AS total_calories_consumed,
                SUM(calories_burned) AS total_calories_burned
                FROM calories
                WHERE user_id = ?
                GROUP BY timestamp
                ORDER BY timestamp
            ''', (self.user_id,))

            data = cursor.fetchall()

            if not data:
                input("--- No caloric data found for the user. Press enter to return to menu ---")
                return

            # Extract data for plotting
            dates = [entry[0] for entry in data]
            total_calories_consumed = [entry[1] if entry[1] is not None else 0 for entry in data]
            total_calories_burned = [entry[2] if entry[2] is not None else 0 for entry in data]

            # Calculate daily net calories (consumed - burned)
            net_calories = [consumed - burned for consumed, burned in zip(total_calories_consumed, total_calories_burned)]

            # Plotting
            plt.plot(dates, net_calories, label='Daily Calories Total')
            plt.axhline(y=daily_calorie_goal, color='r', linestyle='--', label='Daily Calorie Goal')

            plt.xlabel('Date')
            plt.ylabel('Calories')
            plt.title('Caloric Progress Tracker')
            plt.legend()
            plt.show()

        except sqlite3.Error as e:
            print(f'Error occured while trying to view caloric progress graph: {e}')
            raise

        finally:
            if 'cursor' in locals() and cursor is not None:
                cursor.close()
            
    # Function to calculate exercise goal progress
    def view_exercise_progress(self):
        """
        View and display the exercise goal progress of the user, plotting a graph.

        Returns:
        - None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Retrieve exercise goals and latest entries
                cursor.execute('''
                    SELECT g.exercise_name, g.target_reps, g.target_weight, g.target_distance, g.target_duration, e.reps, e.weight, e.distance, e.duration
                    FROM goals g
                    LEFT JOIN (
                        SELECT user_id, name, reps, weight, distance, duration
                        FROM exercises
                        WHERE user_id = ?
                    ) e ON g.exercise_name = e.name
                    WHERE g.target_reps IS NOT NULL
                        OR g.target_weight IS NOT NULL
                        OR g.target_distance IS NOT NULL
                        OR g.target_duration IS NOT NULL
                ''', (self.user_id,))

                progress_data = cursor.fetchall()
                
                exercise_names = [entry[0] for entry in progress_data]
                bar_width = 0.15
                index = np.arange(len(exercise_names))

                # Filter out exercises with no goals
                progress_data = [entry for entry in progress_data if any(entry[1:])]

                if not progress_data:
                    print("No exercise goals found. Set exercise goals to track progress.")
                    return


                categories = ["Reps", "Weight", "Duration", "Distance"]

                for i, category in enumerate(categories):
                    values = []
                    for entry in progress_data:
                        goal_value = entry[i + 1]
                        actual_value = entry[i + 5]

                    if goal_value is not None and goal_value != 0:
                        # Calculate progress percentage only if actual_value is not None
                        if actual_value is not None:
                            percentage_progress = min((actual_value / goal_value) * 100, 100)
                        else:
                            percentage_progress = 0
                        values.append(percentage_progress)
                    else:
                        values.append(0)  # Replace None with 0 for plotting

                # Plot the bar graph
                plt.bar(index + i * bar_width, values, bar_width, label=category)

                plt.xlabel("Exercises")
                plt.ylabel("Progress (%)")
                plt.title("Exercise Progress")
                plt.xticks(index + bar_width, exercise_names)
                plt.legend()
                plt.show()

        except sqlite3.Error as e:
            print(f"Error occurred while trying to view exercise progress graph: {e}")

        finally:
            if 'cursor' in locals() and cursor is not None:
                cursor.close()
                
    # Function to update user profile
    def update_profile(self):
        """
        Update the user's profile, allowing modifications to weight, exercise goals, and fitness goals.

        Returns:
        - None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                print("Update Profile\n")
                print("1. Update Weight")
                print("2. Add an Exercise Goal")
                print("3. Update Fitness Goal")
                print("4. Exit")

                option = input("Select an option: ")

                if option == "1":
                    new_weight = self.get_float_input("Enter your new weight (kg): ")

                    # Recalculate BMR with the new weight
                    # Retrieve user information
                    cursor.execute('''
                        SELECT height, age, gender
                        FROM users
                        WHERE id = ?
                    ''', (self.user_id,))

                    user_biometrics = cursor.fetchone()
                    if user_biometrics:
                        height, age, gender = user_biometrics

                    new_bmr = self.calculate_bmr(gender, new_weight, height, age)

                    cursor.execute('''
                        UPDATE users
                        SET weight = ?
                        WHERE id = ?
                    ''', (new_weight, self.user_id))
                    cursor.execute('''
                        UPDATE goals
                        SET daily_calorie_goal = ?
                        WHERE user_id = ?                       
                    ''', (new_bmr, self.user_id))
                    input("--- Weight and BMR updated successfully. Press enter to return to menu ---")

                elif option == "2":
                    # Add exercise goal logic
                    exercise_name = input("Enter the exercise name: ")
                    attribute = input("Enter the goal attribute (reps, weight, distance, duration): ")
                    target_value = self.get_float_input(f"Enter target {attribute} (enter 0 if not applicable): ")

                    # Check if a goal already exists for the exercise and attribute
                    cursor.execute('''
                        SELECT * FROM goals
                        WHERE user_id = ? AND exercise_name = ? AND target_{0} IS NOT NULL
                    '''.format(attribute.lower()), (self.user_id, exercise_name))

                    existing_goal = cursor.fetchone()

                    if existing_goal:
                        # Update the existing goal
                        cursor.execute('''
                            UPDATE goals
                            SET target_{0} = ?
                            WHERE user_id = ? AND exercise_name = ?
                        '''.format(attribute.lower()), (target_value, self.user_id, exercise_name))
                    else:
                        # Insert a new goal
                        cursor.execute('''
                            INSERT INTO goals (user_id, exercise_name, target_{0})
                            VALUES (?, ?, ?)
                        '''.format(attribute.lower()), (self.user_id, exercise_name, target_value))

                    input("--- Exercise goal added successfully! Press enter to return to menu ---")

                elif option == "3":
                    new_goal = input("Enter your new fitness goal (lose/gain/maintain): ").lower()
                    cursor.execute('''
                        UPDATE users
                        SET fitness_goal = ?
                        WHERE id = ?
                    ''', (new_goal, self.user_id))
                    input("--- Fitness goal updated successfully. Press enter to return to menu ---")

                elif option == "4":
                    return
                else:
                    print("Invalid option. Please try again.")

        except sqlite3.Error as e:
            print(f'Error occurred while trying to update user profile: {e}')
            raise

        finally:
            if 'cursor' in locals() and cursor is not None:
                cursor.close()
    
    # Displaying the menu (done)
    def main(self):
        """
        The main menu of the Fitness Tracker application. Allows users to log in, register,
        and perform various actions based on their authentication status.

        When the user is not logged in:
        - Options:
            1. Log In
            2. Register
            3. Exit

        When the user is logged in:
        - Options:
            1. Log Exercise
            2. Log Workout
            3. Log Food
            4. Create Exercise Routine
            5. View Exercise Routines
            6. View Caloric Progress
            7. View Exercise Progress
            8. Update Profile
            9. Log Out

        Returns:
        - None
        """
        try:
            while True:
                if self.user_id is None:
                    print("\nFitness Tracker - Main Menu:")
                    print("1. Log In")
                    print("2. Register")
                    print("3. Exit")
                else:
                    print("\nFitness Tracker - Logged In:")
                    print("1. Log Exercise")
                    print("2. Log Workout")
                    print("3. Log Food")
                    print("4. Create Exercise Routine")
                    print("5. View Exercise Routines")
                    print("6. View Caloric Progress")
                    print("7. View Exercise Progress")
                    print("8. Update Profile")
                    print("9. Log Out")

                option = input("Select an option: ")

                if self.user_id is None:
                    if option == "1":
                        user = self.login()
                        if user:
                            print("--- Login successful! ---")
                            self.user_id = user[0]
                        else:
                            print("--- Login failed. Please check your username and password ---")
                    elif option == "2":
                        self.user_id = self.register()
                        if self.user_id:
                            input(f"--- Registration successful. Welcome! Press enter to continue to the menu ---")
                        else:
                            input("Registration failed. Please choose a different username. Press enter to return to the menu")
                    elif option == "3":
                        input("Goodbye!")
                        break
                    else:
                        print("Invalid option. Please try again.")
                else:
                    if option == "1":
                        self.log_exercise()
                    elif option == "2":
                        self.log_workout()
                    elif option == "3":
                        self.log_food()
                    elif option == "4":
                        self.create_routine()
                    elif option == "5":
                        self.view_routines()
                    elif option == "6":
                        self.view_caloric_progress()
                    elif option == "7":
                        self.view_exercise_progress()
                    elif option == "8":
                        if self.update_profile():
                            print("Exiting Fitness Tracker. Goodbye!")
                            break
                    elif option == "9":
                        print("Logging out.")
                        self.user_id = None
                    else:
                        print("Invalid option. Please try again.")
            
        except sqlite3.Error as e:
                print(f'Main menu Error: {e}')
                raise

if __name__ == "__main__":
    fitness_tracker = FitnessTracker()
    fitness_tracker.main()