set dotenv-load := true

_default:
    @just --list

# Setup developer environment.
setup: install

# Poetry install.
install:
    poetry install

# Crawl using the specified spider.
get EXPERT_REGEX COURSE_REGEX=".+" OUTPUT_DIR=`pwd` FLAT_OUTPUT="0":
    poetry run scrapy crawl \
        -a "username=${GRAPPLERSGUIDE_USERNAME}" \
        -a "password=${GRAPPLERSGUIDE_PASSWORD}" \
        -a "expert_regex={{EXPERT_REGEX}}" \
        -a "course_regex={{COURSE_REGEX}}" \
        -s "FLAT_OUTPUT={{FLAT_OUTPUT}}" \
        -s "OUTPUT_DIR={{OUTPUT_DIR}}" \
        expert-courses
