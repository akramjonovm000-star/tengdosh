from aiogram import Router
from .election_admin import router as election_admin_router

admin_router = Router()
admin_router.include_router(election_admin_router)
