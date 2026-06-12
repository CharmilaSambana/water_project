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

    # 🔥 SKIP TOP GARBAGE ROWS
    df = df.iloc[3:].reset_index(drop=True)

    # 🔥 RENAME COLUMNS MANUALLY (BASED ON YOUR FILE)
    df.columns = [
        "Date", "c1", "c2", "Inflow", "c4", "Outflow",
        "c6", "c7", "c8", "c9", "c10", "c11", "c12", "c13"
    ]

    # 🔥 SELECT ONLY REQUIRED
    df = df[["Date", "Inflow", "Outflow"]]

    # 🔥 CLEAN DATA
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Inflow"] = pd.to_numeric(df["Inflow"], errors="coerce")
    df["Outflow"] = pd.to_numeric(df["Outflow"], errors="coerce")

    df = df.dropna()

    return df

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
