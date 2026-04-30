#include <bits/stdc++.h>
using namespace std;

int lengthOfLIS(vector<int>& nums) {
    vector<int> temp;

    for (int num : nums) {
        auto it = lower_bound(temp.begin(), temp.end(), num);

        if (it == temp.end()) {
            temp.push_back(num);
        } else {
            *it = num;
        }
    }

    return temp.size();
}

int main() {
    vector<int> nums = {10,9,2,5,3,7,101,18};
    cout << lengthOfLIS(nums);
    return 0;
}