from engine import BaseCrawler
from models import Section, Chapter, Book, ChapterMeta, Paragraph, ChapterType, BookMeta
import re
from typing import Optional
from bs4 import BeautifulSoup
import opencc


class MasiroCrawler(BaseCrawler):

    def __init__(self, url: str):
        super().__init__(url)
        self.root_url = 'https://book.sfacg.com'
        self.text_converter = opencc.OpenCC('t2s')

    def crawl(self):
        html = self._get_html(self.book_url)
        book_info_page = BeautifulSoup(html, 'html.parser')
        self.book.meta.title = book_info_page.find('h1', class_='title').findChild('span', class_='text').text
        self.book.meta.author = [book_info_page.find('div', class_='author-name').span.string]
        try:
            self.book.meta.cover = book_info_page.find('div', class_='summary-pic').img.attrs['src']
        except AttributeError:
            self.book.meta.cover = input('Please input the cover url: ')
        self.book.meta.description = book_info_page.find('p', class_='introduce').text
        self.book.meta.publisher = 'Sfacg'
        self.book.meta.language = 'zh-CN'
        self.book.meta.identifier = 'sf_book_' + self.book_url.split('/')[-1]
        self.book.meta.meta = {'source': self.book_url}
        chapter_page_html = self._get_html(self.book_url + '/MainIndex/')
        chapter_page = BeautifulSoup(chapter_page_html, 'html.parser')
        chapter_list = chapter_page.findAll('div', class_='story-catalog')
        section_count: int = 0
        chapter_count: int = 0
        for li in chapter_list:
            section_count += 1
            section_name = li.findChild('div', class_='catalog-hd').h3.text.split('】')[-1].strip()
            current_section = Section(section_name=section_name, section_order=section_count)
            for chapter_a in li.findAll('li'):
                if chapter_a.a.span is not None and chapter_a.a.span.text == 'VIP':
                    continue
                current_chapter = self.parse(self.root_url + chapter_a.a['href'])
                if current_chapter is None:
                    continue
                chapter_count += 1
                current_chapter.metadata.section_name = self.text_converter.convert(current_section.section_name)
                current_chapter.metadata.section_order = current_section.section_order
                current_chapter.metadata.chapter_order = chapter_count
                current_section.section_content.append(current_chapter)
            self.book.sections.append(current_section)

    def parse(self, chapter_url: str) -> Optional[Chapter]:
        chapter = Chapter()
        html = self._get_html(chapter_url)
        if '付费阅读' in html:
            print('Chapter is not free content, skip')
            return None
        chapter_page = BeautifulSoup(html, 'html.parser')
        chapter_title = chapter_page.find('h1', class_='article-title').text
        chapter.metadata.chapter_name = chapter_title
        title = Paragraph(type=Paragraph.ParagraphType.Title, content=chapter_title)
        chapter.paragraphs.append(title)
        content_box = chapter_page.find('div', class_='article-content')
        # for paragraph in content_box.findAll('p'):
        chapter.paragraphs.append(Paragraph(type=Paragraph.ParagraphType.HTML, content=self.process_text(content_box.prettify())))
        print("Parsed chapter: " + chapter.metadata.chapter_name)
        return chapter

    @classmethod
    def process_text(cls, text: str) -> str:
        """
        remove contents between （ and ）
        :param text:
        :return:
        """
        text = text.replace('color: #444444;', '')
        text = text.replace('background-color: #ffffff;', '')
        converter = opencc.OpenCC('t2s')
        text = converter.convert(text)
        return text


if __name__ == "__main__":
    crawler = MasiroCrawler('https://book.sfacg.com/Novel/' + input('SF book id: '))
    crawler.set_headers({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36'
    })
    crawler.run()
    crawler.save_as_epub()

