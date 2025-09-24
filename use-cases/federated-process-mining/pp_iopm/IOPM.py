import itertools

from pp_iopm.Organization import Organization
from pp_iopm.Handover import Handover


class IOPM():

    def __init__(self, org_number):
        self.org_number = org_number
        self.org_list = []
        for org_id in range(org_number):
            org = Organization()
            org.id = org_id
            self.org_list.append(org)

    def define_orgs(self, org_names, org_activities):
        for index, org in enumerate(self.org_list):
            org.name = org_names[index]
            org.act_list = org_activities[index]

    def get_act_list_of_org(self, name):
        for org in self.org_list:
            if org.name == name:
                return org.act_list
        return []

    def get_org_of_act(self, act):
        for org in self.org_list:
            if act in org.act_list:
                return org.name
        return ""

    def create_handover_tables(self, log):
        handover_tables = []
        for org in self.org_list:
            handover_table = {"org": org.name, "table": []}
            handover_tables.append(handover_table)

        for case in log:
            for index, event in enumerate(case):
                if index == 0:
                    previous_act = ""
                else:
                    previous_act = current_act
                current_act = event["concept:name"]
                current_org = self.get_org_of_act(current_act)
                previous_org = self.get_org_of_act(previous_act)
                if current_org != previous_org and previous_org != "" and current_org != "":
                    for handover_tab in handover_tables:
                        if handover_tab["org"] == previous_org:
                            handover_record = Handover()
                            if len(handover_tab["table"]) > 0:
                                handover_record.id = handover_tab["table"][-1].id + 1
                            else:
                                handover_record.id = 1
                            handover_record.case_id = case.attributes["concept:name"]
                            handover_record.org = previous_org
                            handover_record.act = previous_act
                            handover_record.org_to = current_org
                            handover_tab["table"].append(handover_record)

                        if handover_tab["org"] == current_org:
                            handover_record = Handover()
                            if len(handover_tab["table"]) > 0:
                                handover_record.id = handover_tab["table"][-1].id + 1
                            else:
                                handover_record.id = 1
                            handover_record.case_id = case.attributes["concept:name"]
                            handover_record.org = current_org
                            handover_record.act = current_act
                            handover_record.org_from = previous_org
                            handover_tab["table"].append(handover_record)

        return handover_tables

    def get_handover_table_with_name(self, handover_tables, org_name):
        for item in handover_tables:
            if item["org"] == org_name:
                return item["table"]
        return []

    def get_handover_records_of_case(self, handover_table, case_id):
        records_of_case = []
        for record in handover_table:
            if record.case_id == case_id:
                records_of_case.append(record)
        return records_of_case

    def get_first_match_from(self,records_from, record):
        for record_from in records_from:
            if record_from.org_to == record.org:
                return record_from

    def get_first_match_to(self, records_to, record):
        for record_to in records_to:
            if record_to.org_from == record.org:
                return record_to

    def handover_miner(self, handover_tables, handover_tab, case_id, case_handovers, HOR):
        while len(case_handovers) > 0:
            first_rec = case_handovers[0]
            hor = ["", ""]

            if first_rec.org_to != "":
                hor[0] = first_rec.act

            else:
                handover_tab_from = self.get_handover_table_with_name(handover_tables, first_rec.org_from)
                case_handovers_from = self.get_handover_records_of_case(handover_tab_from, case_id)
                # first_rec_from = case_handovers_from[0]

                first_rec_from = self.get_first_match_from(case_handovers_from,first_rec)
                hor[0] = first_rec_from.act

                handover_tab_from.remove(first_rec_from)

            if first_rec.org_from != "":
                hor[1] = first_rec.act

            else:
                handover_tab_to = self.get_handover_table_with_name(handover_tables, first_rec.org_to)
                case_handovers_to = self.get_handover_records_of_case(handover_tab_to, case_id)
                # first_rec_to = case_handovers_to[0]

                first_rec_to = self.get_first_match_to(case_handovers_to, first_rec)
                hor[1] = first_rec_to.act

                handover_tab_to.remove(first_rec_to)

            case_handovers.pop(0)
            handover_tab.remove(first_rec)
            HOR.append(tuple(hor))

        return HOR

    # Algorithm 1
    def discover_handover_relations(self, handover_tables, case_ids):
        HOR = []
        for case_id in case_ids:
            for handover_item in handover_tables:
                handover_tab = handover_item["table"]
                case_handovers = self.get_handover_records_of_case(handover_tab, case_id)
                HOR = self.handover_miner(handover_tables, handover_tab, case_id, case_handovers, HOR)

        handover_to = []
        handover_from = []
        for item in HOR:
            handover_to.append(item[0])
            handover_from.append(item[1])

        return HOR, handover_to, handover_from


    def update_cuel_subcon(self, cuel, handover_relations):
        DEFAULT_ARTIFICIAL_START_ACTIVITY = "▶"
        DEFAULT_ARTIFICIAL_END_ACTIVITY = "■"
        add_set = set()
        delete_list = []
        from collections import defaultdict
        dict_rel = defaultdict(int)
        for item in handover_relations:
            dict_rel[item] += 1

        hor_permutations = list(itertools.permutations([hor for hor in handover_relations], 2))
        for hor_pair in set(hor_permutations):
            if hor_pair[0] != hor_pair[1]:
                for dfr in cuel:
                    if dfr[0] == hor_pair[0][0] and dfr[1] == hor_pair[1][1] and \
                            (DEFAULT_ARTIFICIAL_START_ACTIVITY, hor_pair[0][1]) in cuel \
                            and (hor_pair[1][0], DEFAULT_ARTIFICIAL_END_ACTIVITY) in cuel:
                        delete_list.append(dfr)
                        delete_list.append((DEFAULT_ARTIFICIAL_START_ACTIVITY, hor_pair[0][1]))
                        delete_list.append((hor_pair[1][0], DEFAULT_ARTIFICIAL_END_ACTIVITY))
                        add_set.add(hor_pair[0])
                        add_set.add(hor_pair[1])

        for del_item in delete_list:
            if del_item in cuel:
                cuel.remove(del_item)

        for add_item in add_set:
            for i in range(dict_rel[add_item]):
                cuel.append(add_item)

        remaining_hor = []
        for hor in handover_relations:
            if hor not in add_set:
                remaining_hor.append(hor)

        return cuel, remaining_hor

    def update_cuel_any_type(self, cuel, handover_relations, handover_to, handover_from):
        DEFAULT_ARTIFICIAL_START_ACTIVITY = "▶"
        DEFAULT_ARTIFICIAL_END_ACTIVITY = "■"
        add_set = set()
        delete_list = []
        from collections import defaultdict
        dict_rel = defaultdict(int)
        for item in handover_relations:
            dict_rel[item] += 1

        hor_permutations = list(itertools.permutations([hor for hor in handover_relations], 2))
        for hor_pair in set(hor_permutations):
            if hor_pair[0] != hor_pair[1]:
                for dfr in cuel:
                    if dfr[0] == hor_pair[0][0] and dfr[1] == hor_pair[1][1] and \
                            (DEFAULT_ARTIFICIAL_START_ACTIVITY, hor_pair[0][1]) in cuel \
                            and (hor_pair[1][0], DEFAULT_ARTIFICIAL_END_ACTIVITY) in cuel:
                        delete_list.append(dfr)
                        delete_list.append((DEFAULT_ARTIFICIAL_START_ACTIVITY, hor_pair[0][1]))
                        delete_list.append((hor_pair[1][0], DEFAULT_ARTIFICIAL_END_ACTIVITY))
                        add_set.add(hor_pair[0])
                        add_set.add(hor_pair[1])
                    if dfr[0] == hor_pair[0][0] and dfr[1] == hor_pair[1][1]:
                        handover_to_match = self.check_to_match(cuel, hor_pair[0][1], handover_to)
                        if handover_to_match:
                            handover_from_match = self.check_from_match(cuel, hor_pair[1][0], handover_from)
                            if handover_from_match:
                                delete_list.append(dfr)
                                delete_list.append(handover_to_match)
                                delete_list.append(handover_from_match)
                                add_set.add(hor_pair[0])
                                add_set.add(hor_pair[1])

        for del_item in delete_list:
            if del_item in cuel:
                cuel.remove(del_item)

        for add_item in add_set:
            for i in range(dict_rel[add_item]):
                cuel.append(add_item)

        remaining_hor = []
        for hor in handover_relations:
            if hor not in add_set:
                remaining_hor.append(hor)

        cuel, remaining_hor = self.update_cuel_scm(cuel,remaining_hor)

        return cuel

    def update_cuel_other(self, cuel, handover_relations, handover_to, handover_from):

        add_set = set()
        delete_list = []
        from collections import defaultdict
        dict_rel = defaultdict(int)
        for item in handover_relations:
            dict_rel[item] += 1

        hor_permutations = list(itertools.permutations([hor for hor in handover_relations], 2))
        for hor_pair in set(hor_permutations):
            if hor_pair[0] != hor_pair[1]:
                for dfr in cuel:
                    if dfr[0] == hor_pair[0][0] and dfr[1] == hor_pair[1][1]:
                        handover_to_match = self.check_to_match(cuel, hor_pair[0][1], handover_to)
                        if handover_to_match:
                            handover_from_match = self.check_from_match(cuel, hor_pair[1][0], handover_from)
                            if handover_from_match:
                                delete_list.append(dfr)
                                delete_list.append(handover_to_match)
                                delete_list.append(handover_from_match)
                                add_set.add(hor_pair[0])
                                add_set.add(hor_pair[1])

        for del_item in delete_list:
            if del_item in cuel:
                cuel.remove(del_item)

        for add_item in add_set:
            for i in range(dict_rel[add_item]):
                cuel.append(add_item)

        remaining_hor = []
        for hor in handover_relations:
            if hor not in add_set:
                remaining_hor.append(hor)

        return cuel,remaining_hor


    def check_to_match(self, cuel, fixed_connection, handover_to):
        for x in handover_to:
            if (x,fixed_connection) in cuel:
                return (x,fixed_connection)
        return False

    def check_from_match(self, cuel, fixed_connection, handover_from):
        for x in handover_from:
            if (fixed_connection,x) in cuel:
                return (fixed_connection,x)
        return False

    def update_cuel_subcon_scm(self, cuel, handover_relations):

        cuel, remaining_hor = self.update_cuel_subcon(cuel, handover_relations)
        cuel, remaining_hor = self.update_cuel_scm(cuel, remaining_hor)

        return cuel

    def update_cuel_scm(self, cuel, handover_relations):
        DEFAULT_ARTIFICIAL_START_ACTIVITY = "▶"
        DEFAULT_ARTIFICIAL_END_ACTIVITY = "■"
        add_list = []
        for hor in handover_relations:
            found_start = False
            found_end = False
            delete_list = []
            for dfr in cuel:
                if not found_end and dfr[0] == hor[0] and dfr[1] == DEFAULT_ARTIFICIAL_END_ACTIVITY:
                    found_end = True
                    delete_list.append(dfr)
                if not found_start and dfr[0] == DEFAULT_ARTIFICIAL_START_ACTIVITY and dfr[1] == hor[1]:
                    found_start = True
                    delete_list.append(dfr)
            if found_start and found_end:
                for dfr in delete_list:
                    cuel.remove(dfr)
                cuel.append(hor)
                add_list.append(hor)

        remaining_handover = []
        for handover in handover_relations:
            if handover not in add_list:
                remaining_handover.append(handover)

        return cuel,remaining_handover