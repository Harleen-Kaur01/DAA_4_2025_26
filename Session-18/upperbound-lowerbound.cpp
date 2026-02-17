#include <bits/stdc++.h>
using namespace std;

int main()
{
    vector<int> A = {1,2,3};
    vector<int> B = {1,1,2,3};

    int target = 4;

    sort(B.begin(), B.end());

    int count = 0;

    for(int i = 0; i < A.size(); i++)
    {
        int need = target - A[i];

        int low = 0, high = B.size() - 1, first = -1;
        while(low <= high)
        {
            int mid = (low + high) / 2;

            if(B[mid] == need)
            {
                first = mid;
                high = mid - 1;
            }
            else if(B[mid] < need)
                low = mid + 1;
            else
                high = mid - 1;
        }

        low = 0, high = B.size() - 1;
        int last = -1;
        while(low <= high)
        {
            int mid = (low + high) / 2;

            if(B[mid] == need)
            {
                last = mid;
                low = mid + 1;
            }
            else if(B[mid] < need)
                low = mid + 1;
            else
                high = mid - 1;
        }

        if(first != -1)
            count += last - first + 1;
    }

    cout << count;
}
