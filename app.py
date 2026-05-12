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

        # 🔥 READ EXCEL WITH CORRECT HEADER ROW
        df = pd.read_excel(file, header=2)

        # CLEAN COLUMN NAMES
        df.columns = df.columns.astype(str).str.strip()

        # RENAME BASED ON YOUR FILE
        df = df.rename(columns={
            df.columns[0]: "Date",
            df.columns[1]: "Inflow",
            df.columns[2]: "Outflow"
        })

        # KEEP REQUIRED
        df = df[["Date", "Inflow", "Outflow"]]

        # CLEAN DATA
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df["Inflow"] = pd.to_numeric(df["Inflow"], errors="coerce")
        df["Outflow"] = pd.to_numeric(df["Outflow"], errors="coerce")

        df = df.dropna()

        if len(df) == 0:
            return "❌ No valid data found after cleaning"

        # ----------------------
        # DAILY
        # ----------------------
        df["Balance"] = df["Inflow"] - df["Outflow"]

        stress = len(df[df["Balance"] < 0])
        excess = len(df[df["Balance"] >= 0])
        moderate = len(df[(df["Balance"] >= -5) & (df["Balance"] <= 5)])

        # ----------------------
        # MONTHLY
        # ----------------------
        df["Month"] = df["Date"].dt.to_period("M").astype(str)

        monthly = df.groupby("Month").agg({
            "Inflow": "sum",
            "Outflow": "sum"
        }).reset_index()

        monthly["Balance"] = monthly["Inflow"] - monthly["Outflow"]

        stress_months = len(monthly[monthly["Balance"] < 0])
        excess_months = len(monthly[monthly["Balance"] >= 0])

        # ----------------------
        # TOTAL
        # ----------------------
        total_inflow = df["Inflow"].sum()
        total_outflow = df["Outflow"].sum()
        balance = total_inflow - total_outflow

        # ----------------------
        # RESULT
        # ----------------------
        result = f"""
        📊 TOTAL RECORDS: {len(df)} <br><br>

        Total Inflow: {total_inflow} <br>
        Total Outflow: {total_outflow} <br>
        Balance: {balance} <br><br>

        🌊 Stress Days: {stress} <br>
        ⚖ Moderate Days: {moderate} <br>
        ✅ Excess Days: {excess} <br><br>

        📅 Stress Months: {stress_months} <br>
        📅 Excess Months: {excess_months}
        """

        return render_template("index.html", result=result)

    except Exception as e:
        return f"❌ ERROR: {str(e)}"


if __name__ == "__main__":
    app.run(debug=True)
