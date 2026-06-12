from flask import Flask, render_template, request
import pandas as pd
import pdfplumber

app = Flask(__name__)

# ----------------------
# HOME ROUTE (IMPORTANT)
# ----------------------
@app.route("/")
def home():
    return render_template("index.html")


# ----------------------
# DETECT YEAR
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
    return 2023


# ----------------------
# PROCESS DATA
# ----------------------

def process_dataframe(df):

    df = df.iloc[3:].reset_index(drop=True)
    df.columns = df.columns.astype(str)

    all_data = []
    year = 2017  # change per file if needed

    # 🔥 LOOP ALL MONTH BLOCKS
    col_index = 0
    month = 1

    while col_index + 5 < len(df.columns):

        try:
            date_col = df.columns[col_index]
            inflow_col = df.columns[col_index + 3]
            outflow_col = df.columns[col_index + 5]

            temp = df[[date_col, inflow_col, outflow_col]].copy()
            temp.columns = ["Date", "Inflow", "Outflow"]

            # CLEAN
            temp["Date"] = pd.to_numeric(temp["Date"], errors="coerce")

            temp["Date"] = pd.to_datetime({
                "year": year,
                "month": month,
                "day": temp["Date"]
            }, errors="coerce")

            temp["Inflow"] = pd.to_numeric(temp["Inflow"], errors="coerce")
            temp["Outflow"] = pd.to_numeric(temp["Outflow"], errors="coerce")

            temp = temp.dropna()

            if len(temp) > 5:
                all_data.append(temp)

        except:
            pass

        col_index += 6   # move to next month block
        month += 1

    if len(all_data) > 0:
        return pd.concat(all_data, ignore_index=True)

    return None

# ----------------------
# UPLOAD ROUTE
# ----------------------
@app.route("/upload", methods=["POST"])
def upload():
    try:
        file = request.files["file"]
        filename = file.filename.lower()

        # READ FILE
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
            return render_template("index.html", error="❌ Unsupported file")

        # PROCESS
        df = process_dataframe(df)

        if df is None or len(df) == 0:
            return render_template("index.html", error="❌ No valid data")

        # ANALYSIS
        df["Balance"] = df["Inflow"] - df["Outflow"]

        stress = len(df[df["Balance"] < 0])
        moderate = len(df[(df["Balance"] >= -5) & (df["Balance"] <= 5)])
        excess = len(df[df["Balance"] > 5])

        df["Month"] = df["Date"].dt.to_period("M").astype(str)

        monthly = df.groupby("Month").agg({
            "Inflow": "sum",
            "Outflow": "sum"
        }).reset_index()

        monthly["Balance"] = monthly["Inflow"] - monthly["Outflow"]

        stress_months = monthly[monthly["Balance"] < 0]["Month"].tolist()
        moderate_months = monthly[(monthly["Balance"] >= -5) & (monthly["Balance"] <= 5)]["Month"].tolist()
        excess_months = monthly[monthly["Balance"] > 5]["Month"].tolist()

        # TOTALS
        total_inflow = round(df["Inflow"].sum(), 2)
        total_outflow = round(df["Outflow"].sum(), 2)
        balance = round(total_inflow - total_outflow, 2)

        # SEND CLEAN DATA (NO STRING FORMAT)
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
                               excess_months=excess_months
                               )

    except Exception as e:
        return render_template("index.html", error=str(e))


# ----------------------
# RUN
# ----------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
