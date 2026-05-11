import pandas as pd
import mysql.connector
import os

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="water_db"
)

cursor = db.cursor()

print("🚀 Starting Import...\n")

for file in os.listdir("."):
    if file.endswith(".xlsx"):
        print("📂 Reading:", file)

        df = pd.read_excel(file, skiprows=4, header=None)

        for i in range(len(df)):
            row = df.iloc[i]

            try:
                date = row[0]

                # Skip invalid date
                if pd.isna(date):
                    continue

                # Convert safely
                inflow = pd.to_numeric(row[5], errors='coerce')
                outflow = pd.to_numeric(row[6], errors='coerce')

                # Skip if values missing
                if pd.isna(inflow) or pd.isna(outflow):
                    continue

                evaporation = 0
                waste = 0

                # 🔥 DEBUG PRINT (VERY IMPORTANT)
                print(date, inflow, outflow)

                sql = """
                INSERT INTO water_data (date, inflow, outflow, evaporation, waste)
                VALUES (%s, %s, %s, %s, %s)
                """

                cursor.execute(sql, (date, inflow, outflow, evaporation, waste))

            except Exception as e:
                print("❌ Error row:", e)

db.commit()

print("\n🎉 DATA IMPORT COMPLETED!")