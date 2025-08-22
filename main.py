from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from routes.auth import auth_router
from routes.user import user_router
from routes.fcm_token import fcm_token_router
from routes.invoice import invoice_router
from routes.version import version_router

# Admin Side
from admin.routes.admin import admin_router
from admin.routes.genre import genre_router
from admin.routes.content import content_router
from admin.routes.episodes import episode_router
from admin.routes.promocode import promocode_router
from admin.routes.plan import plan_router

#User side
from user.routes.contents import content_router as user_content_router
from user.routes.episode import episode_router as user_episode_router
from user.routes.watch_history import watch_history_router
from user.routes.user_saved import saved_router as user_saved_router
from user.routes.plans import plan_router as user_plan_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# General
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(fcm_token_router)
app.include_router(invoice_router)
app.include_router(version_router)
# Admin
app.include_router(admin_router)
app.include_router(genre_router)
app.include_router(content_router)
app.include_router(episode_router)
app.include_router(promocode_router)
app.include_router(plan_router)
# User
app.include_router(user_content_router)
app.include_router(user_episode_router)
app.include_router(watch_history_router)
app.include_router(user_saved_router)
app.include_router(user_plan_router)