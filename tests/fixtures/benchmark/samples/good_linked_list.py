class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def reverse_list(head):
    """Reverse a singly linked list in-place.

    Three-pointer technique: prev, current, next_node.
    Time: O(n). Space: O(1).
    """
    prev = None
    current = head
    while current:
        next_node = current.next
        current.next = prev
        prev = current
        current = next_node
    return prev
