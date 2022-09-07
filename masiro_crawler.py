from engine import BaseCrawler
from models import Section, Chapter, Book, ChapterMeta, Paragraph, ChapterType, BookMeta
import re
from typing import Optional
from bs4 import BeautifulSoup


class MasiroCrawler(BaseCrawler):

    def __init__(self, url: str):
        super().__init__(url)
        self.root_url = 'https://masiro.me'

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
                    chapter_count += 1
                    current_chapter = self.parse(self.root_url + chapter_a['href'])
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
        chapter.metadata.chapter_name = chapter_page.find('span', class_='novel-title').div.text.strip().replace(u'\u3000', u'').replace(u'\xa0 ', u'')
        title = Paragraph(type=Paragraph.ParagraphType.Title, content=chapter.metadata.chapter_name)
        chapter.paragraphs.append(title)
        content_box = chapter_page.find('div', class_='nvl-content')
        for paragraph in content_box.findAll('p'):
            chapter.paragraphs.append(Paragraph(type=Paragraph.ParagraphType.HTML, content=self.process_text(paragraph.prettify())))
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
        return text


if __name__ == "__main__":
    crawler = MasiroCrawler('https://masiro.me/admin/novelView?novel_id=247')
    crawler.set_headers({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36',
        'Cookie': 'remember_admin_59ba36addc2b2f9401580f014c7f58ea4e30989d=eyJpdiI6InFGU2pMK3p4Z0ZBS0VHOUlLdzBkMGc9PSIsInZhbHVlIjoiMWpnYnZQOGprUWR0Nm9xY01Ub290Wk4zZTJsVERCdkpcL3drXC9pOVl6UjlJMk1FTzhweHBURWxGSGxidVI5VDVVUXJDOTg2bUJUNEt1akhQWU5aQzVPd050ZXNsV3ZjTFlsRm9tWWlTcGFzdHNUWDJQUExLNkVReHNreUU2bzZiUjAyblA5d3VKa1crMUxLZkdNNXc0eDV1QVNKcm1GUElEd0paSmcxREJCSEkrRDI0UDh4NTRnQ2FBNm5uWE5JTFYiLCJtYWMiOiI5NjE5MDc1ZDZkOGYwNGQ3NjQ2OTQxZTMxM2M0MzBlN2Q5ODUwMzU0YWY3ZmY3Y2Q4NmRlZGY1MjQ2ZmY4M2MyIn0%3D; last_signin=1659100751213; __cf_bm=O33ZqQNq29.gp1A_v4KaXDddY7u5wFdE7z8h.ZWyhDw-1659105665-0-ATJC2tx0Q2ZElKnVCs6z+NQSbaPNWnaLWNsCYquSmyDo80CigBhEIXSdQKN9c9Ww5Ebs5l9zGYzM5NQBDbYe+7GIrpUQDD6jlysPkdYwa1vJymRF2K+J9yXJ3MHAenjNxw==; XSRF-TOKEN=eyJpdiI6IjZHbXl2ZUZkNG4rMjF4WHQ5RklablE9PSIsInZhbHVlIjoidUFDQTA2SUx1UGtrN0lDbTdJUEtrMFlqQnYxMmM1cjM2UTloSGFcL2k0QWJwcGdHM3ByRjNFc1dxc1ljaE9XUFwvMzdzV1wvRjA5ODFJaDRMUG43NXpSZ1E9PSIsIm1hYyI6IjZmNmM4MjkzMmY2YWZhZGQ4NmFhNmJmMTJmZmRmNmNhYTI4MTMzODU1MmM0MDA2YjQwZDNiZmZiYmE1NDFmMWEifQ%3D%3D; laravel_session=eyJpdiI6IlwvWDgzVlNcL2dXbmJXTkg2VlBYaFJZUT09IiwidmFsdWUiOiJpUk9PWjdpVlFuQkU4YndDRUVmdEMxNXdiK3dXWEZZcFYxU0d5RnVKWkl1TUVyNW12SU1BQkZ5OEdPZ2hSaHdKbTBUZitCVWMzTVprVU5GaVlscis0UT09IiwibWFjIjoiMDU0YTlkM2E2YWZjZjUxZmJjYmM1NDUxNmMyYjg0N2JjYjJlNjFjZjYxY2ViZjFlODA2MzUzZmUxZTY5YzNhOCJ9'
    })
    crawler.run()
    crawler.save_as_epub()

