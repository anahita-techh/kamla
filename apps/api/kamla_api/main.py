from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from kamla_api.api.v1.me import router as me_router
from kamla_api.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title="KAMLA API", version="0.1.0")
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(me_router, prefix="/v1")

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()
