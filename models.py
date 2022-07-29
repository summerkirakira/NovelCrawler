from pydantic import BaseModel
from typing import Optional
import enum


class BookMeta(BaseModel):
    title: str
    author: Optional[list[str]] = None
    description: Optional[str] = None
    language: Optional[str] = None
    meta: Optional[dict[str, str]] = None
    cover: Optional[str] = None
    publisher: Optional[str] = None
    identifier: Optional[str] = None


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
    meta: Optional[dict[str, str]] = None


class Paragraph(BaseModel):
    class ParagraphType(enum.Enum):
        Image = 0
        Text = 1
        Title = 2

    type: ParagraphType = ParagraphType.Text
    content: str


class Chapter(BaseModel):
    metadata: ChapterMeta = ChapterMeta()
    paragraphs: list[Paragraph] = []


class Section(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    section_name: str
    section_order: int
    section_content: list[Chapter] = []


class Book(BaseModel):
    meta: BookMeta
    sections: list[Section] = []

