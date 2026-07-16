"""FastAPI application factory for mydash-web."""

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mydash.api.routers import brief, health


def create_app() -> FastAPI:
    load_dotenv()
    app = FastAPI(
        title="mydash", version="0.5.0", description="Personal API dashboard."
    )

    allow_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        # Production: add concrete deploy origins (e.g. Vercel app URL).
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router=health.router, prefix="/api/v1")
    app.include_router(router=brief.router, prefix="/api/v1")
    # Config API deferred (JSON config → likely SQL later).

    return app


app = create_app()
