import numpy as np
# import matplotlib.pyplot as plt
import pandas as pd
from bs4 import BeautifulSoup
import re

# Assumptions:
#   there are no hard rules as to what constitutes a language name
#   language is usually in <h1>, <h2>, or <h3>
#   we can only be sure that a number represents solution length when it is followed by "bytes" or alike
#   language is at the top-most found header


byte_ex = re.compile(r"\d+\s*(byte|char|character|operation)")  # n bytes
trail_ex = re.compile(r"[\s,-]+$")  # Trailing whitespace and some characters
brackets_ex = re.compile(r"\([^\(\)]*\)") # This wont count in ex. "C++14 (86 bytes)"
pre_brackets_ex = re.compile(r"\([^\(\)]+(byte|char|character|operation)s?\)")  # So we perform a prior subs. with this


def find_lang(headers):
    """
    :param headers: List of headers as text
    :return: First match or None
    """
    res = []

    # Try to find header with "n bytes" or similar
    for h in headers:
        match = byte_ex.search(h)
        if match:
            res.append(h[:match.start()])

    # Remove trailing whitespace
    res = [trail_ex.sub('', h) for h in res]
    # Assume first match is result
    return res[0] if res else None


def get_headers(soup, level):
    """

    :param soup:
    :param level: h1, h2, or h3
    :return:
    """
    # Extract headers (capitalize and pure text)
    res = [h.get_text(separator=" ").capitalize() for h in soup.find_all(level)]

    # Remove brackets from expressions like "(n bytes)" => "n bytes"
    for i, h in enumerate(res):
        occ = pre_brackets_ex.search(h)
        if occ:
            s, e = occ.span()
            res[i] = ''.join([h[:s], occ.group()[1:-1], h[e:]])

    # Remove things in brackets
    res = [brackets_ex.sub('', h) for h in res]

    return res


def prepare(content):
    soup = BeautifulSoup(content, 'html.parser')
    # remove <strike>, <s>, <del> (people cross out old solutions)
    _extracted = [s.extract() for s in soup(['strike', 's', 'del'])]
    # Prettify to get rid of whitespace
    soup.prettify()
    return soup


def attempt(content):
    soup = prepare(content)

    # Assuming top-most header contains name of language
    for level in ['h1', 'h2', 'h3']:
        h = get_headers(soup, level)
        lang = find_lang(h)
        if lang:
            break

    return lang


def row_gen(posts):
    # PosTypeId == 2 -> Answer
    for body in posts.loc[posts.PostTypeId == 2, "Body"]:
        lang = attempt(body)
        if lang:
            yield lang


if __name__ == '__main__':
    posts_df = pd.read_csv("data/Posts.csv")
    print("Loaded data.")

    languages = pd.DataFrame(row_gen(posts_df), columns=['Language'])
    print(languages.value_counts().head(32))
    print("Extracted language names.")

    print(f"Processed {100.0*len(languages)/len(posts_df)}% entries")
