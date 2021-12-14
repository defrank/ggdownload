import scrapy


class CoursesSpider(scrapy.Spider):
    name = "courses"
    allowed_domains = [
        "grapplersguide.com",
        "thestrikersguide.com",
        "theweaponsguide.com",
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
                cb_kwargs={"expert": expert},
            )

    def parse_courses(self, response, expert: str):
        self.logger.debug("Parsing courses for expert, %s", expert)
        course_links = response.css("div.node-main div.node-title > a")
        for link in course_links:
            title = link.xpath("text()").get()
            course_path = link.attrib["href"]
            yield scrapy.Request(
                url=response.urljoin(course_path),
                callback=self.parse_course,
                cb_kwargs={"title": title, "expert": expert},
            )

    def parse_course(self, response, title: str, expert: str):
        self.logger.debug("Parsing course, %s, by expert, %s", title, expert)
        lesson_sections = response.css("div.block-container")
        for section_index, section in enumerate(lesson_sections, 1):
            section_title = section.css("h2.block-header > a::text").get()
            lesson_links = section.css("h3.node-title > a")
            for link_index, link in enumerate(lesson_links, 1):
                lesson_title = link.xpath("text()").get()
                lesson_path = link.attrib["href"]
                yield scrapy.Request(
                    url=response.urljoin(lesson_path),
                    callback=self.parse_lesson,
                    cb_kwargs={
                        "course_title": title,
                        "section_index": section_index,
                        "section_title": section_title,
                        "lesson_index": link_index,
                        "lesson_title": lesson_title,
                    },
                )

    def parse_lesson(
        self,
        response,
        course_title: str,
        section_index: int,
        section_title: str,
        lesson_index: int,
        lesson_title: str,
    ):
        self.logger.debug(
            "Parsing lesson, %s -> %d - %s -> %d - %s",
            course_title,
            section_index,
            section_title,
            lesson_index,
            lesson_title,
        )
        download_link = response.xpath(
            "//li[@id='lesson-actions']//a[contains(@href, '/download')]"
        )
        download_path = download_link.attrib["href"]
        yield scrapy.Request(
            url=response.urljoin(download_path),
            callback=self.parse_download,
            cb_kwargs={
                "course_title": course_title,
                "section_index": section_index,
                "section_title": section_title,
                "lesson_index": lesson_index,
                "lesson_title": lesson_title,
            },
        )

    def parse_download(
        self,
        response,
        course_title: str,
        section_index: int,
        section_title: str,
        lesson_index: int,
        lesson_title: str,
    ):
        self.logger.debug(
            "Downloading lesson, %s -> %d - %s -> %d - %s",
            course_title,
            section_index,
            section_title,
            lesson_index,
            lesson_title,
        )
        yield {
            "course_title": course_title,
            "section_index": section_index,
            "section_title": section_title,
            "lesson_index": lesson_index,
            "lesson_title": lesson_title,
            "url": response.url,
        }
