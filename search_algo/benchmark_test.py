"""
Benchmark suite for file lookup strategies using pytest-benchmark.

This script generates sample files of varying sizes, instantiates the
`FileLookup` class in both cached and non-cached modes, and benchmarks
different search implementations (linear, readlines, mmap, grep, awk, and
cache-based). The results help evaluate the relative performance and
scalability of each method across different file sizes.
"""
import pytest
from pytest_benchmark.plugin import BenchmarkFixture  
from pathlib import Path
from .lookup import FileLookup


# ------------------- Benchmark setup for file sizes -------------------
FILE_SIZES = [10000, 25000, 50000, 100000, 250000]


@pytest.fixture(scope="session", params=FILE_SIZES, ids=lambda n: f"{n}_lines")
def sample_file_(
    tmp_path_factory: pytest.TempPathFactory, request: pytest.FixtureRequest
):
    """Generate sample files of varying sizes for benchmarking."""
    size = request.param
    path = tmp_path_factory.mktemp("data") / f"lookup_{size}.txt"
    with open(path, "w", encoding="utf-8") as f:
        for i in range(size):
            f.write(f"key{i}\n")
        f.write("needle\n")
    return path


@pytest.fixture
def lookup_reread_true(sample_file_: Path):
    """FileLookup with cache disabled (always fresh search)."""
    return FileLookup(sample_file_, reread_on_query=True)


@pytest.fixture
def lookup_reread_false(sample_file_: Path):
    """FileLookup with cache enabled (populate once, then lookup)."""
    return FileLookup(sample_file_, reread_on_query=False)


# ------- Benchmarks Tests ---------
@pytest.mark.benchmark(group="search_methods", min_rounds=10)
def test_linear_search(benchmark: BenchmarkFixture,
                       lookup_reread_true: FileLookup):
    assert benchmark(lookup_reread_true.linear_search, b"needle\n") is True


@pytest.mark.benchmark(group="search_methods", min_rounds=10)
def test_readlines_search(benchmark: BenchmarkFixture,
                          lookup_reread_true: FileLookup):
    assert benchmark(lookup_reread_true.readlines_search, b"needle\n") is True


@pytest.mark.benchmark(group="search_methods", min_rounds=10)
def test_mmap_search(benchmark: BenchmarkFixture,
                     lookup_reread_true: FileLookup):
    assert benchmark(lookup_reread_true.mmap_search, b"needle\n") is True


@pytest.mark.benchmark(group="search_methods", min_rounds=10)
def test_grep_search(benchmark: BenchmarkFixture,
                     lookup_reread_true: FileLookup):
    assert benchmark(lookup_reread_true.grep_search, b"needle\n") is True


@pytest.mark.benchmark(group="search_methods", min_rounds=10)
def test_grep_search_m1(benchmark: BenchmarkFixture,
                        lookup_reread_true: FileLookup):
    assert benchmark(lookup_reread_true.grep_search_m_1, b"needle\n") is True


@pytest.mark.benchmark(group="search_methods", min_rounds=10)
def test_search_awk(benchmark: BenchmarkFixture,
                    lookup_reread_true: FileLookup):
    assert benchmark(lookup_reread_true.search_awk, b"needle\n") is True


@pytest.mark.benchmark(group="search_methods", min_rounds=10)
def test_cache_lookup(benchmark: BenchmarkFixture,
                      lookup_reread_false: FileLookup):
    assert benchmark(lookup_reread_false.cache_lookup, b"needle\n") is True
