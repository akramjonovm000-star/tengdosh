from aiogram import Router

from .dashboard import router as dashboard_router
from .work_directions import router as work_directions_router
from .my_students import router as my_students_router

from .lookup import router as lookup_router

router = Router()

router.include_router(dashboard_router)
router.include_router(work_directions_router)
router.include_router(my_students_router)
router.include_router(lookup_router)
