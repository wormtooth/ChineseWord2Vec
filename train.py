import argparse
import logging
import os

from gensim.models import Word2Vec
from gensim.models.word2vec import LineSentence
from gensim.models.callbacks import CallbackAny2Vec

import settings

logger = settings.LOGGER


class TrainLogger(CallbackAny2Vec):

    def __init__(self):
        self.epoch = 0
        self.loss_prev = 0.0
        self.test_words = ['学习', '国家', '汽车', '狗', '高兴']

    def on_train_begin(self, model):
        logger.info(f'Training begins ...')

    def on_train_end(self, model):
        logger.info(f'Training ends.')

    def on_epoch_begin(self, model):
        self.epoch += 1
        logger.info(f'Epoch {self.epoch} begins ...')

    def on_epoch_end(self, model):
        running_loss = model.get_latest_training_loss()
        loss = running_loss - self.loss_prev
        self.loss_prev = running_loss
        logger.info(f'Epoch {self.epoch} ends with loss: {loss:.4f}.')
        for word in self.test_words:
            similar_words = model.wv.most_similar(word, topn=5)
            logger.info(f'Similar words of {word}: {similar_words}')


@logger.catch(level=logging.WARNING)
def train(opts):
    # model path
    name = f'{opts.name_prefix}_vs{opts.vector_size}w{opts.window}mc{opts.min_count}.model'
    path = os.path.join(settings.FOLDER, name)

    # train model
    model = Word2Vec(
        corpus_file=opts.input_file,
        size=opts.vector_size,
        window=opts.window,
        min_count=opts.min_count,
        iter=opts.epochs,
        workers=opts.workers,
        compute_loss=True,
        callbacks=[TrainLogger()],
    )

    # save model
    logger.info('Saving model ...')
    model.save(path)
    logger.info(f'Saved model to {path}')


def get_train_options():
    parser = argparse.ArgumentParser(
        description="Train Chinese Word2Vec",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '--vector_size', '-vs', type=int, default=100,
        help='Dimensionality of the word vectors.'
    )
    parser.add_argument(
        '--window', '-w', type=int, default=5,
        help='Maximum distance between the current and predicted word within a sentence.'
    )
    parser.add_argument(
        '--min_count', '-mc', type=int, default=5,
        help='Ignores all words with total frequency lower than this.'
    )
    parser.add_argument(
        '--workers', type=int, default=4,
        help='Use these many worker threads to train the model.'
    )
    parser.add_argument(
        '--epochs', '-e', type=int, default=5,
        help='Number of iterations (epochs) over the corpus. '
    )
    parser.add_argument(
        '--input_file', '-i', type=str, default=settings.ZHWIKI_CLEANED_PATH,
        help='Input file to train the model. '
        'Format: each row is an article or a sentence, with words separated by whitespace.',
    )
    parser.add_argument(
        '--name_prefix', '-np', type=str, default='wordvec',
        help='Name prefix for the model. '
        'The actual name consist of the prefix and some other parameters of the model.'
    )
    opts = parser.parse_args()
    return opts


if __name__ == '__main__':
    opts = get_train_options()
    train(opts)
