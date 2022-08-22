# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
# from itemadapter import ItemAdapter
import functools as fn
import logging


class CoursePipeline:
    def open_spider(self, spider):
        self.logger.debug("Spider opened: %s", spider.name)

    def process_item(self, item, spider):
        self.logger.debug("Pipeline processed %s item: %s", spider.name, item)
        return item

    def close_spider(self, spider):
        self.logger.debug("Spider closed: %s", spider.name)

    @fn.cached_property
    def logger(self):
        return logging.getLogger(f"{__name__}.{self.__class__.__name__}")
