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