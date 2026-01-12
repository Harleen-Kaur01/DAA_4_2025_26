#include <iostream>
#include <vector>
#include <algorithm>
#include <chrono>

using namespace std;
using namespace std::chrono;

long long operations = 0;
int maxDepth = 0;

void complexRec(int n, int depth) {
    maxDepth = max(maxDepth, depth);
    if (n <= 2) {
        return;
    }

    int p = n;
    while (p > 0) {
        operations++;
        vector<int> temp(n);
        operations += n; 
        for (int i = 0; i < n; i++) {
            temp[i] = i ^ p;
            operations++;
        }
        p >>= 1;
    }

    vector<int> small(n);
    operations += n;

    for (int i = 0; i < n; i++) {
        small[i] = i * i;
        operations++;
    }

    reverse(small.begin(), small.end());
    operations += n;

    complexRec(n / 2, depth + 1);
    complexRec(n / 2, depth + 1);
    complexRec(n / 2, depth + 1);
}

int main() {
    int n;
    cout << "Enter value of n: ";
    cin >> n;

    operations = 0;
    maxDepth = 0;

    auto start = high_resolution_clock::now();
    complexRec(n, 1);
    auto end = high_resolution_clock::now();

    auto duration = duration_cast<milliseconds>(end - start);

    cout << "\nResults for n = " << n << endl;
    cout << "Total Operations: " << operations << endl;
    cout << "Maximum Recursion Depth: " << maxDepth << endl;
    cout << "Execution Time: " << duration.count() << " ms" << endl;

    // relation =3t(n/2)+nlogn+2n+2;
    // complexity=n^log(3,2)   n to power log 3 base 2
    
    return 0;
}