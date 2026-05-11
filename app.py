from flask import Flask, render_template, request
import pandas as pd
import os

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():
    result = None

    if request.method == "POST":
        file = request.files["file"]

        if file:
            try:
                # Read Excel (skip top messy rows)
                df = pd.read_excel(file, skiprows=3)

                # Rename required columns (based on your file structure)
                df = df.rename(columns={
                    df.columns[6]: "Inflow",
                    df.columns[11]: "Outflow"
                })

                # Remove empty rows
                df = df.dropna(subset=["Inflow", "Outflow"])

                # Convert to numeric
                df["Inflow"] = pd.to_numeric(df["Inflow"], errors='coerce')
                df["Outflow"] = pd.to_numeric(df["Outflow"], errors='coerce')

                # Drop invalid rows again
                df = df.dropna(subset=["Inflow", "Outflow"])

                # Calculate balance
                df["Balance"] = df["Inflow"] - df["Outflow"]

                # Classification
                stress = df[df["Balance"] < 0]
                moderate = df[(df["Balance"] >= 0) & (df["Balance"] < 20)]
                excess = df[df["Balance"] >= 20]

                # Result output
                result = f"""
                Total Records: {len(df)} <br>
                ❌ Stress Days: {len(stress)} <br>
                ⚠️ Moderate Days: {len(moderate)} <br>
                ✅ Excess Days: {len(excess)}
                """

            except Exception as e:
                result = f"Error processing file: {str(e)}"

    return render_template("index.html", result=result)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
