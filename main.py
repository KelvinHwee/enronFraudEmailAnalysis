#######################################################################################################################
#   Background of code
#######################################################################################################################
'''
- We attempt to discover or mine information from the email dataset in different ways / visualization methods
- if an email contains forwarded messages, it seems like the original messages are not found in other parts of the data
"emails_df_feat.Subject.value_counts().head(20)" does not show much repeats
'''

#######################################################################################################################
#   Basic configuration steps
#######################################################################################################################

# - import basic python packages
import warnings
import tkinter  # to show plot in Pycharm

warnings.simplefilter(action='ignore', category=FutureWarning)

# - import packages for data manipulations
import numpy as np
import pandas as pd
from datetime import date, datetime
from collections import Counter
import random

# - import packages for visualisation
import plotly.graph_objects as go
import plotly.io as pio
pio.renderers.default = "browser" # to plot a static version, change "browser" to "svg"
from pyvis.network import Network
import networkx as nx
import matplotlib.pyplot as plt
from tqdm import tqdm

# - import packages for NLP
'''
- for the installation of "en_core_web_sm", we use the following command in terminal
- pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.1.0/en_core_web_sm-3.1.0.tar.gz
- the file was then downloaded to this folder: 
- /home/kelvinhwee/.cache/pip/wheels/62/79/40/648305f0a2cd1fdab236bd6764ba467437c5fae2a925768153 
- (look out for the installation completion message in the terminal)
- we copied the zipped file, and extracted the "en_core_web_sm-3.1.0" folder (containing the "config.cfg" file) into the
- working directory 
'''
import re
import spacy
from spacy import displacy
from spacy.matcher import Matcher
from spacy.tokens import Span
from nltk.tokenize import sent_tokenize
import nltk

nltk.download('punkt') # uncomment this if you run into punkt download issues

# - we load the spacy trained pipelines (for English); this is an English pipeline optimized for CPU
nlp = spacy.load('en_core_web_sm-3.1.0')

# - initialise the spacy Matcher with a vocab; matcher must always share the same vocab with the documents it operate on
matcher = Matcher(nlp.vocab)

# - other configurations
pd.set_option("display.max_column", None)
source_filepath = '/home/kelvinhwee/PycharmProjects/sourceFiles'

# - packages created
from utils import extract_domain, reformat_email_func
from utils import one_to_one_mapping
from utils import get_relation, get_entities

########################################################################################################################
#   Read CSV data file
########################################################################################################################
'''
- The Enron email dataset contains approximately 500,000 emails generated by employees of the Enron Corporation. 
- It was obtained by the Federal Energy Regulatory Commission during its investigation of Enron's collapse.
- This is the May 7, 2015 Version of dataset, as published at https://www.cs.cmu.edu/~./enron/
- we note that there are only two columes, "file" and "message"
'''

# # - read in the CSV data
# emails_df = pd.read_csv(source_filepath + '/emails.csv')
#
# - read in the sample CSV data
# import random
# sample_vals = random.sample(list(range(emails_df.shape[0])), 5000)
# emails_df.loc[sample_vals].to_csv(source_filepath + '/sample_emails.csv')

emails_df = pd.read_csv(source_filepath + '/sample_emails.csv')
print("We look at a sample of the data: \n", emails_df.head(10))

# - we take a look at some specific instances of "message"
print(emails_df["message"][8])  # "X-From" and "X-To" field corresponds to the "From" and "To", but more explicit
print(emails_df["message"][88])  # "Subject" field seems to be blank


########################################################################################################################
#   Feature engineering - extract critical data points from email messages
########################################################################################################################

# - replace some characters
for i in range(emails_df.shape[0]):
    temp_text = emails_df["message"][i]
    new_text = temp_text.replace("\n ", " ")  # some "\n " in subject; , clean them to space character
    # new_text = new_text.replace("\n\n", "\n")  # dropped this; the one after "filename" always has double "\n"
    new_text = new_text.replace("Re: ", "")  # some "Re: " in subject; , clean them to blanks
    new_text = new_text.replace("Fw: ", "")  # some "Fw: " in subject; , clean them to blanks
    new_text = new_text.replace("\n\t", "")  # very long recipient list has "\n\t"; clean them to blanks
    new_text = new_text.replace(" : ", "")  # some ":" in subject; , clean them to blanks
    new_text = new_text.replace("[IMAGE]", "")  # some "[IMAGE]" tags; , clean them to blanks
    emails_df.loc[i, "message"] = new_text

# - we collate the list of "keys"
keys_list = ['Message-ID', 'Date', 'From', 'To', 'Subject', 'Cc', 'Mime-Version', 'Content-Type',
             'Content-Transfer-Encoding', 'Bcc', 'X-From', 'X-To', 'X-cc', 'X-bcc', 'X-Folder', 'X-Origin',
             'X-FileName']

fields_list = keys_list + ["Sent"]  # to add in additional fields to clean (for RegEx later)
fields_list_plus = fields_list + [i.lower() for i in fields_list] \
                   + [i.upper() for i in fields_list]  # include variations of lower and upper case

# - create dictionary (using dictionary comprehension) to do "conversion" later on (you will see)
keys_dict = {i: [k, len(k)] for i, k in enumerate(keys_list)}

# - we first compile the list of regex logic first
clean_html_tags = re.compile("<[/]*.*?>|&nbsp;")
clean_multi_space = re.compile("[\s]{2,}")
clean_field_headers = re.compile('|'.join([item + ":" for item in fields_list_plus]))
clean_emails = re.compile("[\w._]+@[\w.]+")
clean_fwds = re.compile("[-_]{2,}.*?[-_]{2,}|FW:|Fwd:|RE:")  # cleans "Forwarded by" in between long dashes and others
clean_unintended_sends = re.compile("[-_*]{2,}.*?[-_*]{2,}")
clean_dashes = re.compile("[-]{2,}")
clean_transmission_warn = re.compile(r"The information.*?any computer.")  # cleans warning texts
clean_datetime = re.compile("[\d]{1,2}/[\d]{1,2}/[\d]{4}\s+[\d]{1,2}:[\d]{1,2}[:\d]*\s+[AMPM]+")  # for format DD/MM/YYYY XX:XX:XX AM/PM
clean_multi_symbols = re.compile("[>,(\"\'\\!.\[\]-]+\s?[>,(\"\'\\!.\[\]-]+")  # e.g. "> >", ", , ", ", ("
clean_addr_code = re.compile("[, ]*[A-Z]{2}\s+[\d]{5}")  # cleans ", TX 77082"
clean_phone_fax = re.compile("[\d]*[-]*[\d]{3}-[\d]{3}-[\d]{4}[\s]*[(]*\w*[)]*")  # "713-853-3989 (Phone)", "713-646-3393(Fax", "1-888-334-4204"
clean_phone_ctrycode = re.compile("\([\d]{3}\)[\s]*[\d]{3}-[\d]{4}")  # (281) 558-9198, (713) 670-2457
clean_link = re.compile(r"[http]*[https]*[:/]*/?[\w]+[.][\w]+.*[.][\w]+")  # e.g. http://explorer.msn.com, https://explorer.msn.com.net"
clean_email_codes = re.compile("[=][\d]+")  # clear email codes "=19", "=20"
clean_very_long_text = re.compile("[\w+]{20,}")
# Other things to clean: Staff Meeting - Mt. Ranier 5/30/2001 Time: 1:00 PM - 3:00 PM (Central Standard Time)

# - we try to do a batch-wise extraction of the email contents based on the placeholders e.g. "To", "From", "Subject"
list_of_dict = []
for i in range(emails_df.shape[0]):  # i=4

    email_dict = {}  # empty dictionary to store the key-value pair
    temp_str = emails_df["message"][i].split("\n")  # assign string to variable; so can insert values to specific place

    # this step uses the above created dictionary to "impute" keys if there are missing key values, e.g. "To", "Cc"
    for pos in range(len(keys_list)):
        if temp_str[pos][0:len(keys_dict[pos][0])] != keys_dict[pos][0]:
            temp_str.insert(pos, str(keys_dict[pos][0]) + ': ')

    # this step performs the split and extract the key-value pair for the standard known field headers
    for j in range(0, 17):
        key = temp_str[j].split(":")[0]
        val = ':'.join(temp_str[j].split(":")[1:]).strip()
        email_dict[key] = val

    # this step saves the body of the text; we apply some regex logic
    text_body = temp_str[17:]
    text_body = " ".join([text for text in text_body]).strip()  # joins back all elements into a single string

    # apply regex logic
    text_body = re.sub(clean_field_headers, "", text_body)
    text_body = re.sub(clean_html_tags, "", text_body)
    text_body = re.sub(clean_emails, "", text_body)
    text_body = re.sub(clean_fwds, " ", text_body)
    text_body = re.sub(clean_unintended_sends, " ", text_body)
    text_body = re.sub(clean_dashes, " ", text_body)
    text_body = re.sub(clean_transmission_warn, " ", text_body)
    text_body = re.sub(clean_datetime, " ", text_body)
    text_body = re.sub(clean_link, " ", text_body)
    text_body = re.sub(clean_phone_fax, " ", text_body)
    text_body = re.sub(clean_phone_ctrycode, " ", text_body)
    text_body = re.sub(clean_addr_code, " ", text_body)
    text_body = re.sub(clean_email_codes, "", text_body)
    text_body = re.sub(clean_very_long_text, "", text_body)
    text_body = re.sub(clean_multi_symbols, " ", text_body)
    text_body = re.sub(clean_multi_space, " ", text_body)
    text_body = re.sub(clean_multi_symbols, " ", text_body)
    text_body = re.sub(clean_multi_space, " ", text_body)

    # this step saves the email body text as a value to the key named "body"
    email_dict["body"] = text_body.strip()

    # append the dictionary to a list, and later store as a dataframe
    list_of_dict.append(email_dict)

# - we compile the dictionary into a dataframe (rename columns) and print a few examples to take a look
emails_df_feat = pd.DataFrame(list_of_dict)
emails_df_feat.columns = ['Message-ID', 'DateTime', 'From', 'To', 'Subject', 'Cc', 'Mime-Version',  # Date -> DateTime
                          'Content-Type', 'Content-Transfer-Encoding', 'Bcc', 'X-From', 'X-To',
                          'X-cc', 'X-bcc', 'X-Folder', 'X-Origin', 'X-FileName', 'body']

# - we further clean up the email addresses in the "From". "To", "Cc", "Bcc" fields using Regex groups
# - e.g "houston <.ward@enron.com>", "e-mail <.brandon@enron.com>"; unlike the usual "houston.ward@enron.com"
reformat_emails = re.compile(r"(?P<part1>[\w-]+)[<\s]*(?P<part2>[\w.\'\W]+)(?P<domain>[@\w.-]+)")

cleaned_from_emails = reformat_email_func(emails_df_feat, "From", reformat_emails)
cleaned_to_emails = reformat_email_func(emails_df_feat, "To", reformat_emails)
cleaned_cc_emails = reformat_email_func(emails_df_feat, "Cc", reformat_emails)
cleaned_bcc_emails = reformat_email_func(emails_df_feat, "Bcc", reformat_emails)

# - replace the columns with the cleaned up emails
emails_df_feat.From = cleaned_from_emails
emails_df_feat.To = cleaned_to_emails
emails_df_feat.Cc = cleaned_cc_emails
emails_df_feat.Bcc = cleaned_bcc_emails

# - create new columns to include reformatted data: date, time, domain name (From and To) for emails
'''
- it seems like strptime cannot handle Timezone codes directly and more steps are required
- we are not going to need Timezone information for our purpose, so we are going to ignore them
'''
emails_df_feat["date"] = emails_df_feat["DateTime"].apply(lambda x: datetime
                                                          .strptime(x[:-6], "%a, %d %b %Y %H:%M:%S %z")
                                                          .strftime("%Y-%m-%d"))

emails_df_feat["time"] = emails_df_feat["DateTime"].apply(lambda x: datetime
                                                          .strptime(x[:-6], "%a, %d %b %Y %H:%M:%S %z")
                                                          .strftime("%H:%M:%S"))

emails_df_feat["From_domain"] = extract_domain(emails_df_feat, "From")
emails_df_feat["To_domain"] = extract_domain(emails_df_feat, "To")
emails_df_feat["Cc_domain"] = extract_domain(emails_df_feat, "Cc")
emails_df_feat["Bcc_domain"] = extract_domain(emails_df_feat, "Bcc")


# - we take a quick look at some of the rows based on some sample name matches; we used "apply" together with
# - "str" and "contains", and together with "loc", we can extract rows based on columns that have lists as elements
# - https://www.chicagotribune.com/sns-ap-enron-trial-glance-story.html
convicted_names = ['kenneth.lay','jeffrey.skilling','kevin.howard','michael.krautz','joe.hirko','rex.shelby',
                   'scott.yeager','andrew.fastow','david.bermingham','giles.darby','gary.mulgrew','daniel.bayly',
                   'james.brown','robert.furst','william.fuhs','dan.boyle','sheila.kahanek','christopher.calger',
                   'richard.causey','lfastow','paula.rieker','ken.rice','mark.koenig','kevin.hannon','tim.despain',
                   'jeff.richter','ben.glisan','david.delainey','michael.kopper','tim.belden','larry.lawyer',
                   'david.duncan','wes.colwell','raymond.bowen']

print(emails_df_feat.loc[(emails_df_feat.To.apply(lambda x : str(x)).str.contains('|'.join(convicted_names))), :].head())


########################################################################################################################
#   Find relationships using Sankey diagram - spot associations based on email address domains rather than names
########################################################################################################################

# - create the dataframe that will contain the "source" and "destination"
source_domains = emails_df_feat.From_domain.to_list()
dest_domains = [list(set(emails_df_feat.loc[num, "To_domain"])) for num in
                range(emails_df_feat.shape[0])]  # de-duplicated

# - introduce the source and destination lists and the dataframe with all the one-to-one mapping will be done
sankey_source, sankey_destin, source_dest_map_dedup, counter = one_to_one_mapping(source_domains, dest_domains)

# - obtain a dictionary to map the domain names into indices for purpose of plotting Sankey diagram
full_list_of_domains = sorted(list(set(sankey_source + sankey_destin)))
domain_dict = {domain: num for num, domain in enumerate(full_list_of_domains)}  # dictionary comprehension on key-value

# - create the fields required for the Sankey diagram
s2 = []  # to be directly used in plotting the Sankey diagram
d2 = []  # to be directly used in plotting the Sankey diagram
v2 = []  # to be directly used in plotting the Sankey diagram
for i in range(len(source_dest_map_dedup)):
    tag1 = source_dest_map_dedup[i]
    s2.append(domain_dict[tag1[0]])
    d2.append(domain_dict[tag1[1]])
    v2.append(counter[tag1[0], tag1[1]])

# - plot the sankey diagram
random.seed(24)
sample_vals = random.sample(range(0, len(s2)), 120)  # we sample 120 entries

fig1 = go.Figure(data=[go.Sankey(
                    node = dict(
                    pad = 5, thickness = 20, line = dict(color = "black", width = 0.5),
                    label = full_list_of_domains, color = "#3944BC"
                    ),
                    link = dict(source = [s2[i] for i in sample_vals],
                                target = [d2[i] for i in sample_vals],
                                value = [v2[i] for i in sample_vals],
                                color = "#F699CF"))])

fig1.update_layout(title_text="Sankey Diagram to show associations based on email domains", font_size=10)
fig1.show()


########################################################################################################################
#   Knowledge graph - to discover associations / information from email messages
########################################################################################################################
'''
- building graphs requires nodes and edges; same goes for knowledge graphs
- the nodes are going to be the entities mentioned in the sentences; edges are the relationships connecting the nodes
- convert the email bodies into sentences

- NOTE: plotting Knowledge Graph for email messages may not be quite feasible given the way that emails are written, the
- reason for doing Knowledge Graph for this exercise is purely for learning purposes

- References: https://gist.github.com/quadrismegistus/92a7fba479fc1e7d2661909d19d4ae7e, 
- https://pyvis.readthedocs.io/en/latest/tutorial.html, https://github.com/WestHealth/pyvis,
- https://www.analyticsvidhya.com/blog/2019/10/how-to-build-knowledge-graph-text-using-spacy/
'''
# - create the required "document"; we further create sentence tokens to extract the entities and relationships
# full_email_doc = nlp(' '.join(emails_df_feat.body.to_list()))
email_doc_sentences = sent_tokenize(' '.join(emails_df_feat.body.to_list()))

# - extract the entities and relations (if the entity pair does not contain just a 'blank' entity)
# - this for loop takes a while, we use TQDM here to track its progress
entity_pairs = []
relations = []
exclusion_list = ['','you','i','me','them','we','they','it','this','who','us','he','that','she','what','>']
for i in tqdm(email_doc_sentences):
    if (get_entities(i)[0].lower() not in exclusion_list) and (get_entities(i)[1].lower() not in exclusion_list):
        entity_pairs.append(get_entities(i))
        relations.append(get_relation(i))

# - we print the top 50 entity pairs and top 50 relations; choose one to plot for the Knowledge Graph later
print(pd.Series(entity_pairs).value_counts().head(50))
print(pd.Series(relations).value_counts().head(50))

# - create the dataframe for Knowledge Graph
source_kg = [s[0] for s in entity_pairs]
destin_kg = [d[1] for d in entity_pairs]
know_df = pd.DataFrame({'source': source_kg, 'destination': destin_kg, 'edge': relations})

# - identify if the nodes contain names of interest (based on Wikipedia, the C-suite officers)
name_patterns = '[Ee]nron|[Bb]yron|[Kk]enneth|[Jj]effrey|[Ss]killing|[Aa]ndrew|[Ff]astow'

# - we create the filtered dataframe for Knowledge Graph based on name matching patterns
filtered_know_df = know_df.loc[(know_df.source.str.contains(name_patterns)) |
                               know_df.destination.str.contains(name_patterns), :].reset_index(drop=True)

sample_idx1 = random.sample(range(0, filtered_know_df.shape[0]), 120)  # we sample 120 entries
filtered_know_df = filtered_know_df.loc[sample_idx1, :].reset_index(drop=True)

# - create the nodes list with the colours; nodes are coloured if they contain the names of interest
full_nodes = filtered_know_df.source.to_list() + filtered_know_df.destination.to_list()
color_nodes = ['red' if re.findall(name_patterns, i.lower()) != [] else '#3944BC' for i in full_nodes]
image_nodes = ["/home/kelvinhwee/PycharmProjects/enronFraudEmailAnalysis/bad guy.JPG"
               if re.findall(name_patterns, i.lower()) != []
               else "/home/kelvinhwee/PycharmProjects/enronFraudEmailAnalysis/good guy.JPG" for i in full_nodes]

nodes_color_df = pd.DataFrame({'node': full_nodes, 'color': color_nodes, 'image': image_nodes})

# - plot the Knowledge Graph: initialise the networkx graph object
G_know = nx.Graph()

# - plot the Knowledge Graph: add nodes (do we want to consider the weightage)
for i in range(nodes_color_df.shape[0]):
    G_know.add_node(nodes_color_df["node"][i], color=nodes_color_df["color"][i],
                    shape='image',
                    image=nodes_color_df["image"][i])

# - plot the Knowledge Graph: add edges (label the edges with the relation)
for i in range(filtered_know_df.shape[0]):
    G_know.add_edge(filtered_know_df["source"][i], filtered_know_df["destination"][i],
                    label=filtered_know_df["edge"][i], title=filtered_know_df["edge"][i])

# - plot the final graph using Pyvis (https://pyvis.readthedocs.io/en/latest/documentation.html)
nt_know = Network(height=1000, width=1200, directed=True)
nt_know.toggle_hide_edges_on_drag(True)

# - BarnesHut is a quadtree based gravity model. It is the fastest
nt_know.barnes_hut(spring_length=10, overlap=0.5, gravity=-10000, central_gravity=0.8)
nt_know.from_nx(G_know)
nt_know.show("knowledge_graph.html")


########################################################################################################################
#   Network graph to show the connections between various parties; scoring of parties and plot graph based on them
########################################################################################################################
'''

References: https://networkx.org/documentation/stable/reference/algorithms/index.html
'''
# - get the one-to-one mapping for the email addresses
email_sender_list = emails_df_feat.From.to_list()
email_recipient_list = emails_df_feat.To.to_list()
net_source, net_destin, source_dest_net_map, _  = one_to_one_mapping(email_sender_list, email_recipient_list)

# - create the dataframe for Network Graph
net_df = pd.DataFrame({'source': net_source, 'destination': net_destin})

# - we create the filtered dataframe for Network Graph and drop 'blank' destinations and the self-sending ones
filtered_net_df = net_df.loc[net_df.destination != '', :].reset_index(drop = True)
filtered_net_df = filtered_net_df.loc[filtered_net_df.source != filtered_net_df.destination, :].reset_index(drop = True)

# - we identify which rows contain some of the names of interest (based on Wikipedia, the C-suite officers)
name_patterns_net = '[Ss]killing|[Ff]astow|[Jj]usbasche|[Cc]ooper|[Bb]elden'
interest_idx = filtered_net_df.loc[filtered_net_df.source.str.contains(name_patterns_net) |
                                   filtered_net_df.destination.str.contains(name_patterns_net), :].head(300).index

# - we identify names that we want to exclude
name_patterns_excl = '[Tt]echnology|outlook.team'
excl_idx = filtered_net_df.loc[filtered_net_df.source.str.contains(name_patterns_excl) |
                               filtered_net_df.destination.str.contains(name_patterns_excl), :].index

# - complete the list
list_of_idx = [num for num in range(filtered_net_df.shape[0]) if num not in list(excl_idx) + list(interest_idx)]

# - we take a sample of the dataframe for plotting the graph
sample_idx2 = random.sample(list_of_idx, min(3000, len(list_of_idx))) + list(interest_idx) # sample the emails

# - final sample dataframe for plotting
sample_net_df = filtered_net_df.loc[sample_idx2 + list(interest_idx), :].reset_index(drop=True)

# - create the list of source and destination nodes
full_nodes_net = sample_net_df.source.to_list() + sample_net_df.destination.to_list()

# - we colour based on emails that contain names of interest, and whether the email address is an 'Enron' email
color_nodes_net = []
for i in full_nodes_net:
    if re.findall(name_patterns_net, i.lower()):
        color_nodes_net.append('red')
    elif 'enron' in i.lower():
        color_nodes_net.append('#AEF359')
    else:
        color_nodes_net.append('#3944BC')

nodes_color_net_df = pd.DataFrame({'node': full_nodes_net, 'color': color_nodes_net})

# - plot the Network Graph: initialise the networkx graph object
G_net = nx.Graph()

# - plot the Network Graph: add nodes (do we want to consider the weightage)
for i in range(nodes_color_net_df.shape[0]):
    G_net.add_node(nodes_color_net_df["node"][i], color=nodes_color_net_df["color"][i], layout = 'hierarchical')

# - plot the Network Graph: add edges (label the edges with the relation)
for i in range(sample_net_df.shape[0]):
    G_net.add_edge(sample_net_df["source"][i], sample_net_df["destination"][i])

# - plot the final graph using Pyvis (https://pyvis.readthedocs.io/en/latest/documentation.html)
nt_network = Network(height=1000, width=1200, directed=True)
nt_network.toggle_hide_edges_on_drag(False)
nt_network.from_nx(G_net)
nt_network.show("network_graph.html")


# - we try to derive the degree centrality score of the nodes
deg_cent_G1 = nx.degree_centrality(G_net)
deg_g1_df = pd.DataFrame(deg_cent_G1.items(), columns=['Emails', 'Deg_centrality'])\
                            .sort_values(by = "Deg_centrality", ascending=False)

print('We look at the top 10 email addresses (for degree centrality): ', deg_g1_df.head(10))


# - we try to derive the closeness centrality score of the nodes
close_cent_G1 = nx.closeness_centrality(G_net)
close_g1_df = pd.DataFrame(close_cent_G1.items(), columns=['Emails', 'Closeness_centrality'])\
                            .sort_values(by = "Closeness_centrality", ascending=False)

print('We look at the top 10 email addresses (for closeness centrality): ', close_g1_df.head(10))


# - we try to derive the between centrality score of the nodes
btwn_cent_G1 = nx.betweenness_centrality(G_net)
btwn_g1_df = pd.DataFrame(btwn_cent_G1.items(), columns=['Emails', 'Betweeness_centrality'])\
                            .sort_values(by = "Betweeness_centrality", ascending=False)

print('We look at the top 10 email addresses (for betweeness centrality): ', btwn_g1_df.head(10))


# - we combine the scores and return the top 3 and its graph
cent_scores_df = deg_g1_df.merge(close_g1_df, how='left', on='Emails').merge(btwn_g1_df, how='left', on='Emails')
cent_scores_df["Total_scores"] = cent_scores_df.Deg_centrality * \
                                 cent_scores_df.Closeness_centrality * \
                                 cent_scores_df.Betweeness_centrality

cent_scores_df = cent_scores_df.sort_values(by="Total_scores", ascending=False)

print('We look at the top 10 email addresses (for total score): ', cent_scores_df.head(10))


# - plot graph for the top 3 most central nodes
top3_emails = cent_scores_df.loc[:2, "Emails"].to_list()

top3_net_df = filtered_net_df.loc[filtered_net_df.source.isin(top3_emails) |
                                  filtered_net_df.destination.isin(top3_emails), :].reset_index(drop=True)

# - create the list of source and destination nodes
top3_nodes_net = top3_net_df.source.to_list() + top3_net_df.destination.to_list()

# - we colour based on emails that contain names of interest, and whether the email address is an 'Enron' email
top3_color_nodes_net = []
for i in top3_nodes_net:
    if i in top3_emails:
        top3_color_nodes_net.append('red')
    elif 'enron' in i.lower():
        top3_color_nodes_net.append('#AEF359')
    else:
        top3_color_nodes_net.append('#3944BC')

top3_nodes_color_net_df = pd.DataFrame({'node': top3_nodes_net, 'color': top3_color_nodes_net})

# - plot the Network Graph: initialise the networkx graph object
G_net_top3 = nx.Graph()

# - plot the Network Graph: add nodes (do we want to consider the weightage)
for i in range(top3_nodes_color_net_df.shape[0]):
    G_net_top3.add_node(top3_nodes_color_net_df["node"][i],
                        color=top3_nodes_color_net_df["color"][i],
                        layout = 'hierarchical')

# - plot the Network Graph: add edges (label the edges with the relation)
for i in range(top3_net_df.shape[0]):
    G_net_top3.add_edge(top3_net_df["source"][i], top3_net_df["destination"][i])

# - plot the final graph using Pyvis (https://pyvis.readthedocs.io/en/latest/documentation.html)
top3_network = Network(height=1000, width=1200, directed=True)
top3_network.toggle_hide_edges_on_drag(False)
top3_network.from_nx(G_net_top3)
top3_network.show("network_graph_top3.html")



