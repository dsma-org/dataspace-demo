import json
import os

import pm4py

current_dir = os.path.dirname(os.path.realpath(__file__))

with(open(os.path.join(current_dir, 'aggregated_result.json'))) as f:
    loaded_result = json.load(f)
    dict_freq, dict_start, dict_end = (loaded_result['dict_freq'], loaded_result['dict_start'],
                                                            loaded_result['dict_end'])
    dict_freq = {(entry['from'], entry['to']): entry['count'] for entry in dict_freq}

pm4py.save_vis_dfg(dict_freq, dict_start, dict_end, file_path=os.path.join(current_dir, 'aggregated_result.pdf'))
pm4py.view_dfg(dict(dict_freq), dict(dict_start), dict(dict_end), format="pdf")