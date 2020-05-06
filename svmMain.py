import time
from svm import SVMWrapper
from cache import Cache
from preprocessing import PreprocessorFactory
from collections import Counter

current_milli_time = lambda: int(round(time.time() * 1000))

#------------------------------------------------------------
#start timing
millis = current_milli_time()
#------------------------------------------------------------

dtype = 'reuters'
#dtype = 'twentyNews'

cache = Cache(dtype)

print("----------------------------------------------")
print("Categories > 200 Articles")
print([cat for cat in cache.categories if (cache.categories[cat] > 200)])
print("----------------------------------------------")

print("----------------------------------------------")
print("start SVM, all Categories, with params: ")
print(cache.bestParamsLarge)

wrapper = SVMWrapper(-1, dtype)
wrapper.processDataset(cache.bestParamsLarge, False)

print("----------------------------------------------")
print("start SVM, Categories >= 200 Articles, with params: ")
print(cache.bestParamsSmall)

wrapper = SVMWrapper(7, dtype)
wrapper.processDataset(cache.bestParamsSmall, False)

#------------------------------------------------------------
#end timing
print("-----------------------------------------------")
print("Time: " + str(current_milli_time() - millis))
print("-----------------------------------------------")
#------------------------------------------------------------
