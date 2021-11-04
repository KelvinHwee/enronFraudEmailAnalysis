########################################################################################################################
#   Basic required packages
########################################################################################################################
import pandas as pd
from collections import Counter
import re
from spacy.matcher import Matcher
from spacy.tokens import Span
import spacy

nlp = spacy.load('en_core_web_sm-3.1.0')


########################################################################################################################
#   create function to extract the domain names from the email addresses
########################################################################################################################

def extract_domain(df, col_name):
    list_of_domains = []
    for num in range(df.shape[0]):
        try:
            list_of_domains.append(list(set([re.findall(r"@(.*)[.]", i)[0]
                                             for i in df.loc[num, col_name].split(",")])))
        except:
            list_of_domains.append(list())  # this appends an empty list

    return list_of_domains


########################################################################################################################
#   create function to do 1-to-1 mapping from source-to-target
########################################################################################################################

# - for cases where there is one source to multiple targets, the mapping will ensure that each target is mapped to the
# - same source

def one_to_one_mapping(source_list, dest_list):

    df1 = pd.DataFrame({'source': source_list, 'destination': dest_list})
    df1['count_dest'] = df1.destination.apply(lambda x: len(x))

    # - we want to drop those rows where there is no 'destination'
    df2 = df1.loc[df1.count_dest > 0, :]
    df2 = df2.reset_index(drop=True)

    df2["expanded_source"] = [df2.loc[num, 'source'] * df2.loc[num, "count_dest"] for num in range(df2.shape[0])]
    df3 = df2.loc[:,["expanded_source", 'destination']]

    # - split up the lists (especially rows with multiple "sources" and "destinations") for purpose of Sankey diagram
    source = []
    destin = []
    for num in range(df3.shape[0]):

        s1 = df3.expanded_source[num]
        d1 = df3.destination[num]

        if len(s1) == 1: # to handle the singular sources / destinations within the list
            source.append(s1[0])
            destin.append(d1[0])

        else: # to handle multiple sources / destinations within the same list
            for sub_num in range(len(s1)):
                source.append(s1[sub_num])
                destin.append(d1[sub_num])

    # - obtain source-to-destination tuple mapping
    source_dest_map = tuple(zip(source, destin))
    counter = Counter(list(source_dest_map))

    # - get a de-duplicated source_dest_map (drop repeats; above non-deduplicated map is required only for counting)
    source_dest_map_dedup = sorted(tuple(set(source_dest_map)))

    return source, destin, source_dest_map_dedup, counter


########################################################################################################################
#   function to extract entities for Knowledge Graph
########################################################################################################################
'''
- taken from: https://www.analyticsvidhya.com/blog/2019/10/how-to-build-knowledge-graph-text-using-spacy/
- there are entities whose names made up of multiple words; these words are "compounds" and we are to put them together 
'''


def get_entities(sent):
    ## chunk 1
    ent1 = ""
    ent2 = ""

    prv_tok_dep = ""  # dependency tag of previous token in the sentence
    prv_tok_text = ""  # previous token in the sentence

    prefix = ""
    modifier = ""

    #############################################################

    for tok in nlp(sent):
        ## chunk 2
        # if token is a punctuation mark then move on to the next token
        if tok.dep_ != "punct":
            # check: token is a compound word or not
            if tok.dep_ == "compound":
                prefix = tok.text
                # if the previous word was also a 'compound' then add the current word to it
                if prv_tok_dep == "compound":
                    prefix = prv_tok_text + " " + tok.text

            # check: token is a modifier or not
            if tok.dep_.endswith("mod") == True:
                modifier = tok.text
                # if the previous word was also a 'compound' then add the current word to it
                if prv_tok_dep == "compound":
                    modifier = prv_tok_text + " " + tok.text

            ## chunk 3
            if tok.dep_.find("subj") == True:
                ent1 = modifier + " " + prefix + " " + tok.text
                prefix = ""
                modifier = ""
                prv_tok_dep = ""
                prv_tok_text = ""

                ## chunk 4
            if tok.dep_.find("obj") == True:
                ent2 = modifier + " " + prefix + " " + tok.text

            ## chunk 5
            # update variables
            prv_tok_dep = tok.dep_
            prv_tok_text = tok.text

    return [ent1.strip(), ent2.strip()]


########################################################################################################################
#   function to extract relations for Knowledge Graph
########################################################################################################################
'''
- taken from: https://www.analyticsvidhya.com/blog/2019/10/how-to-build-knowledge-graph-text-using-spacy/
- to extract the relation, we have to find the "ROOT" of the sentence (also is the verb of the sentence)
'''


def get_relation(sent):
    doc = nlp(sent)
    matcher = Matcher(nlp.vocab)  # Matcher class object

    # define the pattern; we can "print(spacy.explain("prep"))" to find out what the labels mean
    # "prep" is prepositional modifier; other POS tags can be found: https://v2.spacy.io/api/annotation
    pattern = [{'DEP': 'ROOT'}, {'DEP': 'prep', 'OP': "?"}, {'DEP': 'agent', 'OP': "?"}, {'POS': 'ADJ', 'OP': "?"}]

    matcher.add("matching_1", [pattern])

    matches = matcher(doc)
    k = len(matches) - 1

    span = doc[matches[k][1]:matches[k][2]]

    return span.text


# def key_val(df, dict, i, j):
#     key = df["message"][i].split("\n")[j].split(":")[0]
#     val = ':'.join(df["message"][i].split("\n")[j].split(":")[1:]).strip()
#
#     return key, val


# i = 77
# test_str = emails_df["message"][i].split("\n")
# for pos in range(len(keys_list)):
#     if test_str[pos][0:len(keys_dict[pos][0])] != keys_dict[pos][0]:
#         test_str.insert(pos, str(keys_dict[pos][0]) + ': ')
#
# test_str[:17]

# for i, k in enumerate(keys_list):
#     keys_dict[i] = [k, len(k)]

# clean_numbers = re.compile("\B[\d-]+\B")
# clean_datetime = re.compile("\d+/\d+/\d+\s+\d+:\d+:\d+\s+[AMPM]+") # for datetime format DD/MM/YYYY XX:XX:XX AM/PM
# clean_fwds = re.compile("[-]{2,}[\s]+[\w\s/:](.*?)+[-]{2,}") # cleans the "Forwarded by" in between the long dashes
# clean_link = re.compile(r"http[s]*://+[\w]+[.][\w]+[.][\w]+") # e.g. http://explorer.msn.com
# clean_multi_symbols = re.compile("[>,(]+\s?[>,(]+") # e.g. "> >", ", , ", ", ("

# re.findall(r"@([\w-]+).[\w]+", "billw@calpine.no.com")
# re.findall(r"@(.*)[.]", "billw@calpine.no.gogo.com")
#
# emails_df_feat.loc[11, "To_domain"]
# emails_df_feat.loc[1, "X-From"]
#
# emails_df_feat.iloc[0:50, 20:24]
# emails_df_feat.loc[11, "To"]
#
# def extract_domain(df, col_name):
#     list_of_domains = []
#     for num in range(df.shape[0]):
#         try:
#             # list_of_domains.append(list(set([re.findall(r"@([\w]+).[\w]+", i)[0]
#             #                             for i in df.loc[num, col_name].split(",")])))
#             list_of_domains.append(list(set([re.findall(r"@(.*)[.]", i)[0]
#                                         for i in df.loc[num, col_name].split(",")])))
#         except:
#             list_of_domains.append(list()) # this appends an empty list
#
#     return list_of_domains

# dest_domains   = [list(set(emails_df_feat.loc[num, "To_domain"] +
#                            emails_df_feat.loc[num, "Cc_domain"] +
#                            emails_df_feat.loc[num, "Bcc_domain"]))
#                            for num in range(emails_df_feat.shape[0])]

# doc = nlp("John completed the task")
# for tok in full_email_doc:
#     print(tok.text, "...", tok.dep_)

# test_doc = ' '.join(emails_df_feat.body.to_list())[1000:2500]
# full_email_doc = nlp(test_doc)

# entity_pairs = []
# for i in tqdm(email_doc_sentences):
#     ent = get_entities(i)
#     if ent not in entity_pairs:
#         entity_pairs.append(ent)


# nxg = nx.complete_graph(5)
# nt_know.from_nx(nxg)
# nt_know.show("name.html")
#
# type(nxg) # networkx.classes.graph.Graph
# type(G_kg)
#
# nxg = nx.draw(G_kg, with_labels=True, node_color='skyblue', edge_cmap=plt.cm.Blues, pos = pos)
# nt_know.from_nx(nxg)
# nt_know.show("name.html")
#
# nxg = nx.empty_graph(G_kg, with_labels=True, node_color='skyblue', edge_cmap=plt.cm.Blues, pos = pos)
# nt_know.from_nx(nxg)
# nt_know.show("name.html")
#
#
# g = Network()
# g.add_node(1)
# g.add_node(2)
# g.add_edge(1, 2,data={1})
# g.add_edge(1, 2,data={2})
# type(g)


# G_kg = nx.from_pandas_edgelist(know_df.loc[know_df["edge"].isin(["contact", "received"]), :], "source", "destination",
#                                edge_attr = True, create_using = nx.MultiDiGraph())
#
# plt.figure(figsize=(12,12))
# pos = nx.spring_layout(G_kg)
# nx.draw(G_kg, with_labels=True, node_color = 'skyblue', edge_cmap = plt.cm.Blues, pos = pos)
# plt.show()
#
# nt_know = Network()
#
# plt.figure(figsize=(12,12))
# pos = nx.spring_layout(G_kg)
# nt_know.from_nx(G_kg, with_labels=True, node_color='skyblue', pos = pos)
# nt_know.show()
#
#
#
#
# G = nx.Graph()
# G.add_node('a',color='red',size=4)
# G.add_node('b',color='#30a1a5',size=3)
# G.add_node('c',color='green',size=1)
# G.add_edge('a','b',weight=1023)
# G.add_edge('a','c',weight=435)
# G.add_edge('b','c',weight=100)
# nt_know.from_nx(G)
# nt_know.show("name2.html")


# source_dest_df1 = pd.DataFrame({'source': source_domains, 'destination': dest_domains})
# source_dest_df1['count_dest'] = source_dest_df1.destination.apply(lambda x : len(x))
# print(source_dest_df1.head(15))
#
# # - we want to drop those rows where there is no 'destination'
# source_dest_df2 = source_dest_df1.loc[source_dest_df1.count_dest > 0, :]
# source_dest_df2 = source_dest_df2.reset_index(drop = True)
#
# # - we want to duplicate the "source" if there are multiple "destinations" for purpose of plotting Sankey diagram
# # - so that we can get the 1-to-1 relationship mapping, from "source" to "destination"
# source_dest_df2["expanded_source"] = [source_dest_df2.loc[num, "source"] * source_dest_df2.loc[num, "count_dest"]
#                                       for num in range(source_dest_df2.shape[0])]
#
# source_dest_df3 = source_dest_df2.loc[:,["expanded_source", "destination"]]
# print(source_dest_df3.head(15))
#
# # - split up the lists (especially rows with multiple "sources" and "destinations") for purpose of Sankey diagram
# sankey_source = []
# sankey_destin = []
# for num in range(source_dest_df3.shape[0]):
#
#     s1 = source_dest_df3.expanded_source[num]
#     d1 = source_dest_df3.destination[num]
#
#     if len(s1) == 1: # to handle the singular sources / destinations within the list
#         sankey_source.append(s1[0])
#         sankey_destin.append(d1[0])
#
#     else: # to handle multiple sources / destinations within the same list
#         for sub_num in range(len(s1)):
#             sankey_source.append(s1[sub_num])
#             sankey_destin.append(d1[sub_num])
#
# # - obtain source-to-destination tuple mapping to count occurrences of mapping for computing "value" field for Sankey
# source_dest_map = tuple(zip(sankey_source, sankey_destin))
# counter = Counter(list(source_dest_map))
#
# # - get a de-duplicated source_dest_map (to drop the repeats; above non-deduplicated map is required only for counting)
# source_dest_map_dedup = sorted(tuple(set(source_dest_map)))

