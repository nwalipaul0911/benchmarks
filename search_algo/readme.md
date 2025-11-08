# Search Algorithm Benchmark

This module benchmarks different search algorithms for finding strings in text files, comparing various methods including linear search, memory-mapped files, grep, awk, and cached lookups.

## Overview

The benchmark tests the following search methods:
- Linear search (line by line)
- Readlines search (load all lines at once)
- Memory-mapped (mmap) search
- Grep search (with and without -m1 flag)
- Awk search
- Cache-based lookup

## Setup

### Virtual Environment

1. Create a virtual environment:
```sh
python -m venv venv
```

2. Activate the virtual environment:
- Windows:
```sh
venv\Scripts\activate
```
- Linux/MacOS:
```sh
source venv/bin/activate
```

3. Install dependencies:
```sh
pip install -r requirements.txt
```

## Running the Benchmark

The benchmark uses pytest-benchmark to test each search method against files of different sizes (10K, 25K, 50K, 100K, and 250K lines).

To run the benchmark:

```sh
pytest --benchmark-save=baseline
```

To Export to CSV:
```sh
pytest-benchmark compare --csv benchmark_results.csv
```


## Understanding Results

The benchmark measures:
- Mean execution time
- Standard deviation
- Rounds per second
- Min/max time per operation

Results are grouped by:
- File size (10K to 250K lines)
- Search method
- Cache strategy (enabled/disabled)

## Implementation Details

The benchmark test creates temporary files with varying sizes, each containing a "needle" string to search for at the end of the file. Each search method is tested against these files multiple times (minimum 10 rounds) to ensure reliable results.