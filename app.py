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

        # CLEAN COLUMNS
        df.columns = df.columns.str.strip()

        # SAFE CHECK (PREVENT CRASH)
        if len(df.columns) < 3:
            return "❌ Excel must have at least 3 columns (Date, Inflow, Outflow)"

        # MANUAL SAFE MAPPING (NO GUESS CRASH)
        df = df.rename(columns={
            df.columns[0]: "Date",
            df.columns[1]: "Inflow",
            df.columns[2]: "Outflow"
        })

        # DATE FIX
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.dropna(subset=["Date"])

        # ANALYSIS
        df["Balance"] = df["Inflow"] - df["Outflow"]

        stress = len(df[df["Balance"] < 0])
        excess = len(df[df["Balance"] >= 0])
        moderate = len(df[(df["Balance"] >= -5) & (df["Balance"] <= 5)])

        # MONTHLY
        df["Month"] = df["Date"].dt.to_period("M").astype(str)

        monthly = df.groupby("Month").sum(numeric_only=True).reset_index()

        total_inflow = df["Inflow"].sum()
        total_outflow = df["Outflow"].sum()
        balance = total_inflow - total_outflow

        result = f"""
        📊 TOTAL RECORDS: {len(df)} <br><br>

        Total Inflow: {total_inflow} <br>
        Total Outflow: {total_outflow} <br>
        Balance: {balance} <br><br>

        🌊 Stress Days: {stress} <br>
        ⚖ Moderate Days: {moderate} <br>
        ✅ Excess Days: {excess}
        """

        return render_template("index.html", result=result)

    except Exception as e:
        return f"❌ ERROR: {str(e)}"


if __name__ == "__main__":
    app.run(debug=True)
