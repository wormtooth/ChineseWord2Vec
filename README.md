# 中文词向量

本项目使用 [gensim](https://radimrehurek.com/gensim/models/word2vec.html) 和新闻、维基百科等中文语料来训练获取中文词向量。使用前请安装 `requirements.txt` 中的库：

```bash
pip install -r requirements.txt
```

## 维基百科语料

在此项目根目录下执行：

```bash
python zhwiki.py
```

这会自动下载、预处理并训练词向量。所有的数据存在 **data** 文件夹中。下载的数据是 **zhwiki-latest-pages-articles.xml.bz2** ，大概是 2G。处理好的数据是 **zhwiki-cleaned.txt**，大概是 1.1G。模型存在 **zhwiki_vs100w5mc5.model** 和其他相关文件中，加起来大概 600M。

## 新闻语料

在此项目根目录下执行：

```bash
python news2016zh.py
```

这会自动下载、解压、预处理并训练词向量。所有的数据存在 **data** 文件夹中。下载的数据是 **news2016zh.zip** ，大概是 3.6G。解压得到两个 json 文件：**news2016zh_train.json (8.3G)** 和 **news2016zh_valid.json (271M)**。 处理好的数据是 **news2016_cleaned.txt (5.7 G)**。模型存在 **news2016_vs100w5mc5.model** 和其他相关文件中，加起来大概 800M。

## 其他语料

如果有其他语料，我们可以使用 **train.py** 训练词向量。比如

```bash
python train.py --input_file path\to\input\file --name_prefix=chinese_word2vec
```

使用的语料 (input_file) 的每一行代表一个句子或者一篇文章，必须使用空格将各个词分开。请查看 **train.py** 代码或者使用

```
python train.py --help
```

了解如何使用 **train.py**。

## 待解决问题

- [x] 语料预处理无法使用多进程。