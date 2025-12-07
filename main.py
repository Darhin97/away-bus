from asyncio import tasks
from contextlib import asynccontextmanager
from rich import print, panel

from scalar_fastapi import get_scalar_api_reference
from fastapi import FastAPI, BackgroundTasks
from starlette.middleware.cors import CORSMiddleware

from api.router import master_router
from core.exceptions import add_exception_handlers
from database.session import create_db_tables
from services.notification import NotificationService


@asynccontextmanager
async def lifespan_handler(app: FastAPI):
    print(panel.Panel("server started", border_style="green"))
    await create_db_tables()
    yield
    print(panel.Panel("server stopped", border_style="red"))


app = FastAPI(
    title="Fastship Api",
    description="Delivery management system for sellers and delivery agents",
    docs_url=None,  # disables auto generated docs
    redoc_url=None,  # disables auto generated redocs
    version="0.1.0",
)


# CORS MIDDLEWARE
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
)


# router for all endpoints
app.include_router(master_router)

# add custom exception
add_exception_handlers(app)


# server running status
@app.get("/")
async def root():
    return {"message": "Server is running...."}


# @app.get("/mail")
# async def send_test_mail(tasks: BackgroundTasks):
#     tasks.add_task(
#         NotificationService().send_email(
#             recipients=["johnbrownn1900@gmail.com"],
#             subject="Test Mail",
#             body="You shouldn't be interested in every body",
#         )
#     )
#
#     return {"detail": "Mail sent for ✅"}


# scalar docs
@app.get("/docs", include_in_schema=False)
async def get_scalar():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title="Scalar API",
    )
