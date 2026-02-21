from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from app.core.config import settings
from app.models.schemas import UserExtract

security = HTTPBearer()

def get_supabase() -> Client:
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        raise HTTPException(status_code=500, detail="Supabase credentials not configured in backend")
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

async def verify_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserExtract:
    """
    Middleware that takes the Bearer token sent from Next.js, 
    validates it against Supabase, and extracts the User ID.
    """
    token = credentials.credentials
    supabase = get_supabase()
    
    try:
        # Validate JWT and get user session
        user_response = supabase.auth.get_user(token)
        
        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return UserExtract(
            id=user_response.user.id,
            email=user_response.user.email
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
