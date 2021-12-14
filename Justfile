set dotenv-load := true

_default:
    @just --list

# Crawl using the specified spider.
crawl SPIDER="courses":
    poetry run scrapy crawl \
        -a "username=${GRAPPLERSGUIDE_USERNAME}" \
        -a "password=${GRAPPLERSGUIDE_PASSWORD}" \
        "{{SPIDER}}"
