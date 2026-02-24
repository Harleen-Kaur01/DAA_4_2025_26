class Solution {
  public:
    int spanningTree(int V, vector<vector<int>>& edges) {
        // code here
        int e=edges.size();
        vector<vector<pair<int,int>>> adj(V); //int,int=weight,vertex
        for(int i=0;i<e;i++){
            int u,v,w;
            u=edges[i][0];
            v=edges[i][1];
            w=edges[i][2];
            adj[u].push_back({w,v});
            adj[v].push_back({w,u});
        }
        vector<bool> visited(V,false);
        priority_queue<pair<int,int>,vector<pair<int,int>>,greater<pair<int,int>>> pq; //int,int = weight,vertex
        pq.push({0,0});
        int minCost=0;
        while(!pq.empty()){
            int wi=pq.top().first;
            int ui=pq.top().second;
            pq.pop();
                if(!visited[ui]){
                    minCost+=wi;
                }
            visited[ui]=true;
            for(auto pr:adj[ui]){
                int vi=pr.second;
                int currW=pr.first;
                if(!visited[vi]){
                    pq.push({currW,vi});
                }
            }
            }
        return minCost;
        }
};