class Solution {
public:

    bool dfs(int src, int dest, vector<vector<int>>& adj, vector<bool>& visited) {

        if (src == dest)
            return true;

        visited[src] = true;

        for (int neighbor : adj[src]) {
            if (!visited[neighbor]) {
                if (dfs(neighbor, dest, adj, visited))
                    return true;
            }
        }

        return false;
    }

    int kruskalsMST(int V, vector<vector<int>>& edges) {

        sort(edges.begin(), edges.end(), [](vector<int>& a, vector<int>& b) {
            return a[2] < b[2];
        });

        vector<vector<int>> adj(V);

        int mstWeight = 0;
        int edgeCount = 0;

        for (auto &edge : edges) {

            int u = edge[0];
            int v = edge[1];
            int wt = edge[2];

            vector<bool> visited(V, false);

            if (!dfs(u, v, adj, visited)) {

                adj[u].push_back(v);
                adj[v].push_back(u);

                mstWeight += wt;

                edgeCount++;

                if (edgeCount == V - 1)
                    break;
            }
        }

        return mstWeight;
    }
};