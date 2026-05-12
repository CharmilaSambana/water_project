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

        # READ EXCEL (skip top rows)
        df = pd.read_excel(file, header=1)

        # CLEAN COLUMNS
        df.columns = df.columns.str.strip()

        # RENAME IMPORTANT COLUMNS
        df = df.rename(columns={
            "Date": "Date",
            "Inflows (in Cusecs)": "Inflow",
            "Total Out flows (in Cusecs)": "Outflow"
        })

        # KEEP ONLY REQUIRED COLUMNS
        df = df[["Date", "Inflow", "Outflow"]]

        # REMOVE EMPTY ROWS
        df = df.dropna(subset=["Date"])

        # CONVERT DATE
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.dropna(subset=["Date"])

        # CONVERT NUMBERS
        df["Inflow"] = pd.to_numeric(df["Inflow"], errors="coerce")
        df["Outflow"] = pd.to_numeric(df["Outflow"], errors="coerce")

        df = df.dropna(subset=["Inflow", "Outflow"])

        # ----------------------
        # DAILY ANALYSIS
        # ----------------------
        df["Balance"] = df["Inflow"] - df["Outflow"]

        stress_days = df[df["Balance"] < 0]
        excess_days = df[df["Balance"] >= 0]
        moderate_days = df[(df["Balance"] >= -5) & (df["Balance"] <= 5)]

        # ----------------------
        # MONTHLY ANALYSIS
        # ----------------------
        df["Month"] = df["Date"].dt.to_period("M").astype(str)

        monthly = df.groupby("Month").agg({
            "Inflow": "sum",
            "Outflow": "sum"
        }).reset_index()

        monthly["Balance"] = monthly["Inflow"] - monthly["Outflow"]

        stress_months = monthly[monthly["Balance"] < 0]
        excess_months = monthly[monthly["Balance"] >= 0]

        # ----------------------
        # WATER BALANCE
        # ----------------------
        total_inflow = df["Inflow"].sum()
        total_outflow = df["Outflow"].sum()
        total_balance = total_inflow - total_outflow

        # ----------------------
        # NRW
        # ----------------------
        monthly["NRW"] = monthly["Outflow"] - monthly["Inflow"]
        high_nrw = monthly[monthly["NRW"] > 0]

        # ----------------------
        # RESULT
        # ----------------------
        result = f"""
        📊 TOTAL RECORDS: {len(df)} <br><br>

        Total Inflow: {total_inflow} <br>
        Total Outflow: {total_outflow} <br>
        Balance: {total_balance} <br><br>

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
        return f"❌ ERROR: {str(e)}"


if __name__ == "__main__":
    app.run(debug=True)
