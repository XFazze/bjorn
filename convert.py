import sqlite3
conn = sqlite3.connect('data/league.sqlite')
cursor = conn.cursor()

ranks_mmr_new = [0,700,800,900,1000,1100,1200,1300,1400,1500,1600,1700,1800,1900,2000,2100,2200,2300,2400,2500,2600,2700,2800,2900,3000]
ranks_mmr_old = [0,750,800,850,900,950,1000,1050,1100,1150,1200,1250,1300,1350,1400,1450,1500,1550,1600,1650,1700,1750,1800,1850,1900,5000000000]

def old_to_new_mmr(mmr):
    for i in range(len(ranks_mmr_new)):
        if mmr < ranks_mmr_old[1]:
            temp = mmr/ranks_mmr_old[1]
            new_mmr = temp*ranks_mmr_new[1]
            return int(new_mmr)
        if mmr >= ranks_mmr_old[i] and mmr < ranks_mmr_old[i+1]:
            #print("temp =", mmr, ranks_mmr_old[i])
            temp = mmr - ranks_mmr_old[i]
            new_mmr = (temp*2) + ranks_mmr_new[i]
            return new_mmr

cursor.execute("SELECT discord_id, mmr, timestamp FROM mmr_history")

rows = cursor.fetchall()
for row in rows:
    discord_id = row[0]
    mmr = row[1]
    timestampen = row[2]
    if timestampen < "2024-04-10 19:00:00.000000":
        new_mmr = old_to_new_mmr(mmr)
        cursor.execute("UPDATE mmr_history SET mmr = ? WHERE discord_id = ? AND timestamp = ?", (new_mmr, discord_id,timestampen))
        #print(mmr, new_mmr)

conn.commit()
cursor.close()
conn.close()