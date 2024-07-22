import os
import random
import subprocess
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from .database import get_db_connection
import boto3
from botocore.exceptions import NoCredentialsError

app = FastAPI()

class UserProfile(BaseModel):
    username: str
    email: str
    bio: str

class CronJob(BaseModel):
    name: str
    command: str
    schedule: str

s3 = boto3.client('s3')

# Mount the static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("templates/index.html") as f:
        return HTMLResponse(content=f.read(), status_code=200)

@app.post("/create_profile/")
async def create_profile(profile: UserProfile):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Generate a unique random integer ID
    while True:
        profile_id = random.randint(1, 1000000)  # Adjust the range as needed
        cursor.execute("SELECT 1 FROM user_profiles WHERE id = %s", (profile_id,))
        if cursor.fetchone() is None:
            break

    cursor.execute(
        "INSERT INTO user_profiles (id, username, email, bio) VALUES (%s, %s, %s, %s)",
        (profile_id, profile.username, profile.email, profile.bio)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Profile created successfully", "id": profile_id}

@app.get("/profiles/")
async def get_profiles():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, bio FROM user_profiles")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    profile = [{"id": row[0], "username": row[1], "email": row[2], "bio": row[3]} for row in rows]
    print(profile)  # Print the profiles to the console
    return {"profiles": profile}

@app.post("/upload_file/")
async def upload_file(file: bytes, filename: str):
    try:
        s3.put_object(Bucket='your_bucket_name', Key=filename, Body=file)
    except NoCredentialsError:
        raise HTTPException(status_code=400, detail="Credentials not available")
    return {"message": "File uploaded successfully"}

@app.get("/dashboard_data/")
async def get_dashboard_data():
    # Example data; replace with actual logic
    data = {
        "profiles_count": 100,
        "average_age": 30
    }
    return data

@app.get("/cron_jobs/")
async def get_cron_jobs():
    cron_jobs = []
    try:
        with open('cron_jobs.txt', 'r') as f:
            for line in f:
                parts = line.strip().split(';')
                if len(parts) == 4:
                    cron_jobs.append({
                        'name': parts[0],
                        'command': parts[1],
                        'schedule': parts[2],
                        'status': parts[3]
                    })
    except FileNotFoundError:
        return {"cron_jobs": []}
    return {"cron_jobs": cron_jobs}

@app.post("/create_cron_job/")
async def create_cron_job(cron_job: CronJob):
    cron_entry = f"{cron_job.schedule} {cron_job.command}\n"
    try:
        with open('cron_jobs.txt', 'a') as f:
            f.write(f"{cron_job.name};{cron_job.command};{cron_job.schedule};Pending\n")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create cron job")
    
    # Save the job in the system's crontab
    try:
        with open('temp_cron', 'w') as f:
            subprocess.run(['crontab', '-l'], stdout=f, stderr=subprocess.PIPE)
            f.write(cron_entry)
        subprocess.run(['crontab', 'temp_cron'], check=True)
        os.remove('temp_cron')
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail="Failed to update crontab")

    return {"message": "Cron job created successfully"}

@app.post("/run_cron_job/")
async def run_cron_job(name: str):
    try:
        with open('cron_jobs.txt', 'r') as f:
            lines = f.readlines()
        
        with open('cron_jobs.txt', 'w') as f:
            for line in lines:
                if line.startswith(name):
                    f.write(f"{line.strip().split(';')[0]};{line.strip().split(';')[1]};{line.strip().split(';')[2]};Running\n")
                else:
                    f.write(line)
        
        # Execute the cron job command immediately
        cron_command = [line.strip().split(';')[1] for line in lines if line.startswith(name)][0]
        subprocess.run(cron_command, shell=True, check=True)
        
        return {"message": "Cron job executed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to execute cron job")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)