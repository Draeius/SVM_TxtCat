import json
from collections import Counter
from progress.counter import Counter as PCounter
from progress.bar import ChargingBar
from sklearn.model_selection import GridSearchCV
from sklearn.svm import SVC
from data import SetFactory
from preprocessing import PreprocessorFactory

import data
import preprocessing


class Cache:

    _recreateCacheFile = False

    def __init__(self, dtype='reuters'):
        self._articleCount = 0
        self._words = {}
        self._bestParams = {"C": 1000, "gamma": 0.001, "kernel": "rbf"}
        self._categories = []
        if self._recreateCacheFile:
            self.writeCache(dtype)

        self.getCache()

    @property
    def articleCount(self) -> int:
        return self._articleCount

    @property
    def words(self):
        return self._words

    @property
    def bestParamsSmall(self):
        return self._bestParamsLarge

    @property
    def bestParamsLarge(self):
        return self._bestParamsLarge

    @property
    def categories(self):
        return self._categories
    
    def getCache(self):
        # read cache from cache file
        try:
            file = open("cache", "r")
        except FileNotFoundError:
            print("initializing Cache")
            self.writeCache()

        data = json.load(file)
        self._articleCount = data['articleCount']
        self._words = data['words']
        self._bestParamsSmall = data['bestParamsSmall']
        self._bestParamsLarge = data['bestParamsLarge']
        self._categories = Counter(data['categories'])

    def analyzeArticles(self, preprocessor: preprocessing.Preprocessor, dtype='reuters'):
        #check data type
        if dtype == 'reuters':
            #initialize SoupLoader
            soupLoader = data.SoupLoader(-1)
            provider = data.ReutersProvider(soupLoader)
        else:
            provider = data.TwentyNewsProvider('../TwentyNews/')

        #start Counters
        bar = PCounter("Analyzing Articles: ")
        counter = Counter()
        occurances = Counter()
        categories = Counter()
        while True:
            try:
                #increase bar progress
                bar.next()
                
                #throws an exception if there are no more articles. saving is not needed
                article = data.ArticleFactory.GET_NEXT_ARTICLE(provider)

                #update the counter with the preprocessed array of words
                words = preprocessor.process(article).preprocessed
                counter.update(words)
                #update in how many articles these words occur
                occurances.update(list(words.keys()))
                #update categories counter
                categories.update([article.category])

            except data.OutOfArticlesError:
                #abort while loop. No more Articles
                break
        
        bar.finish()

        self._articleCount = bar.index
        self._words = self.cropWords(counter, occurances)
        self._categories = categories

    def cropWords(self, words: Counter, occurances: Counter) -> Counter:
        result = Counter()
        for word in words:
            #check if word is within acceptable bounds
            if words[word] >= 10 and words[word] < 10000 and occurances[word] > 10:
                result.update([word])
        
        #print 10 most common words
        print(words.most_common(10))

        #reset counter to zero
        for x in result:
            result[x] = 0

        print("Total word count: " + str(len(result)))

        return result

    def recalcBestParams(self, limitCategories = -1):
        #init Preprocessor
        preprocessor = PreprocessorFactory.FACTORY(list(
            self.words.keys()))

        #categories limited to the most x common ones?
        if limitCategories > 0:
            categories = [item[0] for item in list(self.categories.most_common(limitCategories))]
        else:
            #all categories allowed
            categories = []

        #prepare dataset
        dataSet = SetFactory.PREPARE_DATASET(int(self.articleCount / 2), preprocessor,
                self.articleCount, categories)

        #init GridSearch for best parameters
        gsc = GridSearchCV(
        estimator=SVC(kernel='rbf'),
        param_grid=[{
            'C': [1, 100, 1000],
            'gamma': [0.001, 0.005, 0.1, 1, 3, 5],
            'kernel': ['linear']
        },
        {
            'C': [1, 100, 1000],
            'gamma': [0.001, 0.005, 0.1, 1, 3, 5],
            'kernel': ['rbf']
        },
        {
            'C': [1, 100, 1000],
            'degree': [1, 2, 3, 4, 5],
            'gamma': [0.001, 0.005, 0.1, 1, 3, 5],
            'kernel': ['poly']
        }],
        cv=5, scoring=None, verbose=5, n_jobs=1)

        #do it!!
        gridResult = gsc.fit(dataSet[0].getTextArray(), dataSet[0].getCategories())

        return gridResult.best_params_

    def writeCache(self, dtype='reuters'):
        #save the cache file
        cache = {}
        
        self.analyzeArticles(preprocessing.PreprocessorFactory.CACHE_FACTORY(), dtype)

        cache['articleCount'] = self.articleCount
        cache['bestParamsLarge'] = self.bestParamsLarge
        cache['bestParamsSmall'] = self.bestParamsSmall
        cache['words'] = self.words
        cache['categories'] = self.categories

        file = open("cache", "w+")
        file.write(json.dumps(cache))
        file.close()
