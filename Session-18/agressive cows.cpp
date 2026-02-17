class Solution {
public:

    bool canPlace(vector<int>& stalls, int k, int dist) {

        int cows = 1;
        int last = stalls[0];

        for (int i = 1; i < stalls.size(); i++) {

            if (stalls[i] - last >= dist) {

                cows++;
                last = stalls[i];

                if (cows >= k)
                    return true;
            }
        }
        return false;
    }
    int aggressiveCows(vector<int> &stalls, int k) {

        sort(stalls.begin(), stalls.end());

        int low = 1;
        int high = stalls.back() - stalls[0];
        int ans = 0;
        while (low <= high) {

            int mid = (low + high) / 2;

            if (canPlace(stalls, k, mid)) {

                ans = mid;
                low = mid + 1;
            }
            else {

                high = mid - 1;
            }
        }
        return ans;
    }
};
