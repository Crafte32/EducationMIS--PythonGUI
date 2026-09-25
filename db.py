import sys
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

class SchoolDatabase:
    def __init__(self, uri="mongodb://localhost:27017/", db_name="school_mis_pro"):
        try:
            self.client = MongoClient(uri, serverSelectionTimeoutMS=2000)
            self.db = self.client[db_name]
            self.students = self.db["students"]
            self.teachers = self.db["teachers"]
            self.client.server_info()
            print("Connected to MongoDB successfully!")
            self.repair_database()
        except Exception as e:
            print(f"Database Connection Error: {e}")
            sys.exit(1)

    def repair_database(self):
        default_months = [
            {"month": m, "status": "Unpaid"} for m in 
            ["January", "February", "March", "April", "May", "June", 
             "July", "August", "September", "October", "November", "December"]
        ]
        self.teachers.update_many(
            {"salary_records": {"$exists": False}},
            {"$set": {"salary_records": default_months}}
        )
        self.students.update_many(
            {"payment_history": {"$exists": False}},
            {"$set": {"payment_history": []}}
        )

    def add_student(self, data):
        if "payment_history" not in data:
            data["payment_history"] = []
        return self.students.insert_one(data)

    def get_students(self, query={}):
        return list(self.students.find(query))

    def update_student(self, student_id, data):
        return self.students.update_one({"_id": ObjectId(student_id)}, {"$set": data})

    def delete_student(self, student_id):
        return self.students.delete_one({"_id": ObjectId(student_id)})

    def record_student_payment(self, student_id, payment_amount, new_due):
        now = datetime.now()
        payment_entry = {
            "timestamp": now,
            "year": now.year,
            "month": now.strftime("%B"),
            "amount": payment_amount
        }
        return self.students.update_one(
            {"_id": ObjectId(student_id)},
            {
                "$set": {"fees_due": new_due},
                "$push": {"payment_history": payment_entry}
            }
        )

    def add_teacher(self, data):
        if "salary_records" not in data:
            default_months = [
                {"month": m, "status": "Unpaid"} for m in 
                ["January", "February", "March", "April", "May", "June", 
                 "July", "August", "September", "October", "November", "December"]
            ]
            data["salary_records"] = default_months
        return self.teachers.insert_one(data)

    def get_teachers(self, query={}):
        return list(self.teachers.find(query))

    def update_teacher(self, teacher_id, data):
        return self.teachers.update_one({"_id": ObjectId(teacher_id)}, {"$set": data})

    def delete_teacher(self, teacher_id):
        return self.teachers.delete_one({"_id": ObjectId(teacher_id)})