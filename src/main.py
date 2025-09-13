from fastapi import FastAPI, Depends
from pymongo import MongoClient
from dotenv import dotenv_values
from contextlib import asynccontextmanager
from src.routes import router
from src.helper import schema
from fastapi.security import OAuth2PasswordRequestForm

config = dotenv_values(".env")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.mongodb_client = MongoClient(config["MONGO_URI"])
    app.database = app.mongodb_client[config["DB_NAME"]]
    # Ensure unique index on employee_id bonus task
    app.database["employees"].create_index("employee_id", unique=True)
    # schema validation bonus task
    app.database.command({
        "collMod": "employees",
        "validator": {"$jsonSchema": schema},
        "validationLevel": "strict"
    })
    yield
    app.mongodb_client.close()


app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username == config["username"] and form_data.password == config["password"]:
        from src.auth import create_access_token
        access_token = create_access_token(data={"sub": form_data.username})
        return {"access_token": access_token, "token_type": "bearer"}
    else:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )    
    

app.include_router(router)


