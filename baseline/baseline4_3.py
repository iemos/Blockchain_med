# baseline4_3
# ts range query
# use liststreamkeys to directly range query
# NOT WORKING



# Most lines' ref-ID are refer back to the same original ID,
# which means those lines' User and Resource are the same. For this
# reason, we can exculde User and Resource in transaction. When node
# queries User and Resource, the baseline4 first get its original
# Node+ID, and use Node+ID to query additional result and union them

from config import ATTRIBUTE, ATTRIBUTE_NAME, MAX_RESULT
from util import getData, createStream, ENCODE_FORMAT, database
from sortedcontainers import SortedList


DO_VALIDATION = False

att_dict = {key: value for key, value in zip(ATTRIBUTE, ATTRIBUTE_NAME)}
att_name_index = {value: counter for counter,
                  value in enumerate(ATTRIBUTE_NAME)}


def createStreams(api):
    for att in ATTRIBUTE_NAME:
        createStream(api, att)


def insert(api, data):
    result = api.listunspent(0)
    txid = result["result"][0]["txid"]
    vout = result["result"][0]["vout"]
    address = api.getaddresses()["result"][0]
    for line in data:
        hexstr = line.encode(ENCODE_FORMAT).hex()
        values = line.split(" ")
        data = []
        short = ATTRIBUTE_NAME.copy()
        short.remove('User')
        short.remove('Resource')
        if values[att_name_index['ID']] == values[att_name_index['Ref-ID']]:
            for att, v in zip(ATTRIBUTE_NAME, values):
                data.append({"for": att, "key": v, "data": hexstr})
        else:
            for key in short:
                data.append(
                    {"for": key, "key": values[att_name_index[key]], "data": hexstr})
        txid = api.createrawtransaction(
            [{'txid': txid, 'vout': vout}], {address: 0}, data, 'send')["result"]
        vout = 0


# sort the result in memory
# NEED TO TEST AGAIN
def pointQuery(api, attribute, value):
    result = getData(api.liststreamkeyitems(
        attribute, value, False, MAX_RESULT)["result"])
    temp = []
    if attribute == "User" or attribute == "Resource":
        for line in result:
            node, ID = line.split(" ")[1:3]
            RIDResult = getData(api.liststreamkeyitems(
                'Ref-ID', ID, False, MAX_RESULT)["result"])
            for r in RIDResult:
                if r.split(" ")[1] == node:
                    temp += [r]
    result += temp
    return result


def rangeQuery(api, start, end):
    result = []
    stream = att_dict['T']
    results = api.liststreamkeys(stream, list(
        map(str, range(start, end))), True)["result"]
    # print(results)
    # input()
    for r in results:
        # if > 1. deal it later
        if r['items'] >= 1:
            result.append(bytes.fromhex(
                r["first"]["data"]).decode(ENCODE_FORMAT))

            # # timestamps = api.liststreamkeys(stream)["result"]
            # # print(timestamps)
            # # input()
            # sl = SortedList(list(map(int, [key['key'] for key in timestamps])))
            # temp = api.liststreamkeys(stream, list(
            #     map(str, sl.irange(start, end))), True)["result"]
            # # print(*result, sep='\n')
            # # input()
            # for r in temp:
            #     result.append(bytes.fromhex(r["first"]["data"]).decode(ENCODE_FORMAT))
            # # for timestamp in sl.irange(start, end):
            #     result += getData(api.liststreamkeyitems(stream,
            #                                              str(timestamp))['result'])
            # print(result)
            # input()
            # ts = [v[0] for v in database["Timestamp"].values()][:400]
            # sl = SortedList(ts, key=lambda a: a.split(" ")[0])
            # ans = list(sl.irange(str(start), str(end)))
            # if set(result) != set(ans):
            #     print('result:\n', *result, sep='\n')
            #     print('ans:\n', *ans, sep='\n')
            # #     print('result:\n', *(set(result) - set(ans)), sep='\n')
            #     print('ans:\n', *(set(ans) - set(result)), sep='\n')

    return result


def andQuery(api, attAndVal):
    resultSet = []
    for attr, value in attAndVal:
        resultSet.append(set(pointQuery(api, attr, value)))
    result = resultSet[0]
    for i in range(1, len(resultSet)):
        result &= resultSet[i]
    return list(result)


def sortResult(results, attribute, reverse=False):
    return results.sort(reverse=reverse, key=lambda line: int(line.split(" ")[att_name_index[attribute]]))
