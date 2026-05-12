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

        # READ FULL EXCEL
        df = pd.read_excel(file)

        # CLEAN COLUMN NAMES
        df.columns = df.columns.astype(str).str.strip()

        # 🔍 FIND REQUIRED COLUMNS AUTOMATICALLY
        date_col = None
        inflow_col = None
        outflow_col = None

        for col in df.columns:
            col_lower = col.lower()

            if "date" in col_lower or "day" in col_lower:
                date_col = col
            elif "inflow" in col_lower:
                inflow_col = col
            elif "out" in col_lower:
                outflow_col = col

        if not date_col or not inflow_col or not outflow_col:
            return f"❌ Could not detect required columns. Found columns: {list(df.columns)}"

        # RENAME
        df = df.rename(columns={
            date_col: "Date",
            inflow_col: "Inflow",
            outflow_col: "Outflow"
        })

        # KEEP ONLY REQUIRED
        df = df[["Date", "Inflow", "Outflow"]]

        # CLEAN DATA
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df["Inflow"] = pd.to_numeric(df["Inflow"], errors="coerce")
        df["Outflow"] = pd.to_numeric(df["Outflow"], errors="coerce")

        # REMOVE INVALID ROWS
        df = df.dropna()

        # 🚨 IMPORTANT CHECK
        if len(df) == 0:
            return "❌ No valid numeric data found after cleaning. Check Excel format."

        # ----------------------
        # DAILY ANALYSIS
        # ----------------------
        df["Balance"] = df["Inflow"] - df["Outflow"]

        stress = len(df[df["Balance"] < 0])
        excess = len(df[df["Balance"] >= 0])
        moderate = len(df[(df["Balance"] >= -5) & (df["Balance"] <= 5)])

        # ----------------------
        # MONTHLY ANALYSIS
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
