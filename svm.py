import numpy as np
from progress.bar import ChargingBar
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, recall_score, precision_score

from cache import Cache
from data import SetFactory
from preprocessing import PreprocessorFactory


class SVMWrapper:

    def __init__(self, limitCategories = -1, dtype = 'reuters'):
        #init cache
        self._cache = Cache()

        #get preprocessors
        preprocessor = PreprocessorFactory.FACTORY(list(
            self._cache.words.keys()))

        #check if categories are limites
        if limitCategories > 0:
            #get allowed categories
            categories = [item[0] for item in list(self._cache.categories.most_common(limitCategories))]
        else:
            categories = []

        #get the dataset
        self._dataSet = SetFactory.PREPARE_DATASET(int(self._cache.articleCount / 2), preprocessor,
            self._cache.articleCount, categories, dtype=dtype)

    def getDataset(self):
        return self._dataSet

    def processDataset(self,  bestParams, verbose: bool):
        #local reference for performance reasons
        dataSet = self._dataSet

        #check for degree, wich is not in the array for most kernels
        if 'degree' in bestParams:
            #init svm
            svm = SVC(kernel=bestParams["kernel"], C=bestParams["C"], degree=bestParams["degree"], gamma=bestParams["gamma"],
                        coef0=0.1, shrinking=True, decision_function_shape="ovr",
                        tol=0.001, cache_size=200, verbose=False, max_iter=-1)
        else:
            #init svm
            svm = SVC(kernel=bestParams["kernel"], C=bestParams["C"], gamma=bestParams["gamma"],
                        coef0=0.1, shrinking=True, decision_function_shape="ovr",
                        tol=0.001, cache_size=200, verbose=False, max_iter=-1)

        print("fitting SVM ...")
        svm.fit(dataSet[0].getTextArray(), dataSet[0].getCategories())

        print("testing SVM ...")

        #------------------------------------------------------------------------------
        #get svm scores
        predicted = svm.predict(dataSet[1].getTextArray())
        #meanAcc = svm.score(dataSet[1].getTextArray(),
        #                    dataSet[1].getCategories())
        accuracy = accuracy_score(dataSet[1].getCategories(), predicted)
        recall = recall_score(dataSet[1].getCategories(), predicted, average='macro')
        precision = precision_score(dataSet[1].getCategories(), predicted, average='macro')
        
        wRecall = recall_score(dataSet[1].getCategories(), predicted, average='weighted')
        wPrecision = precision_score(dataSet[1].getCategories(), predicted, average='weighted')
        #------------------------------------------------------------------------------

        print(
            "######################################################################"
        )
        #print("Mean Accuracy: " + str(meanAcc))
        print("Accuracy: " + str(accuracy))
        print("Recall: " + str(recall))
        print("Precision: " + str(precision))
        print("Weighted recall: " + str(wRecall))
        print("Weighted precision: " + str(wPrecision))
