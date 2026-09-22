from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app import models, schema, utils
from app.database import Base, engine, get_db

Base.metadata.create_all(bind=engine)
app = FastAPI(title="URL Shortener API", description="A URL shortener API built with FastAPI, PostgreSQL and SQLAlchemy", version="1.0.0")

@app.post("/shorten", response_model=schema.UrlResponse, status_code=status.HTTP_201_CREATED, summary="Shorten a URL")
def shorten_url(payload: schema.CreateUrl, request: Request, db: Session = Depends(get_db)):
    target_url_str = str(payload.url)
    if payload.custom_alias:
        existing = db.query(models.URL).filter(models.URL.short_url == payload.custom_alias).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Custom alias already exists.")
        short_code = payload.custom_alias
    else:
        existing_url = (db.query(models.URL).filter(models.URL.original_url == target_url_str).first())
        if existing_url:
            base_url = str(request.base_url).rstrip('/')
            return schema.UrlResponse(short_url=f"{base_url}/{existing_url.short_url}", target_url=existing_url.original_url, short_code=existing_url.short_url)
        while True:
            short_code = utils.generate_short_code()
            if not db.query(models.URL).filter(models.URL.short_url == short_code).first():
                break
    db_item = models.URL(original_url=target_url_str, short_url=short_code)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    base_url = str(request.base_url).rstrip('/')
    return schema.UrlResponse(short_url=f"{base_url}/{db_item.short_url}", target_url=db_item.original_url, short_code=db_item.short_url)

@app.get("/{code}", response_class=RedirectResponse, status_code=status.HTTP_307_TEMPORARY_REDIRECT, summary="Redirect to the original URL")
def redirect_to_original_url(code: str, db: Session = Depends(get_db)):
    db_item = db.query(models.URL).filter(models.URL.short_url == code).first()
    if not db_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Short URL not found")
    db_item.clicks += 1
    db.commit()
    return RedirectResponse(url=db_item.original_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)

@app.get("/stats/{code}", response_model=schema.UrlStatsResponse, status_code=status.HTTP_200_OK, summary="Get stats for a short URL")
def get_url_stats(code: str, db: Session = Depends(get_db)):
    db_item = db.query(models.URL).filter(models.URL.short_url == code).first()
    if not db_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Short URL not found")
    return schema.URLStatsResponse(short_url=db_item.short_url, target_url=db_item.original_url, clicks=db_item.clicks, created_at=db_item.created_at)
