from fastapi import APIRouter
from controllers.proxy_curl_controller import router as proxy_curl_router

router = APIRouter()

router.include_router(proxy_curl_router, prefix="/proxy-curl", tags=["Proxy Curl"])

