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

        # READ RAW FILE (NO HEADER)
        df = pd.read_excel(file, header=None)

        # DROP EMPTY ROWS
        df = df.dropna(how="all").reset_index(drop=True)

        # 🔍 FIND HEADER ROW (WHERE "Date" EXISTS)
        header_row = None
        for i in range(len(df)):
            row_text = " ".join(df.iloc[i].astype(str)).lower()
            if "date" in row_text and "inflow" in row_text:
                header_row = i
                break

        if header_row is None:
            return "❌ Header row not found in Excel"

        # SET HEADER
        df.columns = df.iloc[header_row]
        df = df.iloc[header_row + 1:].reset_index(drop=True)

        # CLEAN COLUMN NAMES
        df.columns = df.columns.astype(str).str.strip()

        # 🔍 FIND REQUIRED COLUMNS
        date_col = [c for c in df.columns if "date" in c.lower() or "day" in c.lower()][0]
        inflow_col = [c for c in df.columns if "inflow" in c.lower()][0]
        outflow_col = [c for c in df.columns if "out" in c.lower()][0]

        # EXTRACT REQUIRED DATA
        df = df[[date_col, inflow_col, outflow_col]]
        df.columns = ["Date", "Inflow", "Outflow"]

        # CLEAN VALUES
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df["Inflow"] = pd.to_numeric(df["Inflow"], errors="coerce")
        df["Outflow"] = pd.to_numeric(df["Outflow"], errors="coerce")

        # REMOVE INVALID ROWS
        df = df.dropna()

        if len(df) == 0:
            return "❌ Data extraction failed. No valid rows found."

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
