def knapsack_fantasy(players, max_budget):
    """
    0/1 Knapsack using Dynamic Programming.
    players: list of dicts [{'id': 'P1', 'name': 'Player 1', 'cost': 8.5, 'value': 120}, ...]
    max_budget: float (e.g. 100.0)
    Returns the maximum value and the list of selected players.
    Note: To use standard DP, we should scale costs to integers.
    """
    # Scale costs by 10 to make them integers (e.g., 8.5 -> 85)
    budget = int(max_budget * 10)
    n = len(players)
    
    # DP table: dp[i][w] represents max value with first i items and weight limit w
    dp = [[0 for _ in range(budget + 1)] for _ in range(n + 1)]
    
    for i in range(1, n + 1):
        item_cost = int(players[i-1].get('cost', 0) * 10)
        item_val = players[i-1].get('value', 0)
        
        for w in range(1, budget + 1):
            if item_cost <= w:
                dp[i][w] = max(item_val + dp[i-1][w - item_cost], dp[i-1][w])
            else:
                dp[i][w] = dp[i-1][w]
                
    # Backtrack to find selected players
    selected = []
    w = budget
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i-1][w]:
            selected.append(players[i-1])
            w -= int(players[i-1].get('cost', 0) * 10)
            
    return {"max_value": dp[n][budget], "team": selected}

def constrained_knapsack_fantasy(batters, bowlers, wkar, req_bat, req_bowl, req_wkar, max_budget):
    """
    Multi-stage Dynamic Programming for Constrained 0/1 Knapsack.
    Finds exactly req_bat batters, req_bowl bowlers, and req_wkar WKs within max_budget.
    """
    budget = int(max_budget * 10)
    
    def solve_role(players, req_count):
        n = len(players)
        dp = [[[-1] * (budget + 1) for _ in range(req_count + 1)] for __ in range(n + 1)]
        for i in range(n + 1):
            for w in range(budget + 1):
                dp[i][0][w] = 0
                
        for i in range(1, n + 1):
            cost = int(players[i-1].get('cost', 0) * 10)
            val = players[i-1].get('value', 0)
            
            for k in range(1, req_count + 1):
                for w in range(budget + 1):
                    best = dp[i-1][k][w]
                    if cost <= w and dp[i-1][k-1][w-cost] != -1:
                        pick_val = dp[i-1][k-1][w-cost] + val
                        if pick_val > best:
                            best = pick_val
                    dp[i][k][w] = best
        return dp

    def backtrack_role(dp, players, req, final_w):
        selected = []
        curr_req = req
        curr_w = final_w
        for i in range(len(players), 0, -1):
            if curr_req == 0: break
            cost = int(players[i-1].get('cost', 0) * 10)
            if curr_w >= cost and dp[i-1][curr_req-1][curr_w-cost] != -1:
                val = players[i-1].get('value', 0)
                if dp[i][curr_req][curr_w] == dp[i-1][curr_req-1][curr_w-cost] + val:
                    selected.append(players[i-1])
                    curr_req -= 1
                    curr_w -= cost
                    continue
        return selected

    dp_bat = solve_role(batters, req_bat)
    dp_bowl = solve_role(bowlers, req_bowl)
    dp_wkar = solve_role(wkar, req_wkar)
    
    final_bat = dp_bat[-1][req_bat] if req_bat > 0 else [0]*(budget+1)
    final_bowl = dp_bowl[-1][req_bowl] if req_bowl > 0 else [0]*(budget+1)
    final_wkar = dp_wkar[-1][req_wkar] if req_wkar > 0 else [0]*(budget+1)
    
    combined_bb = [-1] * (budget + 1)
    split_bb = [-1] * (budget + 1)
    
    for w in range(budget + 1):
        best_val = -1
        best_w1 = -1
        for w1 in range(w + 1):
            w2 = w - w1
            v1 = final_bat[w1]
            v2 = final_bowl[w2]
            if v1 != -1 and v2 != -1:
                if v1 + v2 > best_val:
                    best_val = v1 + v2
                    best_w1 = w1
        combined_bb[w] = best_val
        split_bb[w] = best_w1
        
    max_val = -1
    best_w_bb = -1
    best_w3 = -1
    
    for w in range(budget + 1):
        for w3 in range(budget + 1 - w):
            v_bb = combined_bb[w]
            v_wkar = final_wkar[w3]
            if v_bb != -1 and v_wkar != -1:
                if v_bb + v_wkar > max_val:
                    max_val = v_bb + v_wkar
                    best_w_bb = w
                    best_w3 = w3
                    
    if max_val == -1:
        return {"error": "Budget too low or not enough players to fill roles"}
        
    w1 = split_bb[best_w_bb]
    w2 = best_w_bb - w1
    w3 = best_w3
    
    team = []
    if req_bat > 0: team.extend(backtrack_role(dp_bat, batters, req_bat, w1))
    if req_bowl > 0: team.extend(backtrack_role(dp_bowl, bowlers, req_bowl, w2))
    if req_wkar > 0: team.extend(backtrack_role(dp_wkar, wkar, req_wkar, w3))
    
    return {"max_value": max_val, "team": team}


def max_subarray_peak(runs_array):
    """
    Maximum Subarray Problem (Kadane's Algorithm) - Divide & Conquer / DP approach.
    Finds the contiguous phase of matches/overs with maximum runs/impact.
    runs_array: list of ints
    Returns the max sum, start index, and end index.
    """
    if not runs_array:
        return {"max_sum": 0, "start": -1, "end": -1}
        
    max_so_far = float('-inf')
    current_max = 0
    start_idx = 0
    end_idx = 0
    temp_start = 0
    
    for i in range(len(runs_array)):
        current_max += runs_array[i]
        
        if current_max > max_so_far:
            max_so_far = current_max
            start_idx = temp_start
            end_idx = i
            
        if current_max < 0:
            current_max = 0
            temp_start = i + 1
            
    return {"max_sum": max_so_far, "start": start_idx, "end": end_idx}


def rabin_karp_search(text, pattern):
    """
    Rabin-Karp String Matching Algorithm.
    Returns the starting indices of all occurrences of pattern in text.
    """
    text = text.lower()
    pattern = pattern.lower()
    n = len(text)
    m = len(pattern)
    if m == 0 or m > n:
        return []
        
    d = 256 # number of characters in the alphabet
    q = 101 # prime number
    
    h = 1
    for i in range(m - 1):
        h = (h * d) % q
        
    p_hash = 0
    t_hash = 0
    
    for i in range(m):
        p_hash = (d * p_hash + ord(pattern[i])) % q
        t_hash = (d * t_hash + ord(text[i])) % q
        
    res = []
    
    for i in range(n - m + 1):
        if p_hash == t_hash:
            match = True
            for j in range(m):
                if text[i + j] != pattern[j]:
                    match = False
                    break
            if match:
                res.append(i)
                
        if i < n - m:
            t_hash = (d * (t_hash - ord(text[i]) * h) + ord(text[i + m])) % q
            if t_hash < 0:
                t_hash = t_hash + q
                
    return res


def merge_sort_impact(arr, key='impact_score', reverse=True):
    """
    Merge Sort implementation to sort objects based on a specific key.
    Used for sorting players by their dynamically calculated impact score.
    """
    if len(arr) > 1:
        mid = len(arr) // 2
        L = arr[:mid]
        R = arr[mid:]

        merge_sort_impact(L, key, reverse)
        merge_sort_impact(R, key, reverse)

        i = j = k = 0

        while i < len(L) and j < len(R):
            # Compare based on key and reverse flag
            l_val = L[i].get(key, 0)
            r_val = R[j].get(key, 0)
            
            condition = l_val > r_val if reverse else l_val < r_val
            
            if condition:
                arr[k] = L[i]
                i += 1
            else:
                arr[k] = R[j]
                j += 1
            k += 1

        while i < len(L):
            arr[k] = L[i]
            i += 1
            k += 1

        while j < len(R):
            arr[k] = R[j]
            j += 1
            k += 1
            
    return arr


# =====================================================================
# PHASE 1: NEW DAA ALGORITHMS (RESUME-WORTHY UPGRADE)
# =====================================================================

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False
        self.players = [] # Store references to players that end at this node or match the prefix

class PlayerTrie:
    """
    Prefix Trie for ultra-fast autocomplete. O(M) search time.
    """
    def __init__(self):
        self.root = TrieNode()
        
    def insert(self, player_dict):
        # Insert by full name, first name, last name to allow flexible searching
        name = player_dict['name'].lower()
        parts = name.split()
        suffixes = [name] + parts
        
        for word in suffixes:
            node = self.root
            for char in word:
                if char not in node.children:
                    node.children[char] = TrieNode()
                node = node.children[char]
                # Store reference in every node along the path for instant prefix retrieval
                if player_dict not in node.players:
                    node.players.append(player_dict)
            node.is_end_of_word = True

    def search_prefix(self, prefix):
        prefix = prefix.lower()
        node = self.root
        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]
        
        # Sort by impact or runs if needed, but here we just return the list
        return node.players[:15] # Return top 15 matches instantly


from collections import deque

def build_player_graph(partnerships, players_dict):
    """
    Builds an adjacency list graph from partnership data.
    """
    graph = {}
    for p_id in players_dict:
        graph[p_id] = set()
        
    for p in partnerships:
        p1 = p['player1_id']
        p2 = p['player2_id']
        if p1 in graph and p2 in graph:
            graph[p1].add(p2)
            graph[p2].add(p1)
            
    return graph

def shortest_path_bfs(graph, start_id, target_id):
    """
    Breadth-First Search (BFS) to find the shortest path between two players
    in the partnership network (Degrees of Separation).
    """
    if start_id not in graph or target_id not in graph:
        return None
        
    if start_id == target_id:
        return [start_id]
        
    queue = deque([[start_id]])
    visited = set([start_id])
    
    while queue:
        path = queue.popleft()
        current_node = path[-1]
        
        for neighbor in graph.get(current_node, []):
            if neighbor == target_id:
                return path + [neighbor]
                
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(path + [neighbor])
                
    return None # No connection found
