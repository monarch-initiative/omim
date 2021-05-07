import re
from omim2mondo.utils.romanplus import *


def cleanup_label(label):
    """
    Reformat the ALL CAPS OMIM labels to something more pleasant to read.
    This will:
    1.  remove the abbreviation suffixes
    2.  convert the roman numerals to integer numbers
    3.  make the text title case,
        except for suplied conjunctions/prepositions/articles
    :param label:
    :return:
    """
    conjunctions = ['and', 'but', 'yet', 'for', 'nor', 'so']
    little_preps = [
        'at', 'by', 'in', 'of', 'on', 'to', 'up', 'as', 'it', 'or']
    articles = ['a', 'an', 'the']

    # remove the abbreviation
    lbl = label.split(r';')[0]

    fixedwords = []
    i = 0
    for wrd in lbl.split():
        i += 1
        # convert the roman numerals to numbers,
        # but assume that the first word is not
        # a roman numeral (this permits things like "X inactivation"
        if i > 1 and re.match(romanNumeralPattern, wrd):
            num = fromRoman(wrd)
            # make the assumption that the number of syndromes are <100
            # this allows me to retain "SYNDROME C"
            # and not convert it to "SYNDROME 100"
            if 0 < num < 100:
                # get the non-roman suffix, if present.
                # for example, IIIB or IVA
                suffix = wrd.replace(toRoman(num), '', 1)
                fixed = ''.join((str(num), suffix))
                wrd = fixed

        # capitalize first letter
        wrd = wrd.title()

        # replace interior conjunctions, prepositions,
        # and articles with lowercase
        if wrd.lower() in (conjunctions + little_preps + articles) and i != 1:
            wrd = wrd.lower()

        fixedwords.append(wrd)

    lbl = ' '.join(fixedwords)
    # print (label, '-->', lbl)
    return lbl
