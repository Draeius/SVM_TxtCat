import re
from typing import List
from collections import Counter

from data import Article

class Process:
    def process(self, words: List[str]) -> List[str]:
        pass


class Strategy:

    _lastLetters = List[str]
    _measure = List[int]
    _containsVowel = False
    _doubleConsonant = False
    _endsWithPattern = False

    _pattern = ".*[b-df-hj-np-tv-z][aiueo][b-df-hj-np-tvz].{{{suffixlen}}}$"
    _applyRegex = ""
    _suffixLen = 0
    _replacement = ""
    _suffix = ""

    def apply(self, word: str) -> str:
        """
        Applies this strategy to the given word regardless of wether it is applicable or not.
        """

        return re.sub(self._applyRegex, self._replacement, word, 0)

    def isApplicable(self, word: str, wordMeasure: int) -> str:
        """
        Checks if this strategy is applicable or not
        """

        if len(word) <= self._suffixLen:
            return False

        #word does not end with the suffix of this strategy
        if not word.endswith(self._suffix):
            return False

        #measure is important, if it is not empty
        #wordMeasure has to be in measure for this strategy to be applicable
        if self._measure and wordMeasure not in self._measure:
            return False

        #last letter is important
        if self._lastLetters:
            #test all letters that matter
            found = False
            for letter in self._lastLetters:
                #check letter
                if self.lastLetterEquals(word, letter):
                    found = True
                #did not find any
                if not found:
                    return False

        #vowels matter
        if self._containsVowel:
            #check for vowels
            vowel = self.containsVowel(word)
            #did not find any
            if not vowel:
                return False

        #needs a double consonant before the suffix
        if self._doubleConsonant:
            consonant = self.doubleConsonant(word)
            #did not find a consonant
            if not consonant:
                return False

        #needs a specific pattern before the suffix
        if self._endsWithPattern:
            pattern = self.endsWithPattern(word)
            #did not find it
            if not pattern:
                return False

        #all conditions met
        return True

    def lastLetterEquals(self, text: str, letter: str) -> bool:
        """
        Checks if the last letter before the suffix is the given letter
        """
        #get last letter of the word stem in lower case
        return text[-1 * self._suffixLen - 1].lower() == letter

    def containsVowel(self, text: str) -> bool:
        """
        Checks for vowels in the given word
        """
        return any(char in ["a", "i", "u", "e", "o", "A", "I", "U", "E", "O"]
                   for char in text[:-1 * self._suffixLen])

    def doubleConsonant(self, text: str) -> bool:
        """
        checks if the letter before the suffix is a double consonant
        """
        if (self._suffixLen + 1) >= len(text):
            return False
        #last stem letter is a consonant
        if (text[-1 * self._suffixLen -
                 1].lower() not in ["a", "i", "u", "e", "o"]):
            #check for double consonant
            return text[-1 * self._suffixLen -
                        1].lower() == text[-1 * self._suffixLen - 2].lower()

        return False

    def endsWithPattern(self, text: str) -> bool:
        """
        Checks if the word before the suffix ends witch a given pattern
        """
        if self._invertPattern:
            return not re.search(self._pattern, text)
        return re.search(self._pattern, text)

    def __init__(self,
                 suffix: str,
                 replacement: str,
                 lastLetters: List[str],
                 measure: List[int],
                 containsVowel: bool,
                 doubleConsonant: bool,
                 endsWithPattern: bool,
                 invertPattern=False):

        self._suffixLen = len(suffix)
        self._pattern = re.compile(
            self._pattern.format(suffixlen=self._suffixLen), re.IGNORECASE)
        self._measure = measure
        self._lastLetters = lastLetters
        self._containsVowel = containsVowel
        self._doubleConsonant = doubleConsonant
        self._endsWithPattern = endsWithPattern

        self._applyRegex = re.compile(suffix + "$", re.IGNORECASE)
        self._replacement = replacement
        self._suffix = suffix
        self._invertPattern = invertPattern


class Tokenizer:
    def __init__(self, keepPunctuation: bool, keepCaps: bool):
        self._keepPunctuation = keepPunctuation
        self._keepCaps = keepCaps

    def erasePunctuation(self, text: str) -> str:
        replacements = {
            ",": " ",
            ".": " ",
            ";": " ",
            ":": " ",
            "/": " ",
            "(": " ",
            ")": " ",
            "{": " ",
            "}": " ",
            "+": " ",
            "-": " ",
            "<": " ",
            ">": " ",
            '"': " ",
            "'": " ",
            "*": " ",
            "!": " ",
            "?": " ",
            "^": " ",
            "\u007f": ""
        }
        return "".join([replacements.get(c, c) for c in text])

    def tokenize(self, text: str) -> List[str]:
        if not self._keepPunctuation:
            text = self.erasePunctuation(text)

        if not self._keepCaps:
            text = text.lower()

        return text.split()


class SingleLetterStrategy(Strategy):
    def apply(self, word: str) -> str:
        return word[:-1]

    def isApplicable(self, word: str, wordMeasure: int) -> bool:
        return self.doubleConsonant(word) and not (self.lastLetterEquals(
            word, "l") or self.lastLetterEquals(
                word, "s") or self.lastLetterEquals(word, "z"))


class Stemmer(Process):

    _measureRegex = "^[b-df-hj-np-tv-z]*([aiueo]+[b-df-hj-np-tv-z]+){{{}}}[aiueo]*$"

    #-----------------------------------------------------------------------------------
    #a whole lot of Porter's stemming rules...
    _step1a = [
        Strategy("sses", "ss", [], [], False, False, False),
        Strategy("ies", "i", [], [], False, False, False),
        Strategy("ss", "ss", [], [], False, False, False),
        Strategy("s", "", [], [], False, False, False)
    ]

    _step1b = [
        Strategy("eed", "ee", [], range(1, 100), False, False, False),
        Strategy("ed", "", [], [], True, False, False),
        Strategy("ing", "", [], [], True, False, False)
    ]

    _step1bnext = [
        Strategy("at", "ate", [], [], False, False, False),
        Strategy("bl", "ble", [], [], False, False, False),
        Strategy("iz", "ize", [], [], False, False, False),
        SingleLetterStrategy("", "", [
            "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "m", "n",
            "o", "p", "q", "r", "t", "u", "v", "w", "x", "y"
        ], [], False, True, False),
        Strategy("", "e", [], [1], False, False, True)
    ]

    _step1c = [Strategy("y", "i", [], [], True, False, False)]

    _step2 = [
        Strategy("ational", "ate", [], range(1, 100), False, False, False),
        Strategy("tional", "tion", [], range(1, 100), False, False, False),
        Strategy("enci", "ence", [], range(1, 100), False, False, False),
        Strategy("anci", "ance", [], range(1, 100), False, False, False),
        Strategy("izer", "ize", [], range(1, 100), False, False, False),
        Strategy("abli", "able", [], range(1, 100), False, False, False),
        Strategy("alli", "al", [], range(1, 100), False, False, False),
        Strategy("entli", "ent", [], range(1, 100), False, False, False),
        Strategy("eli", "e", [], range(1, 100), False, False, False),
        Strategy("ousli", "ous", [], range(1, 100), False, False, False),
        Strategy("ization", "ize", [], range(1, 100), False, False, False),
        Strategy("ation", "ate", [], range(1, 100), False, False, False),
        Strategy("ator", "ate", [], range(1, 100), False, False, False),
        Strategy("alism", "al", [], range(1, 100), False, False, False),
        Strategy("iveness", "ive", [], range(1, 100), False, False, False),
        Strategy("fulness", "ful", [], range(1, 100), False, False, False),
        Strategy("ousness", "ous", [], range(1, 100), False, False, False),
        Strategy("aliti", "al", [], range(1, 100), False, False, False),
        Strategy("iviti", "ive", [], range(1, 100), False, False, False),
        Strategy("biliti", "ble", [], range(1, 100), False, False, False)
    ]

    _step3 = [
        Strategy("icate", "ic", [], range(1, 100), False, False, False),
        Strategy("ative", "", [], range(1, 100), False, False, False),
        Strategy("alize", "al", [], range(1, 100), False, False, False),
        Strategy("icite", "ic", [], range(1, 100), False, False, False),
        Strategy("ical", "ic", [], range(1, 100), False, False, False),
        Strategy("ful", "", [], range(1, 100), False, False, False),
        Strategy("ness", "", [], range(1, 100), False, False, False)
    ]

    _step4 = [
        Strategy("al", "", [], range(2, 100), False, False, False),
        Strategy("ance", "", [], range(2, 100), False, False, False),
        Strategy("ence", "", [], range(2, 100), False, False, False),
        Strategy("er", "", [], range(2, 100), False, False, False),
        Strategy("ic", "", [], range(2, 100), False, False, False),
        Strategy("able", "", [], range(2, 100), False, False, False),
        Strategy("ible", "", [], range(2, 100), False, False, False),
        Strategy("ant", "", [], range(2, 100), False, False, False),
        Strategy("ement", "", [], range(2, 100), False, False, False),
        Strategy("ment", "", [], range(2, 100), False, False, False),
        Strategy("ent", "", [], range(2, 100), False, False, False),
        Strategy("ion", "", ["s", "t"], range(2, 100), False, False, False),
        Strategy("ou", "", [], range(2, 100), False, False, False),
        Strategy("ism", "", [], range(2, 100), False, False, False),
        Strategy("ate", "", [], range(2, 100), False, False, False),
        Strategy("iti", "", [], range(2, 100), False, False, False),
        Strategy("ous", "", [], range(2, 100), False, False, False),
        Strategy("ive", "", [], range(2, 100), False, False, False),
        Strategy("ize", "", [], range(2, 100), False, False, False)
    ]

    _step5a = [
        Strategy("e", "", [], range(2, 100), False, False, False),
        Strategy("e", "", [], [1], False, False, False, True)
    ]

    _step5b = [
        SingleLetterStrategy("e", "", ["l"], range(2, 100), False, True, False)
    ]
    #-----------------------------------------------------------------------------------

    def process(self, words: List[str]) -> List[str]:
        indices = range(len(words))

        for index in indices:
            wordMeasure = self.getMeasure(words[index])

            # Step 1 ----------------------------------------------------------

            words[index] = self.applyList(self._step1a, words[index],
                                          wordMeasure)[0]
            step1b = self.applyList(self._step1b, words[index], wordMeasure)
            words[index] = step1b[0]

            if step1b[1] == 2 or step1b[1] == 3:
                words[index] = self.applyList(self._step1bnext, words[index],
                                              wordMeasure)[0]

            words[index] = self.applyList(self._step1c, words[index],
                                          wordMeasure)[0]

            # Step 2 ----------------------------------------------------------

            words[index] = self.applyList(self._step2, words[index],
                                          wordMeasure)[0]

            # Step 3 ----------------------------------------------------------

            words[index] = self.applyList(self._step3, words[index],
                                          wordMeasure)[0]

            # Step 4 ----------------------------------------------------------

            words[index] = self.applyList(self._step4, words[index],
                                          wordMeasure)[0]

            # Step 5 ----------------------------------------------------------

            words[index] = self.applyList(self._step5a, words[index],
                                          wordMeasure)[0]
            words[index] = self.applyList(self._step5b, words[index],
                                          wordMeasure)[0]

        return words

    def applyList(self, strategies, word: str, wordMeasure: int) -> str:
        #apply porter strategies
        counter = 0
        for strat in strategies:
            counter += 1
            if strat.isApplicable(word, wordMeasure):
                return [strat.apply(word), counter]
        return [word, counter]

    def getMeasure(self, word: str) -> int:
        #get porters word measure
        for index in range(100):
            if re.search(self._measureRegex.format(index), word,
                         re.IGNORECASE):
                return index
        return -1


class StopwordEraser(Process):

    stopwords = [
        "mln", "dlr", "reuters", "\x03", 'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', "aren't", 'as', 'at', 'be',
        'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by', "can't", 'cannot', 'could', "couldn't", 'did', "didn't", 'do', 'does', "doesn't",
        'doing', "don't", 'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had', "hadn't", 'has', "hasn't", 'have', "haven't", 'having', 'he', "he'd",
        "he'll", "he's", 'her', 'here', "here's", 'hers', "herself'", 'him', 'himself', 'his', 'how', "how's", 'i', "i'd", "i'll", "i'm", "i've", "if'", 'in', 'into', 'is',
        "isn't", 'it', "it's", 'its', 'itself', "let's", 'me', 'more', 'most', "mustn't", 'my', 'myself', 'no', 'nor', 'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other',
        'ought', 'our', 'ours',	'ourselves', 'out', 'over', 'own', 'same', "shan't", 'she', "she'd", "she'll", "she's", 'should', "shouldn't", 'so', 'some', 'such', 'than',
        'that', "that's", 'the', "their'", 'theirs', 'them', 'themselves', 'then', 'there', "there's", 'these', 'they', "they'd", "they'll", "they're", "they've", 'this',
        'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was', "wasn't", 'we', "we'd", "we'll", "we're", "we've", 'were', "weren't", 'what', "what's", 'when',
        "when's", 'where', "where's", 'which', 'while', 'who', "who's", 'whom', 'why', "why's", 'with', "won't", 'would', "wouldn't", 'you', "you'd", "you'll", "you're", "you've",
        'your', 'yours', 'yourself', 'yourselves'
    ]

    def process(self, words: List[str]) -> List[str]:
        #only return words that are not in the stopword array
        return [word for word in words if not word in self.stopwords]


class NumberEraser(Process):
    def process(self, words: List[str]) -> List[str]:
        #find all numbers and replace with /number/
        regex = re.compile(r".*\d")
        for index in range(len(words)):
            if re.match(regex, words[index]):
                words[index] = "/number/"
        return words


class GarbageEraser(Process):

    _blaRegex = r"^b+l+a+$"
    _noVocalRegex = r"^[b-df-hj-np-tv-z]*$"

    def process(self, words: List[str]) -> List[str]:
        blaRegex = re.compile(self._blaRegex)
        noVocalRegex = re.compile(self._noVocalRegex)
        #there are seriously a whole lot of blas in this articles .... -.-
        return [
            word for word in words
            if (not re.match(blaRegex, word)) and len(word) > 1 and (
                not re.match(noVocalRegex, word))
        ]


class IllicitWordEraser(Process):
    def __init__(self, allowedWords: List[str]):
        self._allowedWords = allowedWords

    def process(self, words: List[str]) -> List[str]:
        #return only words that are in allowedWords list
        return [word for word in words if word in self._allowedWords]


class Preprocessor:
    #regex template to test for words
    #_regexTemplate = "^[b-df-hj-np-tv-z]*([aiueo]+[b-df-hj-np-tv-z]+){{{}}}[aiueo]*$"

    def addProcessor(self, process: Process) -> None:
        self._processors.append(process)

    def process(self, article: Article) -> Article:
        #process the given article
        #first: tokenization
        words = self._tokenizer.tokenize(article.text)

        #all the other preprocessors
        for proc in self._processors:
            words = proc.process(words)

        #count the words
        self._counter.update(words)

        #pass a copy to the article.
        #copy is necessary to not count all words in all articles
        article.preprocessed = self._counter.copy()

        #reset counter
        self.resetCounter()

        return article

    def resetCounter(self) -> None:
        for index in self._counter:
            self._counter[index] = 0

    def __init__(self, allowedWords):
        self._processors = []
        self._tokenizer = Tokenizer(False, False)
        self._counter = Counter(allowedWords)


class PreprocessorFactory:

    instance = None

    @staticmethod
    def FACTORY(allowedWords: List[str]) -> Preprocessor:
        # create standard Preprocessor
        if PreprocessorFactory.instance == None:
            preprocessor = Preprocessor(allowedWords)
            preprocessor.addProcessor(StopwordEraser())
            preprocessor.addProcessor(NumberEraser())
            preprocessor.addProcessor(GarbageEraser())
            preprocessor.addProcessor(Stemmer())
            preprocessor.addProcessor(IllicitWordEraser(allowedWords))
            PreprocessorFactory.instance = preprocessor
            return preprocessor
        return PreprocessorFactory.instance

    @staticmethod
    def CACHE_FACTORY() -> Preprocessor:
        #create a preprocessor to build the cache
        preprocessor = Preprocessor([])
        preprocessor.addProcessor(StopwordEraser())
        preprocessor.addProcessor(NumberEraser())
        preprocessor.addProcessor(GarbageEraser())
        preprocessor.addProcessor(Stemmer())

        return preprocessor
