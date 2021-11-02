########################################################################################################################
#   Basic required packages
########################################################################################################################
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
            list_of_domains.append(list()) # this appends an empty list

    return list_of_domains


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
    #############################################################

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

  # Matcher class object
  matcher = Matcher(nlp.vocab)

  #define the pattern
  pattern = [{'DEP':'ROOT'},
            {'DEP':'prep','OP':"?"},
            {'DEP':'agent','OP':"?"},
            {'POS':'ADJ','OP':"?"}]

  matcher.add("matching_1", None, pattern)

  matches = matcher(doc)
  k = len(matches) - 1

  span = doc[matches[k][1]:matches[k][2]]

  return(span.text)












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
