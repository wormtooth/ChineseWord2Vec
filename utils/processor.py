import json
import os
from multiprocessing import Process, Queue, Value
from typing import Iterable, List

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


def _worker(pipelines: List[Pipeline], source: Queue, sink: Queue):
    """Process articles from `soure` and put the processed article into `sink`.

    Note:
        `ConvertT2S` pipeline needs to be reinitialized in order to avoid problems
        on macOS.

    Args:
        pipelines (List[Pipeline]): list of pipelines to process articles.
        source (Queue): source of articles to process.
        sink (Queue): sink of processed articles.
    """
    pipelines = list(pipelines)
    for i, p in enumerate(pipelines):
        if isinstance(p, ConvertT2S):
            pipelines[i] = ConvertT2S()

    def processor(article):
        for p in pipelines:
            article = p(article)
        return article

    while True:
        article = source.get()
        if article == 'EXIT':
            return
        article = list(processor(article))
        sink.put(article)


def _writer(path: str, sink: Queue):
    """Write articles from `processor.sink` to disk.

    Args:
        path (str): Path to the file on disk.
        sink (Queue): Processed articles to write on disk.
    """
    writer = Write2File(path)
    logger = settings.LOGGER
    count = 0
    while True:
        article = sink.get()
        if article == 'EXIT':
            logger.info(f'All {count} articles saved to {path}.')
            return
        writer(article)
        count += 1
        if count % 10000 == 0:
            logger.info(f'{count} articles processed.')


class Processor(Pipeline):

    def __init__(self,  pipelines=[]):
        self.pipelines = pipelines
        self.logger = settings.LOGGER

    def process(self, article):
        for func in self.pipelines:
            article = func(article)
        return article

    def process_all_single_thread(self,
                                  articles: Iterable[Iterable[str]],
                                  output_path: str):
        """Process all articles within a single thread.

        Args:
            articles (Iterable[Iterable[str]]): Articles to process.
            output_path (str): Path to the output file on disk to save processed articles.
        """
        self.logger.info('Begin to process all articles ...')

        count = 0
        writer = Write2File(output_path)
        for article in articles:
            article = self.process(article)
            writer.process(article)
            count += 1
            if count % 10000 == 0:
                self.logger.info(f'{count} articles processed.')

        self.logger.info(
            f'Finish writing {count} processed articles to {output_path}')

    def process_all(self,
                    articles: Iterable[Iterable[str]],
                    output_path: str,
                    use_multiprocessing: bool = True,
                    workers: int = 4, max_queue_size: int = 1000):
        """Process all articles.

        Args:
            articles (Iterable[Iterable[str]]): Articles to process.
            output_path (str): Path to the output file on disk to save processed articles.
            use_multiprocessing (bool, optional): Whether to use multi processes. Defaults to True.
            workers (int, optional): Number of workers to process articles. Defaults to 4.
            max_queue_size (int, optional): Maxixum size for both queues source and sink.
                Defaults to 1000.
        """

        if not use_multiprocessing:
            return self.process_all_single_thread(articles, output_path)

        workers = max(workers, 1)

        self.logger.info('Begin to process all articles ...')

        # create Queue for multiprocessing
        source = Queue(maxsize=max_queue_size)
        sink = Queue(maxsize=max_queue_size)

        # create worker processes
        worker_processes = []
        for _ in range(workers):
            worker_proc = Process(
                target=_worker,
                args=(self.pipelines, source, sink)
            )
            worker_proc.daemon = True
            worker_proc.start()
            worker_processes.append(worker_proc)
        self.logger.info(f'{workers} processes start to process articles.')

        # create writer process
        writer_proc = Process(target=_writer, args=(output_path, sink))
        writer_proc.daemon = True
        writer_proc.start()
        self.logger.info(
            f'A process starts to write processed article to disk.')

        # put articles into source for workers to process
        count = 0
        for article in articles:
            source.put(article)
            count += 1
        for _ in range(workers):
            source.put('EXIT')

        for p in worker_processes:
            p.join()
        self.logger.info(f'Finish processing {count} articles.')

        sink.put('EXIT')
        writer_proc.join()

    def __repr__(self):
        return f'Processor(pipelines={repr(self.pipelines)}'
