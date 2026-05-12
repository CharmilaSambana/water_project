from flask import Flask, render_template, request
import pandas as pd
import pdfplumber

app = Flask(__name__)

# ----------------------
# DETECT YEAR FUNCTION
# ----------------------
def detect_year(df):
    for col in df.columns:
        try:
            temp = pd.to_datetime(df[col], errors="coerce")
            years = temp.dt.year.dropna()
            if len(years) > 0:
                return int(years.mode()[0])
        except:
            continue
    return 2023  # fallback


# ----------------------
# PROCESS DATA FUNCTION
# ----------------------
def process_dataframe(df):

    df = df.dropna(how="all").reset_index(drop=True)
    all_data = []

    # Convert all column names to string
    df.columns = df.columns.astype(str)

    year_value = detect_year(df)

    # 🔍 FIND ALL INFLOW & OUTFLOW COLUMNS
    inflow_cols = [col for col in df.columns if "inflow" in col.lower()]
    outflow_cols = [col for col in df.columns if "out" in col.lower()]

    # Assume date columns are just before inflow columns
    for i in range(len(inflow_cols)):

        try:
            inflow_col = inflow_cols[i]
            outflow_col = outflow_cols[i]

            # Try to get corresponding date column
            inflow_index = df.columns.get_loc(inflow_col)
            date_col = df.columns[inflow_index - 1]

            temp = df[[date_col, inflow_col, outflow_col]].copy()
            temp.columns = ["Date", "Inflow", "Outflow"]

            # Convert day
            temp["Date"] = pd.to_numeric(temp["Date"], errors="coerce")

            # Assign proper date
            temp["Date"] = pd.to_datetime({
                "year": year_value,
                "month": i + 1,
                "day": temp["Date"]
            }, errors="coerce")

            temp["Inflow"] = pd.to_numeric(temp["Inflow"], errors="coerce")
            temp["Outflow"] = pd.to_numeric(temp["Outflow"], errors="coerce")

            temp = temp.dropna()

            if len(temp) > 10:
                all_data.append(temp)

        except:
            continue

    if len(all_data) > 0:
        return pd.concat(all_data, ignore_index=True)

    return None
    
@app.route("/upload", methods=["POST"])
def upload():
    try:
        file = request.files["file"]
        filename = file.filename.lower()

        # ----------------------
        # READ FILE
        # ----------------------
        if filename.endswith(".xlsx") or filename.endswith(".xls"):
            df = pd.read_excel(file)

        elif filename.endswith(".csv"):
            df = pd.read_csv(file)

        elif filename.endswith(".pdf"):
            data = []
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    table = page.extract_table()
                    if table:
                        for row in table:
                            data.append(row)

            df = pd.DataFrame(data)

        else:
            return "❌ Unsupported file format"

        # ----------------------
        # PROCESS DATA
        # ----------------------
        df = process_dataframe(df)

        if df is None or len(df) == 0:
            return "❌ Could not extract valid data from file"

        # ----------------------
        # ANALYSIS
        # ----------------------
        df["Balance"] = df["Inflow"] - df["Outflow"]

        stress = len(df[df["Balance"] < 0])
        excess = len(df[df["Balance"] >= 0])
        moderate = len(df[(df["Balance"] >= -5) & (df["Balance"] <= 5)])

        df["Month"] = df["Date"].dt.to_period("M").astype(str)

        monthly = df.groupby("Month").agg({
            "Inflow": "sum",
            "Outflow": "sum"
        }).reset_index()

        monthly["Balance"] = monthly["Inflow"] - monthly["Outflow"]

        stress_months = monthly[monthly["Balance"] < 0]["Month"].tolist()
        excess_months = monthly[monthly["Balance"] >= 0]["Month"].tolist()

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

        📅 Stress Months: {len(stress_months)} → {stress_months} <br>
        📅 Excess Months: {len(excess_months)} → {excess_months}
        """

        return render_template("index.html", result=result)

    except Exception as e:
        return f"❌ ERROR: {str(e)}"


if __name__ == "__main__":
    app.run(debug=True)
