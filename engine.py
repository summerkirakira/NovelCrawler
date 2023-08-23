import pathlib
import requests
import json
import abc
from models import Paragraph, Chapter, Section, Book
from pathlib import Path
from converter import Markdowns2EpubConverter
from pydantic import BaseModel


requests.DEFAULT_RETRIES = 20


class CrawlerConfig(BaseModel):
    headers: dict
    config: dict = {}


class BaseCrawler:
    def __init__(self, book_url):
        self.book_url = book_url
        self.config = self.parse_config()
        self.headers = self.config.headers
        self.book: Book = Book()
        self.out_put_path = Path('output')
        self.out_put_path.mkdir(exist_ok=True)

    def set_headers(self, headers) -> 'BaseCrawler':
        self.headers = headers
        return self

    def _get_html(self, url: str) -> str:
        while True:
            try:
                if 'proxy' in self.config.config:
                    r = requests.get(url, headers=self.headers, proxies=self.config.config['proxy'])
                else:
                    r = requests.get(url, headers=self.headers)
                return r.text
            except Exception as e:
                print(f"在请求{url}时发生错误: {e}，正在重试...")
                continue

    def add_section(self, section: Section):
        self.book.sections.append(section)

    def set_save_path(self, path: Path) -> 'BaseCrawler':
        if not path.exists():
            print(f'{path} not exists, abort')
            return self
        self.out_put_path = path
        return self

    def save_as_markdown(self):
        for file in self.out_put_path.glob('*.md'):
            file.unlink()
        self.save_book_meta()
        self.save_chapters()

    def save_as_epub(self):
        self.out_put_path = Path('output')
        self.save_as_markdown()
        if "proxy" in self.config.config:
            converter = Markdowns2EpubConverter(proxy=self.config.config['proxy'])
        else:
            converter = Markdowns2EpubConverter()
        converter.set_md_path(self.out_put_path)
        converter.convert().save_to_file(pathlib.Path(f'{self.book.meta.title}.epub'))

    def save_book_meta(self):
        with open(self.out_put_path / 'book_meta.json', 'w', encoding='utf-8') as f:
            json.dump(self.book.meta.dict(), f, indent=4, ensure_ascii=False)

    def save_chapters(self):
        for section in self.book.sections:
            for chapter in section.section_content:
                chapter.metadata.chapter_name = chapter.metadata.chapter_name.replace('/', '_')
                with open(self.out_put_path / f'{chapter.metadata.chapter_name}.md', 'w', encoding='utf-8') as f:
                    f.write(self.chapter2md(chapter))

    @classmethod
    def chapter2md(cls, chapter: Chapter) -> str:
        md = '---\n'
        for k, v in chapter.metadata.dict().items():
            if k == 'meta' and v is not None:
                for kk, vv in v.items():
                    md += f'{kk}: {vv}\n'
                continue
            if k == 'chapter_type':
                continue
            md += f'{k}: {v}\n'
        md += '---\n\n'
        for paragraph in chapter.paragraphs:
            md += cls.paragraph2md(paragraph)
        return md

    @classmethod
    def paragraph2md(cls, paragraph: Paragraph) -> str:
        if paragraph.type == Paragraph.ParagraphType.Image:
            return f'![{paragraph.content}]({paragraph.content})\n'
        if paragraph.type == Paragraph.ParagraphType.Title:
            return f'# {paragraph.content}\n'
        if paragraph.type == Paragraph.ParagraphType.HTML:
            f'{paragraph.content}\n'
        return f'{paragraph.content}\n'

    @abc.abstractmethod
    def crawl(self):
        pass

    @abc.abstractmethod
    def parse(self, chapter_url: str) -> Chapter:
        pass

    def run(self):
        self.crawl()

    def parse_config(self) -> CrawlerConfig:
        config_path = Path('config') / f'{self.__class__.__name__}.json'
        if not config_path.exists():
            print(f'{config_path} not exists, abort')
            raise FileNotFoundError
        with open(config_path, 'r', encoding='utf-8') as f:
            config = CrawlerConfig(**json.load(f))
        return config

    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        filename = filename.replace('/', '_').replace('\\', '_').replace(':', '：').replace('*', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_').replace('?', '？')
        return filename
