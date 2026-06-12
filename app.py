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

    # Skip header rows
    df = df.iloc[3:].reset_index(drop=True)

    data = []

    year = 2017

    # 🔥 MANUALLY PICK MONTH BLOCKS (based on your sheet)
    # Format: [Date, Inflow, Outflow] repeating

    month_blocks = [
        (0, 3, 5),    # Jan
        (6, 9, 11),   # Feb
        (12, 15, 17), # Mar
        (18, 21, 23), # Apr
        (24, 27, 29), # May
        (30, 33, 35), # Jun
        (36, 39, 41), # Jul
        (42, 45, 47), # Aug
        (48, 51, 53), # Sep
        (54, 57, 59), # Oct
        (60, 63, 65), # Nov
        (66, 69, 71)  # Dec
    ]

    for m, (d_col, i_col, o_col) in enumerate(month_blocks, start=1):
        try:
            temp = df.iloc[:, [d_col, i_col, o_col]].copy()
            temp.columns = ["Date", "Inflow", "Outflow"]

            # Clean
            temp["Date"] = pd.to_numeric(temp["Date"], errors="coerce")
            temp["Inflow"] = pd.to_numeric(temp["Inflow"], errors="coerce")
            temp["Outflow"] = pd.to_numeric(temp["Outflow"], errors="coerce")

            temp = temp.dropna()

            if len(temp) > 5:
                temp["Date"] = pd.to_datetime({
                    "year": year,
                    "month": m,
                    "day": temp["Date"]
                })
                data.append(temp)

        except:
            continue

    if len(data) == 0:
        return None

    return pd.concat(data, ignore_index=True)

# ----------------------
# UPLOAD
# ----------------------
@app.route("/upload", methods=["POST"])
def upload():
    try:
        file = request.files["file"]

        df = pd.read_excel(file)

        df = process_dataframe(df)

        if df is None or len(df) == 0:
            return render_template("index.html", error="❌ Could not extract data from file")

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
