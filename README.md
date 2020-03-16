# PRIPEL


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
- epsilon: Strength of the differential privacy guarantee
- n: Maximum prefix of considered traces for the trace-variant-query
- k: Prunning parameter of the trace-variant-query. At least k traces must appear in a noisy variant count to be part of the result of the query
