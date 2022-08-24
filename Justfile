set dotenv-load := true

_default:
    @just --list

# Setup developer environment.
setup: install

# Poetry install.
install:
    poetry install

# Crawl using the specified spider.
crawl SPIDER="expert-courses" FLAT_OUTPUT="0" OUTPUT_DIR=`pwd`:
    poetry run scrapy crawl \
        -a "username=${GRAPPLERSGUIDE_USERNAME}" \
        -a "password=${GRAPPLERSGUIDE_PASSWORD}" \
        -s "FLAT_OUTPUT={{FLAT_OUTPUT}}" \
        -s "OUTPUT_DIR={{OUTPUT_DIR}}" \
        "{{SPIDER}}"
