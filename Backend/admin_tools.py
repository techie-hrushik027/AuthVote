import pymysql, secrets, sys, os, smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
load_dotenv()

SENDER_EMAIL = os.getenv("EMAIL_SENDER")
SENDER_APP_PASSWORD = os.getenv("EMAIL_PASSWORD")

def get_db(): 
    return pymysql.connect(
        host=os.getenv("DB_HOST"), 
        user=os.getenv("DB_USER"), 
        password=os.getenv("DB_PASSWORD"), 
        database=os.getenv("DB_NAME"), 
        cursorclass=pymysql.cursors.DictCursor
    )

def send_real_email(recipient, name, pin):
    try:
        msg = MIMEText(f"Hello {name},\n\nYour highly secure MIT-WPU Election PIN is: {pin}\n\nDo not share this with anyone. The admin team cannot recover this PIN if lost.")
        msg['Subject'] = 'Your Official AuthVote Election PIN'
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print(f"[!] Failed to send email to {recipient}: {e}")

def execute_action(action):
    db = get_db()
    try:
        with db.cursor() as cursor:
            if action == "email":
                cursor.execute("SELECT voter_id, name, email FROM VoterRegistry WHERE hashed_pin = 'PENDING'")
                voters = cursor.fetchall()
                if not voters:
                    print("\n No pending voters found. Everyone is secured.")
                    return
                print("\n Generating Cryptographic PINs and Sending Emails...")
                for v in voters:
                    pin = ''.join(secrets.choice("0123456789") for _ in range(4))
                    cursor.execute("UPDATE VoterRegistry SET hashed_pin = SHA2(%s, 256) WHERE voter_id = %s", (pin, v['voter_id']))
                    send_real_email(v['email'], v['name'], pin)
                    print(f"\n REAL EMAIL SENT -> To: {v['email']}")
                db.commit()

            elif action == "start":
                cursor.execute("UPDATE ElectionState SET state = 'ACTIVE' WHERE id = 1")
                db.commit()
                print("\n ELECTION STATE: ACTIVE. The FastAPI Server will now accept logins.")

            elif action == "end":
                cursor.execute("UPDATE ElectionState SET state = 'ENDED' WHERE id = 1")
                cursor.execute("SELECT c.name, COUNT(v.vote_id) as vote_count FROM CandidateRegistry c LEFT JOIN VoteBox v ON c.candidate_id = v.candidate_id GROUP BY c.candidate_id")
                results = cursor.fetchall()
                file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Admin_Console", "live_results.txt")
                with open(file_path, "w") as f:
                    for r in results: f.write(f"{r['name']},{r['vote_count']}\n")
                db.commit()
                print("\n ELECTION STATE: ENDED. Polls closed. Data piped to C++ Engine.")

            elif action == "reset_voters":
                cursor.callproc('sp_reset_election')
                db.commit()
                print("\n All voters and votes wiped.We are ready for a fresh election setup.")

            elif action == "reset_candidates":
                cursor.callproc('sp_reset_candidates')
                db.commit()
                print("\n CANDIDATES WIPED. Ready for new election setup.")

            elif action == "add_voter":
                print("\n--- ENTER NEW SINGLE VOTER ---")
                prn = input("Enter PRN: ")
                name = input("Enter Full Name: ")
                email = input("Enter Email: ")
                dob = input("Enter DOB (YYYY-MM-DD) or press enter to skip: ") or None
                mother = input("Enter Mother's First Name or press enter to skip: ") or None
                father = input("Enter Father's First Name or press enter to skip: ") or None
                bg = input("Enter Blood Group (e.g. O+) or press enter to skip: ") or None
                city = input("Enter City or press enter to skip: ") or None
                aadhar = input("Enter Aadhar Last 4 Digits or press enter to skip: ") or None
                sql = "INSERT INTO VoterRegistry (prn, name, email, dob, mother_name, father_name, blood_group, city, aadhar_last_4, hashed_pin) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'PENDING')"
                cursor.execute(sql, (prn, name, email, dob, mother, father, bg, city, aadhar))
                db.commit()
                print(f"\n✅ Voter '{name}' added successfully! Status is PENDING. Run Option [7] to email their PIN.")

            elif action == "add_candidates":
                print("\n ENTER NEW CANDIDATES ->")
                n = int(input("Enter number of candidates to insert: "))
                for i in range(n):
                    print(f"\nEnter details for Candidate {i+1}:")
                    cid = input("Enter Candidate ID (e.g., 1, 2, 3): ")
                    name = input("Enter Candidate Name: ")
                    council = input("Enter Council (e.g., Engineering): ")
                    cursor.execute("INSERT INTO CandidateRegistry (candidate_id, name, council) VALUES (%s, %s, %s)", (cid, name, council))
                db.commit()
                print(f"\n✅ {n} Candidates successfully added to the database.")
    finally: db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1: execute_action(sys.argv[1])