from pathlib import Path
from typing import List, Optional, Counter

import numpy as np
from progress.bar import ChargingBar
from bs4 import BeautifulSoup
import data


class OutOfArticlesError(Exception):
    pass


class Article:
    #contains one Text and its data

    def __init__(self, text: str, category: str):
        self.text = text
        self.category = category
        self.preprocessed = Counter()

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, text: str) -> None:
        #check if text is none
        if text == None:
            raise ValueError("Text must not be None")

        #strip unnecessary whitespaces
        text = text.strip()

        #check if text is empty
        if text == "":
            raise ValueError("Text must not be empty.")

        self._text = text

    @property
    def category(self) -> str:
        return self._category

    @category.setter
    def category(self, category: str) -> None:
        #check if category is none
        if category == None:
            raise ValueError("Category must not be None")

        #strip unnecessary whitespaces
        category = category.strip()

        #check if category is empty
        if category == "":
            raise ValueError("Category must not be empty.")

        self._category = category

    @property
    def preprocessed(self) -> Counter:
        return self._preprocessed

    @preprocessed.setter
    def preprocessed(self, preprocessed: Counter):
        self._preprocessed = preprocessed

    @property
    def vector(self) -> List[int]:
        return list(self.preprocessed.values())

    @property
    def normalized(self) -> List[int]:
        return self.vector / np.linalg.norm(self.vector)

    def process(self, preprocessor):
        self.preprocessed = preprocessor.process(self).preprocessed


class SoupLoader:

    _max = 22

    def __init__(self, stopAtFileNumber):
        self._stopAt = stopAtFileNumber
        self._currentSoup = None
        self._startedSearch = False
        self._counter = 0

    def _stopAtFile(self) -> bool:
        return (self._stopAt > -1) and (self._counter == self._stopAt)

    def _getPath(self) -> Path:
        return Path('../Reuters/')

    def _getNextFile(self, increment=True) -> Optional[Path]:
        #as the files are numbered:
        #if counter is max, return None
        if (self._counter == self._max):
            return None

        #stop somewhere in the middle?
        if self._stopAtFile():
            #stop just once
            self._stopAt = -1
            return None

        #create the filename with leading zero
        filename = 'reut2-{}.sgm'.format(f"{self._counter:03d}")

        if (increment):
            self._counter += 1

        return self._getPath() / filename

    def _getNextSoup(self) -> Optional[BeautifulSoup]:
        #get file Directory
        fileDir = self._getNextFile()
        if (fileDir == None):
            return None

        #open file
        f = open(fileDir, 'r')
        data = f.read()

        return BeautifulSoup(data, "html.parser")

    def getCurrentSoup(self) -> Optional[BeautifulSoup]:
        if self._currentSoup == None:
            #started a new file, so reset flag
            self._startedSearch = False
            self._currentSoup = self._getNextSoup()

        return self._currentSoup

    def getNextReutersTag(self) -> Optional[BeautifulSoup]:
        soup = self.getCurrentSoup()

        #already started searching
        if self._startedSearch:
            tag = soup.find_next("reuters")
            if tag == None:
                #end of file, start with next one
                self._currentSoup = self._getNextSoup()
                self._startedSearch = False
                return self.getNextReutersTag()
        else:
            self._startedSearch = True
            #is there a soup to search in?
            if soup != None:
                tag = soup.find("reuters")
            else:
                #no further files
                return None

        #set soup to tag, in order to not find the same tag over and over again
        self._currentSoup = tag
        return tag


class AbstractProvider:
    
    def getCategory(self) -> str:
        pass

    def getText(self) -> str:
        pass

    def next(self):
        pass

    def isValidElement(self):
        pass


class ReutersProvider(AbstractProvider):

    def __init__(self, soupLoader: SoupLoader):
        self._soupLoader = soupLoader
        self._soup = None

    def getCategory(self) -> str:
        #check topics tag
        topics = self._soup.find("topics")

        if topics == None:
            #topics not found, search places
            topics = self._soup.find("places")

        if topics != None:
            #extract topic wrapper
            ds = topics.find("d")
            #check if there is a wrapper
            if ds != None:
                return ds.text

        #no suitable topic found, raise error
        raise ValueError("There was no suitable topic found in the article")


    def getText(self) -> str:
        #search for main body
        body = self._soup.find("body")
        if body != None:
            #body found, return text
            return body.text

        #no main body found -> no article -> raise error
        raise ValueError("There was no text found in this article")

    def next(self):
        self._soup = self._soupLoader.getNextReutersTag()

    def isValidElement(self):
        return self._soup != None
    
class TwentyNewsProvider(AbstractProvider):

    def __init__(self, filePath):
        self.dataSet = []
        self._current = -1
        self._max = 0
        self.load(filePath)
        
    def load(self, filePath):
        entries = Path(filePath)
        dataSet = []
        path = [x for x in entries.iterdir() if x.is_dir()]
        for directory in path:
            direct = [x for x in directory.iterdir()]
            print(directory.name)
            for afile in direct:
                f = afile.open()
                text = f.readlines()
                del text[0:2]
                newText = " ".join(text)
                newText = newText.strip()
                notAllowed = [None, ""]
                if newText not in notAllowed:
                    try:
                        article = Article(newText, directory.name)
                        dataSet.append(article)
                    except ValueError as error:
                        import sys
                        #extend stacktrace and message of cought exception
                        raise type(error)("The file: " + str(afile) + "had an error:\n" + "Could not create Article. Reason: " + str(error)).with_traceback(sys.exc_info()[2])
                
        self._max = len(dataSet)
        self.dataSet = dataSet
                
    def getCategory(self):
        return self.dataSet[self._current].category
        
    def getText(self):
        return self.dataSet[self._current].text
        
    def next(self):
        self._current = self._current + 1
        
    def isValidElement(self):
        if self._current < self._max:
            return True
        else:
            return False


class ArticleFactory:

    @staticmethod
    def FACTORY(provider: AbstractProvider, allowedCategories = []) -> Article:
        try:
            #get the category of the article
            category = provider.getCategory()
            #get the text of the article
            text = provider.getText()

            #if allowedCategories is empty, all are allowed, check for categories otherwise
            if len(allowedCategories) == 0:
                return Article(text, category)
            elif category in allowedCategories:
                return Article(text, category)
            else:
                raise ValueError("Category not allowed.")

        except ValueError as error:
            import sys
            #extend stacktrace and message of cought exception
            raise type(error)("Could not create Article. Reason: " +
                              str(error)).with_traceback(sys.exc_info()[2])

    @staticmethod
    def GET_NEXT_ARTICLE(provider: AbstractProvider, allowedCategories = []) -> Article:
        provider.next()
        while provider.isValidElement():
            try:
                article = ArticleFactory.FACTORY(provider, allowedCategories)
            except ValueError:
                #Article is probably faulty, so just skip it
                provider.next()
            else:
                #creation worked, return the article
                return article

        raise OutOfArticlesError("No more articles found")


class DataSet:

    def getTextArray(self):
        return self._textArray

    def getCategories(self):
        return self._categories

    def getPreprocessed(self):
        return self._preprocessed

    def setTextArray(self, textArray):
        self._textArray = textArray

    def setCategories(self, categoryArray):
        self._categories = categoryArray

    def append(self, article: Article) -> None:
        #append article to arrays
        if article.preprocessed != []:
            self._textArray.append(article.normalized)
            self._preprocessed.append(article.preprocessed)
            self._categories.append(article.category)

    def __init__(self):
        self._textArray = []
        self._preprocessed = []
        self._categories = []


class SetFactory:
    from preprocessing import Preprocessor

    @staticmethod
    def PREPARE_DATASET(trainingArticleCount, preprocessor: Preprocessor,
                        maxArticles, allowedCategories = [], dtype='reuters') -> List[DataSet]:
        #create Array with two datasets. One training, one test
        dataSet = [DataSet(), DataSet()]
        #check datatype and initialize provider
        if dtype == 'reuters':
            soupLoader = SoupLoader(-1)
            provider = ReutersProvider(soupLoader)
        else:
            provider = TwentyNewsProvider('../TwentyNews/')

        #start nice percentage bar. Good to have visuals ;)
        bar = ChargingBar("Preparing dataset: ", max=maxArticles)
        while bar.index <= maxArticles:
            try:
                #try to create a new article
                article = ArticleFactory.GET_NEXT_ARTICLE(provider, allowedCategories)
                article.process(preprocessor)

                #append the article to the dataset
                dataSet[int(bar.index / trainingArticleCount)].append(article)
                
                bar.next()
            except OutOfArticlesError:
                #bar would stop at 99% if not increased once more
                bar.next()
                break

        bar.finish()
        return dataSet
