from pm4py.objects.log.importer.xes import factory as xes_import_factory
from pm4py.objects.log.exporter.xes import factory as xes_exporter
from pm4py.objects.log.util import sampling
from tracematcher import TraceMatcher as TraceMatcher
from attributeAnonymizier import AttributeAnonymizier as AttributeAnonymizier
from trace_variant_query import privatize_tracevariants
import datetime
import sys

def freq(lst):
    d = {}
    for i in lst:
        if d.get(i):
            d[i] += 1
        else:
            d[i] = 1
    return d

log_path = sys.argv[1]
epsilon = float(sys.argv[2])
N = int(sys.argv[3])
k = int(sys.argv[4])

sample_path = "/Users/stephan/Repositories/event_log_publishing_privacy/data_example/sample.xes"
#P = round(len(log) * 0.01)


new_ending = "_epsilon_" + str(epsilon) + "_P" + str(k) + "_anonymizied.xes"

result_log_path = log_path.replace(".xes",new_ending)

starttime = datetime.datetime.now()
log = xes_import_factory.apply(log_path)

starttime_tv_query = datetime.datetime.now()
tv_query_log = privatize_tracevariants(log, epsilon, k, N)
print(len(tv_query_log))
endtime_tv_query = datetime.datetime.now()
print("Time of TV Query: " + str((endtime_tv_query - starttime_tv_query)))
starttime_trace_matcher = datetime.datetime.now()
traceMatcher = TraceMatcher(tv_query_log,log)
matchedLog = traceMatcher.matchQueryToLog()
print(len(matchedLog))
endtime_trace_matcher = datetime.datetime.now()
print("Time of TraceMatcher: " + str((endtime_trace_matcher - starttime_trace_matcher)))
distributionOfAttributes = traceMatcher.getAttributeDistribution()
occurredTimestamps, occurredTimestampDifferences = traceMatcher.getTimeStampData()
print(min(occurredTimestamps))
starttime_attribute_anonymizer = datetime.datetime.now()
attributeAnonymizier = AttributeAnonymizier()
anonymiziedLog, attritbuteDistribution = attributeAnonymizier.anonymize(matchedLog,distributionOfAttributes,epsilon,occurredTimestampDifferences,occurredTimestamps)
endtime_attribute_anonymizer = datetime.datetime.now()
print("Time of attribute anonymizer: " +str(endtime_attribute_anonymizer - starttime_attribute_anonymizer))
xes_exporter.export_log(anonymiziedLog, result_log_path)
endtime = datetime.datetime.now()
print("Complete Time: " + str((endtime-starttime)))

print("Time of TV Query: " + str((endtime_tv_query - starttime_tv_query)))
print("Time of TraceMatcher: " + str((endtime_trace_matcher - starttime_trace_matcher)))
print("Time of attribute anonymizer: " +str(endtime_attribute_anonymizer - starttime_attribute_anonymizer))

print(result_log_path)
print(freq(attritbuteDistribution))