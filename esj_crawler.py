from engine import BaseCrawler
from models import Section, Chapter, Book, ChapterMeta, Paragraph, ChapterType, BookMeta
import re
from typing import Optional
from bs4 import BeautifulSoup
from bs4.element import NavigableString
import opencc


class EsjCrawler(BaseCrawler):

    def __init__(self, url: str):
        super().__init__(url)
        self.root_url = 'https://www.esjzone.cc/'
        self.cover_url = ''

    def crawl(self):
        html = self._get_html(self.book_url)
        book_info_page = BeautifulSoup(html, 'html.parser')
        book_detail = book_info_page.find('div', class_='book-detail')
        self.book.meta.title = self.process_text(book_detail.h2.text)

        for child in book_detail.ul.children:
            if child.name == 'li' and child.strong.text == '作者:':
                self.book.meta.author = [child.a.text]
                break
        self.book.meta.cover = book_info_page.find('div', class_='product-gallery').a['href']
        self.book.meta.description = self.process_text(book_info_page.find("div", class_='description').text)
        self.book.meta.publisher = 'Esj'
        self.book.meta.language = 'zh-CN'
        self.book.meta.identifier = 'Esj_book_' + self.book_url.replace(self.root_url, '').replace('/', '')
        self.book.meta.meta = {'source': self.book_url}
        chapter_ul = book_info_page.find('div', id='chapterList')
        section_count: int = 0
        chapter_count: int = 0
        current_section: Optional[Section] = Section(section_name="番外", section_order=section_count)
        for li in chapter_ul:
            if isinstance(li, NavigableString):
                continue
            if li.name == 'p':
                if current_section is not None:
                    if len(current_section.section_content) > 0:
                        self.book.sections.append(current_section)
                section_name = self.sanitize_filename(self.process_text(li.text))
                section_count += 1
                current_section = Section(section_name=section_name, section_order=section_count)
            elif li.name == 'a':
                chapter_count += 1
                current_chapter = self.parse(li['href'])
                current_chapter.metadata.section_name = current_section.section_name
                current_chapter.metadata.section_order = current_section.section_order
                current_chapter.metadata.chapter_order = chapter_count
                current_section.section_content.append(current_chapter)
            elif li.name == 'details':
                if current_section is not None:
                    if len(current_section.section_content) > 0:
                        self.book.sections.append(current_section)
                section_name = self.sanitize_filename(self.process_text(li.summary.text))
                section_count += 1
                current_section = Section(section_name=section_name, section_order=section_count)
                for a in li:
                    if a.name == 'a':
                        chapter_count += 1
                        current_chapter = self.parse(a['href'])
                        current_chapter.metadata.section_name = current_section.section_name
                        current_chapter.metadata.section_order = current_section.section_order
                        current_chapter.metadata.chapter_order = chapter_count
                        current_section.section_content.append(current_chapter)

        if current_section is not None:
            self.book.sections.append(current_section)

    def parse(self, chapter_url: str) -> Chapter:
        chapter = Chapter()
        html = self._get_html(chapter_url)
        chapter_page = BeautifulSoup(html, 'html.parser')
        chapter.metadata.chapter_name = self.sanitize_filename(self.process_text(chapter_page.find('h2').text.strip()))
        title = Paragraph(type=Paragraph.ParagraphType.Title, content=chapter.metadata.chapter_name)
        chapter.paragraphs.append(title)
        content_box = chapter_page.find(class_='forum-content')
        chapter.paragraphs.append(Paragraph(type=Paragraph.ParagraphType.HTML, content=self.process_text(content_box.prettify())))
        print("Parsed chapter: " + chapter.metadata.chapter_name)
        return chapter

    def set_cover(self, image_url: str):
        self.cover_url = image_url

    @classmethod
    def process_text(cls, text: str) -> str:
        """
        remove contents between （ and ）
        :param text:
        :return:
        """
        converter = opencc.OpenCC('t2s')
        text = converter.convert(text)
        return text


if __name__ == "__main__":
    crawler = EsjCrawler(input("请输入小说目录页地址："))
    crawler.run()
    crawler.save_as_epub()

