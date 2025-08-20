import unittest
import uuid
from typing import Dict, Any, List, Optional, Tuple

# --- Code from the original script ---
# We include the classes and functions here to make the test script self-contained.

METADATA_KEY = "stable_id"

class ResourceNode:
    def __init__(self, name: str, attributes: Dict[str, Any] = None):
        self.name = name
        self.attributes = attributes if attributes is not None else {}
        self.children: List['ResourceNode'] = []
        self.attributes.setdefault(METADATA_KEY, None)

    def add_child(self, child_node: 'ResourceNode'):
        self.children.append(child_node)

    @property
    def stable_id(self) -> Optional[str]:
        return self.attributes.get(METADATA_KEY)

def assign_keys(node: ResourceNode) -> None:
    if not node.stable_id:
        node.attributes[METADATA_KEY] = str(uuid.uuid4())
    for child in node.children:
        assign_keys(child)

def create_state_snapshot(node: ResourceNode, path_to_root: List[str]) -> Dict[str, Any]:
    state_map = {}
    if not node.stable_id:
        return {}
    state_map[node.stable_id] = {"path_to_root": path_to_root, "name": node.name}
    new_path_for_children = path_to_root + [node.stable_id]
    for child in node.children:
        child_map = create_state_snapshot(child, new_path_for_children)
        state_map.update(child_map)
    return state_map

def generate_forwarding_rules(before_state: Dict[str, Any], after_state: Dict[str, Any]) -> Dict[Tuple, Any]:
    forwarding_map: Dict[Tuple, Any] = {}
    for key, before_attrs in before_state.items():
        after_attrs = after_state.get(key)
        if after_attrs is None:
            continue
        if before_attrs != after_attrs:
            hashable_key = tuple(sorted((k, tuple(v) if isinstance(v, list) else v) for k, v in before_attrs.items()))
            forwarding_map[hashable_key] = {"new_location_key": key}
    return forwarding_map

# --- Unit Test Suite ---

class TestTreeDifferencing(unittest.TestCase):

    def setUp(self):
        """Set up a standard tree for use in multiple tests."""
        self.root = ResourceNode("root")
        self.topics = ResourceNode("topics")
        self.guides = ResourceNode("guides")
        self.root.add_child(self.topics)
        self.root.add_child(self.guides)
        self.install = ResourceNode("install")
        self.guides.add_child(self.install)
        assign_keys(self.root)

    def test_assign_keys(self):
        """Verify that all nodes in a tree are assigned a unique, stable ID."""
        all_nodes = [self.root, self.topics, self.guides, self.install]
        all_ids = set()
        for node in all_nodes:
            self.assertIsNotNone(node.stable_id)
            self.assertIsInstance(node.stable_id, str)
            all_ids.add(node.stable_id)
        # Check for uniqueness
        self.assertEqual(len(all_nodes), len(all_ids))

    def test_create_state_snapshot(self):
        """Verify that the state snapshot correctly captures the tree structure."""
        state = create_state_snapshot(self.root, [])
        self.assertEqual(len(state), 4) # root, topics, guides, install
        
        # Check the state of the 'install' node specifically
        install_state = state.get(self.install.stable_id)
        self.assertIsNotNone(install_state)
        self.assertEqual(install_state['name'], 'install')
        # Path should be [root_id, guides_id]
        expected_path = [self.root.stable_id, self.guides.stable_id]
        self.assertEqual(install_state['path_to_root'], expected_path)

    def test_generate_forwarding_rules_no_change(self):
        """Verify that no rules are generated when states are identical."""
        before_state = create_state_snapshot(self.root, [])
        after_state = create_state_snapshot(self.root, [])
        rules = generate_forwarding_rules(before_state, after_state)
        self.assertEqual(len(rules), 0)

    def test_generate_forwarding_rules_with_move(self):
        """Verify a correct forwarding rule is created when a node moves."""
        before_state = create_state_snapshot(self.root, [])
        
        # Simulate the move: guides/install -> topics/install
        node_to_move = self.guides.children.pop(0)
        self.topics.add_child(node_to_move)
        
        after_state = create_state_snapshot(self.root, [])
        
        rules = generate_forwarding_rules(before_state, after_state)
        self.assertEqual(len(rules), 1)

        # Check that the rule correctly points to the moved node's key
        forward_info = list(rules.values())[0]
        self.assertEqual(forward_info['new_location_key'], self.install.stable_id)

    def test_generate_forwarding_rules_with_rename(self):
        """Verify a correct forwarding rule is created when a node is renamed."""
        before_state = create_state_snapshot(self.root, [])
        
        # Simulate the rename: install -> install-guide
        self.install.name = "install-guide"
        
        after_state = create_state_snapshot(self.root, [])
        
        rules = generate_forwarding_rules(before_state, after_state)
        self.assertEqual(len(rules), 1)

        forward_info = list(rules.values())[0]
        self.assertEqual(forward_info['new_location_key'], self.install.stable_id)

    def test_generate_forwarding_rules_with_deletion(self):
        """Verify no rule is generated for a deleted node."""
        before_state = create_state_snapshot(self.root, [])
        
        # Simulate deletion
        self.guides.children.pop(0)
        
        after_state = create_state_snapshot(self.root, [])
        
        rules = generate_forwarding_rules(before_state, after_state)
        # The current implementation does not track deletions, so no rules are made.
        self.assertEqual(len(rules), 0)


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
