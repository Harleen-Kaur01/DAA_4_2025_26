#include <iostream>
using namespace std;

class Node {
public:
    int data;
    Node* next;

    Node(int val) {
        data = val;
        next = NULL;
    }
};

class Queue {
private:
    Node* frontNode;
    Node* rearNode;
    int count;

public:
    Queue() {
        frontNode = rearNode = NULL;
        count = 0;
    }

    void enqueue(int x) {
        Node* newNode = new Node(x);

        if (rearNode == NULL) {
            frontNode = rearNode = newNode;
        } else {
            rearNode->next = newNode;
            rearNode = newNode;
        }
        count++;
        cout << x << " enqueued\n";
    }

    void dequeue() {
        if (frontNode == NULL) {
            cout << "Queue Underflow\n";
            return;
        }

        Node* temp = frontNode;
        cout << temp->data << " dequeued\n";

        frontNode = frontNode->next;
        delete temp;
        count--;

        if (frontNode == NULL) {
            rearNode = NULL;
        }
    }

    int front() {
        if (frontNode == NULL) {
            cout << "Queue is empty\n";
            return -1;
        }
        return frontNode->data;
    }

    int rear() {
        if (rearNode == NULL) {
            cout << "Queue is empty\n";
            return -1;
        }
        return rearNode->data;
    }

    int size() {
        return count;
    }

    void display() {
        if (frontNode == NULL) {
            cout << "Queue is empty\n";
            return;
        }

        Node* temp = frontNode;
        cout << "Queue: ";
        while (temp != NULL) {
            cout << temp->data << " ";
            temp = temp->next;
        }
        cout << endl;
    }
};

int main() {
    Queue q;

    q.enqueue(10);
    q.enqueue(20);
    q.enqueue(30);

    q.display();

    cout << "Front: " << q.front() << endl;
    cout << "Rear: " << q.rear() << endl;
    cout << "Size: " << q.size() << endl;

    q.dequeue();
    q.display();

    cout << "Size: " << q.size() << endl;

    return 0;
}