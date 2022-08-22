import dataclasses as dc
import operator as op
import urllib.parse
from typing import FrozenSet, Optional, Tuple

import scrapy


@dc.dataclass(frozen=True)
class Expert:
    name: str


@dc.dataclass(frozen=True)
class Course:
    title: str
    expert: Expert


@dc.dataclass(frozen=True)
class Section:
    position: int
    title: str
    course: Course


@dc.dataclass(frozen=True)
class Lesson:
    position: int
    title: str
    url: str
    section: Section
    breadcrumbs: Optional[Tuple[str, ...]] = None
    tags: Optional[FrozenSet[str]] = None


@dc.dataclass(frozen=True)
class Download:
    file_name: str
    public_name: str
    base_file_name: str
    extension: str
    download_name: str
    size: str
    height: int
    width: int
    video_file_id: str
    download_url: str
    lesson: Lesson


class CoursesSpider(scrapy.Spider):
    name = "courses"
    allowed_domains = [
        "grapplersguide.com",
        "thestrikersguide.com",
        "theweaponsguide.com",
        "vimeo.com",
    ]
    login_urls = [
        "https://grapplersguide.com/second-portal/login",
    ]

    def __init__(self, username: str, password: str):
        self._username = username
        self._password = password
        super().__init__()

    def start_requests(self):
        self.logger.debug("Starting requests...")
        for url in self.login_urls:
            yield scrapy.Request(url=url, callback=self.parse_login)

    def parse_login(self, response):
        self.logger.debug("Logging in...")
        return scrapy.FormRequest.from_response(
            response,
            formdata={"login": self._username, "password": self._password},
            callback=self.parse_experts,
        )

    def parse_experts(self, response):
        self.logger.debug("Listing experts...")
        # response.css("select#topic option")
        options = response.xpath("//select[@id='expert']/option[@value!='']")
        for option in options:
            expert = option.xpath("text()").get()
            courses_path = option.attrib["value"]
            yield scrapy.Request(
                url=response.urljoin(courses_path),
                callback=self.parse_courses,
                cb_kwargs={"expert": Expert(name=expert)},
            )

    def parse_courses(self, response, expert: Expert):
        self.logger.debug("Parsing courses for expert, %s", expert)
        course_links = response.css("div.node-main div.node-title > a")
        for link in course_links:
            title = link.xpath("text()").get()
            course_path = link.attrib["href"]
            course = Course(title=title, expert=expert)
            yield scrapy.Request(
                url=response.urljoin(course_path),
                callback=self.parse_course,
                cb_kwargs={"course": course},
            )

    def parse_course(self, response, course: Course):
        self.logger.debug("Parsing course: %s", course)
        lesson_sections = response.css("div.block-container")
        for section_index, section in enumerate(lesson_sections, 1):
            section_title = section.css("h2.block-header > a::text").get()
            lesson_links = section.css("h3.node-title > a")
            section = Section(
                position=section_index,
                title=section_title,
                course=course,
            )
            for link_index, link in enumerate(lesson_links, 1):
                lesson_title = link.xpath("text()").get()
                lesson_path = link.attrib["href"]
                lesson = Lesson(
                    position=link_index,
                    title=lesson_title,
                    url=link,
                    section=section,
                )
                yield scrapy.Request(
                    url=response.urljoin(lesson_path),
                    callback=self.parse_lesson,
                    cb_kwargs={"lesson": lesson},
                )

    def parse_lesson(self, response, lesson: Lesson):
        self.logger.debug("Parsing lesson: %s", lesson)

        breadcrumb_links = response.xpath(
            "(//ul[contains(@class, 'p-breadcrumbs')])[1]/li/a"
        )
        breadcrumbs = tuple(
            name
            for link in breadcrumb_links
            for name in link.xpath("span[@itemprop='name']/text()").getall()
            if name != "Home"
        )

        tags = response.css("dl.tagList dd a.tagItem::text")
        tags = frozenset(tag.strip() for tag in tags.getall())

        download_link = response.xpath(
            "//li[@id='lesson-actions']//a[contains(@href, '/download')]"
        )
        download_path = download_link.attrib["href"]
        yield scrapy.Request(
            url=response.urljoin(download_path),
            callback=self.parse_download_page,
            cb_kwargs={
                "lesson": dc.replace(
                    lesson,
                    breadcrumbs=breadcrumbs,
                    tags=tags,
                ),
            },
        )

    def parse_download_page(self, response, lesson: Lesson):
        assert lesson.breadcrumbs is not None, "breadcrumbs must be a tuple"
        assert lesson.tags is not None, "tags must be a frozenset"
        self.logger.debug("Parsing download page: %s", lesson)
        url = urllib.parse.urlsplit(response.url)
        _, user_id, resource, some_other_id, video_id = url.path.split("/")
        assert resource == "download", f"Want `download`, got `{resource}`"
        path = f"/{user_id}/{resource}/data/{some_other_id}/{video_id}"
        query_string = urllib.parse.urlencode({"action": "load_download_data"})
        headers = {"x-requested-with": "XMLHttpRequest"}
        yield scrapy.Request(
            url=response.urljoin(f"{path}?{query_string}"),
            headers=headers,
            callback=self.parse_download_data,
            cb_kwargs={"lesson": lesson},
        )

    def parse_download_data(self, response, lesson: Lesson):
        self.logger.debug("Parsing download data: %s", lesson)
        data = response.json()
        files = data["download_config"]["files"]
        highest_quality_file = max(files, key=op.itemgetter("height"))
        download_fields = {field.name for field in dc.fields(Download)}
        yield Download(
            lesson=lesson,
            **{
                key: value
                for key, value in highest_quality_file.items()
                if key in download_fields
            },
        )
