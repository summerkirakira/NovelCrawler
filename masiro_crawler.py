from engine import BaseCrawler
from models import Section, Chapter, Book, ChapterMeta, Paragraph, ChapterType, BookMeta
import re
from typing import Optional
from bs4 import BeautifulSoup
import opencc


class MasiroCrawler(BaseCrawler):

    def __init__(self, url: str):
        super().__init__(url)
        self.root_url = 'https://masiro.me'
        self.text_converter = opencc.OpenCC('t2s')

    def crawl(self):
        html = self._get_html(self.book_url)
        book_info_page = BeautifulSoup(html, 'html.parser')
        self.book.meta.title = book_info_page.find('div', class_='novel-title').text
        novel_detail = book_info_page.find('div', class_='n-detail')
        self.book.meta.author = [novel_detail.find('div', class_='author').a.string]
        self.book.meta.cover = self.root_url + book_info_page.find('div', class_='mailbox-attachment-icon').a.img['src']
        self.book.meta.description = book_info_page.find('div', class_='brief').text.replace('简介：', '')
        self.book.meta.publisher = 'Masiro'
        self.book.meta.language = 'zh-CN'
        self.book.meta.identifier = 'masiro_book_' + self.book_url.split('=')[-1]
        self.book.meta.meta = {'source': self.book_url}
        chapter_ul = book_info_page.find('ul', class_='chapter-ul')
        section_count: int = 0
        chapter_count: int = 0
        current_section: Optional[Section] = None
        for li in chapter_ul.findAll('li'):
            if li.get('class') and 'chapter-box' in li.get('class'):
                if current_section is not None:
                    self.book.sections.append(current_section)
                section_name = li.b.text.strip().replace(u'\u3000', u'').replace(u'\xa0 ', u'')
                section_count += 1
                current_section = Section(section_name=section_name, section_order=section_count)
            else:
                for chapter_a in li.findAll('a'):
                    current_chapter = self.parse(self.root_url + chapter_a['href'])
                    if current_chapter is None:
                        continue
                    chapter_count += 1
                    current_chapter.metadata.section_name = self.text_converter.convert(current_section.section_name)
                    current_chapter.metadata.section_order = current_section.section_order
                    current_chapter.metadata.chapter_order = chapter_count
                    current_section.section_content.append(current_chapter)

        if current_section is not None:
            self.book.sections.append(current_section)

    def parse(self, chapter_url: str) -> Optional[Chapter]:
        chapter = Chapter()
        html = self._get_html(chapter_url)
        if '立即打钱' in html:
            return None
        chapter_page = BeautifulSoup(html, 'html.parser')
        chapter.metadata.chapter_name = self.text_converter.convert(chapter_page.find('span', class_='novel-title').div.text.strip().replace(u'\u3000', u'').replace(u'\xa0 ', u''))
        title = Paragraph(type=Paragraph.ParagraphType.Title, content=chapter.metadata.chapter_name)
        chapter.paragraphs.append(title)
        content_box = chapter_page.find('div', class_='nvl-content')
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
        text = re.sub(r'（受丘.*?）', '', text)
        text = re.sub(r'\(受丘.*?\)', '', text)
        text = text.replace('color: #444444;', '')
        text = text.replace('background-color: #ffffff;', '')
        converter = opencc.OpenCC('t2s')
        text = converter.convert(text)
        return text


if __name__ == "__main__":
    crawler = MasiroCrawler(input('Masiro URL: '))
    crawler.run()
    crawler.save_as_epub()

