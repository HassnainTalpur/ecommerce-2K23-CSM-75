from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.api.routes import auth, categories, products, skus, variants
from app.errors import ApiError, api_error_handler, validation_error_handler


app = FastAPI(title="ReadySafe Catalog Administration API", version="0.2.0")
app.add_exception_handler(ApiError, api_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)

app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(variants.router)
app.include_router(skus.router)

