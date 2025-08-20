import uuid
from typing import Dict, Any, List, Optional, Tuple

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

    state_map[node.stable_id] = {
        "path_to_root": path_to_root,
        "name": node.name
    }
    
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
            # Create a hashable, immutable key from the dictionary's contents
            # by converting the list to a tuple and creating a tuple of items.
            hashable_key = tuple(sorted((k, tuple(v) if isinstance(v, list) else v) for k, v in before_attrs.items()))
            forwarding_map[hashable_key] = {
                "new_location_key": key
            }
        
    return forwarding_map

def pretty_print_tree(node: ResourceNode, indent: str = ""):
    """Recursively prints the resource tree in a human-readable format."""
    print(f"{indent}- {node.name} (ID: {node.stable_id})")
    for child in node.children:
        pretty_print_tree(child, indent + "  ")

def pretty_print_forwarding_rules(rules: Dict[Tuple, Any]):
    """Prints the forwarding rules in a human-readable format."""
    if not rules:
        print("No changes detected.")
        return

    print(f"Generated {len(rules)} forwarding rule(s):")
    for i, (old_state_tuple, forward_info) in enumerate(rules.items()):
        # Convert the tuple key back into a dictionary for readability
        old_state_dict = dict(old_state_tuple)
        # Convert the inner path_to_root tuple back to a list
        if 'path_to_root' in old_state_dict:
            old_state_dict['path_to_root'] = list(old_state_dict['path_to_root'])

        print(f"\n--- Rule {i+1} ---")
        print("  Old State:")
        for key, value in old_state_dict.items():
            print(f"    - {key}: {value}")
        print("  Forwards To:")
        print(f"    - new_location_key: {forward_info['new_location_key']}")


def main():
    # 1. Setup the initial resource tree
    root = ResourceNode("root")
    topics = ResourceNode("topics")
    guides = ResourceNode("guides")
    root.add_child(topics)
    root.add_child(guides)
    
    science = ResourceNode("science", {"author": "Gemini"})
    install = ResourceNode("install", {"version": "1.0"})
    topics.add_child(science)
    guides.add_child(install)

    # 2. Assign keys to all nodes
    assign_keys(root)
    
    # 3. Create the "before" state snapshot and pretty print the tree
    before_state = create_state_snapshot(root, [])
    
    print("--- Before State Tree ---")
    pretty_print_tree(root)
    print("\n--- Refactoring Tree ---\n")

    # 4. Simulate a refactoring by moving and renaming a node
    node_to_move = guides.children.pop(0)
    node_to_move.name = "install-guide"
    topics.add_child(node_to_move)

    # 5. Create the "after" state snapshot
    after_state = create_state_snapshot(root, [])
    
    # 6. Generate the forwarding rules by comparing the two dictionaries
    forwarding_rules = generate_forwarding_rules(before_state, after_state)
    
    # 7. Print the resulting forwarding rules in a clean format
    print("--- Generated Forwarding Rules ---")
    pretty_print_forwarding_rules(forwarding_rules)


if __name__ == "__main__":
    main()
