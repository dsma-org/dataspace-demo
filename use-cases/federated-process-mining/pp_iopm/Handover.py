import json


class Handover():
    def __init__(self):
        self.id = 0
        self.case_id = 0
        self.org = ""
        self.act = ""
        self.org_from = ""
        self.org_to = ""

    def toJSON(self):
        return json.dumps(
            self,
            default=lambda o: o.__dict__,
            sort_keys=True,
        )

    def fromJSON(json_data):
        result = Handover()

        result.id = json_data['id']
        result.case_id = json_data['case_id']
        result.org = json_data['org']
        result.act = json_data['act']
        result.org_from = json_data['org_from']
        result.org_to = json_data['org_to']

        return result