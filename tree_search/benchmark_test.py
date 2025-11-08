import pytest
from .tree_search import TreeSearch
import sys
from collections import deque


class Node:
    """A Node class with corrected, encapsulated properties."""
    def __init__(self, val=None):
        self.val = val
        self._children = []
    
    @property
    def children(self):
        """Returns a *copy* of the children list."""
        return list(self._children)

    @children.setter
    def children(self, new_children):
        """Stores a *copy* of the new list."""
        self._children = list(new_children)

    def add_child(self, node):
        """Helper method to build the tree."""
        self._children.append(node)
        return node # Return child to allow chaining if needed

    def __repr__(self):
        return f"<Node: {self.val}>"

# --- Test Suite Setup ---

@pytest.fixture(scope="session")
def sophisticated_tree():
    """
    Builds a large, non-trivial tree once per test session.
    Depth = 10, Width = 3. Total nodes = 1 + 3 + 9 + ... + 3^9 = 29,524
    """
    # Increase recursion depth limit for deep tree creation (if using recursive builder)
    # Since we use an iterative (queue) builder, this isn't strictly needed
    # but is good practice for deep tree work.
    sys.setrecursionlimit(2000)

    MAX_DEPTH = 10
    WIDTH = 3
    
    root = Node('root_0')
    counter = 1
    
    queue = deque([(root, 1)]) # (node, current_depth)
    
    target_middle_val = None
    target_leaf_val = None
    
    while queue:
        parent, depth = queue.popleft()
        
        # Stop building when we reach max depth
        if depth == MAX_DEPTH:
            continue
            
        for i in range(WIDTH):
            val = f'node_{counter}'
            child = Node(val)
            parent.add_child(child)
            counter += 1
            
            # Find a "middle" node: halfway deep, middle child
            if depth == MAX_DEPTH // 2 and i == (WIDTH // 2):
                target_middle_val = child.val
                
            # Find a "deep leaf" node: max depth, last child
            if depth == MAX_DEPTH - 1 and i == (WIDTH - 1):
                target_leaf_val = child.val
                
            queue.append((child, depth + 1))

    print(f"\n--- Built tree with {counter} nodes (Depth={MAX_DEPTH}, Width={WIDTH}) ---")

    return {
        "root_node": root,
        "target_root": 'root_0',
        "target_middle": target_middle_val, # A node BFS will find faster
        "target_leaf": target_leaf_val,   # A node DFS *might* find faster (but here, it's the "worst case" for DFS)
        "target_not_found": "value_does_not_exist_12345",
    }

@pytest.fixture(
    params=["root", "middle", "leaf", "not_found"],
    ids=["target=ROOT", "target=MIDDLE", "target=LEAF", "target=NOT_FOUND"]
)
def search_params(request, sophisticated_tree):
    """
    This fixture parameterizes the tests. It will run each test
    function four times, once for each 'param'.
    """
    key = f"target_{request.param}"
    target_val = sophisticated_tree[key]
    root_node = sophisticated_tree["root_node"]
    
    # expected result: None if not_found, otherwise a Node
    expected_is_none = (request.param == "not_found")
    
    return root_node, target_val, expected_is_none


# --- Benchmark Tests ---

def test_dfs_benchmark(benchmark, search_params):
    """
    Benchmarks the DFS function against all target types.
    Also validates the search result is correct.
    """
    root, target, expected_is_none = search_params

    # benchmark() runs the function many times and returns its result
    result = benchmark(TreeSearch.dfs, root, target)
    
    # --- Correctness Assertion ---
    if expected_is_none:
        assert result is None, f"DFS found '{target}' when it shouldn't have."
    else:
        assert result is not None, f"DFS failed to find '{target}'."
        assert result.val == target, f"DFS found wrong node. Expected '{target}', got '{result.val}'."

def test_bfs_benchmark(benchmark, search_params):
    """
    Benchmarks the BFS function against all target types.
    Also validates the search result is correct.
    """
    root, target, expected_is_none = search_params
    
    result = benchmark(TreeSearch.bfs, root, target)
    
    # --- Correctness Assertion ---
    if expected_is_none:
        assert result is None, f"BFS found '{target}' when it shouldn't have."
    else:
        assert result is not None, f"BFS failed to find '{target}'."
        assert result.val == target, f"BFS found wrong node. Expected '{target}', got '{result.val}'."