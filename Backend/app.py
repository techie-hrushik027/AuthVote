from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import pymysql, uuid, os, hashlib
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "Frontend")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def get_db(): 
    return pymysql.connect(
        host=os.getenv("DB_HOST"), 
        user=os.getenv("DB_USER"), 
        password=os.getenv("DB_PASSWORD"), 
        database=os.getenv("DB_NAME"), 
        cursorclass=pymysql.cursors.DictCursor
    )

@app.get("/")
async def read_index(): return FileResponse(os.path.join(FRONTEND_DIR, "login.html"))

@app.get("/{filename}")
async def serve_file(filename: str): 
    if filename == "favicon.ico": return {} 
    path = os.path.join(FRONTEND_DIR, filename)
    if os.path.exists(path): return FileResponse(path)
    raise HTTPException(404, "File not found")

@app.post("/api/login")
async def login(data: dict):
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT state FROM ElectionState WHERE id = 1")
            state = cursor.fetchone()['state']
            if state == 'PENDING': raise HTTPException(403, "Election has not started yet.")
            if state == 'ENDED': raise HTTPException(403, "Election has concluded.")

            # WE ADDED 'has_voted' TO THE SELECT QUERY HERE:
            cursor.execute("""SELECT voter_id, locked_status, has_voted, (hashed_pin = SHA2(%s, 256)) AS is_pin_correct, dob, mother_name, father_name, blood_group, city, aadhar_last_4, email FROM VoterRegistry WHERE prn = %s""", (data.get("pin"), data.get("prn")))
            voter = cursor.fetchone()
            
            if not voter or not voter['is_pin_correct']: raise HTTPException(401, "Invalid PRN or PIN")
            if voter['locked_status'] != 'ACTIVE': raise HTTPException(401, "Account Locked")
            
            # THE NEW FRONT-DOOR BLOCK:
            if voter['has_voted']: raise HTTPException(403, "You have already cast your vote.")
            
            s_id = str(uuid.uuid4())
            cursor.execute("INSERT INTO SessionManagement (session_id, voter_id, rapid_fire_timeout) VALUES (%s, %s, %s)", (s_id, voter['voter_id'], datetime.now() + timedelta(seconds=90)))
            db.commit()
            
            profile = {k: voter[k] for k in ['dob', 'mother_name', 'father_name', 'blood_group', 'city', 'aadhar_last_4', 'email'] if voter[k]}
            return {"session_id": s_id, "voter_id": voter['voter_id'], "profile": profile}
    finally: db.close()

@app.post("/api/violation")
async def log_violation(data: dict):
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("UPDATE VoterRegistry SET violation_count = violation_count + 1 WHERE prn = %s", (data.get("prn"),))
            cursor.execute("SELECT violation_count FROM VoterRegistry WHERE prn = %s", (data.get("prn"),))
            if cursor.fetchone()['violation_count'] >= 3: cursor.callproc('sp_revoke_voter', (data.get("prn"), "Tab Switch/Timeout Limit"))
            db.commit()
    finally: db.close()

@app.get("/api/candidates")
async def get_candidates():
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT candidate_id, name, council FROM CandidateRegistry")
            return cursor.fetchall()
    finally: db.close()

@app.post("/api/cast_vote")
async def cast_vote(data: dict):
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT voter_id FROM VoterRegistry WHERE prn = %s", (data.get("prn"),))
            voter = cursor.fetchone()
            cursor.execute("SELECT session_id FROM SessionManagement WHERE voter_id = %s ORDER BY created_at DESC LIMIT 1", (voter['voter_id'],))
            session = cursor.fetchone()
            receipt = str(uuid.uuid4())
            h = hashlib.sha256(f"{voter['voter_id']}{data.get('candidate_id')}{receipt}".encode()).hexdigest()
            cursor.callproc('sp_cast_vote', (voter['voter_id'], data.get('candidate_id'), session['session_id'], h, receipt))
            db.commit()
            return {"receipt": h}
    finally: db.close()

@app.get("/api/admin/stats")
async def admin_stats():
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT c.name, COUNT(v.vote_id) as votes FROM CandidateRegistry c LEFT JOIN VoteBox v ON c.candidate_id = v.candidate_id GROUP BY c.candidate_id")
            votes = cursor.fetchall()
            cursor.execute("SELECT COUNT(*) as v FROM LoginAudit WHERE action = 'ADMIN_REVOKE'")
            violations = cursor.fetchone()['v']
            cursor.execute("SELECT COUNT(*) as t FROM VoterRegistry")
            total = cursor.fetchone()['t']
            cursor.execute("SELECT COUNT(*) as v FROM VoterRegistry WHERE has_voted = TRUE")
            voted = cursor.fetchone()['v']
            return {"votes": votes, "violations": violations, "total_voters": total, "total_voted": voted}
    finally: db.close()