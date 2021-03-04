import json
import os
from multiprocessing import Process, Queue, Value
from typing import Iterable

import jieba
import settings
from opencc import OpenCC

from .download import download


class Pipeline:
    """Base class to process an article.

    All subclasses of `Pipeline` needs to implement `process(article)`.

    Instances of `Pipeline` and its subclasses are callable, redirected to
    `self.process`.
    """

    def process(self, article: Iterable[str]) -> Iterable[str]:
        """Method to process an article.

        Args:
            article (Iterable[str]): Iterable of tokens in an article.

        Raises:
            NotImplementedError: Subclass needs to implement this method,
            otherwise, NotImplementedError will be raised.

        Returns:
            Iterable[str]: Iterable of tokens in the processed article.
        """
        raise NotImplementedError()

    def __call__(self, article):
        return self.process(article)

    def __repr__(self):
        return self.__class__.__name__


class ConvertT2S(Pipeline):
    """Convert traditional Chinese to simplified Chinese using OpenCC.
    """

    def __init__(self):
        super().__init__()
        self.converter = OpenCC('t2s.json')

    def process(self, article):
        return map(self.converter.convert, article)


class CutSentence(Pipeline):
    """Cut sentences of an article into tokens using jieba.
    """

    def process(self, article):
        for phrase in article:
            yield from jieba.cut(phrase)


class RemoveNonChineseWords(Pipeline):
    """Remove non Chinese tokens.
    """

    def process(self, article):
        return filter(self.filter_func, article)

    def filter_func(self, s):
        return all('\u4e00' < c < '\u9fff' for c in s)


class RemoveStopwords(Pipeline):
    """Remove stopwords of an article.

    Args:
        stopwords (Iterable[str], optional): stopwords, default to None.
        By default, it fetches stopwords from stopwords-iso/stopwords-zh.
    """

    def __init__(self, stopwords: Iterable[str] = None):
        super().__init__()
        if stopwords is None:
            if not os.path.exists(settings.STOPWORDS_PATH):
                download(settings.STOPWORDS_URL, settings.STOPWORDS_PATH)
            with open(settings.STOPWORDS_PATH, 'r') as f:
                stopwords = json.load(f)
        self.stopwords = set(stopwords)

    def process(self, article):
        return filter(self.filter_func, article)

    def filter_func(self, w):
        return w not in self.stopwords


class Write2File(Pipeline):
    """Write an article to file.

    Args:
        path (str): path to the file on disk.
        mode (str, optional): mode used to open the file. Default to 'w'.
        separator (str, optional): separator of tokens of the article.
        Default to whitespace.
    """

    def __init__(self, path: str, mode: str = 'w', separator: str = ' '):
        super().__init__()
        self.path = path
        self.out = open(path, mode)
        self.separator = separator

    def process(self, article):
        self.out.write(self.separator.join(article))
        self.out.write('\n')
        return article


def enqueue_articles(processor: 'Processor'):
    """Read articles from `processor.articles` and put them into `processor.source`.

    Args:
        processor (Processor): The processor is a subclass of `Pipeline`, and it contains
        multiple pipelines to process articles.
    """
    for article in processor.articles_gen(processor.input_path):
        processor.source.put(article)
    for _ in range(processor.workers):
        processor.source.put('EXIT')


def process_articles(processor: 'Processor'):
    """Process articles from `processor.soure` and put the processed article
    into `processor.sink`.

    Args:
        processor (Processor): The processor is a subclass of `Pipeline`, and it contains
        multiple pipelines to process articles.
    """
    while True:
        article = processor.source.get()
        if article == 'EXIT':
            return
        article = list(processor(article))
        processor.sink.put(article)


def write_articles(processor: 'Processor'):
    """Write articles from `processor.sink` to disk.

    Args:
        processor (Processor): The processor is a subclass of `Pipeline`, and it contains
        multiple pipelines to process articles.
    """
    writer = Write2File(processor.output_path)
    while True:
        article = processor.sink.get()
        if article == 'EXIT':
            return
        processor.articles_count.value += 1
        if processor.articles_count.value % 10000 == 0:
            processor.logger.info(
                f'{processor.articles_count.value} articles processed.')
        writer(article)


class Processor(Pipeline):

    def __init__(self,  pipelines=[]):
        self.pipelines = pipelines
        self.logger = settings.LOGGER

    def process(self, article):
        for func in self.pipelines:
            article = func(article)
        return article

    def process_all_single_thread(self,
                                  article_gen,
                                  input_path,
                                  output_path):
        self.logger.info('Begin to process all articles ...')
        articles_count = 0
        writer = Write2File(output_path)
        for article in article_gen(input_path):
            article = self.process(article)
            writer.process(article)
            articles_count += 1
            if articles_count % 10000 == 0:
                self.logger.info(f'{articles_count} articles processed.')
        self.logger.info(f'Finish processing all articles.')
        self.logger.info(
            f'Finish writing all processed articles to {output_path}')
        self.logger.info(f'Processed {articles_count} articles')

    def process_all(self,
                    articles_gen,
                    input_path,
                    output_path,
                    use_multiprocessing=False,
                    workers=4, max_queue_size=1000):

        if not use_multiprocessing:
            return self.process_all_single_thread(articles_gen, input_path, output_path)

        self.articles_gen = articles_gen
        self.input_path = input_path
        self.output_path = output_path
        self.workers = max(workers, 1)

        self.logger.info('Begin to process all articles ...')
        self.source = Queue(maxsize=max_queue_size)
        self.sink = Queue(maxsize=max_queue_size)
        self.articles_count = Value('L', 0)

        processes = []

        reader_proc = Process(target=enqueue_articles, args=(self, ))
        reader_proc.daemon = True
        reader_proc.start()
        self.logger.info('A process starts to read articles to be processed.')
        processes.append(reader_proc)

        for _ in range(self.workers):
            worker_proc = Process(target=process_articles, args=(self, ))
            worker_proc.daemon = True
            worker_proc.start()
            processes.append(worker_proc)
        self.logger.info(f'{workers} processes start to process articles.')

        writer_proc = Process(target=write_articles, args=(self, ))
        writer_proc.daemon = True
        writer_proc.start()
        self.logger.info(
            f'A process starts to write processed article to disk.')

        for p in processes:
            p.join()
        self.logger.info(f'Finish processing all articles.')

        self.sink.put('EXIT')
        writer_proc.join()
        self.logger.info(
            f'Finish writing all processed articles to {output_path}')
        self.logger.info(f'Processed {self.articles_count.value} articles')

    def __repr__(self):
        return f'Processor(pipelines={repr(self.pipelines)}'
