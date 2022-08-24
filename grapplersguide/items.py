# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html
import dataclasses as dc
import pathlib
from typing import FrozenSet, Optional, Tuple


@dc.dataclass(frozen=True)
class Expert:
    name: str

    # TODO(dfrank): Implement other rich comparisons
    def __lt__(self, other):
        return self.name < other.name


@dc.dataclass(frozen=True)
class Course:
    title: str
    expert: Expert

    def __lt__(self, other):
        if self.expert is other.expert or self.expert == other.expert:
            return self.title < other.title
        return self.expert < other.expert


@dc.dataclass(frozen=True)
class Section:
    position: int
    title: str
    course: Course

    def __lt__(self, other):
        if self.course is other.course or self.course == other.course:
            return self.position < other.position
        return self.course < other.course


@dc.dataclass(frozen=True)
class Lesson:
    position: int
    title: str
    url: str
    section: Section
    breadcrumbs: Optional[Tuple[str, ...]] = None
    tags: Optional[FrozenSet[str]] = None

    def __lt__(self, other):
        if self.section is other.section or self.section == other.section:
            return self.position < other.position
        return self.section < other.section


@dc.dataclass(frozen=True)
class Video:
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
    download_path: Optional[pathlib.Path] = None

    def __lt__(self, other):
        if self.lesson is other.lesson or self.lesson == other.lesson:
            return self.file_name < other.file_name
        return self.lesson < other.lesson
