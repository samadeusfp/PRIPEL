import numpy as np
from pm4py.objects.log import log as event_log
import datetime
from dateutil.tz import tzutc

TRACE_START = "TRACE_START"
TRACE_END = "TRACE_END"
EVENT_DELIMETER = ">>>"


def privatize_tracevariants(log, epsilon,P,N):
    # transform log into event view and get prefix frequencies
    print("Retrieving true prefix frequencies", end='')
    event_int_mapping = create_event_int_mapping(log)
    known_prefix_frequencies = get_prefix_frequencies_from_log(log)
    events = list(event_int_mapping.keys())
    events.remove(TRACE_START)
    print("Done")

    final_frequencies = {}
    trace_frequencies = {"": 0}
    for n in range(1, N + 1):
        # get prefix_frequencies, using either known frequency, or frequency of parent, or 0
        trace_frequencies = get_prefix_frequencies_length_n(trace_frequencies, events,             n, known_prefix_frequencies)
        # laplace_mechanism
        trace_frequencies = apply_laplace_noise_tf(trace_frequencies, epsilon)

        # prune
        trace_frequencies = prune_trace_frequencies(trace_frequencies, P, known_prefix_frequencies)
        # print(trace_frequencies)
        # add finished traces to output, remove from list, sanity checks
        new_frequencies = {}
        for entry in trace_frequencies.items():
            if TRACE_END in entry[0]:
                final_frequencies[entry[0] ] = entry[1]
            else:
                new_frequencies[entry[0]] = entry[1]
        trace_frequencies = new_frequencies
        # print(trace_frequencies)
        print(n)
    return generate_pm4py_log(final_frequencies)

def create_event_int_mapping(log):
    event_name_list=[]
    for trace in log:
        for event in trace:
            event_name = event["concept:name"]
            if not str(event_name) in event_name_list:
                event_name_list.append(event_name)
    event_int_mapping={}
    event_int_mapping[TRACE_START]=0
    current_int=1
    for event_name in event_name_list:
        event_int_mapping[event_name]=current_int
        current_int=current_int+1
    event_int_mapping[TRACE_END]=current_int
    return event_int_mapping

def get_prefix_frequencies_from_log(log):
    prefix_frequencies = {}
    for trace in log:
        current_prefix = ""
        for event in trace:
            current_prefix = current_prefix + event["concept:name"] + EVENT_DELIMETER
            if current_prefix in prefix_frequencies:
                frequency = prefix_frequencies[current_prefix]
                prefix_frequencies[current_prefix] += 1
            else:
                prefix_frequencies[current_prefix] = 1
        current_prefix = current_prefix + TRACE_END
        if current_prefix in prefix_frequencies:
            frequency = prefix_frequencies[current_prefix]
            prefix_frequencies[current_prefix] += 1
        else:
            prefix_frequencies[current_prefix] = 1
    return prefix_frequencies


def get_prefix_frequencies_length_n(trace_frequencies, events, n, known_prefix_frequencies):
    prefixes_length_n = {}
    for prefix, frequency in trace_frequencies.items():
        for new_prefix in pref(prefix, events, n):
            if new_prefix in known_prefix_frequencies:
                new_frequency = known_prefix_frequencies[new_prefix]
                prefixes_length_n[new_prefix] = new_frequency
            else:
                prefixes_length_n[new_prefix] = 0
    return prefixes_length_n



def prune_trace_frequencies(trace_frequencies, P, known_prefix_frequencies):
    pruned_frequencies = {}
    for entry in trace_frequencies.items():
        if entry[1] >= P:
            pruned_frequencies[entry[0]] = entry[1]
    return pruned_frequencies


def pref(prefix, events, n):
    prefixes_length_n = []
    if not TRACE_END in prefix:
        for event in events:
            current_prefix = ""
            if event == TRACE_END:
                current_prefix = prefix + event
            else:
                current_prefix = prefix + event + EVENT_DELIMETER
            prefixes_length_n.append(current_prefix)
    return prefixes_length_n


def apply_laplace_noise_tf(trace_frequencies, epsilon):
    lambd = 1 / epsilon
    for trace_frequency in trace_frequencies:
        noise = int(np.random.laplace(0, lambd))
        trace_frequencies[trace_frequency] = trace_frequencies[trace_frequency] + noise
        if trace_frequencies[trace_frequency] < 0:
            trace_frequencies[trace_frequency] = 0
    return trace_frequencies

def generate_pm4py_log(trace_frequencies):
    log = event_log.EventLog()
    trace_count = 0
    for variant in trace_frequencies.items():
        frequency=variant[1]
        activities=variant[0].split(EVENT_DELIMETER)
        for i in range (0,frequency):
            trace = event_log.Trace()
            trace.attributes["concept:name"] = trace_count
            trace_count = trace_count + 1
            for activity in activities:
                if not TRACE_END in activity:
                    event = event_log.Event()
                    event["concept:name"] = str(activity)
                    event["time:timestamp"] = datetime.datetime(1970, 1, 1, 0, 0, 0, tzinfo=tzutc())
                    trace.append(event)
            log.append(trace)
    return log