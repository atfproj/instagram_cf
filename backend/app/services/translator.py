import logging
import hashlib
import re
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from openai import OpenAI
from app.core.config import settings
from app.models.translation import TranslationCache

logger = logging.getLogger(__name__)


# Маппинг языков для DeepSeek
LANGUAGE_NAMES = {
    "en": "английский",
    "ru": "русский",
    "es": "испанский",
    "fr": "французский",
    "de": "немецкий",
    "it": "итальянский",
    "pt": "португальский",
    "pl": "польский",
    "tr": "турецкий",
    "ar": "арабский",
    "zh": "китайский",
    "ja": "японский",
    "ko": "корейский",
    "hi": "хинди",
    "nl": "голландский",
    "sv": "шведский",
    "da": "датский",
    "no": "норвежский",
    "fi": "финский",
    "cs": "чешский",
    "uk": "украинский",
}


class TranslatorService:
    """Сервис для переводов через DeepSeek API"""
    
    def __init__(self):
        if not settings.DEEPSEEK_API_KEY:
            logger.warning("DEEPSEEK_API_KEY не установлен. Переводы будут недоступны.")
            self.client = None
        else:
            self.client = OpenAI(
                api_key=settings.DEEPSEEK_API_KEY,
                base_url=settings.DEEPSEEK_BASE_URL
            )
    
    def _get_cache_key(self, text: str, language_from: str, language_to: str) -> str:
        """Генерация ключа для кэша"""
        key_string = f"{text}|{language_from}|{language_to}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_language_name(self, lang_code: str) -> str:
        """Получить название языка для промпта"""
        return LANGUAGE_NAMES.get(lang_code.lower(), lang_code)
    
    def _extract_hashtags(self, text: str) -> Tuple[str, str]:
        """
        Извлечь хештеги из текста
        
        Args:
            text: Исходный текст
            
        Returns:
            Tuple[str, str]: (текст без хештегов, строка с хештегами)
        """
        # Находим все хештеги (слова, начинающиеся с #)
        hashtags = re.findall(r'#\w+', text)
        hashtags_str = ' '.join(hashtags) if hashtags else ''
        
        # Удаляем хештеги из текста
        text_without_hashtags = re.sub(r'#\w+\s*', '', text).strip()
        
        return text_without_hashtags, hashtags_str
    
    def _restore_hashtags(self, text: str, hashtags: str) -> str:
        """
        Восстановить хештеги в тексте
        
        Args:
            text: Текст без хештегов
            hashtags: Строка с хештегами
            
        Returns:
            str: Текст с хештегами в конце
        """
        if not hashtags:
            return text
        
        # Добавляем хештеги в конец текста
        return f"{text}\n\n{hashtags}".strip()
    
    def translate(
        self,
        text: str,
        language_from: str,
        language_to: str,
        db: Session,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Перевести текст
        
        Args:
            text: Исходный текст
            language_from: Код исходного языка (ru, en, etc.)
            language_to: Код целевого языка
            db: Сессия БД для кэша
            use_cache: Использовать кэш
            
        Returns:
            dict: {
                "success": bool,
                "translated_text": str,
                "from_cache": bool,
                "error": str (если ошибка)
            }
        """
        if not self.client:
            return {
                "success": False,
                "translated_text": text,
                "from_cache": False,
                "error": "DeepSeek API ключ не настроен"
            }
        
        # Проверяем кэш
        if use_cache:
            cache_key = self._get_cache_key(text, language_from, language_to)
            cached = db.query(TranslationCache).filter(
                TranslationCache.text_original == text,
                TranslationCache.language_from == language_from,
                TranslationCache.language_to == language_to
            ).first()
            
            if cached:
                logger.debug(f"Перевод найден в кэше: {language_from} -> {language_to}")
                return {
                    "success": True,
                    "translated_text": cached.text_translated,
                    "from_cache": True
                }
        
        # Если язык одинаковый, возвращаем оригинал
        if language_from.lower() == language_to.lower():
            return {
                "success": True,
                "translated_text": text,
                "from_cache": False
            }
        
        try:
            # Формируем промпт для перевода
            lang_from_name = self._get_language_name(language_from)
            lang_to_name = self._get_language_name(language_to)
            
            prompt = f"""Переведи следующий текст с {lang_from_name} на {lang_to_name}. 
Переведи только текст, сохранив все эмодзи, хэштеги и форматирование. 
Не добавляй никаких пояснений или комментариев.

Текст для перевода:
{text}"""
            
            # Отправляем запрос к DeepSeek API
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": "Ты профессиональный переводчик. Переводи текст точно, сохраняя стиль и эмоциональную окраску."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Низкая температура для более точного перевода
                max_tokens=2000
            )
            
            translated_text = response.choices[0].message.content.strip()
            
            # Сохраняем в кэш
            if use_cache:
                cache_entry = TranslationCache(
                    text_original=text,
                    language_from=language_from,
                    language_to=language_to,
                    text_translated=translated_text,
                    service="deepseek"
                )
                db.add(cache_entry)
                db.commit()
            
            logger.info(f"Перевод выполнен: {language_from} -> {language_to}")
            
            return {
                "success": True,
                "translated_text": translated_text,
                "from_cache": False
            }
            
        except Exception as e:
            logger.error(f"Ошибка при переводе через DeepSeek: {e}", exc_info=True)
            return {
                "success": False,
                "translated_text": text,  # Возвращаем оригинал при ошибке
                "from_cache": False,
                "error": str(e)
            }
    
    def translate_batch(
        self,
        texts: list,
        language_from: str,
        language_to: str,
        db: Session
    ) -> Dict[str, str]:
        """
        Перевести несколько текстов
        
        Args:
            texts: Список текстов для перевода
            language_from: Код исходного языка
            language_to: Код целевого языка
            db: Сессия БД
            
        Returns:
            dict: {original_text: translated_text}
        """
        results = {}
        
        for text in texts:
            result = self.translate(text, language_from, language_to, db)
            if result["success"]:
                results[text] = result["translated_text"]
            else:
                results[text] = text  # Оставляем оригинал при ошибке
        
        return results
    
    def paraphrase(
        self,
        text: str,
        language: str,
        db: Session,
        variation_index: int = 0
    ) -> Dict[str, Any]:
        """
        Перефразировать текст, сохраняя смысл и хештеги
        
        Args:
            text: Исходный текст
            language: Язык текста
            db: Сессия БД
            variation_index: Индекс вариации (для создания разных вариантов)
            
        Returns:
            dict: {
                "success": bool,
                "paraphrased_text": str,
                "error": str (если ошибка)
            }
        """
        if not self.client:
            return {
                "success": False,
                "paraphrased_text": text,
                "error": "DeepSeek API ключ не настроен"
            }
        
        try:
            # Извлекаем хештеги
            text_without_hashtags, hashtags = self._extract_hashtags(text)
            
            # Если текст пустой (только хештеги), возвращаем оригинал
            if not text_without_hashtags.strip():
                return {
                    "success": True,
                    "paraphrased_text": text
                }
            
            lang_name = self._get_language_name(language)
            
            # Формируем промпт для перефразирования
            prompt = f"""Перефразируй следующий текст на {lang_name}, сохранив смысл и эмоциональную окраску.
Используй другие слова и конструкции, но сохрани основную мысль.
Сохрани все эмодзи и форматирование.
Не добавляй никаких пояснений или комментариев.

Текст для перефразирования:
{text_without_hashtags}"""
            
            # Используем немного более высокую температуру для вариативности
            temperature = 0.5 + (variation_index * 0.1)  # 0.5, 0.6, 0.7 и т.д.
            temperature = min(temperature, 0.8)  # Максимум 0.8
            
            # Отправляем запрос к DeepSeek API
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": "Ты профессиональный копирайтер. Перефразируй текст, сохраняя смысл, но используя другие слова и конструкции."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=temperature,
                max_tokens=2000
            )
            
            paraphrased_text = response.choices[0].message.content.strip()
            
            # Восстанавливаем хештеги
            final_text = self._restore_hashtags(paraphrased_text, hashtags)
            
            logger.info(f"Перефразирование выполнено для языка {language}, вариация {variation_index}")
            
            return {
                "success": True,
                "paraphrased_text": final_text
            }
            
        except Exception as e:
            logger.error(f"Ошибка при перефразировании через DeepSeek: {e}", exc_info=True)
            return {
                "success": False,
                "paraphrased_text": text,  # Возвращаем оригинал при ошибке
                "error": str(e)
            }


# Глобальный экземпляр сервиса
translator_service = TranslatorService()

