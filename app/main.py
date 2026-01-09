from fastapi import FastAPI
from celery.signals import setup_logging as celery_setup_logging

from app.core.logging_config import setup_logging
from app.core.celery_app import celery_app
from app.schemas import MediaRequest
from app.tasks import orchestrator

setup_logging()

app = FastAPI()


@celery_setup_logging.connect
def on_celery_setup_logging(**kwargs):
    setup_logging()


@app.post("/process_media")
def process_media(data: MediaRequest):
    task = orchestrator.delay(data.model_dump(mode="json"))

    return {"task_id": task.id, "status": "accepted"}
