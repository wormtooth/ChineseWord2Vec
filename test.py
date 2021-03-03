from gensim.models import Word2Vec
from train import TrainLogger

if __name__ == '__main__':
    model = Word2Vec.load('data/zhwiki_vs100w5mc5.model')
    sim_words = model.wv.most_similar(
        positive=['国王', '女'],
        negative=['男'],
        topn=5
    )
    print(sim_words)