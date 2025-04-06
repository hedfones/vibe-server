import logging
from contextlib import asynccontextmanager

import structlog
import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from endpoints.assistant import router as assistant_router
from endpoints.auth import router as auth_router
from endpoints.conversation import router as conversation_router
from endpoints.emails import process_all_unread_emails_in_business_inbox
from endpoints.emails import router as emails_router
from endpoints.files import router as files_router
from endpoints.notions import router as notion_router  # or from endpoints.notation.py if you prefer
from source.utils import db

scheduler = AsyncIOScheduler()


async def scheduled_task() -> dict[int, dict[str, int]]:
    # Replace with your function call
    business_list = db.get_scheduled_services(service_type="email_draft")
    return_values: dict[int, dict[str, int]] = {}
    for business in business_list:
        drafts_created_count = process_all_unread_emails_in_business_inbox(business, action="draft")
        return_values[business.id] = {"drafts_created": drafts_created_count}
    return return_values


@asynccontextmanager
async def lifespan(_: FastAPI):
    _ = scheduler.add_job(scheduled_task, "interval", minutes=1)  # Adjust the interval as needed
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # "http://localhost:8080",
        # "https://app.hedfones.com",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(conversation_router, prefix="/conversation", tags=["conversation"])
app.include_router(files_router, prefix="/files", tags=["files"])
app.include_router(notion_router, prefix="/notion", tags=["notion"])
app.include_router(assistant_router, prefix="/assistant", tags=["assistant"])
app.include_router(emails_router, prefix="/emails", tags=["emails"])

structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
