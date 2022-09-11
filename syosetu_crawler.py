from engine import BaseCrawler
from models import Section, Chapter, Book, ChapterMeta, Paragraph, ChapterType, BookMeta
import re
from typing import Optional
from bs4 import BeautifulSoup
from bs4.element import NavigableString


class MasiroCrawler(BaseCrawler):

    def __init__(self, url: str):
        super().__init__(url)
        self.root_url = 'https://ncode.syosetu.com/'
        self.cover_url = ''

    def crawl(self):
        html = self._get_html(self.book_url)
        book_info_page = BeautifulSoup(html, 'html.parser')
        self.book.meta.title = book_info_page.find('p', class_='novel_title').text
        self.book.meta.author = [book_info_page.find('div', class_='novel_writername').a.string]
        self.book.meta.cover = self.cover_url
        self.book.meta.description = book_info_page.find(id='novel_ex').text.replace('<br>', '\n')
        self.book.meta.publisher = 'Syosetu'
        self.book.meta.language = 'ja-JP'
        self.book.meta.identifier = 'syosetu_book_' + self.book_url.replace(self.root_url, '').replace('/', '')
        self.book.meta.meta = {'source': self.book_url}
        chapter_ul = book_info_page.find('div', class_='index_box')
        section_count: int = 0
        chapter_count: int = 0
        current_section: Optional[Section] = Section(section_name="正文", section_order=section_count)
        for li in chapter_ul:
            if isinstance(li, NavigableString):
                continue
            if li.name == 'div':
                if current_section is not None:
                    self.book.sections.append(current_section)
                section_name = li.text.strip().replace(u'\u3000', u'').replace(u'\xa0 ', u'')
                section_count += 1
                current_section = Section(section_name=section_name, section_order=section_count)
            else:
                chapter_count += 1
                current_chapter = self.parse(self.root_url + li.dd.a['href'])
                current_chapter.metadata.section_name = current_section.section_name
                current_chapter.metadata.section_order = current_section.section_order
                current_chapter.metadata.chapter_order = chapter_count
                current_section.section_content.append(current_chapter)

        if current_section is not None:
            self.book.sections.append(current_section)
        a = 1

    def parse(self, chapter_url: str) -> Chapter:
        chapter = Chapter()
        html = self._get_html(chapter_url)
        chapter_page = BeautifulSoup(html, 'html.parser')
        chapter.metadata.chapter_name = chapter_page.find('p', class_='novel_subtitle').text.strip().replace(u'\u3000', u'').replace(u'\xa0 ', u'')
        title = Paragraph(type=Paragraph.ParagraphType.Title, content=chapter.metadata.chapter_name)
        chapter.paragraphs.append(title)
        content_box = chapter_page.find(id='novel_honbun')
        chapter.paragraphs.append(Paragraph(type=Paragraph.ParagraphType.HTML, content=self.process_text(content_box.prettify())))
        print("Parsed chapter: " + chapter.metadata.chapter_name)
        return chapter

    @classmethod
    def process_text(cls, text: str) -> str:
        """
        :param text:
        :return:
        """
        text = text.replace('color: #444444;', '')
        text = text.replace('background-color: #ffffff;', '')
        return text

    def set_cover(self, image_url: str):
        self.cover_url = image_url


if __name__ == "__main__":
    crawler = MasiroCrawler(input('Enter the url of the book: '))
    crawler.set_headers({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36'
    })
    crawler.set_cover(input('Enter the url of the cover: '))
    crawler.run()
    crawler.save_as_epub()

