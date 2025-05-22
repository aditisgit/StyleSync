import pandas as pd
import MySQLdb

# Load CSV
df = pd.read_csv('Final_OutfitRecommendations_With_TshirtColors.csv')

# Connect to DB
conn = MySQLdb.connect(
    host="localhost",
    user="aditi",
    passwd="aditi",  # Replace with your actual password
    db="StyleSync"
)
cursor = conn.cursor()

for index, row in df.iterrows():
    cursor.execute("""
        INSERT INTO OutfitRecommendations (
            Topwear, Bottomwear, Footwear, Accessory,
            Gender, BodyType, SkinTone, AestheticID, OccasionID
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        row['Topwear'], row['Bottomwear'], row['Footwear'], row['Accessory'],
        row['Gender'], row['BodyType'], row['SkinTone'],
        int(row['AestheticID']), int(row['OccasionID'])
    ))

conn.commit()
cursor.close()
conn.close()
print("Data imported successfully.")
