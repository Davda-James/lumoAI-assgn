from src.auth import verify_token
from fastapi import APIRouter, Body, Request, HTTPException, Query, Depends
from fastapi.encoders import jsonable_encoder
from typing import List
from src.models import employees, employeeUpdate

router = APIRouter(
    prefix="/employees",
    tags=["employees"],
)

@router.post("/", response_description="Add new employee")
async def create_employee(request: Request, employee: employees = Body(...), token_data: dict = Depends(verify_token)):
    employee = jsonable_encoder(employee)
    from datetime import datetime, date
    # Convert joining_date to datetime for MongoDB
    if "joining_date" in employee:
        if isinstance(employee["joining_date"], str):
            employee["joining_date"] = datetime.strptime(employee["joining_date"], "%Y-%m-%d")
        elif isinstance(employee["joining_date"], date):
            employee["joining_date"] = datetime.combine(employee["joining_date"], datetime.min.time())
    try:
        result = request.app.database["employees"].insert_one(employee)
        if result.acknowledged:
            return {"msg": "Employee inserted successfully", "id": str(result.inserted_id)}
        raise HTTPException(status_code=500, detail="Insert failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/avg-salary", response_description="Get average salary by department")
async def get_avg_salary_by_department(request: Request, token_data: dict = Depends(verify_token)):
    try:
        pipeline = [
            {"$group": {"_id": "$department", "average_salary": {"$avg": "$salary"}}},
            {"$project": {"_id": 0, "department": "$_id", "average_salary": 1}}
        ]
        avg_salary_by_dept = list(request.app.database["employees"].aggregate(pipeline))
        return avg_salary_by_dept
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_description="Get employees by department")
async def get_employees_by_department(request: Request, department: str = Query(...)):
    try:
        pipeline = [{"$match": {"department": department}}]
        employees_list = list(request.app.database["employees"].aggregate(pipeline))
        for i in employees_list:
            i["_id"] = str(i["_id"])
            # Convert datetime to ISO string for JSON serialization
            if "joining_date" in i and hasattr(i["joining_date"], "isoformat"):
                i["joining_date"] = i["joining_date"].isoformat()
        return employees_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_description="Search employee based on skills")
async def search_employee_by_skills(request: Request, skills: List[str] = Query(...)):
    try:
        pipeline = [
            {
                "$match": {
                    "$or": [
                        {"skills": {"$regex": skill, "$options": "i"}}
                        for skill in skills
                    ]
                }
            },
            {"$project": {"_id": 0}}
        ]
        employees_list = list(request.app.database["employees"].aggregate(pipeline))

        if not employees_list:
            raise HTTPException(status_code=404, detail="Employee search not found")

        return employees_list

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Optional one
@router.get("/list", response_description="Get all employeed but with pagination")
async def get_employees(request: Request, page: int = Query(1, ge=1), page_size:int = Query(10, ge=1, le=100), token_data: dict = Depends(verify_token)):
    try:
        skip = (page-1)*page_size
        cursor = (
            request.app.database["employees"]
            .find( {}, {"_id": 0} )  
            .skip(skip)
            .limit(page_size)   
        )
        employees_list = list(cursor)

        total_count = request.app.database["employees"].count_documents({})
        total_pages = (total_count + page_size - 1) // page_size
        
        return {
            "page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": total_pages,
            "employees": employees_list
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{employee_id}", response_description="Get a single employee", )
async def get_employee(employee_id: str, request: Request, token_data: dict = Depends(verify_token)):
    try:
        employee = request.app.database["employees"].find_one({"employee_id": employee_id} , {"_id": 0})
        if employee:
            # Convert joining_date to ISO string for JSON serialization
            if "joining_date" in employee and hasattr(employee["joining_date"], "isoformat"):
                employee["joining_date"] = employee["joining_date"].isoformat()
            return employee
        raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{employee_id}", response_description="Update an employee")
async def update_employee(employee_id: str, request: Request, employee: employeeUpdate = Body(...)):
    try:
        from datetime import datetime, date
        update_data = jsonable_encoder(employee, exclude_unset=True)
        if "joining_date" in update_data:
            if isinstance(update_data["joining_date"], str):
                update_data["joining_date"] = datetime.strptime(update_data["joining_date"], "%Y-%m-%d")
            elif isinstance(update_data["joining_date"], date):
                update_data["joining_date"] = datetime.combine(update_data["joining_date"], datetime.min.time())
        if update_data:
            result = request.app.database["employees"].update_one(
                {"employee_id": employee_id}, {"$set": update_data}
            )
            if result.modified_count == 1:
                updated = request.app.database["employees"].find_one({"employee_id": employee_id}, { "_id" : 0})
                if updated:
                    if "joining_date" in updated and hasattr(updated["joining_date"], "isoformat"):
                        updated["joining_date"] = updated["joining_date"].isoformat()
                    return updated
            existing = request.app.database["employees"].find_one({"employee_id": employee_id}, { "_id" : 0})
            if existing and "joining_date" in existing and hasattr(existing["joining_date"], "isoformat"):
                existing["joining_date"] = existing["joining_date"].isoformat()
            return existing
        raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{employee_id}", response_description="Delete an employee")
async def delete_employee(employee_id: str, request: Request, token_data: dict = Depends(verify_token)  ):
    try:
        employee = request.app.database["employees"].find_one({"employee_id": employee_id}, { "_id": 0})
        if employee:
            if "joining_date" in employee and hasattr(employee["joining_date"], "isoformat"):
                employee["joining_date"] = employee["joining_date"].isoformat()
            request.app.database["employees"].delete_one({"employee_id": employee_id})
            return {"msg": "success", "deleted_employee": employee}
        raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
