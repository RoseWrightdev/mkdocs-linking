import uuid
from typing import Dict, Any, List, Optional, Tuple

# Define a constant for the metadata key used to store stable IDs.
METADATA_KEY = "stable_id"

class ResourceNode:
    """
    Represents a node in a hierarchical resource tree.

    Each node has a name, optional attributes, and a list of children nodes.
    A stable ID is automatically assigned or can be provided in attributes.
    """
    def __init__(self, name: str, attributes: Dict[str, Any] = None):
        """
        Initializes a ResourceNode.

        Args:
            name: The name of the resource represented by the node.
            attributes: A dictionary of additional attributes for the node.
                        If not provided, an empty dictionary is used.
                        A stable ID can be included here with the key METADATA_KEY.
        """
        self.name = name
        self.attributes = attributes if attributes is not None else {}
        self.children: List['ResourceNode'] = []
        # Ensure the METADATA_KEY exists in attributes, setting to None if not present.
        self.attributes.setdefault(METADATA_KEY, None)

    def add_child(self, child_node: 'ResourceNode'):
        """
        Adds a child node to the current node.

        Args:
            child_node: The ResourceNode to add as a child.
        """
        self.children.append(child_node)

    @property
    def stable_id(self) -> Optional[str]:
        """
        Gets the stable ID of the node.

        Returns:
            The stable ID string or None if not yet assigned.
        """
        return self.attributes.get(METADATA_KEY)

def assign_keys(node: ResourceNode) -> None:
    """
    Recursively assigns a unique stable ID to each node in the tree if it doesn't already have one.

    Uses UUIDs to generate unique IDs.

    Args:
        node: The root node of the tree to assign keys to.
    """
    if not node.stable_id:
        node.attributes[METADATA_KEY] = str(uuid.uuid4())
    for child in node.children:
        assign_keys(child)

def create_state_snapshot(node: ResourceNode, path_to_root: List[str]) -> Dict[str, Any]:
    """
    Creates a snapshot of the tree's state, mapping stable IDs to their attributes and path.

    Args:
        node: The current node being processed.
        path_to_root: A list of stable IDs representing the path from the root to the parent of the current node.

    Returns:
        A dictionary where keys are stable IDs and values are dictionaries
        containing the node's path to the root and its name.
    """
    state_map = {}
    if not node.stable_id:
        # If a node doesn't have a stable ID, it's not included in the state snapshot.
        return {}

    # Store the current node's state information.
    state_map[node.stable_id] = {
        "path_to_root": path_to_root,
        "name": node.name
    }

    # Recursively create snapshots for children, adding the current node's ID to the path.
    new_path_for_children = path_to_root + [node.stable_id]
    for child in node.children:
        child_map = create_state_snapshot(child, new_path_for_children)
        state_map.update(child_map)

    return state_map

def generate_forwarding_rules(before_state: Dict[str, Any], after_state: Dict[str, Any]) -> Dict[Tuple, Any]:
    """
    Generates forwarding rules based on the differences between two state snapshots.

    Rules are generated for nodes that exist in both states but have changed attributes
    (specifically, their path or name).

    Args:
        before_state: The state snapshot before a change (e.g., refactoring).
        after_state: The state snapshot after a change.

    Returns:
        A dictionary where keys are hashable representations of the old state attributes
        and values indicate the new location key (the stable ID).
    """
    forwarding_map: Dict[Tuple, Any] = {}

    # Iterate through the keys (stable IDs) in the 'before' state.
    for key, before_attrs in before_state.items():
        # Get the corresponding attributes from the 'after' state.
        after_attrs = after_state.get(key)

        # If the node doesn't exist in the 'after' state, skip it (it was likely deleted).
        if after_attrs is None:
            continue

        # If the node exists in both states but its attributes have changed, generate a rule.
        if before_attrs != after_attrs:
            # Create a hashable, immutable key from the dictionary's contents
            # by converting the list to a tuple and creating a tuple of items.
            # This allows the dictionary to be used as a key in another dictionary.
            hashable_key = tuple(sorted((k, tuple(v) if isinstance(v, list) else v) for k, v in before_attrs.items()))
            forwarding_map[hashable_key] = {
                "new_location_key": key  # The stable ID in the after state is the new location.
            }

    return forwarding_map

def pretty_print_tree(node: ResourceNode, indent: str = ""):
    """
    Recursively prints the resource tree in a human-readable format.

    Args:
        node: The current node to print.
        indent: The indentation string to use for the current level.
    """
    print(f"{indent}- {node.name} (ID: {node.stable_id})")
    for child in node.children:
        pretty_print_tree(child, indent + "  ")

def pretty_print_forwarding_rules(rules: Dict[Tuple, Any]):
    """
    Prints the forwarding rules in a human-readable format.

    Args:
        rules: The dictionary of forwarding rules generated by generate_forwarding_rules.
    """
    if not rules:
        print("No changes detected.")
        return

    print(f"Generated {len(rules)} forwarding rule(s):")
    for i, (old_state_tuple, forward_info) in enumerate(rules.items()):
        # Convert the tuple key back into a dictionary for readability
        old_state_dict = dict(old_state_tuple)
        # Convert the inner path_to_root tuple back to a list for printing
        if 'path_to_root' in old_state_dict:
            old_state_dict['path_to_root'] = list(old_state_dict['path_to_root'])

        print(f"\n--- Rule {i+1} ---")
        print("  Old State:")
        for key, value in old_state_dict.items():
            print(f"    - {key}: {value}")
        print("  Forwards To:")
        print(f"    - new_location_key: {forward_info['new_location_key']}")


def main():
    """
    Demonstrates the usage of the ResourceNode and related functions.

    Sets up an initial tree, assigns stable IDs, simulates a refactoring
    (moving and renaming a node), creates state snapshots before and after,
    generates forwarding rules, and prints the results.
    """
    # 1. Setup the initial resource tree
    print("--- Setting up initial tree ---")
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
    print("--- Assigning stable IDs ---")
    assign_keys(root)

    # 3. Create the "before" state snapshot and pretty print the tree
    before_state = create_state_snapshot(root, [])

    print("\n--- Before State Tree ---")
    pretty_print_tree(root)
    print("\n--- Simulating Refactoring (Moving and Renaming) ---\n")

    # 4. Simulate a refactoring by moving and renaming a node
    # Get the 'install' node from the 'guides' parent and remove it.
    node_to_move = guides.children.pop(0)
    # Rename the node.
    node_to_move.name = "install-guide"
    # Add the node to the 'topics' parent.
    topics.add_child(node_to_move)

    # 5. Create the "after" state snapshot
    print("--- Creating After State Snapshot ---")
    after_state = create_state_snapshot(root, [])

    # 6. Generate the forwarding rules by comparing the two dictionaries
    print("--- Generating Forwarding Rules ---")
    forwarding_rules = generate_forwarding_rules(before_state, after_state)

    # 7. Print the resulting forwarding rules in a clean format
    print("\n--- Generated Forwarding Rules ---")
    pretty_print_forwarding_rules(forwarding_rules)


if __name__ == "__main__":
    main()