"""
Calculates statistics for a set of annotated documents.
Accepts an argument for brat or jsonl formatted data.
Calculates total # annotations, mean/sd/median/max/min per
document, and total number of tokens/sentences in corpus and per document.

Author: Serena G. Lotreck
"""
import argparse
from os import listdir
from os.path import abspath, join, basename, splitext
from collections import defaultdict
import jsonlines
import numpy as np
import pandas as pd
import spacy


def compile_text_stats(num_sents_per_doc, num_tokens_per_doc):
    """
    Compile summary statistics dataframe for text.

    parameters:
        num_sents_per_doc, list of int: list of number of sentences
            in each document
        num_tokens_per_doc, list of int: list of number of tokens in
            each document

    returns:
        text_stats_df, df: dataframe of text stats
    """
    text_stats_names = ['total_num', 'mean_per_doc', 'std_per_doc',
            'median_per_doc', 'max_per_doc', 'min_per_doc']
    text_stats_dict = {'sentences':[sum(num_sents_per_doc),
        np.mean(num_sents_per_doc), np.std(num_sents_per_doc),
        np.median(num_sents_per_doc), max(num_sents_per_doc),
        min(num_sents_per_doc)],
        "tokens":[sum(num_tokens_per_doc), np.mean(num_tokens_per_doc),
            np.std(num_tokens_per_doc), np.median(num_tokens_per_doc),
            max(num_tokens_per_doc), min(num_tokens_per_doc)]}

    # Make into df with names as idx
    idx = pd.Index(text_stats_names)
    text_stats_df = pd.DataFrame(text_stats_dict, index=idx)

    return text_stats_df


def get_text_stats_dygiepp(corpus_file):
    """
    Gets total number of tokens and sentences in the document, as well as
    mean/median/max/min per document for both tokens and sentences for a
    dygiepp-formatted dataset.

    parameters:
        corpus_file, str: path to the corpus file

    returns:
        text_stats_df, df: pandas df with text stats
    """
    # Read in files
    with jsonlines.open(corpus_file) as reader:
        corpus = []
        for obj in reader:
            corpus.append(obj)

    # Get per doc stats
    num_sents_per_doc = []
    num_tokens_per_doc = []
    for doc in corpus:
        num_sents = len(doc["sentences"])
        num_tokens = sum([len(sent) for sent in doc["sentences"]])
        num_sents_per_doc.append(num_sents)
        num_tokens_per_doc.append(num_tokens)

    # Compile into overall stats
    text_stats_df = compile_text_stats(num_sents_per_doc, num_tokens_per_doc)

    print(f'\nSnapshot of the text stats df:\n{text_stats_df}')

    return text_stats_df

def get_text_stats_brat(corpus_dir):
    """
    Gets total number of tokens and sentences in the document, as well as
    mean/median/max/min per document for both tokens and sentences for a
    brat-formatted dataset.

    parameters:
        corpus_dir, str: path to the corpus

    returns:
        text_stats_df, df: pandas df with text stats
    """
    # Read in .txt files
    files = {}
    for f in listdir(corpus_dir):
        if '.txt' in f:
            with open(join(corpus_dir, f)) as myf:
                lines = myf.read()
                files[f] = lines

    # Get per doc stats
    nlp = spacy.load("en_core_sci_sm")
    num_sents_per_doc = [len(list(nlp(doc).sents)) for doc in files.values()]
    num_tokens_per_doc = [len(nlp(doc)) for doc in files.values()]

    # Compile into overall stats
    text_stats_df = compile_text_stats(num_sents_per_doc, num_tokens_per_doc)

    print(f'\nSnapshot of the text stats df:\n{text_stats_df}')

    return text_stats_df


def compile_ann_stats(single_doc_anns):
    """
    Get summary statistics for annotation numbers.

    parameters:
        single_doc_anns, dict: keys are doc keys or filenames and values
            are tuples of (num_ent, num_rel) for the doc

    returns:
        ann_stats_df, df: dataframe of sumamry statistics
    """
    ann_stats_names = ['total_num_anns', 'mean_anns_per_doc',
            'std_anns_per_doc', 'med_anns_per_doc', 'max_anns_per_doc',
            'min_anns_per_doc']

    ents_per_doc = [val[0] for key, val in single_doc_anns.items()]
    rels_per_doc = [val[1] for key, val in single_doc_anns.items()]

    corpus_stats ={'entities':[sum(ents_per_doc), np.mean(ents_per_doc),
        np.std(ents_per_doc), np.median(ents_per_doc), max(ents_per_doc),
        min(ents_per_doc)],
    'relations':[sum(rels_per_doc), np.mean(rels_per_doc),
        np.std(rels_per_doc), np.median(rels_per_doc), max(rels_per_doc),
        min(rels_per_doc)]}

    # Make into df with names as index
    idx = pd.Index(ann_stats_names)
    ann_stats_df = pd.DataFrame(corpus_stats, index=idx)

    return ann_stats_df


def get_annotation_stats_dygiepp(corpus_file):
    """
    Get total # annotations, as well as mean/median/max/min per document,
    for both entities and relations for a dygiepp-formatted corpus.

    parameters:
        corpus_file, str: path to jsonl file with corpus

    returns:
        ann_stats_df, df: pandas df containing stats
    """
    # Read in documents
    with jsonlines.open(corpus_file) as reader:
        corpus = []
        for obj in reader:
            corpus.append(obj)

    # Get number of ents and rels per document
    single_doc_anns = {}
    for doc in corpus:
        total_ents = 0
        total_rels = 0
        for i, sent in enumerate(doc["sentences"]):
            total_ents += len(doc["ner"][i])
            total_rels += len(doc["relations"][i])

        single_doc_anns[doc["doc_key"]] = (total_ents, total_rels)

    # Compile stats
    ann_stats_df = compile_ann_stats(single_doc_anns)

    print(f'\nSnapshot of annotation statistics:\n{ann_stats_df}')

    return ann_stats_df


def get_annotation_stats_brat(corpus_dir):
    """
    Gets total # annotations in the corpus, as well as mean/median/max/min per
    document, for both entities and relations for a brat-formatted corpus.

    parameters:
        corpus_dir, str: path to the corpus

    returns:
        ann_stats_df, df: pandas df containing stats
    """
    # Read in .ann files
    files = {}
    for f in listdir(corpus_dir):
        if '.ann' in f:
            with open(join(corpus_dir, f)) as myf:
                lines = myf.readlines()
                files[f] = lines

    # Get number of each type of ann per doc
    single_doc_anns = {}
    for name, doc in files.items():
        total_ents =  0
        total_rels = 0
        for line in doc:
            if line[0] == 'T':
                total_ents += 1
            elif line[0] == 'R':
                total_rels += 1

        single_doc_anns[name] = (total_ents, total_rels)

    # Compile into overall stats
    ann_stats_df = compile_ann_stats(single_doc_anns)

    print(f'\nSnapshot of annotation statistics:\n{ann_stats_df}')

    return ann_stats_df


def main(corpus, d_format, out_loc):

    # Get annotation stats
    if d_format == 'brat':
        ann_stats_df = get_annotation_stats_brat(corpus)
    else:
        ann_stats_df = get_annotation_stats_dygiepp(corpus)

    # Get text stats
    if d_format == 'brat':
        text_stats_df = get_text_stats_brat(corpus)
    else:
        text_stats_df = get_text_stats_dygiepp(corpus)

    # Save both
    file_prefix = basename(corpus)
    if d_format == 'dygiepp':
        file_prefix = splitext(file_prefix)[0]
    print(f'\nSaving annotation stats as {out_loc}/{file_prefix}_annotation_stats.csv')
    print(f'\nSaving text stats as {out_loc}/{file_prefix}_text_stats.csv')
    ann_stats_df.to_csv(f'{out_loc}/{file_prefix}_annotation_stats.csv')
    text_stats_df.to_csv(f'{out_loc}/{file_prefix}_text_stats.csv')
    print('\nDone!\n')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Get corpus statistics')

    parser.add_argument('corpus', type=str,
            help='Path to directory containing .txt and .ann files for the '
            'corpus if d_format == "brat", otherwise a file path')
    parser.add_argument('out_loc', type=str,
            help='Path for saving corpus stats. Two files will be saved.')
    parser.add_argument('-d_format', type=str, default='brat',
            help='Options are "brat" or "dygiepp", default is "brat"')

    args = parser.parse_args()

    args.corpus = abspath(args.corpus)
    args.out_loc = abspath(args.out_loc)

    main(args.corpus, args.d_format, args.out_loc)
