from pymongo import MongoClient
from config import MONGO_URI, DB_NAME


class Database:

    def __init__(self):
        self.client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=3000
        )

        # Check database connection
        self.client.admin.command("ping")

        self.db = self.client[DB_NAME]

        self.jobs = self.db["jobs"]
        self.candidates = self.db["candidates"]
        self.applications = self.db["applications"]

    def add_job(self, job):
        self.jobs.insert_one(job)

    def get_jobs(self):
        return list(self.jobs.find({}, {"_id": 0}))

    def add_candidate(self, candidate):
        self.candidates.insert_one(candidate)

    def get_candidate(self, candidate_id):
        return self.candidates.find_one(
            {"candidate_id": candidate_id},
            {"_id": 0}
        )

    def search_jobs(self, keyword):
        return list(self.jobs.find({
            "$or": [
                {"title": {"$regex": keyword, "$options": "i"}},
                {"company": {"$regex": keyword, "$options": "i"}},
                {"location": {"$regex": keyword, "$options": "i"}},
                {"skills": {"$regex": keyword, "$options": "i"}}
            ]
        }, {"_id": 0}))

    def close(self):
        self.client.close()