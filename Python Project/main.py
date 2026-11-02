from database import Database
from pymongo.errors import DuplicateKeyError


try:
    db = Database()
except Exception as error:
    print("Could not connect to MongoDB.")
    print("Make sure MongoDB is installed and running.")
    print("Details:", error)
    raise SystemExit(1)


# Create unique IDs for candidates and jobs
db.candidates.create_index("candidate_id", unique=True)
db.jobs.create_index("job_id", unique=True)
db.applications.create_index(
    [("candidate_id", 1), ("job_id", 1)],
    unique=True
)


def seed_jobs():
    if db.jobs.count_documents({}) == 0:
        sample_jobs = [
            {
                "job_id": "J001",
                "title": "Python Developer",
                "company": "ABC Technologies",
                "skills": "Python, SQL",
                "qualification": "BCA",
                "location": "Chandigarh",
                "salary": 45000
            },
            {
                "job_id": "J002",
                "title": "Data Analyst",
                "company": "DataWorks",
                "skills": "Python, SQL, Excel",
                "qualification": "BCA",
                "location": "Chandigarh",
                "salary": 40000
            },
            {
                "job_id": "J003",
                "title": "Web Developer",
                "company": "Tech Solutions",
                "skills": "HTML, CSS, JavaScript",
                "qualification": "BCA",
                "location": "Mohali",
                "salary": 35000
            }
        ]

        db.jobs.insert_many(sample_jobs)


def view_jobs(jobs=None):
    if jobs is None:
        jobs = db.get_jobs()

    print("\n========== AVAILABLE JOBS ==========")

    if not jobs:
        print("No jobs found.")
        return

    for job in jobs:
        print("\nJob ID:", job["job_id"])
        print("Title:", job["title"])
        print("Company:", job["company"])
        print("Skills:", job["skills"])
        print("Qualification:", job["qualification"])
        print("Location:", job["location"])
        print("Monthly Salary: Rs.", job["salary"])
        print("-" * 40)


def search_jobs():
    keyword = input("Enter title, skill, company or location: ").strip()

    if not keyword:
        print("Please enter a search term.")
        return

    view_jobs(db.search_jobs(keyword))


def register_candidate():
    print("\n========== CANDIDATE REGISTRATION ==========")

    candidate = {
        "candidate_id": input("Candidate ID: ").strip(),
        "name": input("Full name: ").strip(),
        "skills": input("Skills (comma separated): ").strip(),
        "qualification": input("Qualification: ").strip(),
        "experience": 0,
        "location": input("Preferred location: ").strip()
    }

    try:
        candidate["experience"] = int(
            input("Experience in years: ")
        )
    except ValueError:
        print("Experience must be a number.")
        return

    if (
        not candidate["candidate_id"]
        or not candidate["name"]
        or not candidate["skills"]
        or not candidate["qualification"]
        or not candidate["location"]
        or candidate["experience"] < 0
    ):
        print("Please enter valid details in all fields.")
        return

    try:
        db.add_candidate(candidate)
        print("Candidate registered successfully!")
    except DuplicateKeyError:
        print("This Candidate ID already exists.")


def post_job():
    print("\n========== POST NEW JOB ==========")

    job = {
        "job_id": input("Job ID: ").strip(),
        "title": input("Job title: ").strip(),
        "company": input("Company: ").strip(),
        "skills": input("Required skills: ").strip(),
        "qualification": input("Qualification: ").strip(),
        "location": input("Location: ").strip()
    }

    try:
        job["salary"] = int(input("Monthly salary: "))
    except ValueError:
        print("Salary must be a number.")
        return

    if not all([
        job["job_id"],
        job["title"],
        job["company"],
        job["skills"],
        job["qualification"],
        job["location"]
    ]) or job["salary"] < 0:
        print("Please enter valid job details.")
        return

    try:
        db.add_job(job)
        print("Job posted successfully!")
    except DuplicateKeyError:
        print("This Job ID already exists.")


def apply_for_job():
    candidate_id = input("Candidate ID: ").strip()
    job_id = input("Job ID: ").strip()

    candidate = db.get_candidate(candidate_id)
    job = db.jobs.find_one({"job_id": job_id})

    if not candidate:
        print("Candidate not found. Register first.")
        return

    if not job:
        print("Job not found.")
        return

    application = {
        "candidate_id": candidate_id,
        "job_id": job_id,
        "status": "Pending"
    }

    try:
        db.applications.insert_one(application)
        print("Job application submitted successfully!")
    except DuplicateKeyError:
        print("You have already applied for this job.")


def view_applications():
    candidate_id = input("Enter Candidate ID: ").strip()

    applications = list(
        db.applications.find(
            {"candidate_id": candidate_id},
            {"_id": 0}
        )
    )

    print("\n========== MY APPLICATIONS ==========")

    if not applications:
        print("No applications found.")
        return

    for application in applications:
        job = db.jobs.find_one({
            "job_id": application["job_id"]
        })

        print("Job:", job["title"] if job else "Unknown")
        print("Company:", job["company"] if job else "Unknown")
        print("Status:", application["status"])
        print("-" * 40)


def update_application_status():
    print("\n1. Pending")
    print("2. Shortlisted")
    print("3. Rejected")

    application_id = input("Candidate ID: ").strip()
    job_id = input("Job ID: ").strip()
    choice = input("Select new status: ").strip()

    statuses = {
        "1": "Pending",
        "2": "Shortlisted",
        "3": "Rejected"
    }

    if choice not in statuses:
        print("Invalid status.")
        return

    result = db.applications.update_one(
        {
            "candidate_id": application_id,
            "job_id": job_id
        },
        {"$set": {"status": statuses[choice]}}
    )

    if result.matched_count:
        print("Application status updated!")
    else:
        print("Application not found.")


def find_job_matches():
    candidate_id = input("Enter Candidate ID: ").strip()
    candidate = db.get_candidate(candidate_id)

    if not candidate:
        print("Candidate not found.")
        return

    candidate_skills = {
        skill.strip().lower()
        for skill in candidate["skills"].split(",")
    }

    matches = []

    for job in db.get_jobs():
        job_skills = {
            skill.strip().lower()
            for skill in job["skills"].split(",")
        }

        common = candidate_skills & job_skills
        score = len(common) / max(len(job_skills), 1) * 60

        if candidate["qualification"].lower() == job["qualification"].lower():
            score += 20

        if candidate["location"].lower() == job["location"].lower():
            score += 20

        matches.append((min(round(score, 2), 100), job, common))

    matches.sort(key=lambda item: item[0], reverse=True)

    print("\n========== BEST JOB MATCHES ==========")

    for score, job, common in matches:
        print(job["title"], "-", job["company"])
        print("Match score:", score, "%")
        print("Matching skills:", ", ".join(sorted(common)) or "None")
        print("Location:", job["location"])
        print("-" * 40)


def application_analysis():
    print("\n========== APPLICATION ANALYSIS ==========")

    for job in db.get_jobs():
        count = db.applications.count_documents({
            "job_id": job["job_id"]
        })

        print(job["title"], ":", count, "application(s)")


def main():
    seed_jobs()

    while True:
        print("\n" + "=" * 50)
        print("       JOB PORTAL MANAGEMENT SYSTEM")
        print("=" * 50)

        print("1. View All Jobs")
        print("2. Search Jobs")
        print("3. Register Candidate")
        print("4. Post New Job")
        print("5. Apply For Job")
        print("6. View My Applications")
        print("7. Update Application Status")
        print("8. Find Best Job Matches")
        print("9. Application Analysis")
        print("0. Exit")

        choice = input("\nEnter your choice: ").strip()

        try:
            if choice == "1":
                view_jobs()
            elif choice == "2":
                search_jobs()
            elif choice == "3":
                register_candidate()
            elif choice == "4":
                post_job()
            elif choice == "5":
                apply_for_job()
            elif choice == "6":
                view_applications()
            elif choice == "7":
                update_application_status()
            elif choice == "8":
                find_job_matches()
            elif choice == "9":
                application_analysis()
            elif choice == "0":
                print("Thank you for using Job Portal Management System!")
                break
            else:
                print("Invalid choice.")
        except Exception as error:
            print("Operation failed:", error)


if __name__ == "__main__":
    try:
        main()
    finally:
        db.close()