schema = {
    "bsonType": "object",
    "required": ["employee_id", "name", "department", "salary", "joining_date", "skills"],
    "properties": {
        "employee_id": {"bsonType": "string"},
        "name": {"bsonType": "string"},
        "department": {"bsonType": "string"},
        "salary": {"bsonType": "double"},
        "joining_date": {"bsonType": "date"},
        "skills": {
            "bsonType": "array",
            "items": {"bsonType": "string"}
        }
    }
}
