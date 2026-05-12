from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():

    try:
        file = request.files["file"]
        df = pd.read_excel(file)

        # -----------------------------
        # CLEAN COLUMN NAMES
        # -----------------------------
        df.columns = df.columns.str.strip()

        # -----------------------------
        # SAFE COLUMN DETECTION
        # -----------------------------
        date_col = df.columns[0]

        inflow_col = [c for c in df.columns if "Inflow" in c or "Inflows" in c][0]
        outflow_col = [c for c in df.columns if "Out" in c][0]

        df = df.rename(columns={
            date_col: "Date",
            inflow_col: "Inflow",
            outflow_col: "Outflow"
        })

        # -----------------------------
        # DATE HANDLING
        # -----------------------------
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.dropna(subset=["Date"])

        # -----------------------------
        # DAILY ANALYSIS
        # -----------------------------
        df["Balance"] = df["Inflow"] - df["Outflow"]

        stress_days = df[df["Balance"] < 0]
        excess_days = df[df["Balance"] >= 0]
        moderate_days = df[(df["Balance"] >= -5) & (df["Balance"] <= 5)]

        # -----------------------------
        # MONTHLY ANALYSIS
        # -----------------------------
        df["Month"] = df["Date"].dt.to_period("M").astype(str)

        monthly = df.groupby("Month").agg({
            "Inflow": "sum",
            "Outflow": "sum"
        }).reset_index()

        monthly["Balance"] = monthly["Inflow"] - monthly["Outflow"]

        stress_months = monthly[monthly["Balance"] < 0]
        excess_months = monthly[monthly["Balance"] >= 0]

        # -----------------------------
        # WATER BALANCE ENGINE
        # -----------------------------
        total_inflow = df["Inflow"].sum()
        total_outflow = df["Outflow"].sum()
        balance = total_inflow - total_outflow

        # -----------------------------
        # NRW CALCULATION
        # -----------------------------
        monthly["NRW"] = monthly["Outflow"] - monthly["Inflow"]

        high_nrw = monthly[monthly["NRW"] > 0]

        # -----------------------------
        # FINAL OUTPUT
        # -----------------------------
        result = f"""
        📊 TOTAL SUMMARY <br><br>

        Records: {len(df)} <br>
        Total Inflow: {total_inflow} <br>
        Total Outflow: {total_outflow} <br>
        Balance: {balance} <br><br>

        🌊 DAILY <br>
        Stress Days: {len(stress_days)} <br>
        Moderate Days: {len(moderate_days)} <br>
        Excess Days: {len(excess_days)} <br><br>

        📅 MONTHLY <br>
        Stress Months: {len(stress_months)} <br>
        Excess Months: {len(excess_months)} <br><br>

        🚰 NRW <br>
        High NRW Months: {len(high_nrw)}
        """

        return render_template("index.html", result=result)

    except Exception as e:
        return f"❌ SERVER ERROR: {str(e)}"


if __name__ == "__main__":
    app.run(debug=True)
