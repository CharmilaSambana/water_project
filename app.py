from flask import Flask, jsonify, render_template
import mysql.connector

# ML imports
from sklearn.linear_model import LinearRegression
import numpy as np

app = Flask(__name__)

# 🔹 MySQL Connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root123",   # 👉 add your password if needed
    database="water_db"
)

# 🟢 HOME
@app.route('/')
def home():
    return "Water Project Running ✅"

# 🟢 DASHBOARD
@app.route('/dashboard')
def dashboard():
    return render_template('index.html')

# 🟢 MONTHLY REPORT
@app.route('/monthly-report')
def monthly_report():
    cursor = db.cursor(dictionary=True)

    query = """
    SELECT 
        MONTH(date) AS month,
        AVG(inflow) AS avg_inflow,
        AVG(outflow) AS avg_outflow
    FROM water_data
    GROUP BY MONTH(date)
    ORDER BY month
    """

    cursor.execute(query)
    data = cursor.fetchall()

    # 🔥 Stress logic
    for row in data:
        if row['avg_inflow'] and row['avg_outflow']:
            if row['avg_inflow'] < row['avg_outflow']:
                row['stress'] = "YES"
            else:
                row['stress'] = "NO"
        else:
            row['stress'] = "NO DATA"

    return jsonify(data)

# 🟢 WASTE REPORT
@app.route('/waste-report')
def waste_report():
    cursor = db.cursor(dictionary=True)

    query = """
    SELECT 
        MONTH(date) AS month,
        SUM(outflow) - SUM(inflow) AS waste
    FROM water_data
    GROUP BY MONTH(date)
    ORDER BY month
    """

    cursor.execute(query)
    data = cursor.fetchall()

    return jsonify(data)

# 🟢 ML PREDICTION
@app.route('/predict')
def predict():
    cursor = db.cursor()

    query = "SELECT MONTH(date), inflow FROM water_data ORDER BY date"
    cursor.execute(query)
    rows = cursor.fetchall()

    X = []
    y = []

    for r in rows:
        if r[1] is not None:
            X.append([r[0]])
            y.append(r[1])

    X = np.array(X)
    y = np.array(y)

    if len(X) == 0:
        return jsonify({"error": "No data available"})

    model = LinearRegression()
    model.fit(X, y)

    prediction = model.predict([[13]])

    return jsonify({
        "predicted_inflow": float(prediction[0])
    })

# 🟢 RUN
if __name__ == '__main__':
    app.run(host="0.0.0.0",port=10000)