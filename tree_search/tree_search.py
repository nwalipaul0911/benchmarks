from collections import deque

class TreeSearch:
    @staticmethod
    def dfs(node, target):
        if node.val == target:
            return node

        for child in node.children:
            result = TreeSearch.dfs(child, target)
            if result:
                return result

        return None 

    @staticmethod
    def bfs(node, target):
        queue = deque([node]) 

        while queue:
            current = queue.popleft() 

            if current.val == target:
                return current

            if hasattr(current, 'children') and current.children:
                queue.extend(current.children)
                
        return None