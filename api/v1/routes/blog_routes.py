from fastapi import APIRouter, HTTPException, Query, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
from api.v1.models.blog import Blog
from api.v1.models.user import User
from api.db.database import get_db
from fastapi.responses import JSONResponse
from typing import List

router = APIRouter()

@router.get("/blogs/latest", response_model=List[dict])
def get_latest_blogs(
    page: int = Query(1, gt=0, description="Page number, must be greater than 0"),
    page_size: int = Query(10, gt=0, le=100, description="Page size, must be between 1 and 100"),
    db: Session = Depends(get_db)
):
    try:
        offset = (page - 1) * page_size
        posts = db.query(Blog).order_by(Blog.created_at.desc()).offset(offset).limit(page_size).all()
        total_posts = db.query(func.count(Blog.id)).scalar()

        results = [
            {
                "title": post.title,
                "excerpt": post.content[:100],  # Adjust excerpt length as needed
                "publish_date": post.created_at,
                "author": db.query(User).filter(User.id == post.author_id).first().username  # Fetch the username from User model
            }
            for post in posts
        ]

        response = {
            "count": total_posts,
            "next": f"/api/v1/blogs/latest?page={page + 1}&page_size={page_size}" if offset + page_size < total_posts else None,
            "previous": f"/api/v1/blogs/latest?page={page - 1}&page_size={page_size}" if page > 1 else None,
            "results": results
        }
        return response
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail="Internal server error.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Error handlers
@router.exception_handler(404)
async def not_found_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=404, content={"error": "Resource not found."})

@router.exception_handler(405)
async def method_not_allowed_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=405, content={"error": "This method is not allowed."})

@router.exception_handler(400)
async def bad_request_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=400, content={"error": "An invalid request was sent."})

@router.exception_handler(Exception)
async def internal_server_error_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": "Internal server error."})