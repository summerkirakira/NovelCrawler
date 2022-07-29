import enum

from pydantic import BaseModel
from typing import Optional
from ebooklib import epub


class ConverterConfig(BaseModel):
    convert_image: bool = True
    style: Optional[str] = None
    lang: Optional[str] = None
    download_headers: dict[str, str] = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/103.0.0.0 Safari/537.36 "
    }


class ChapterType(enum.Enum):
    NOVEL = 0
    COMIC = 1


class ChapterMeta(BaseModel):
    section_name: Optional[str] = None
    section_order: Optional[int] = None
    chapter_order: Optional[int] = None
    chapter_name: Optional[str] = None
    chapter_type: ChapterType = ChapterType.NOVEL
    show_chapter_order: bool = True


class SectionDict(BaseModel):
    class Config:
        arbitrary_types_allowed = True
    section_name: str
    section_order: int
    section_content: dict[int, epub.EpubHtml]


class BookMeta(BaseModel):
    title: str
    author: Optional[list[str]] = None
    description: Optional[str] = None
    language: Optional[str] = None
    meta: Optional[dict[str, str]] = None
    cover: Optional[str] = None
    publisher: Optional[str] = None
    identifier: Optional[str] = None

