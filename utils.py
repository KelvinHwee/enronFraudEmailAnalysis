################################################################################
#   Basic required packages
################################################################################
import re


################################################################################
#   create correlation plots on the oversampled training data
################################################################################

def extract_domain(df, col_name):
    list_of_domains = []
    for num in range(df.shape[0]):
        try:
            list_of_domains.append(list(set([re.findall(r"@(.*)[.]", i)[0]
                                        for i in df.loc[num, col_name].split(",")])))
        except:
            list_of_domains.append(list()) # this appends an empty list

    return list_of_domains






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
