import os

import pm4py
from pm4py.objects.log.exporter.xes import exporter as xes_exporter
from pm4py.objects.log.importer.xes import importer as xes_importer


def create_new_trace(id):
    result = pm4py.objects.log.obj.Trace()
    result.attributes["concept:name"] = f"trace_{id}"
    return result


def preprocess_log_orgs(log, org):
    result = pm4py.objects.log.obj.EventLog()
    id = 0

    trace_list = []
    curr_trace = None

    # Add what happens in the organization itself
    for trace in log:
        for event in trace:
            if event['Org:resource'] == org:
                if curr_trace is None:
                    id += 1
                    curr_trace = create_new_trace(id)
                curr_trace.append(event)
            else:
                if curr_trace is not None:
                    trace_list.append(curr_trace)
                    curr_trace = None
        if curr_trace is not None:
            trace_list.append(curr_trace)
            curr_trace = None

    # Do not add empty traces
    for trace in trace_list:
        if not (len(trace) == 1 and (trace[0]['concept:name'] == "▶" or trace[0]['concept:name'] == "■")) and not (
                len(trace) == 2 and trace[0]['concept:name'] == "▶" and trace[1]['concept:name'] == "■"):
            result.append(trace)

    return result

manufacturer_activities = ["create_purchase_order", "send_order_request", "order_rejection", "invoice_receipt",
                           "payment", "order_confirmation", "goods_receipt", "dispatched", "delivered", "order_check"]
supplier_activities = ["receive_order", "adapt_order", "order_management", "reject", "accept", "order_process",
                       "create_invoice", "order_shipment", "ship_started", "order_dispatch", "send_invoice",
                       "payment_collection"]
shipper_activities = ["receive_request", "preparation", "loading", "transport", "failed_delivery", "delivery"]

current_dir = os.path.dirname(os.path.realpath(__file__))
log_name = "supply_chain.xes"
log_path = os.path.join(current_dir, './orig_data', log_name)
full_log = xes_importer.apply(log_path)

for trace in full_log:
    start_resource = trace[0]['Org:resource']

    new_start_event = pm4py.objects.log.obj.Event()
    new_start_event['Org:resource'] = start_resource
    new_start_event['concept:name'] = "▶"
    trace.insert(0, new_start_event)

    end_resource = trace[-1]['Org:resource']
    new_end_event = pm4py.objects.log.obj.Event()
    new_end_event['Org:resource'] = end_resource
    new_end_event['concept:name'] = "■"
    trace.append(new_end_event)

xes_exporter.apply(preprocess_log_orgs(full_log, "Manufacturer"),
                   os.path.join(current_dir, './organization_data', "manufacturer.xes"))
xes_exporter.apply(preprocess_log_orgs(full_log, "Shipper"),
                   os.path.join(current_dir, './organization_data', "shipper.xes"))
xes_exporter.apply(preprocess_log_orgs(full_log, "Supplier"),
                   os.path.join(current_dir, './organization_data', "supplier.xes"))
