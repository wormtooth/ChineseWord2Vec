import os
from train import get_train_options

from gensim.corpora import WikiCorpus, dictionary

import settings
from utils.download import download
from utils.processor import (ConvertT2S, CutSentence, Processor,
                             RemoveNonChineseWords, RemoveStopwords)
from train import train, get_train_options

logger = settings.LOGGER


def download_zhwiki():
    path = settings.ZHWIKI_PATH
    if os.path.exists(path):
        logger.info(f'zhwiki already downloaded at {path}')
        return
    url = settings.ZHWIKI_URL
    logger.info(f'zhwiki downloading from {url} ...')
    download(url, path)
    logger.info(f'zhwiki downloaded: {path}')


def preprocess_zhwiki():
    output_path = settings.ZHWIKI_CLEANED_PATH
    if os.path.exists(output_path):
        logger.info(f'{output_path} existed. Skip preprocess.')
        logger.info(f'Delete {output_path} if preprocess needs to be redone.')
        return

    input_path = settings.ZHWIKI_PATH
    processor = Processor([
        ConvertT2S(),
        CutSentence(),
        RemoveNonChineseWords(),
        RemoveStopwords(),
    ])
    wiki = WikiCorpus(input_path, dictionary={})
    processor.process_all(wiki.get_texts(), output_path)


def train_zhwiki():
    opts = get_train_options()
    opts.input_file = settings.ZHWIKI_CLEANED_PATH
    opts.name_prefix = 'zhwiki'
    train(opts)


if __name__ == '__main__':
    download_zhwiki()
    preprocess_zhwiki()
    train_zhwiki()
