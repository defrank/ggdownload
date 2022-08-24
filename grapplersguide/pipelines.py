# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
#
# useful for handling different item types with a single interface
# from itemadapter import ItemAdapter
import dataclasses as dc
import functools as fn
import logging
import os.path
import pathlib
from typing import Optional, Union

import itemadapter
import scrapy.http
import scrapy.pipelines.files
import scrapy.settings

from . import items, spiders


def _get_output_dir(settings: scrapy.settings.Settings) -> pathlib.Path:
    return settings.get("OUTPUT_DIR", pathlib.Path.cwd())


def _get_flat_output(settings: scrapy.settings.Settings):
    return settings.getbool("FLAT_OUTPUT", default=False)


class LessonVideosPipeline(scrapy.pipelines.files.FilesPipeline):
    _flat_output: bool
    _output_dir: pathlib.Path

    def __init__(
        self,
        output_dir: Union[str, pathlib.Path],
        flat_output: bool,
    ):
        self._output_dir = pathlib.Path(output_dir).resolve()
        self._flat_output = flat_output
        super().__init__(store_uri=self._output_dir.as_uri())
        # TODO(dfrank): Fix allowing redirects from settings
        self.allow_redirects = True
        self._handle_statuses(self.allow_redirects)

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
        if not isinstance(item, items.Video):
            raise scrapy.exceptions.DropItem(item)
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
        if not isinstance(item, items.Video):
            raise scrapy.exceptions.DropItem(f"item is not a video: {item}")

        video = item
        lesson = video.lesson
        section = lesson.section
        course = section.course
        expert = course.expert
        relative_path = os.path.join(
            expert.name,
            course.title,
            f"{section.position:02d} - {section.title}",
            " ".join(
                [
                    f"{lesson.position:02d}",
                    "-",
                    lesson.title,
                    f"({video.public_name}).{video.extension}",
                ]
            ),
        )
        self.logger.debug("Built relative file path: %s", relative_path)
        return relative_path

    def get_media_requests(self, item: items.Video, info):
        self.logger.debug(
            "Getting media requests for item=%s info=%s",
            item,
            info,
        )
        adapter = itemadapter.ItemAdapter(item)
        yield scrapy.Request(adapter["download_url"])

    def item_completed(self, results, item: items.Video, info):
        if not results:
            raise scrapy.exceptions.DropItem(
                f"Nothing downloaded for item: {item}",
            )
        for ok, result in results:
            if isinstance(result, BaseException):
                self.logger.critical(
                    "Unhandled error downloading item: %s",
                    item,
                    exc_info=result,
                )
                raise scrapy.exceptions.CloseSpider(
                    reason=result.__class__.__name__,
                ) from result
            elif not ok:
                raise scrapy.exceptions.DropItem(
                    f"Failed to download {item}: {result}",
                )

        self.logger.debug(
            "Item is complete: results=%s item=%s info=%s",
            results,
            item,
            info,
        )
        video_path = next(result["path"] for ok, result in results if ok)
        return dc.replace(item, download_path=video_path)

    def close_spider(self, spider: spiders.ExpertCoursesSpider):
        self.logger.debug("Closing %s spider", spider.name)

    @classmethod
    def from_settings(cls, settings: scrapy.settings.Settings):
        logger = logging.getLogger(f"{__name__}.{cls.__name__}")
        logger.debug("Files store: %s", settings.get("FILES_STORE"))
        return cls(
            output_dir=_get_output_dir(settings),
            flat_output=_get_flat_output(settings),
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
            "Processing %s spider item: %s",
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
    def from_settings(cls, settings: scrapy.settings.Settings):
        return cls(output_dir=_get_output_dir(settings))

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
