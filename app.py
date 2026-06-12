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

    # Skip top rows
    df = df.iloc[3:].reset_index(drop=True)

    # 🔥 TAKE FIRST 3 NON-EMPTY COLUMNS
    df = df.dropna(axis=1, how='all')

    # Now pick first 3 columns
    df = df.iloc[:, 0:3]

    df.columns = ["Date", "Inflow", "Outflow"]

    # Clean data
    df["Date"] = pd.to_numeric(df["Date"], errors="coerce")
    df["Inflow"] = pd.to_numeric(df["Inflow"], errors="coerce")
    df["Outflow"] = pd.to_numeric(df["Outflow"], errors="coerce")

    df = df.dropna()

    # Assign date (fixed month)
    df["Date"] = pd.to_datetime({
        "year": 2017,
        "month": 1,
        "day": df["Date"]
    })

    return df


# ----------------------
# UPLOAD
# ----------------------
@app.route("/upload", methods=["POST"])
def upload():
    try:
        file = request.files["file"]

        df = pd.read_excel(file)

        df = process_dataframe(df)

        # Analysis
        df["Balance"] = df["Inflow"] - df["Outflow"]

        # SMART classification
        threshold = df["Balance"].mean()

        stress = len(df[df["Balance"] < threshold - 5])
        moderate = len(df[(df["Balance"] >= threshold - 5) & (df["Balance"] <= threshold + 5)])
        excess = len(df[df["Balance"] > threshold + 5])

        # Totals
        total_inflow = round(df["Inflow"].sum(), 2)
        total_outflow = round(df["Outflow"].sum(), 2)
        balance = round(total_inflow - total_outflow, 2)

        # Month (fixed for demo)
        stress_months = ["2017-01"] if stress > 0 else []
        moderate_months = ["2017-01"] if moderate > 0 else []
        excess_months = ["2017-01"] if excess > 0 else []

        return render_template("index.html",
                total_records=len(df) if df is not None else 0,
                total_inflow=total_inflow if 'total_inflow' in locals() else 0,
                total_outflow=total_outflow if 'total_outflow' in locals() else 0,
                balance=balance if 'balance' in locals() else 0,
                stress_days=stress if 'stress' in locals() else 0,
                moderate_days=moderate if 'moderate' in locals() else 0,
                excess_days=excess if 'excess' in locals() else 0,
                stress_months=stress_months if 'stress_months' in locals() else [],
                moderate_months=moderate_months if 'moderate_months' in locals() else [],
                excess_months=excess_months if 'excess_months' in locals() else []
         )

    except Exception as e:
        return render_template("index.html", error=str(e))
    print("UPLOAD HIT")

# ----------------------
# RUN
# ----------------------
if __name__ == "__main__":
    app.run(debug=True)
