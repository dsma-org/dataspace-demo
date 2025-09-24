class Connector():

    def __init__(self,log):
        self.log = log


    def convert_to_basic_connector(self, with_handover = False, org_name = None, iopm = None):
        basic_conn = {'connector': [], 'handover': 0}
        case_ids = []
        for case in self.log:
            case_ids.append(case.attributes["concept:name"])
            for index, event in enumerate(case):
                if index % 2 == 0:
                    connector = []
                    connector.append(event["concept:name"])
                    if index > 0:
                        connector_2 = []
                        connector_2.append(basic_conn['connector'][-1][1])
                        connector_2.append(event["concept:name"])
                        con_tupe = tuple(connector_2)
                        basic_conn['connector'].append(con_tupe)
                else:
                    connector.append(event["concept:name"])
                    con_tupe= tuple(connector)
                    basic_conn['connector'].append(con_tupe)

        return basic_conn['connector'], case_ids

    def check_handover(self,connector, org_name, iopm):
        act_list = iopm.get_act_list_of_org(org_name)


def convert_list_to_dict(list):
    from collections import defaultdict
    DEFAULT_ARTIFICIAL_START_ACTIVITY = "▶"
    DEFAULT_ARTIFICIAL_END_ACTIVITY = "■"

    dict_freq = defaultdict(int)
    dict_start = defaultdict(int)
    dict_end = defaultdict(int)
    for item in list:
        #ignoring artificial start and end
        if not (item[0] == DEFAULT_ARTIFICIAL_START_ACTIVITY or item[1] == DEFAULT_ARTIFICIAL_END_ACTIVITY):
            dict_freq[item] += 1
        if item[0] == DEFAULT_ARTIFICIAL_START_ACTIVITY:
            dict_start[item[1]] += 1
        if item[1] == DEFAULT_ARTIFICIAL_END_ACTIVITY:
            dict_end[item[0]] += 1
    return dict_freq, dict_start, dict_end