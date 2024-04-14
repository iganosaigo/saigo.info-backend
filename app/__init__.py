__version__ = "0.0.1"

from app.api import routes
from app.core.config import settings
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware


def create_app() -> FastAPI:
    description = """
    SaigoBlog api backend
    Simple API with FastAPI and SqlAlchemy
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=description,
        version=__version__,
        license_info={
            "name": "GPLv3",
            "url": "https://www.gnu.org/licenses/gpl-3.0.en.html",
        },
        openapi_url=settings.OPENAPI_URI,
        docs_url=settings.DOC_URL,
        redoc_url=settings.REDOC_URL,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins="*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(routes.api_router, prefix=settings.API_URL)

    return app
