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

    # Skip top junk rows
    df = df.iloc[3:].reset_index(drop=True)

    # Take only first month (stable demo)
    df = df.iloc[:, [0, 3, 5]]

    df.columns = ["Date", "Inflow", "Outflow"]

    # Clean
    df["Date"] = pd.to_numeric(df["Date"], errors="coerce")
    df["Inflow"] = pd.to_numeric(df["Inflow"], errors="coerce")
    df["Outflow"] = pd.to_numeric(df["Outflow"], errors="coerce")

    df = df.dropna()

    # Assign date
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
                               total_records=len(df),
                               total_inflow=total_inflow,
                               total_outflow=total_outflow,
                               balance=balance,
                               stress_days=stress,
                               moderate_days=moderate,
                               excess_days=excess,
                               stress_months=stress_months,
                               moderate_months=moderate_months,
                               excess_months=excess_months)

    except Exception as e:
        return render_template("index.html", error=str(e))


# ----------------------
# RUN
# ----------------------
if __name__ == "__main__":
    app.run(debug=True)
