import sys
from levenshtein import levenshtein as levenshtein
from collections import deque
from pm4py.objects.log import log as event_log
from scipy.optimize import linear_sum_assignment
import random
import numpy as np

class TraceMatcher:
    def __init__(self,tv_query_log,log):
        self.__timestamp = "time:timestamp"
        self.__allTimestamps = list()
        self.__allTimeStampDifferences = list()
        self.__distanceMatrix = dict()
        self.__trace_variants_query = self.__addTraceToAttribute(tv_query_log)
        self.__trace_variants_log = self.__addTraceToAttribute(log)
        attributeBlacklist = self.__getBlacklistOfAttributes()
        self.__distributionOfAttributes,self.__eventStructure = self.__getDistributionOfAttributesAndEventStructure(log, attributeBlacklist)
        self.__query_log = tv_query_log
        self.__log = log

    def __addTraceToAttribute(self, log):
        trace_variants = dict()
        for trace in log:
            variant = ""
            for event in trace:
                variant = variant + "@" + event["concept:name"]
            trace.attributes["variant"] = variant
            traceSet = trace_variants.get(variant,set())
            traceSet.add(trace)
            trace_variants[variant] = traceSet
        return trace_variants

    def __getBlacklistOfAttributes(self):
        blacklist = set()
        blacklist.add("concept:name")
        blacklist.add(self.__timestamp)
        blacklist.add("variant")
        blacklist.add("EventID")
        blacklist.add("OfferID")
        blacklist.add("matricola")
        return blacklist

    def __handleVariantsWithSameCount(self,variants,traceMatching):
        for variant in variants:
            for trace in self.__trace_variants_query[variant]:
                traceMatching[trace.attributes["concept:name"]] = self.__trace_variants_log[variant].pop()
            del self.__trace_variants_log[variant]
            del self.__trace_variants_query[variant]

    def __handleVariantsUnderrepresentedInQuery(self,variants,traceMatching):
        for variant in variants:
            if variant in self.__trace_variants_query:
                for trace in self.__trace_variants_query.get(variant,list()):
                    traceMatching[trace.attributes["concept:name"]] = self.__trace_variants_log[variant].pop()
                del self.__trace_variants_query[variant]

    def __handleVariantsOverrepresentedInQuery(self,variants,traceMatching):
        for variant in variants:
            for trace in self.__trace_variants_log[variant]:
                traceFromQuery = self.__trace_variants_query[variant].pop()
                traceMatching[traceFromQuery.attributes["concept:name"]] = trace
            del self.__trace_variants_log[variant]

    def __getDistanceVariants(self,variant1,variant2):
        if variant1 not in self.__distanceMatrix:
            self.__distanceMatrix[variant1] = dict()
        if variant2 not in self.__distanceMatrix[variant1]:
            distance = levenshtein(variant1, variant2)
            self.__distanceMatrix[variant1][variant2] = distance
        else:
            distance = self.__distanceMatrix[variant1][variant2]
        return distance

    def __findCLosestVariantInLog(self,variant,log):
        closestVariant = None
        closestDistance = sys.maxsize
        for comparisonVariant in log.keys():
            distance = self.__getDistanceVariants(variant,comparisonVariant)
            if distance < closestDistance:
                closestVariant = comparisonVariant
                closestDistance = distance
        return closestVariant

    def __findOptimalMatches(self):
        rows = list()
        for traceQuery in self.__query_log:
            row = list()
            for traceLog in self.__log:
                row.append(self.__getDistanceVariants(traceQuery.attributes["variant"],traceLog.attributes["variant"]))
            rows.append(row)
        distanceMatrix = np.array(rows)
        row_ind, col_ind = linear_sum_assignment(distanceMatrix)
        traceMatching = dict()
        for (traceQueryPos, traceLogPos) in zip(row_ind, col_ind):
            traceMatching[self.__query_log[traceQueryPos].attributes["concept:name"]] = self.__log[traceLogPos]
        return traceMatching

    def __matchTraces(self,traceMatching):
        for variant in self.__trace_variants_query.keys():
            closestVariant = self.__findCLosestVariantInLog(variant,self.__trace_variants_log)
            for trace in self.__trace_variants_query[variant]:
                traceMatching[trace.attributes["concept:name"]] = self.__trace_variants_log[closestVariant].pop()
                if not self.__trace_variants_log[closestVariant]:
                    del self.__trace_variants_log[closestVariant]
                    if self.__trace_variants_log:
                        closestVariant = self.__findCLosestVariantInLog(variant, self.__trace_variants_log)
                    else:
                        return

    def __getTraceMatching(self):
        traceMatching = dict()
        variantsWithSameCount = set()
        variantsUnderepresentedInQuery = set()
        variantsOverepresentedInQuery = set()
        for variant in self.__trace_variants_log.keys():
            if len(self.__trace_variants_log[variant]) == len(self.__trace_variants_query.get(variant,set())):
                variantsWithSameCount.add(variant)
            elif len(self.__trace_variants_log[variant]) > len(self.__trace_variants_query.get(variant,set())) and len(self.__trace_variants_query.get(variant,set())) != set():
                variantsUnderepresentedInQuery.add(variant)
            elif len(self.__trace_variants_log[variant]) < len(self.__trace_variants_query.get(variant,0)):
                variantsOverepresentedInQuery.add(variant)
        self.__handleVariantsWithSameCount(variantsWithSameCount,traceMatching)
        self.__handleVariantsUnderrepresentedInQuery(variantsUnderepresentedInQuery,traceMatching)
        self.__handleVariantsOverrepresentedInQuery(variantsOverepresentedInQuery,traceMatching)
        self.__matchTraces(traceMatching)
        return traceMatching

    def __resolveTrace(self,traceInQuery,correspondingTrace,distributionOfAttributes):
        eventStacks = self.__transformTraceInEventStack(correspondingTrace)
        previousEvent = None
        for eventNr in range(0,len(traceInQuery)):
            currentEvent = traceInQuery[eventNr]
            activity = currentEvent["concept:name"]
            latestTimeStamp = self.__getLastTimestampTraceResolving(traceInQuery,eventNr)
            if activity in eventStacks:
                currentEvent = self.__getEventAndUpdateFromEventStacks(activity,eventStacks)
                if currentEvent[self.__timestamp] < latestTimeStamp:
                    currentEvent[self.__timestamp] = self.__getNewTimeStamp(previousEvent,currentEvent, eventNr,distributionOfAttributes)
            else:
                currentEvent = self.__createRandomNewEvent(currentEvent,activity,distributionOfAttributes,previousEvent,eventNr)
            traceInQuery[eventNr] = currentEvent
            previousEvent = currentEvent
            self.__debugCheckTimeStamp(traceInQuery, eventNr)
        return traceInQuery

    def __getEventAndUpdateFromEventStacks(self,activity,eventStacks):
        event = eventStacks[activity].popleft()
        if not eventStacks[activity]:
            del eventStacks[activity]
        return event
    def __debugTraceTimestamps(self,trace):
        for eventNr in range(0):
            self.__debugCheckTimeStamp(trace,eventNr)

    def __debugCheckTimeStamp(self,trace,eventNr):
        if eventNr > 0:
            if trace[eventNr -1][self.__timestamp] > trace[eventNr][self.__timestamp]:
                print("Fuck")

    def __getLastTimestampTraceResolving(self,trace,eventNr):
        if eventNr == 0:
            latestTimeStamp = trace[eventNr][self.__timestamp]
        else:
            latestTimeStamp = trace[eventNr - 1][self.__timestamp]
        return latestTimeStamp

    def __transformTraceInEventStack(self,trace):
        eventStacks = dict()
        for event in trace:
            stack = eventStacks.get(event["concept:name"],deque())
            stack.append(event)
            eventStacks[event["concept:name"]] = stack
        return eventStacks

    def __createRandomNewEvent(self,event,activity,distributionOfAttributes,previousEvent,eventNr):
        for attribute in self.__eventStructure[activity]:
            if attribute in distributionOfAttributes and attribute not in event and attribute != self.__timestamp:
                event[attribute] = random.choice(distributionOfAttributes[attribute])
            elif attribute == self.__timestamp:
                event[self.__timestamp] = self.__getNewTimeStamp(previousEvent,event, eventNr,distributionOfAttributes)
        return event

    def __getNewTimeStamp(self,previousEvent,currentEvent,eventNr,distributionOfAttributes):
        if eventNr == 0:
            timestamp = random.choice(self.__allTimestamps)
        else:
            timestamp = previousEvent[self.__timestamp] + random.choice(distributionOfAttributes[self.__timestamp][previousEvent["concept:name"]].get(currentEvent["concept:name"], self.__allTimeStampDifferences))
        return timestamp

    def __resolveTraceMatching(self,traceMatching,distributionOfAttributes,fillUp):
        log = event_log.EventLog()
        for trace in self.__query_log:
            traceID = trace.attributes["concept:name"]
            if fillUp or traceID in traceMatching:
                matchedTrace = self.__resolveTrace(trace,traceMatching.get(traceID,list()),distributionOfAttributes)
                self.__debugTraceTimestamps(matchedTrace)
                log.append(matchedTrace)
        return log

    def __handleAttributesOfDict(self, dictOfAttributes, distributionOfAttributes, attributeBlacklist,previousEvent=None):
        for attribute in dictOfAttributes.keys():
            if attribute not in attributeBlacklist:
                distribution = distributionOfAttributes.get(attribute, list())
                distribution.append(dictOfAttributes[attribute])
                distributionOfAttributes[attribute] = distribution
            elif attribute == self.__timestamp and previousEvent is not None:
                self.__handleTimeStamp(distributionOfAttributes,previousEvent,dictOfAttributes)

    def __handleTimeStamp(self, distributionOfAttributes, previousEvent, currentEvent):
        timeStampsDicts = distributionOfAttributes.get(self.__timestamp, dict())
        activityDict = timeStampsDicts.get(previousEvent["concept:name"],dict())
        timeStampsDicts[previousEvent["concept:name"]] = activityDict
        distribution = activityDict.get(currentEvent["concept:name"], list())
        timeStampDifference = currentEvent[self.__timestamp] - previousEvent[self.__timestamp]
        distribution.append(timeStampDifference)
        activityDict[currentEvent["concept:name"]] = distribution
        distributionOfAttributes[self.__timestamp] = timeStampsDicts
        self.__allTimestamps.append(currentEvent[self.__timestamp])
        self.__allTimeStampDifferences.append(timeStampDifference)

    def __getDistributionOfAttributesAndEventStructure(self, log, attributeBlacklist):
        distributionOfAttributes = dict()
        eventStructure = dict()
        for trace in log:
            self.__handleAttributesOfDict(trace.attributes,distributionOfAttributes,attributeBlacklist)
            previousEvent = None
            currentEvent = None
            for eventNr in range(0,len(trace)):
                if currentEvent is not None:
                    previousEvent = currentEvent
                currentEvent = trace[eventNr]
                self.__handleAttributesOfDict(currentEvent,distributionOfAttributes,attributeBlacklist,previousEvent)
                if not currentEvent["concept:name"] in eventStructure:
                    attributesOfEvent = set(currentEvent.keys())
                    attributesOfEvent.remove("concept:name")
                    eventStructure[currentEvent["concept:name"]] = attributesOfEvent
        return distributionOfAttributes, eventStructure

    def matchQueryToLog(self,fillUp=True,greedy=False):
        if greedy:
            traceMatching = self.__getTraceMatching()
        else:
            traceMatching = self.__findOptimalMatches()
        matched_log = self.__resolveTraceMatching(traceMatching,self.__distributionOfAttributes,fillUp)
        return matched_log

    def getAttributeDistribution(self):
        return self.__distributionOfAttributes

    def getTimeStampData(self):
        return self.__allTimestamps,self.__allTimeStampDifferences