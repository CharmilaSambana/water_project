from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():

    file = request.files["file"]
    df = pd.read_excel(file)

    # 🟢 CLEAN COLUMN NAMES
    df.columns = df.columns.str.strip()

    # 🟢 AUTO MAP COLUMNS (based on your Excel)
    df = df.rename(columns={
        df.columns[0]: "Date",  # first column is Date
        "Inflows (in Cusecs)": "Inflow",
        "Total Out flows (in Cusecs)": "Outflow"
    })

    # 🟢 HANDLE DATE
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])

    # ===============================
    # 🟢 DAILY ANALYSIS
    # ===============================
    df["Balance"] = df["Inflow"] - df["Outflow"]

    stress_days = df[df["Balance"] < 0]
    excess_days = df[df["Balance"] >= 0]

    moderate_days = df[(df["Balance"] >= -5) & (df["Balance"] <= 5)]

    # ===============================
    # 🟢 MONTHLY ANALYSIS
    # ===============================
    df["Month"] = df["Date"].dt.to_period("M").astype(str)

    monthly = df.groupby("Month").agg({
        "Inflow": "sum",
        "Outflow": "sum"
    }).reset_index()

    monthly["Balance"] = monthly["Inflow"] - monthly["Outflow"]

    stress_months = monthly[monthly["Balance"] < 0]
    excess_months = monthly[monthly["Balance"] >= 0]

    # ===============================
    # 🟢 WATER BALANCE ENGINE
    # ===============================
    total_inflow = df["Inflow"].sum()
    total_outflow = df["Outflow"].sum()
    total_balance = total_inflow - total_outflow

    # ===============================
    # 🟢 NRW (NON-REVENUE WATER)
    # ===============================
    monthly["NRW"] = monthly["Outflow"] - monthly["Inflow"]
    monthly["NRW %"] = (monthly["NRW"] / monthly["Inflow"]) * 100

    high_nrw = monthly[monthly["NRW %"] > 20]

    # ===============================
    # 🟢 FINAL REPORT
    # ===============================
    result = f"""
    📊 TOTAL SUMMARY <br><br>

    Total Records: {len(df)} <br>
    Total Inflow: {total_inflow} <br>
    Total Outflow: {total_outflow} <br>
    Balance: {total_balance} <br><br>

    🌊 DAILY ANALYSIS <br>
    Stress Days: {len(stress_days)} <br>
    Moderate Days: {len(moderate_days)} <br>
    Excess Days: {len(excess_days)} <br><br>

    📅 MONTHLY ANALYSIS <br>
    Stress Months: {len(stress_months)} <br>
    Excess Months: {len(excess_months)} <br><br>

    🚰 NRW ANALYSIS <br>
    High NRW Months: {len(high_nrw)} <br>
    """

    return render_template("index.html", result=result)


if __name__ == "__main__":
    app.run(debug=True)
