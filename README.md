# PRIPEL

PRIPEL (Privacy-preserving event log publishing with contextual information) is a framework to publish event logs that fulfill differential privacy.

## Requirements
To run our algorithm you need the following Python packages:
- SciPy (https://www.scipy.org)
- PM4Py (https://pm4py.fit.fraunhofer.de)
- IBM diffprivlib (https://diffprivlib.readthedocs.io/en/latest/)

We did run our algorithm only with Python 3, so we can not guarantee that it works with Python 2.

## How to run PRIPEL
You can run the framework using the following command:
```
python pripel.py <fileName> <epsilon> <n> <k> 
```

The different parameters have the following meaning
- filename: Name of event log (xes-file) that shall be anonymised
- epsilon: Strength of the differential privacy guarantee. It must be a float
- n: Maximum prefix of considered traces for the trace-variant-query. It must be an integer
- k: Prunning parameter of the trace-variant-query. At least k traces must appear in a noisy variant count to be part of the result of the query. It must be an integer

The program will produce a xes-file that contains an anonymised event log.

Please note that certain combinations of n, k and epsilon can lead to very long runtime. If you experience such a runtime, try to higher values for k. Besides that it might help to use a greedy trace matching strategy by setting the parameter <greedy> of the function matchQueryToLog from the class TraceMatcher to true.

Additionally, please note that some event logs contain attributes that are equivalent to a case id. For privacy reasons such attributes must be deleted from the anonymised log. We handle such attributes with a blacklist.

## How to contact us
PRIPEL was developed at the Process-driven Architecture group of Humboldt-Universität zu Berlin. If you want to contact us, just send us a mail at: fahrenks || hu-berlin.de
