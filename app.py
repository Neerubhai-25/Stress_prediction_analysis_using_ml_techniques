
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pandas as pd
import joblib
import json
import os

# =====================================================
# APP CONFIGURATION
# =====================================================

app = Flask(__name__)
app.config["SECRET_KEY"] = "super_secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# =====================================================
# LOAD MODEL
# =====================================================

MODEL_PATH = "stress_model_linear_advanced.pkl"

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError("Model file not found!")

model = joblib.load(MODEL_PATH)
print("Model Loaded Successfully")

# =====================================================
# DATABASE MODELS
# =====================================================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class StressRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    stress_score = db.Column(db.Float)
    stress_level = db.Column(db.String(50))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# =====================================================
# ROUTES
# =====================================================

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = generate_password_hash(request.form["password"])

        if User.query.filter_by(username=username).first():
            return "Username already exists"

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("dashboard"))

        return "Invalid credentials"

    return render_template("login.html")

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

@app.route("/analytics")
@login_required
def analytics():
    records = StressRecord.query.filter_by(user_id=current_user.id)\
        .order_by(StressRecord.date.asc()).all()

    data = [{
        "date": r.date.strftime("%Y-%m-%d"),
        "stress_score": float(r.stress_score)
    } for r in records]

    return render_template("analytics.html",
                           records_json=json.dumps(data))

# =====================================================
# PREDICTION ROUTE
# =====================================================

@app.route("/predict", methods=["POST"])
@login_required
def predict():
    try:
        data = request.json

        # ---------------- DAILY LIMIT ---------------- #
        last_record = StressRecord.query.filter_by(user_id=current_user.id)\
            .order_by(StressRecord.date.desc()).first()

        if last_record and last_record.date.date() == datetime.utcnow().date():
            return jsonify({
                "error": "You already predicted stress today. Please try again tomorrow."
            }), 403

        # ---------------- INPUT VALUES ---------------- #
        study = float(data.get("study", 0))
        sleep = float(data.get("sleep", 0))
        activity = float(data.get("activity", 0))
        social = float(data.get("social", 0))
        gpa = float(data.get("gpa", 0))

        # ---------------- VALIDATION ---------------- #
        if not (0 <= study <= 8):
            return jsonify({"error": "Study hours must be between 0 and 8"}), 400

        if not (1 <= sleep <= 10):
            return jsonify({"error": "Sleep hours must be between 1 and 12"}), 400

        if not (0 <= activity <= 6):
            return jsonify({"error": "Physical activity must be between 0 and 6 hours"}), 400

        if not (0 <= social <= 8):
            return jsonify({"error": "Social hours must be between 0 and 8"}), 400

        if not (0 <= gpa <= 10):
            return jsonify({"error": "GPA must be between 0 and 10"}), 400

        # ---------------- FEATURE MAPPING ---------------- #
        input_data = {}

        for feature in model.feature_names_in_:
            if "Study" in feature:
                input_data[feature] = study
            elif "Sleep" in feature:
                input_data[feature] = sleep
            elif "Physical" in feature:
                input_data[feature] = activity
            elif "Social" in feature:
                input_data[feature] = social
            elif "GPA" in feature:
                input_data[feature] = gpa
            else:
                input_data[feature] = 0

        features = pd.DataFrame([input_data])

        # ---------------- MODEL PREDICTION ---------------- #
        raw_score = float(model.predict(features)[0])
        stress_score = min(100, abs(raw_score) * 3)

        # ---------------- STRESS LEVEL ---------------- #
        if stress_score < 30:
            level = "Low"
            color = "#22c55e"
        elif stress_score < 60:
            level = "Moderate"
            color = "#f59e0b"
        else:
            level = "High"
            color = "#ef4444"

        # ---------------- ADVANCED RECOMMENDATIONS ---------------- #
        recommendations = []

        # Sleep
        if sleep < 6:
            recommendations.append("Insufficient sleep detected. Aim for 7–8 hours for better cognitive performance.")
        elif sleep > 9:
            recommendations.append("Oversleeping may affect productivity. Maintain consistent sleep timing.")
        else:
            recommendations.append("Healthy sleep pattern maintained. Continue consistent bedtime routine.")

        # Study
        if study > 6:
            recommendations.append("High academic load detected. Apply Pomodoro technique for effective focus.")
        elif study < 2:
            recommendations.append("Low study hours observed. Increase focused learning gradually.")

        # Physical Activity
        if activity < 1:
            recommendations.append("Low physical activity may increase stress hormones. Add at least 30 mins exercise.")
        else:
            recommendations.append("Good physical activity supports stress reduction.")

        # Social
        if social < 1:
            recommendations.append("Limited social interaction detected. Engage in meaningful conversations.")
        elif social > 6:
            recommendations.append("Excessive social time may affect academic focus. Maintain balance.")

        # GPA
        if gpa < 5:
            recommendations.append("Academic performance needs structured planning and revision schedule.")
        elif gpa >= 8:
            recommendations.append("Strong academic performance. Avoid burnout by balancing workload.")

        # Combination Logic
        if sleep < 6 and study > 6:
            recommendations.append("High study + low sleep increases burnout risk. Prioritize rest.")

        if activity < 1 and social < 1:
            recommendations.append("Low activity and isolation may elevate stress levels.")

        # Stress-Level Advice
        if level == "High":
            recommendations.append("Practice deep breathing (4-7-8 method) daily.")
            recommendations.append("Break tasks into smaller achievable goals.")
            recommendations.append("Consider discussing concerns with a mentor or counselor.")
            recommendations.append("Limit caffeine and screen time before bed.")
        elif level == "Moderate":
            recommendations.append("Use relaxation breaks and structured scheduling.")
            recommendations.append("Maintain a consistent daily routine.")
            recommendations.append("Track your stress levels and identify triggers.")
        else:
            recommendations.append("Maintain your healthy routine and track daily improvements.")
            recommendations.append("Continue balancing academics, health, and social activities.")      

        while len(recommendations) < 6:
            recommendations.append("Maintain balance between academics, health, and recreation.")

        # ---------------- SAVE RECORD ---------------- #
        new_record = StressRecord(
            user_id=current_user.id,
            stress_score=stress_score,
            stress_level=level
        )

        db.session.add(new_record)
        db.session.commit()

        return jsonify({
            "score": round(stress_score, 2),
            "level": level,
            "color": color,
            "recommendations": recommendations
        })

    except Exception as e:
        print("Prediction Error:", e)
        return jsonify({"error": "Server error during prediction."}), 500

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
