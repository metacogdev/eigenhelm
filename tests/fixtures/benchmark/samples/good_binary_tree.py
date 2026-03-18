class Node:
    def __init__(self, val):
        self.val = val
        self.left = None
        self.right = None


def insert_bst(root, val):
    """Insert value into binary search tree. Returns new root."""
    if root is None:
        return Node(val)
    if val < root.val:
        root.left = insert_bst(root.left, val)
    elif val > root.val:
        root.right = insert_bst(root.right, val)
    return root


def search_bst(root, val):
    """Search for value in BST. Returns node or None."""
    if root is None or root.val == val:
        return root
    if val < root.val:
        return search_bst(root.left, val)
    return search_bst(root.right, val)
