#include <bits/stdc++.h>
using namespace std;

int main() {
    int N;
    cin >> N;

    unordered_map<int, int> findex;
    int sum = 0, maxLen = 0;

    findex[0] = -1;

    for (int i = 0; i < N; i++) {
        char ch;
        cin >> ch;

        if (ch == 'P')
            sum += 1;
        else
            sum -= 1;

        if (findex.count(sum)) {
            maxLen = max(maxLen, i - findex[sum]);
        } else {
            findex[sum] = i;
        }
    }

    cout << maxLen << endl;
    return 0;
}