from flask import Flask, render_template, request
import pandas as pd
import os

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():
    result = None

    if request.method == "POST":
        file = request.files.get("file")

        if file:
            try:
                # Read Excel (skip top unwanted rows)
                df = pd.read_excel(file, skiprows=3)

                # Rename required columns (based on your file structure)
                df = df.rename(columns={
                    df.columns[6]: "Inflow",
                    df.columns[11]: "Outflow",
                    df.columns[0]: "Date"
                })

                # Keep only required columns
                df = df[["Date", "Inflow", "Outflow"]]

                # Remove empty rows
                df = df.dropna(subset=["Inflow", "Outflow"])

                # Convert to numeric (safety)
                df["Inflow"] = pd.to_numeric(df["Inflow"], errors="coerce")
                df["Outflow"] = pd.to_numeric(df["Outflow"], errors="coerce")

                # Drop invalid rows
                df = df.dropna()

                # Calculate balance
                df["Balance"] = df["Inflow"] - df["Outflow"]

                # Classification
                stress = df[df["Balance"] < 0]
                excess = df[df["Balance"] > 0]

                # Convert Date column
                df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

                # Monthly summary
                monthly = df.groupby(df["Date"].dt.to_period("M")).sum(numeric_only=True)

                # Prepare result output
                result = f"""
                ✅ Total Records: {len(df)} <br>
                🔴 Stress Days: {len(stress)} <br>
                🟢 Excess Days: {len(excess)} <br><br>

                📊 Monthly Analysis (first 5 rows): <br>
                {monthly.head().to_html()}
                """

            except Exception as e:
                result = f"❌ Error: {str(e)}"

    return render_template("index.html", result=result)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
