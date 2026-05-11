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
                # Read Excel safely
                df = pd.read_excel(file, engine="openpyxl")

                # Clean column names (remove spaces)
                df.columns = df.columns.str.strip()

                # Try to detect correct columns automatically
                inflow_col = None
                outflow_col = None
                date_col = None

                for col in df.columns:
                    if "inflow" in col.lower():
                        inflow_col = col
                    elif "out" in col.lower():
                        outflow_col = col
                    elif "date" in col.lower():
                        date_col = col

                # Check required columns
                if not inflow_col or not outflow_col:
                    result = "❌ Could not find Inflow/Outflow columns in Excel"
                    return render_template("index.html", result=result)

                # If no date column, create one
                if not date_col:
                    df["Date"] = pd.date_range(start="2020-01-01", periods=len(df))
                    date_col = "Date"

                # Select needed columns
                df = df[[date_col, inflow_col, outflow_col]]

                # Rename columns
                df.columns = ["Date", "Inflow", "Outflow"]

                # Convert to numeric
                df["Inflow"] = pd.to_numeric(df["Inflow"], errors="coerce")
                df["Outflow"] = pd.to_numeric(df["Outflow"], errors="coerce")

                # Drop invalid rows
                df = df.dropna()

                # Calculate balance
                df["Balance"] = df["Inflow"] - df["Outflow"]

                # Classification
                stress = df[df["Balance"] < 0]
                excess = df[df["Balance"] > 0]

                # Convert Date
                df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

                # Monthly summary
                monthly = df.groupby(df["Date"].dt.to_period("M")).sum(numeric_only=True)

                # Final result
                result = f"""
                <b>Total Records:</b> {len(df)} <br>
                <b>Stress Days:</b> {len(stress)} <br>
                <b>Excess Days:</b> {len(excess)} <br><br>

                <b>Monthly Summary:</b><br>
                {monthly.head().to_html()}
                """

            except Exception as e:
                result = f"❌ Error: {str(e)}"

    return render_template("index.html", result=result)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
