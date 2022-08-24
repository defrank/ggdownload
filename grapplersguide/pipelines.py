# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
#
# useful for handling different item types with a single interface
# from itemadapter import ItemAdapter
import functools as fn
import logging
import pathlib
from typing import Optional, Union

import itemadapter
import scrapy.crawler
import scrapy.http
import scrapy.pipelines.files

from . import items, spiders


class LessonVideosPipeline(scrapy.pipelines.files.FilesPipeline):
    _flat_output: bool
    _output_dir: pathlib.Path

    def __init__(
        self,
        output_dir: Union[str, pathlib.Path],
        flat_output: bool = False,
    ):
        self._output_dir = pathlib.Path(output_dir).resolve()
        self._flat_output = flat_output

    @fn.cached_property
    def logger(self):
        return logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def open_spider(self, spider: spiders.ExpertCoursesSpider):
        self.logger.debug("Opening %s spider", spider.name)
        super().open_spider(spider)
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(
            'Output directory for %s spider is "%s"',
            spider.name,
            self._output_dir,
        )

    def process_item(
        self,
        item: items.Video,
        spider: spiders.ExpertCoursesSpider,
    ):
        self.logger.debug(
            "Processing %s spider lesson: %s",
            spider.name,
            item,
        )
        return super().process_item(item, spider)

    def file_path(
        self,
        request: scrapy.Request,
        response: Optional[scrapy.http.Response] = None,
        info=None,
        *,
        item: Optional[items.Video] = None,
    ):
        self.logger.debug(
            "Building file path for request=%s response=%s info=%s item=%s",
            request,
            response,
            info,
            item,
        )
        return super().file_path()

    def get_media_requests(self, item: items.Video, info):
        self.logger.debug(
            "Getting media requests for item=%s info=%s",
            item,
            info,
        )
        adapter = itemadapter.ItemAdapter(item)
        yield scrapy.Request(adapter["download_url"])

    def item_completed(self, results, item: items.Video, info):
        self.logger.debug(
            "Item is complete: results=%s item=%s info=%s",
            results,
            item,
            info,
        )
        # video_path = next(result["path"] for ok, result in results if ok)
        return super().item_completed()

    def close_spider(self, spider: spiders.ExpertCoursesSpider):
        self.logger.debug("Closing %s spider", spider.name)
        super().close_spider(spider)

    @classmethod
    def from_crawler(cls, crawler: scrapy.crawler.Crawler):
        return cls(
            output_dir=crawler.settings.get("OUTPUT_DIR"),
            flat_output=crawler.settings.get("FLAT_OUTPUT"),
        )


class CourseIndexPipeline:
    _index_path: pathlib.Path
    _output_dir: pathlib.Path

    def __init__(
        self,
        output_dir: Union[str, pathlib.Path],
    ):
        self._output_dir = pathlib.Path(output_dir).resolve()
        self._index_path = self._output_dir / "index.md"

    @fn.cached_property
    def logger(self):
        return logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def open_spider(self, spider: spiders.ExpertCoursesSpider):
        self.logger.debug("Opening %s spider", spider.name)
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(
            'Output directory for %s spider is "%s"',
            spider.name,
            self._output_dir,
        )
        self._index_path.touch()
        self._index_file = self._index_path.open("wt")

    def process_item(
        self,
        item: items.Video,
        spider: spiders.ExpertCoursesSpider,
    ):
        self.logger.debug(
            "Processing %s spider lesson: %s",
            spider.name,
            item,
        )

        if not self._index_file.tell():
            self._index_file.write(self._header(item))

        return item

    def close_spider(self, spider: spiders.ExpertCoursesSpider):
        self.logger.debug("Closing %s spider", spider.name)
        self._index_file.close()

    @classmethod
    def from_crawler(cls, crawler: scrapy.crawler.Crawler):
        return cls(
            output_dir=crawler.settings.get("OUTPUT_DIR"),
        )

    @staticmethod
    def _header(video: items.Video):
        lesson = video.lesson
        section = lesson.section
        course = section.course
        expert = course.expert

        return "\n".join(
            [
                f"# {course.title}",
                f"Expert: {expert.name}",
                "",
                "",
            ]
        )
