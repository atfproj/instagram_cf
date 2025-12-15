from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.models.user import User
from app.services.translator import translator_service
from app.api.auth import get_current_user

router = APIRouter(prefix="/api/translations", tags=["translations"])


class TranslationRequest(BaseModel):
    text: str = Field(..., min_length=1)
    language_from: str = Field(..., max_length=10)
    language_to: str = Field(..., max_length=10)
    use_cache: bool = Field(default=True)


class TranslationResponse(BaseModel):
    success: bool
    translated_text: str
    from_cache: bool
    error: Optional[str] = None


class BatchTranslationRequest(BaseModel):
    texts: List[str] = Field(..., min_items=1)
    language_from: str = Field(..., max_length=10)
    language_to: str = Field(..., max_length=10)


class BatchTranslationResponse(BaseModel):
    translations: dict  # {original: translated}


@router.post("/", response_model=TranslationResponse)
def translate_text(
    request: TranslationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Перевести текст на указанный язык
    
    Использует DeepSeek API для перевода с кэшированием результатов.
    """
    result = translator_service.translate(
        text=request.text,
        language_from=request.language_from,
        language_to=request.language_to,
        db=db,
        use_cache=request.use_cache
    )
    
    if not result["success"] and result.get("error"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка перевода: {result.get('error')}"
        )
    
    return TranslationResponse(
        success=result["success"],
        translated_text=result["translated_text"],
        from_cache=result.get("from_cache", False),
        error=result.get("error")
    )


@router.post("/batch", response_model=BatchTranslationResponse)
def translate_batch(
    request: BatchTranslationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Перевести несколько текстов одновременно
    
    Полезно для перевода нескольких постов или вариантов текста.
    """
    translations = translator_service.translate_batch(
        texts=request.texts,
        language_from=request.language_from,
        language_to=request.language_to,
        db=db
    )
    
    return BatchTranslationResponse(translations=translations)


@router.get("/languages")
def get_supported_languages(current_user: User = Depends(get_current_user)):
    """
    Получить список поддерживаемых языков
    
    Возвращает коды языков и их названия для использования в API.
    """
    from app.services.translator import LANGUAGE_NAMES
    
    languages = [
        {"code": code, "name": name}
        for code, name in LANGUAGE_NAMES.items()
    ]
    
    return {
        "languages": languages,
        "count": len(languages)
    }

