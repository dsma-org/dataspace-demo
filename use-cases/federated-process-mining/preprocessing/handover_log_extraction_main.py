import os
from pm4py.objects.log.importer.xes import importer as xes_importer
import pm4py
from pp_iopm.Connector import Connector
from pp_iopm.IOPM import IOPM
import json

current_dir = os.path.dirname(os.path.realpath(__file__))
log_name = "supply_chain.xes"
log_path = os.path.join(current_dir, './orig_data', log_name)
log = xes_importer.apply(log_path)
log = pm4py.insert_artificial_start_end(log)
connector_obj = Connector(log)
basic_conn_all, case_ids = connector_obj.convert_to_basic_connector()

iopm = IOPM(3)
org_names = ["Manufacturer", "Supplier", "Shipper"]
org_abbreviations = {"Ma": "Manufacturer", "Sh": "Shipper", "Su": "Supplier"}
org_activities = [["create_purchase_order", "send_order_request", "order_rejection", "invoice_receipt", "payment",
                   "order_confirmation", "goods_receipt", "dispatched", "delivered", "order_check"],
                  ["receive_order", "adapt_order", "order_management", "reject", "accept", "order_process",
                   "payment_collection"],
                  ["receive_request", "preparation", "loading", "transport", "failed_delivery", "delivery"]
                  ]
iopm.define_orgs(org_names, org_activities)

handover_relations = iopm.create_handover_tables(log)

manufacturer_relations = handover_relations[0]
supplier_relations = handover_relations[1]
shipper_relations = handover_relations[2]

manufacturer_relations['table'] = [v.toJSON() for v in manufacturer_relations['table']]
with(open(os.path.join(current_dir, './organization_data', 'manufacturer_relations.json'), 'w')) as f:
    json.dump(manufacturer_relations, f, sort_keys=True)

supplier_relations['table'] = [v.toJSON() for v in supplier_relations['table']]
with(open(os.path.join(current_dir, './organization_data', 'supplier_relations.json'), 'w')) as f:
    json.dump(supplier_relations, f, sort_keys=True)

shipper_relations['table'] = [v.toJSON() for v in shipper_relations['table']]
with(open(os.path.join(current_dir, './organization_data', 'shipper_relations.json'), 'w')) as f:
    json.dump(shipper_relations, f, sort_keys=True)
