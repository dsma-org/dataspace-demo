import json
import os

from pp_iopm.Connector import convert_list_to_dict
from pp_iopm.Handover import Handover
from pp_iopm.IOPM import IOPM

current_dir = os.path.dirname(os.path.realpath(__file__))

abstractions = {}

with(open(os.path.join(current_dir, 'manufacturer_abstraction.json'))) as f:
    abstractions['Manufacturer'] = json.load(f)

with(open(os.path.join(current_dir, 'shipper_abstraction.json'))) as f:
    abstractions['Shipper'] = json.load(f)

with(open(os.path.join(current_dir, 'supplier_abstraction.json'))) as f:
    abstractions['Supplier'] = json.load(f)

abstractions['Manufacturer'] = [(v[0], v[1]) for v in abstractions['Manufacturer']]
abstractions['Shipper'] = [(v[0], v[1]) for v in abstractions['Shipper']]
abstractions['Supplier'] = [(v[0], v[1]) for v in abstractions['Supplier']]

handover_relations = []

with(open(os.path.join(current_dir, 'manufacturer_relations.json'))) as f:
    handover_relations.append(json.load(f))

with(open(os.path.join(current_dir, 'shipper_relations.json'))) as f:
    handover_relations.append(json.load(f))

with(open(os.path.join(current_dir, 'supplier_relations.json'))) as f:
    handover_relations.append(json.load(f))

handover_relations[0]['table'] = [Handover.fromJSON(json.loads(v)) for v in handover_relations[0]['table']]
handover_relations[1]['table'] = [Handover.fromJSON(json.loads(v)) for v in handover_relations[1]['table']]
handover_relations[2]['table'] = [Handover.fromJSON(json.loads(v)) for v in handover_relations[2]['table']]

iopm = IOPM(3)
org_names = ["Manufacturer", "Supplier", "Shipper"]
org_abbreviations = {"Ma": "Manufacturer", "Sh": "Shipper", "Su": "Supplier"}
org_activities = [["create_purchase_order", "send_order_request", "order_rejection", "invoice_receipt", "payment",
                   "order_confirmation", "goods_receipt", "dispatched", "delivered", "order_check"],
                  ["receive_order", "adapt_order", "order_management", "reject", "accept", "order_process",
                   "create_invoice", "order_shipment", "ship_started", "order_dispatch", "send_invoice",
                   "payment_collection"],
                  ["receive_request", "preparation", "loading", "transport", "failed_delivery", "delivery"]
                  ]
iopm.define_orgs(org_names, org_activities)

case_id_set = set()
case_ids = []
for i in range(len(handover_relations)):
    for v in handover_relations[i]['table']:
        if v.case_id not in case_id_set:
            case_ids.append(v.case_id)
            case_id_set.add(v.case_id)

handover_relations, handover_to, handover_from = iopm.discover_handover_relations(handover_relations, case_ids)

cuel_without_handover = abstractions['Manufacturer'] + abstractions['Shipper'] + abstractions['Supplier']

cuel_with_handover, remaining_handover = iopm.update_cuel_scm(cuel_without_handover, handover_relations)
dict_freq, dict_start, dict_end = convert_list_to_dict(cuel_with_handover + remaining_handover)

with(open(os.path.join(current_dir, 'aggregated_result.json'), 'w')) as f:
    result = {}
    result['dict_freq'] = [{'from': k[0], 'to': k[1], 'count': v} for k,v in dict_freq.items()]
    result['dict_start'] = dict(dict_start)
    result['dict_end'] = dict(dict_end)
    json.dump(result, f)