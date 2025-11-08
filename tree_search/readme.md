# Tree Search Benchmark (Simple)

This project compares two tree search methods: depth-first (DFS) and breadth-first (BFS).

## Setup

1. Create a virtual environment:
```sh
python -m venv venv
```

2. Activate:
- Linux/macOS:
```sh
source venv/bin/activate
```
- Windows:
```sh
venv\Scripts\activate
```

3. Install dependencies:
```sh
pip install -r requirements.txt
```

## Run the tests / benchmarks

Run all benchmarks and save a baseline:
```sh
pytest --benchmark-save=baseline
```

Run only DFS or BFS:
```sh
pytest -k dfs
pytest -k bfs
```

Export comparison to CSV:
```sh
pytest-benchmark compare --csv benchmark_results.csv
```

## Understanding results

- Benchmark JSON files are saved under the `.benchmarks` directory.
- Key metrics: min / mean / max execution time and ops/sec (higher = faster).
- Tests also verify correctness (the found node's value or None).