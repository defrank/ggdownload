# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html
import dataclasses as dc
from typing import FrozenSet, List, Optional, Tuple


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
    download_url: List[str]
    lesson: Lesson
