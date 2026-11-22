from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html, get_swagger_ui_oauth2_redirect_html
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.users.router import router as UserRouter
from app.taskflow.router import router as TFRouter

import swagger_ui_bundle
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)
app.openapi_version="3.0.2"
app.include_router(UserRouter)
app.include_router(TFRouter)

app.mount(
    "/static-swagger",
    StaticFiles(directory=swagger_ui_bundle.swagger_ui_path),
    name="static-swagger",
)


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static-swagger/swagger-ui-bundle.js",
        swagger_css_url="/static-swagger/swagger-ui.css",
    )

@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()

@app.get("/")
def index():
    return {"message": "Hello strager"}