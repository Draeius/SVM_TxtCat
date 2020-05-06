import time
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

print("-----------------------------------------------")
print("Estimating best Params for all Categories:")
print("-----------------------------------------------")

bestParams = cache.recalcBestParams(-1)

print("-----------------------------------------------")
print("Best Params for all Categories:")
print(bestParams)
print("-----------------------------------------------")

print("-----------------------------------------------")
print("Estimating best Params for all Categories:")
print("-----------------------------------------------")

bestParams = cache.recalcBestParams(7)

print("-----------------------------------------------")
print("Best Params for Categories > 200 Articles:")
print(bestParams)
print("-----------------------------------------------")

#------------------------------------------------------------
#end timing
print("-----------------------------------------------")
print("Time: " + str(current_milli_time() - millis))
print("-----------------------------------------------")
#------------------------------------------------------------
