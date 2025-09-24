import json
import os

from pm4py.objects.log.importer.xes import importer as xes_importer

from pp_iopm.Connector import Connector

current_dir = os.path.dirname(os.path.realpath(__file__))
log_name = "supplier.xes"
log_path = os.path.join(current_dir, log_name)
log = xes_importer.apply(log_path)
connector_obj = Connector(log)
abstraction, _ = connector_obj.convert_to_basic_connector()

with(open(os.path.join(current_dir, 'supplier_abstraction.json'), 'w')) as f:
    json.dump(abstraction, f)
