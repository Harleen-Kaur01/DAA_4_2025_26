/**
 * Definition for singly-linked list.
 * struct ListNode {
 *     int val;
 *     ListNode *next;
 *     ListNode() : val(0), next(nullptr) {}
 *     ListNode(int x) : val(x), next(nullptr) {}
 *     ListNode(int x, ListNode *next) : val(x), next(next) {}
 * };
 */
class Solution {
public:
    ListNode* knode(ListNode* head,int k){
        while(k>1 && head){
            head = head->next;
            k--;
        }
        return head;
    }
    void rev(ListNode* head){
        ListNode* prev = nullptr;
        ListNode* curr = head;
        ListNode* after = nullptr;
        while(curr){
            after = curr->next;
            curr->next = prev;
            prev = curr;
            curr = after;
        }
        head = prev;
}
    ListNode* reverseKGroup(ListNode* head, int k) {
        ListNode* dummy = new ListNode(-1);
        ListNode* ptr = dummy;
        ListNode* grphead = head;
        while(grphead){
            ListNode* temp = grphead;
            ListNode* kthnode = knode(grphead,k);
            if(!kthnode) break;
            ListNode* nextnewnode = kthnode->next;
            kthnode->next = nullptr;
            rev(grphead);
            ptr->next = kthnode;
            ptr = grphead;
            grphead->next = nextnewnode;
            grphead = nextnewnode;
        }
        return dummy->next;
    }
};