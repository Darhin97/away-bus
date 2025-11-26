from asyncio import tasks
from contextlib import asynccontextmanager
from rich import print, panel

from scalar_fastapi import get_scalar_api_reference
from fastapi import FastAPI, BackgroundTasks

from api.router import master_router
from database.session import create_db_tables
from services.notification import NotificationService


@asynccontextmanager
async def lifespan_handler(app: FastAPI):
    print(panel.Panel("server started", border_style="green"))
    await create_db_tables()
    yield
    print(panel.Panel("server stopped", border_style="red"))


app = FastAPI(lifespan=lifespan_handler)


# router
app.include_router(master_router)


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
@app.get("/scalar", include_in_schema=False)
async def get_scalar():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title="Scalar API",
    )
