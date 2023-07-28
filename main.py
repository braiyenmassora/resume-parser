from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routers.router import router
import uvicorn, os

app = FastAPI(
    title="TMS Analytics API",
    description="TMS Analytics API",
    version="0.0.1",
    openapi_url="/api/v1/openapi.json",
)

# allow cors requests
# origins = ["local-fe", "localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router)

## RUN!!!
if __name__ == "__main__":
    uvicorn.run(app, port=int(os.environ.get("PORT", 8000)), host="0.0.0.0")
