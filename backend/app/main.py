import os

import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.core.config import ALLOWED_HOSTS, PROJECT_NAME
from app.core.db import close_mongo_connection, connect_to_mongo
from app.routes.admin import router as admin_router
from app.routes.cars import router as car_router
from app.routes.charging import router as charge_router
from app.routes.cpos import router as cpo_router
from app.routes.expenses import router as expense_router
from app.routes.users import router as user_router

app = FastAPI(title=PROJECT_NAME, root_path=os.environ.get('API_ROOT_PATH', ''))

if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.add_event_handler('startup', connect_to_mongo)
app.add_event_handler('shutdown', close_mongo_connection)

app.include_router(admin_router)
app.include_router(car_router, prefix='/car', tags=['Cars'])
app.include_router(cpo_router, prefix='/cpo', tags=['CPOs'])
app.include_router(charge_router, prefix='/charge', tags=['Charging'])
app.include_router(expense_router, prefix='/expense', tags=['Expenses'])
app.include_router(user_router)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
