class TrieNode:
    """A node in the trie with children and end-of-word marker."""

    __slots__ = ("children", "is_end")

    def __init__(self) -> None:
        self.children: dict[str, TrieNode] = {}
        self.is_end = False


class Trie:
    """Prefix tree for efficient string prefix operations.

    Insert, search, and starts_with all run in O(m) where m is key length.
    """

    def __init__(self) -> None:
        self.root = TrieNode()

    def insert(self, word: str) -> None:
        """Insert a word into the trie."""
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end = True

    def search(self, word: str) -> bool:
        """Return True if word is in the trie."""
        node = self._find_node(word)
        return node is not None and node.is_end

    def starts_with(self, prefix: str) -> bool:
        """Return True if any word in the trie starts with prefix."""
        return self._find_node(prefix) is not None

    def _find_node(self, prefix: str) -> TrieNode | None:
        """Traverse trie to the node matching prefix, or None."""
        node = self.root
        for char in prefix:
            if char not in node.children:
                return None
            node = node.children[char]
        return node
