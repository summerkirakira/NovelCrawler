from engine import BaseCrawler
from models import Section, Chapter, Book, ChapterMeta, Paragraph, ChapterType, BookMeta
from typing import Optional
from bs4 import BeautifulSoup
import opencc
import pathlib
import json
from pydantic import BaseModel
from lxml import etree
from lxml.etree import ElementTree
import requests


class CrawlerConfig(BaseModel):
    class ReplaceStr(BaseModel):
        replace_str: str
        replace_to: str

    book_info_page: Optional[str]
    crawler_start_page: Optional[str]
    crawler_stop_page: Optional[str]
    encoding: str = 'utf-8'
    publisher: str
    root_url: str
    book_name_xpath: str
    book_cover_xpath: str
    book_author_xpath: str
    book_intro_xpath: str

    chapter_title_xpath: str
    chapter_content_xpath: str
    next_page_xpath: str
    replace_str_list: list[ReplaceStr]


class UniversalCrawler(BaseCrawler):

    def __init__(self, config_file: str):
        self.config = self.read_config(config_file)
        super().__init__(self.config.book_info_page)
        self.text_converter = opencc.OpenCC('t2s')
        self.current_page_url = self.config.crawler_start_page

    @classmethod
    def read_config(self, config_file: str) -> CrawlerConfig:
        config_file_path = pathlib.Path(config_file)
        if not config_file_path.exists():
            raise FileNotFoundError(f'Config file {config_file} not found')
        with open(config_file_path, 'r') as f:
            config = CrawlerConfig(**json.load(f))
        if config.book_info_page is None:
            config.book_info_page = input('Please input the book info page url: ')
        if config.crawler_start_page is None:
            config.crawler_start_page = input('Please input the crawler start page url: ')
        if config.crawler_stop_page is None:
            config.crawler_stop_page = input('Please input the crawler stop page url: ')
        return config

    def crawl(self):
        html = self._get_html(self.book_url)
        soup = BeautifulSoup(html, 'html.parser')
        book_info_page = etree.HTML(str(soup))
        self.book.meta.title = self.process_text(book_info_page.xpath(self.config.book_name_xpath)[0].text)
        self.book.meta.author = [self.process_text(book_info_page.xpath(self.config.book_author_xpath)[0].text)]
        try:
            self.book.meta.cover = book_info_page.xpath(self.config.book_cover_xpath)[0].attrib['src']
        except IndexError:
            self.book.meta.cover = input('Please input the cover url: ')
        self.book.meta.description = self.process_text(book_info_page.xpath(self.config.book_intro_xpath)[0].text)
        self.book.meta.publisher = self.config.publisher
        self.book.meta.language = 'zh-CN'
        self.book.meta.identifier = self.config.publisher + '|' + self.book_url
        self.book.meta.meta = {'source': self.book_url}
        section_count: int = 0
        chapter_count: int = 0
        self.current_page_url = self.config.crawler_start_page
        current_section = Section(section_name="第一卷", section_order=section_count)
        while True:
            current_chapter = self.parse(self.current_page_url)
            if current_chapter is None:
                break
            chapter_count += 1

            current_chapter.metadata.section_name = "第一卷"
            current_chapter.metadata.section_order = current_section.section_order
            current_chapter.metadata.chapter_order = chapter_count
            current_section.section_content.append(current_chapter)
            if self.current_page_url is None:
                break
        self.book.sections.append(current_section)

    def parse(self, chapter_url: str) -> Optional[Chapter]:
        chapter = Chapter()
        current_page_html = self._get_html(chapter_url)
        current_page_soup = BeautifulSoup(current_page_html, 'html.parser')
        current_page = etree.HTML(str(current_page_soup))

        chapter_title = self.process_text(current_page.xpath(self.config.chapter_title_xpath)[0].text)
        chapter.metadata.chapter_name = chapter_title
        title = Paragraph(type=Paragraph.ParagraphType.Title, content=chapter_title)
        chapter.paragraphs.append(title)
        content_box = current_page.xpath(self.config.chapter_content_xpath)[0]
        # for paragraph in content_box.findAll('p'):
        if self.config.publisher == 'uukanshu':
            for ad in content_box.xpath('//ins[@class="adsbygoogle"]'):
                ad.getparent().remove(ad)
        content_box = etree.tostring(content_box, encoding='unicode', method='html')
        chapter.paragraphs.append(Paragraph(type=Paragraph.ParagraphType.HTML, content=self.process_text(content_box)))
        print("Parsed chapter: " + chapter.metadata.chapter_name)
        if self.current_page_url == self.config.crawler_stop_page:
            self.current_page_url = None
        else:
            self.current_page_url = self.config.root_url + current_page.xpath(self.config.next_page_xpath)[0].attrib['href']
        return chapter

    def process_text(self, text: str) -> str:
        """
        remove contents between （ and ）
        :param text:
        :return:
        """
        text = text.replace('color: #444444;', '')
        text = text.replace('background-color: #ffffff;', '')
        converter = opencc.OpenCC('t2s')
        text = converter.convert(text)
        for replace_str in self.config.replace_str_list:
            text = text.replace(replace_str.replace_str, replace_str.replace_to)
        return text

    def _get_html(self, url: str) -> str:
        r = requests.get(url, headers=self.headers)
        return r.content.decode(self.config.encoding)


if __name__ == "__main__":
    crawler = UniversalCrawler(input('Please input config path: '))
    crawler.set_headers({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36',
        'Host': 'www.uukanshu.com',
    })
    crawler.run()
    crawler.save_as_epub()

