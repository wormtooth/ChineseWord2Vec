import logging
import os

from utils.logger import FileLogger

# folder
HERE = os.path.dirname(os.path.realpath(__file__))
FOLDER = os.path.join(HERE, 'data')
if not os.path.exists(FOLDER):
    os.mkdir(FOLDER)

# zhwiki
ZHWIKI_URL = 'https://dumps.wikimedia.org/zhwiki/latest/zhwiki-latest-pages-articles.xml.bz2'
ZHWIKI_PATH = os.path.join(
    FOLDER,
    'zhwiki-latest-pages-articles.xml.bz2'
)
ZHWIKI_CLEANED_PATH = os.path.join(FOLDER, 'zhwiki-cleaned.txt')

# news2016zh
NEWS2016ZH_FILE_ID = '1TMKu1FpTr6kcjWXWlQHX7YJsMfhhcVKp'
NEWS2016ZH_ZIP_PATH = os.path.join(FOLDER, 'news2016zh.zip')
NEWS2016ZH_PATH = os.path.join(FOLDER, 'news2016zh_train.json')
NEWS2016ZH_CLEANED_PATH = os.path.join(FOLDER, 'news2016zh_cleaned.txt')


# stopwords
STOPWORDS_URL = 'https://raw.githubusercontent.com/stopwords-iso/stopwords-zh/master/stopwords-zh.json'
STOPWORDS_PATH = os.path.join(FOLDER, 'stopwords.json')

# logger
LOGGER_PATH = os.path.join(FOLDER, 'log.txt')
LOGGER = FileLogger(LOGGER_PATH, name='word2vec', level=logging.INFO)
LOGGER.log_to_stdout()