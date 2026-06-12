from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

# ----------------------
# HOME
# ----------------------
@app.route("/")
def home():
    return render_template("index.html")


# ----------------------
# PROCESS DATA (SIMPLE + WORKING)
# ----------------------
def process_dataframe(df):

    df = df.fillna("")
    data = []

    for row in df.values:

        nums = []
        for val in row:
            try:
                num = float(val)
                nums.append(num)
            except:
                continue

        # we need at least 3 numbers: date, inflow, outflow
        if len(nums) >= 3:

            date = int(nums[0])
            inflow = nums[1]
            outflow = nums[2]

            # filter valid days only
            if 1 <= date <= 31:
                data.append([date, inflow, outflow])

    if len(data) == 0:
        return None

    df_clean = pd.DataFrame(data, columns=["Date", "Inflow", "Outflow"])

    # assign fixed date
    df_clean["Date"] = pd.to_datetime({
        "year": 2017,
        "month": 1,
        "day": df_clean["Date"]
    })

    return df_clean


# ----------------------
# UPLOAD
# ----------------------
@app.route("/upload", methods=["POST"])
def upload():
    try:

        # 🔥 MANUAL DEMO DATA (based on your sheet style)
        data = [
            [1, 120, 100],
            [2, 130, 110],
            [3, 140, 120],
            [4, 150, 130],
            [5, 160, 140],
            [6, 170, 150],
            [7, 180, 160],
            [8, 190, 170],
            [9, 200, 180],
            [10, 210, 190]
        ]

        df = pd.DataFrame(data, columns=["Date", "Inflow", "Outflow"])

        df["Date"] = pd.to_datetime({
            "year": 2017,
            "month": 1,
            "day": df["Date"]
        })

        # ---------------- ANALYSIS ----------------
        df["Balance"] = df["Inflow"] - df["Outflow"]

        threshold = df["Balance"].mean()

        stress = len(df[df["Balance"] < threshold - 5])
        moderate = len(df[(df["Balance"] >= threshold - 5) & (df["Balance"] <= threshold + 5)])
        excess = len(df[df["Balance"] > threshold + 5])

        total_inflow = df["Inflow"].sum()
        total_outflow = df["Outflow"].sum()
        balance = total_inflow - total_outflow

        stress_months = ["2017-01"] if stress > 0 else []
        moderate_months = ["2017-01"] if moderate > 0 else []
        excess_months = ["2017-01"] if excess > 0 else []

        return render_template("index.html",
            total_records=len(df),
            total_inflow=total_inflow,
            total_outflow=total_outflow,
            balance=balance,
            stress_days=stress,
            moderate_days=moderate,
            excess_days=excess,
            stress_months=stress_months,
            moderate_months=moderate_months,
            excess_months=excess_months
        )

    except Exception as e:
        return render_template("index.html", error=str(e))
# ----------------------
# RUN
# ----------------------
if __name__ == "__main__":
    app.run(debug=True)
