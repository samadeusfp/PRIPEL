# PRIPEL

PRIPEL (Privacy-preserving event log publishing with contextual information) is a framework to publish event logs that fulfill differential privacy. We provide an implementation of PRETSA in Python 3. Our code is available under the MIT license.

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

### Runtime

Please note that certain combinations of n, k and epsilon can lead to very long runtime. If you experience such a runtime, try to higher values for k. Besides that it might help to use a greedy trace matching strategy by setting the parameter <greedy> of the function matchQueryToLog from the class TraceMatcher to true.

### Customization
Additionally, please note that some event logs contain attributes that are equivalent to a case id. For privacy reasons such attributes must be deleted from the anonymised log. We handle such attributes with a blacklist. See the function __getBlacklistOfAttributes in tracematcher.py and attributeAnonymizier.py.

## Components

### pripel.py
This scripts run the overall PRIPEL-Framework. It takes in the event log (XES-File) performs the PRIPEL-based anonymisation and then saves the resulting anonmyised logs as an XES-File.

### trace_variant_query.py
Performs the trace-variant query on the input log. The query is based on the algorithm described in:
https://link.springer.com/article/10.1007/s12599-019-00613-3


### tracematcher.py
This script mathces the cases from the input event log with the traces from the trace-variant-query. It uses standard assignment algroithm implemented in Numpy.

### attributeAnonymizier.py
In this script the contextual information of the matched log is anonymised.

### levenshtein.py
Contains implementation of the levenshtein-distance for traces. We use it in the tracematcher.py.


## How to contact us
PRIPEL was developed at the Process-driven Architecture group of Humboldt-Universität zu Berlin. If you want to contact us, just send us a mail at: fahrenks || hu-berlin.de
