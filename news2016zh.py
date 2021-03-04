import json
import os

import settings
from train import get_train_options, train
from utils import unzip
from utils.download import download_gdoc
from utils.processor import (CutSentence, Processor, RemoveNonChineseWords,
                             RemoveStopwords)

logger = settings.LOGGER


def download_news2016zh():
    zip_path = settings.NEWS2016ZH_ZIP_PATH
    if os.path.exists(zip_path):
        logger.info(f'news2016zh already downloaded at {zip_path}')
        return
    logger.info('news2016zh downloading ...')
    download_gdoc(settings.NEWS2016ZH_FILE_ID, zip_path)
    logger.info(f'news2016zh downloaded to {zip_path}')


def unzip_news2016zh():
    path = settings.NEWS2016ZH_PATH
    if os.path.exists(path):
        logger.info(f'news2016zh already decompressed.')
        return
    zip_path = settings.NEWS2016ZH_ZIP_PATH
    folder = settings.FOLDER
    logger.info('news2016zh decompressing ...')
    unzip(zip_path, folder)
    logger.info(f'news2016zh decompressed to {folder}')


def article_gen(path):
    with open(path, 'r') as f:
        for line in f:
            article = json.loads(line)['content']
            yield [article]


def preprocess_news2016zh():
    input_path = settings.NEWS2016ZH_PATH
    output_path = settings.NEWS2016ZH_CLEANED_PATH
    if os.path.exists(output_path):
        logger.info(f'{output_path} existed. Skip preprocess.')
        logger.info(f'Delete {output_path} if preprocess needs to be redone.')
        return
    processor = Processor(
        pipelines=[
            CutSentence(),
            RemoveNonChineseWords(),
            RemoveStopwords(),
        ],
    )
    processor.process_all(article_gen, input_path, output_path)


def train_news2016zh():
    opts = get_train_options()
    opts.input_file = settings.NEWS2016ZH_CLEANED_PATH
    opts.name_prefix = 'news2016zh'
    train(opts)


if __name__ == '__main__':
    download_news2016zh()
    unzip_news2016zh()
    preprocess_news2016zh()
    train_news2016zh()
