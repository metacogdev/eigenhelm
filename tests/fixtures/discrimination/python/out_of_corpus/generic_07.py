class Node:
    def __init__(self, data):
        self.data = data
        self.next = None


class LinkedList:
    def __init__(self):
        self.head = None

    def append(self, data):
        new_node = Node(data)
        if self.head is None:
            self.head = new_node
            return
        current = self.head
        while current.next is not None:
            current = current.next
        current.next = new_node

    def to_list(self):
        result = []
        current = self.head
        while current is not None:
            result.append(current.data)
            current = current.next
        return result

    def length(self):
        count = 0
        current = self.head
        while current is not None:
            count += 1
            current = current.next
        return count

    def find(self, value):
        current = self.head
        while current is not None:
            if current.data == value:
                return True
            current = current.next
        return False
