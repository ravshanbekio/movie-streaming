from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from routes.auth import auth_router
from routes.user import user_router
from admin.routes.admin import admin_router
from admin.routes.genre import genre_router
from admin.routes.content import content_router
from admin.routes.episodes import episode_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
#app.mount("/admin", admin_app)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(admin_router)
app.include_router(genre_router)
app.include_router(content_router)
app.include_router(episode_router)