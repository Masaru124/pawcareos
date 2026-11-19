from fastapi import FastAPI

from app.routers import (
    admin,
    appointments,
    auth,
    consults,
    dashboard,
    directory,
    health,
    ops,
    patients,
    portal,
    public,
    rx,
    webhooks,
)

API_PREFIX = "/api/v1"


def create_app() -> FastAPI:
    application = FastAPI(title="PawCare OS API", version="0.1.0")
    for router in (
        health.router,
        auth.router,
        admin.router,
        patients.router,
        portal.router,
        directory.router,
        consults.router,
        rx.router,
        appointments.router,
        dashboard.router,
        ops.router,
        webhooks.router,
    ):
        application.include_router(router, prefix=API_PREFIX)
    application.include_router(public.router)
    return application


app = create_app()
