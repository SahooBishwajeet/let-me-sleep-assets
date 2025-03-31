from manim import *
import json
import time
import argparse
import math
import random


# (Catppuccin theme)
CATPPUCCIN_BG = "#1E1E2E"  # Base background
CATPPUCCIN_TEXT = "#CDD6F4"  # Text color
CATPPUCCIN_BLUE = "#89B4FA"  # Blue for max nodes
CATPPUCCIN_RED = "#F38BA8"  # Red for min nodes
CATPPUCCIN_GREEN = "#A6E3A1"  # Green for selected values
CATPPUCCIN_YELLOW = "#F9E2AF"  # Yellow for highlights
CATPPUCCIN_LAVENDER = "#B4BEFE"  # Lavender for UI elements
CATPPUCCIN_PEACH = "#FAB387"  # Peach for comparison operators
CATPPUCCIN_GRAY = "#6C7086"  # Gray for pruned edges
CATPPUCCIN_SURFACE = "#313244"  # Background for nodes and decision box


class TreeNode:
    """Class representing a node in the game tree."""

    def __init__(self, id, value=None, children=None, parent=None):
        self.id = id
        self.value = value
        self.children = children if children else []
        self.x_pos = 0
        self.y_pos = 0
        self.depth = 0
        self.manim_obj = None
        self.value_text = None
        self.is_max_node = True
        self.alpha = float("-inf")
        self.beta = float("inf")
        self.pruned = False
        self.visits = 0
        self.wins = 0
        self.ucb = 0
        self.parent = parent

    def add_child(self, child):
        """Add a child node."""
        self.children.append(child)
        child.parent = self
        return child


class GameTreeVisualizer(Scene):
    """Manim scene for visualizing game trees and algorithms."""

    def __init__(self, config, tree_data, **kwargs):
        super().__init__(**kwargs)
        self.config = config
        self.tree_data = tree_data
        self.node_radius = config.get("node_radius", 0.3)
        self.level_height = config.get("level_height", 1.0)
        self.animation_speed = config.get("animation_speed", 1.0)
        self.step_by_step = config.get("step_by_step", False)
        self.pause_time = config.get("pause_time", 1.0)
        self.show_alpha_beta = config.get("show_alpha_beta", False)
        self.pruning = config.get("pruning", False)

        self.node_objects = {}
        self.edge_objects = {}
        self.value_objects = {}
        self.alpha_beta_text = {}

        self.root = self.build_tree(tree_data)

        self.camera.background_color = CATPPUCCIN_BG

        self.decision_box = None
        self.decision_title = None
        self.decision_text = None

    def build_tree(self, tree_data):
        """Build the tree structure from JSON data."""
        if not tree_data:
            return None

        root_data = tree_data["root"]
        root = TreeNode(root_data["id"], root_data.get("value"))

        self._build_subtree(root, root_data.get("children", []), 0, True)

        self._calculate_positions(root)

        return root

    def _build_subtree(self, parent, children_data, depth, is_max):
        """Recursively build the tree structure."""
        parent.depth = depth
        parent.is_max_node = is_max

        for child_data in children_data:
            child = TreeNode(child_data["id"], child_data.get("value"), parent=parent)
            parent.add_child(child)
            self._build_subtree(
                child, child_data.get("children", []), depth + 1, not is_max
            )

    def _calculate_positions(self, root):
        """Calculate positions for all nodes in the tree."""

        def count_leaves(node):
            if not node.children:
                return 1
            return sum(count_leaves(child) for child in node.children)

        total_leaves = count_leaves(root)

        leaf_position = 0

        def assign_positions(node):
            nonlocal leaf_position

            node.y_pos = -node.depth * self.level_height

            if not node.children:
                node.x_pos = leaf_position - (total_leaves / 2) - 1.5
                leaf_position += 1
                return node.x_pos, 1

            total_width = 0
            leftmost_pos = float("inf")
            rightmost_pos = float("-inf")

            for child in node.children:
                x_pos, width = assign_positions(child)
                leftmost_pos = min(leftmost_pos, x_pos)
                rightmost_pos = max(rightmost_pos, x_pos)
                total_width += width

            node.x_pos = (leftmost_pos + rightmost_pos) / 2
            return node.x_pos, total_width

        assign_positions(root)

    def create_tree_visualization(self):
        """Create initial visualization of the tree."""

        def create_node_visuals(node):
            # Create background circle for the node
            bg_circle = Circle(
                radius=self.node_radius,
                fill_opacity=1,
                fill_color=CATPPUCCIN_SURFACE,
                stroke_color=CATPPUCCIN_BLUE if node.is_max_node else CATPPUCCIN_RED,
            )
            bg_circle.move_to([node.x_pos, node.y_pos, 0])

            # Create foreground circle for the node
            circle = Circle(
                radius=self.node_radius,
                stroke_color=CATPPUCCIN_BLUE if node.is_max_node else CATPPUCCIN_RED,
            )
            circle.move_to([node.x_pos, node.y_pos, 0])

            # Create ID text
            id_text = Text(str(node.id), font_size=20, color=CATPPUCCIN_TEXT).move_to(
                circle.get_center()
            )

            # Add node type label (MAX or MIN)
            node_type = Text(
                "MAX" if node.is_max_node else "MIN",
                font_size=14,
                color=CATPPUCCIN_TEXT,
            )
            node_type.next_to(circle, UP, buff=0.1)

            # Store the combined object
            node.manim_obj = VGroup(bg_circle, circle, id_text, node_type)
            self.node_objects[node.id] = node.manim_obj

            # Create value placeholder (to be filled later)
            if node.value is not None:
                value_text = Text(str(node.value), font_size=16, color=CATPPUCCIN_TEXT)
                value_text.next_to(circle, DOWN, buff=0.1)
                node.value_text = value_text
                self.value_objects[node.id] = value_text

            # Create edges to children
            for child in node.children:
                create_node_visuals(child)

                edge = Line(
                    [node.x_pos, node.y_pos, 0],
                    [child.x_pos, child.y_pos, 0],
                    stroke_width=2,
                    color=CATPPUCCIN_TEXT,
                )

                key = f"{node.id}-{child.id}"
                self.edge_objects[key] = edge

        create_node_visuals(self.root)

    def create_decision_box(self):
        """Create a dedicated decision box on the right side of the screen."""
        # Create box rectangle
        rect = Rectangle(
            height=4,
            width=3.5,
            fill_color=CATPPUCCIN_SURFACE,
            fill_opacity=1,
            stroke_color=CATPPUCCIN_LAVENDER,
        )
        rect.to_edge(RIGHT, buff=1.0)

        # Create title
        title = Text("Decision Steps", font_size=24, color=CATPPUCCIN_LAVENDER)
        title.next_to(rect, UP, buff=0.2)

        # Initial empty text
        text = Text("Algorithm started...", font_size=16, color=CATPPUCCIN_TEXT)
        text.move_to(rect.get_center())

        self.decision_box = rect
        self.decision_title = title
        self.decision_text = text

        self.play(
            Create(rect), Write(title), Write(text), run_time=1 / self.animation_speed
        )

    def update_decision_box(self, text_content, color=None):
        """Update the text in the decision box with better spacing and consistent coloring."""
        if color is None:
            color = CATPPUCCIN_TEXT

        # Split the text into lines
        lines = text_content.split("\n")
        spaced_text = "\n\n".join(lines)

        new_text = Text(spaced_text, font_size=16, color=color, line_spacing=1.2)
        new_text.move_to(self.decision_box.get_center())
        new_text.scale_to_fit_width(self.decision_box.width * 0.85)

        if new_text.height > self.decision_box.height * 0.85:
            new_text.scale_to_fit_height(self.decision_box.height * 0.85)

        self.play(
            Transform(self.decision_text, new_text), run_time=0.5 / self.animation_speed
        )

        if self.step_by_step:
            self.wait(self.pause_time / 2)

    def construct(self):
        """Main construction method for Manim."""
        # Create the tree visualization
        self.create_tree_visualization()

        # Display the tree structure (edges first, then nodes to ensure nodes are on top)
        for edge in self.edge_objects.values():
            self.play(Create(edge), run_time=0.5 / self.animation_speed)

        for node_obj in self.node_objects.values():
            self.play(Create(node_obj), run_time=0.5 / self.animation_speed)

        # Create the decision box
        self.create_decision_box()

        if self.step_by_step:
            self.wait(self.pause_time)

        # Choose algorithm based on configuration
        if self.config.get("algorithm") == "mcts":
            self.run_mcts()
        else:
            # Default to minimax/alpha-beta
            self.run_minimax()

        # Display final state
        self.wait(2)

    def run_minimax(self):
        """Run the minimax algorithm with visualization."""
        # Title for the algorithm
        title = Text("Minimax Algorithm", font_size=36, color=CATPPUCCIN_LAVENDER)
        title.to_edge(UP)
        self.play(Write(title))

        if self.step_by_step:
            self.wait(self.pause_time)

        # Run the algorithm with visualization
        self.minimax(self.root, float("-inf"), float("inf"))

        # Final annotation
        result_text = Text(
            f"Optimal value: {self.root.value}", font_size=28, color=CATPPUCCIN_GREEN
        )
        result_text.next_to(title, DOWN)
        self.play(Write(result_text))

        # Final decision box update
        self.update_decision_box(
            f"Algorithm completed!\nOptimal value: {self.root.value}", CATPPUCCIN_GREEN
        )

    def minimax(self, node, alpha, beta):
        """Recursive minimax algorithm with alpha-beta pruning."""
        # Store initial alpha-beta values
        node.alpha = alpha
        node.beta = beta

        # Highlight current node
        highlight = node.manim_obj[1].copy()
        highlight.set_fill(CATPPUCCIN_YELLOW, opacity=0.5)

        self.play(FadeIn(highlight), run_time=0.5 / self.animation_speed)

        # Display alpha-beta values if enabled
        alpha_beta_display = None
        if self.show_alpha_beta:
            alpha_beta_text = f"α:{alpha}, β:{beta}"
            alpha_beta_display = Text(
                alpha_beta_text, font_size=14, color=CATPPUCCIN_LAVENDER
            )
            alpha_beta_display.next_to(node.manim_obj, UP, buff=0.3)
            self.play(Write(alpha_beta_display), run_time=0.5 / self.animation_speed)
            self.alpha_beta_text[node.id] = alpha_beta_display

        # Update decision box
        self.update_decision_box(
            f"Processing node {node.id}\n"
            + f"Node type: {'MAX' if node.is_max_node else 'MIN'}\n"
            + (f"Alpha: {alpha}, Beta: {beta}" if self.show_alpha_beta else "")
        )

        # If we're at a leaf node
        if not node.children:
            # Visualize the node value
            if node.value_text is not None:
                self.play(FadeIn(node.value_text), run_time=0.5 / self.animation_speed)

            # Update decision box
            self.update_decision_box(
                f"Leaf node {node.id}\n" + f"Value: {node.value}", CATPPUCCIN_PEACH
            )

            self.play(FadeOut(highlight), run_time=0.5 / self.animation_speed)

            # Remove alpha-beta display when done with this node
            if alpha_beta_display:
                self.play(
                    FadeOut(alpha_beta_display), run_time=0.5 / self.animation_speed
                )

            if self.step_by_step:
                self.wait(self.pause_time / 2)

            return node.value

        # Initialize best value
        if node.is_max_node:
            value = float("-inf")
            best_child = None
        else:
            value = float("inf")
            best_child = None

        # Recursively process children
        for i, child in enumerate(node.children):
            # Skip pruned branches
            if child.pruned:
                continue

            # Update decision box before processing child
            self.update_decision_box(
                f"Node {node.id} ({'MAX' if node.is_max_node else 'MIN'})\n"
                + f"Processing child {child.id}\n"
                + f"Current best: {value if best_child else 'None'}"
            )

            # Process the child
            child_value = self.minimax(child, alpha, beta)

            # Update decision box with comparison
            operator = ">" if node.is_max_node else "<"
            if best_child is None:
                self.update_decision_box(
                    f"Node {node.id} ({'MAX' if node.is_max_node else 'MIN'})\n"
                    + f"First child {child.id} value: {child_value}\n"
                    + f"Setting as current best",
                    CATPPUCCIN_GREEN,
                )
                update_value = True
            else:
                if (node.is_max_node and child_value > value) or (
                    not node.is_max_node and child_value < value
                ):
                    self.update_decision_box(
                        f"Node {node.id} ({'MAX' if node.is_max_node else 'MIN'})\n"
                        + f"{value} {operator} {child_value} is TRUE\n"
                        + f"Updating best to {child_value}",
                        CATPPUCCIN_GREEN,
                    )
                    update_value = True
                else:
                    self.update_decision_box(
                        f"Node {node.id} ({'MAX' if node.is_max_node else 'MIN'})\n"
                        + f"{value} {operator} {child_value} is FALSE\n"
                        + f"Keeping current best: {value}",
                        CATPPUCCIN_PEACH,
                    )
                    update_value = False

            if self.step_by_step:
                self.wait(self.pause_time / 2)

            # Update the value if needed
            if best_child is None or update_value:
                value = child_value
                best_child = child

                # Highlight the edge to the best child
                edge_key = f"{node.id}-{child.id}"
                if edge_key in self.edge_objects:
                    self.play(
                        self.edge_objects[edge_key]
                        .animate.set_color(CATPPUCCIN_GREEN)
                        .set_stroke_width(4),
                        run_time=0.5 / self.animation_speed,
                    )

            # Update alpha/beta
            old_alpha, old_beta = alpha, beta
            if node.is_max_node:
                alpha = max(alpha, value)
            else:
                beta = min(beta, value)

            # Update alpha-beta display if values changed
            if self.show_alpha_beta and (old_alpha != alpha or old_beta != beta):
                # Update the alpha-beta text on the node
                new_alpha_beta_text = f"α:{alpha}, β:{beta}"
                new_alpha_beta_display = Text(
                    new_alpha_beta_text, font_size=14, color=CATPPUCCIN_LAVENDER
                )
                new_alpha_beta_display.next_to(node.manim_obj, UP, buff=0.3)

                self.play(
                    Transform(self.alpha_beta_text[node.id], new_alpha_beta_display),
                    run_time=0.5 / self.animation_speed,
                )

                # Also update in decision box
                self.update_decision_box(
                    f"Node {node.id} ({'MAX' if node.is_max_node else 'MIN'})\n"
                    + f"Updating α/β values:\n"
                    + f"α: {old_alpha} → {alpha}\n"
                    + f"β: {old_beta} → {beta}",
                    CATPPUCCIN_LAVENDER,
                )

            # Check for pruning
            if self.pruning and beta <= alpha:
                # Mark remaining children as pruned
                for remaining_child in node.children[i + 1 :]:
                    remaining_child.pruned = True
                    # Visualize pruning
                    edge_key = f"{node.id}-{remaining_child.id}"
                    if edge_key in self.edge_objects:
                        self.play(
                            self.edge_objects[edge_key]
                            .animate.set_color(CATPPUCCIN_GRAY)
                            .set_opacity(0.5),
                            run_time=0.5 / self.animation_speed,
                        )

                # Update decision box about pruning
                self.update_decision_box(
                    f"Node {node.id} ({'MAX' if node.is_max_node else 'MIN'})\n"
                    + f"PRUNING: β ≤ α ({beta} ≤ {alpha})\n"
                    + f"Skipping remaining children",
                    CATPPUCCIN_YELLOW,
                )

                break

        # Update decision box with final decision
        self.update_decision_box(
            f"Node {node.id} ({'MAX' if node.is_max_node else 'MIN'})\n"
            + f"All children processed\n"
            + f"Final value: {value}",
            CATPPUCCIN_GREEN,
        )

        # Update node value
        node.value = value

        # Visualize the calculated value with green highlight
        value_text = Text(str(value), font_size=16, color=CATPPUCCIN_GREEN)
        value_text.next_to(node.manim_obj, DOWN, buff=0.1)

        if node.value_text is None:
            node.value_text = value_text
            self.value_objects[node.id] = value_text
            self.play(FadeIn(value_text), run_time=0.5 / self.animation_speed)
        else:
            self.play(
                Transform(node.value_text, value_text),
                run_time=0.5 / self.animation_speed,
            )

        # Remove highlight
        self.play(FadeOut(highlight), run_time=0.5 / self.animation_speed)

        if self.step_by_step:
            self.wait(self.pause_time / 2)

        return value

    def run_mcts(self):
        """Run the Monte Carlo Tree Search algorithm with visualization."""
        # Title for the algorithm
        title = Text("Monte Carlo Tree Search", font_size=36, color=CATPPUCCIN_LAVENDER)
        title.to_edge(UP)
        self.play(Write(title))

        if self.step_by_step:
            self.wait(self.pause_time)

        # MCTS parameters
        iterations = self.config.get("mcts_iterations", 10)
        exploration_weight = self.config.get("exploration_weight", 1.4)

        # Initialize UCB1 values and visit counts
        for node_id, node_obj in self.node_objects.items():
            self.get_node_by_id(node_id).visits = 0
            self.get_node_by_id(node_id).wins = 0
            self.get_node_by_id(node_id).ucb = 0

        # Run MCTS iterations
        for iteration in range(1, iterations + 1):
            self.update_decision_box(
                f"MCTS Iteration {iteration}/{iterations}", CATPPUCCIN_LAVENDER
            )

            # Phase 1: Selection
            selected_node = self.mcts_selection(self.root, exploration_weight)

            # Phase 2: Expansion (if needed)
            if selected_node.visits > 0 and selected_node.children:
                expanded_node = self.mcts_expansion(selected_node)
            else:
                expanded_node = selected_node

            # Phase 3: Simulation
            simulation_result = self.mcts_simulation(expanded_node)

            # Phase 4: Backpropagation
            self.mcts_backpropagation(expanded_node, simulation_result)

            # Wait between iterations
            if self.step_by_step:
                self.wait(self.pause_time / 2)

        # Show final statistics
        self.visualize_mcts_stats()

        # Choose best move from root
        best_child = self.get_best_child(
            self.root, 0
        )  # Exploitation only (no exploration)

        # Highlight the best move with a thicker green edge
        edge_key = f"{self.root.id}-{best_child.id}"
        if edge_key in self.edge_objects:
            self.play(
                self.edge_objects[edge_key]
                .animate.set_color(CATPPUCCIN_GREEN)
                .set_stroke_width(6),
                run_time=1 / self.animation_speed,
            )

        # Final annotation
        result_text = Text(
            f"Best move: {best_child.id} (Win rate: {best_child.wins/best_child.visits:.2f})",
            font_size=28,
            color=CATPPUCCIN_GREEN,
        )
        result_text.next_to(title, DOWN)
        self.play(Write(result_text))

        # Final decision box update
        self.update_decision_box(
            f"MCTS completed!\nBest move: {best_child.id}\nWin rate: {best_child.wins/best_child.visits:.2f}",
            CATPPUCCIN_GREEN,
        )

    def get_node_by_id(self, node_id):
        """Helper function to get node by ID."""

        def find_node(node, target_id):
            if node.id == target_id:
                return node
            for child in node.children:
                found = find_node(child, target_id)
                if found:
                    return found
            return None

        return find_node(self.root, node_id)

    def mcts_selection(self, node, exploration_weight):
        """Select a node using UCB1 formula."""
        self.update_decision_box(
            f"Selection phase\nStarting from node {node.id}", CATPPUCCIN_BLUE
        )

        # Highlight the current node
        highlight = node.manim_obj[1].copy()
        highlight.set_fill(CATPPUCCIN_BLUE, opacity=0.5)
        self.play(FadeIn(highlight), run_time=0.5 / self.animation_speed)

        current_node = node
        path = [current_node]

        # Traverse down the tree until we find a node that hasn't been fully explored
        while current_node.children and all(
            child.visits > 0 for child in current_node.children
        ):
            next_node = self.get_best_child(current_node, exploration_weight)

            # Highlight the traversal
            edge_key = f"{current_node.id}-{next_node.id}"
            if edge_key in self.edge_objects:
                self.play(
                    self.edge_objects[edge_key]
                    .animate.set_color(CATPPUCCIN_BLUE)
                    .set_stroke_width(3),
                    run_time=0.5 / self.animation_speed,
                )

            # Move to the next node
            current_node = next_node
            path.append(current_node)

            # Highlight the new node
            new_highlight = current_node.manim_obj[1].copy()
            new_highlight.set_fill(CATPPUCCIN_BLUE, opacity=0.5)
            self.play(FadeIn(new_highlight), run_time=0.5 / self.animation_speed)

            # Update decision box
            self.update_decision_box(
                f"Selection phase\nMoving to node {current_node.id}\n"
                f"UCB1 value: {self.calculate_ucb(current_node, exploration_weight):.3f}\n"
                f"Visits: {current_node.visits}, Wins: {current_node.wins}",
                CATPPUCCIN_BLUE,
            )

            # Fade out previous highlights
            self.play(FadeOut(highlight), run_time=0.5 / self.animation_speed)
            highlight = new_highlight

        # Fade out the last highlight
        self.play(FadeOut(highlight), run_time=0.5 / self.animation_speed)

        # Return the selected node
        self.update_decision_box(
            f"Selection complete\nSelected node: {current_node.id}", CATPPUCCIN_BLUE
        )

        return current_node

    def calculate_ucb(self, node, exploration_weight):
        """Calculate the UCB1 value for a node."""
        if node.visits == 0:
            return float("inf")

        # Calculate exploitation term (win rate)
        exploitation = node.wins / node.visits

        if node.parent is None:
            # If root node (no parent), just use exploitation
            exploration = 0
        elif node.parent.visits == 0:
            # Safety check: if parent has no visits, avoid division by zero
            exploration = float("inf")
        else:
            # Standard UCB formula
            exploration = exploration_weight * math.sqrt(
                math.log(node.parent.visits) / node.visits
            )

        return exploitation + exploration

    def get_best_child(self, node, exploration_weight):
        """Get the child with the highest UCB1 value."""
        best_value = float("-inf")
        best_children = []

        for child in node.children:
            # If child hasn't been visited, prioritize it
            if child.visits == 0:
                return child

            # Calculate UCB value
            ucb = self.calculate_ucb(child, exploration_weight)

            # Update best if higher
            if ucb > best_value:
                best_value = ucb
                best_children = [child]
            elif ucb == best_value:
                best_children.append(child)

        # Randomly choose among best children (tie-breaking)
        return random.choice(best_children)

    def mcts_expansion(self, node):
        """Expand a leaf node by selecting an unexplored child."""
        self.update_decision_box(
            f"Expansion phase\nNode {node.id}\nChoosing unexplored child",
            CATPPUCCIN_PEACH,
        )

        # Find all unvisited children
        unvisited = [child for child in node.children if child.visits == 0]

        if unvisited:
            # Select a random unvisited child
            child = random.choice(unvisited)

            # Highlight the selected child
            highlight = child.manim_obj[1].copy()
            highlight.set_fill(CATPPUCCIN_PEACH, opacity=0.5)
            self.play(FadeIn(highlight), run_time=0.5 / self.animation_speed)

            # Highlight the edge
            edge_key = f"{node.id}-{child.id}"
            if edge_key in self.edge_objects:
                self.play(
                    self.edge_objects[edge_key]
                    .animate.set_color(CATPPUCCIN_PEACH)
                    .set_stroke_width(3),
                    run_time=0.5 / self.animation_speed,
                )

            self.update_decision_box(
                f"Expansion phase\nSelected child {child.id} for expansion",
                CATPPUCCIN_PEACH,
            )

            self.play(FadeOut(highlight), run_time=0.5 / self.animation_speed)

            return child

        # If all children are visited, return the node itself
        return node

    def mcts_simulation(self, node):
        """Run a random simulation from the node to determine outcome."""
        self.update_decision_box(
            f"Simulation phase\nStarting from node {node.id}\nRunning random playout",
            CATPPUCCIN_YELLOW,
        )

        # Highlight the simulation start node
        highlight = node.manim_obj[1].copy()
        highlight.set_fill(CATPPUCCIN_YELLOW, opacity=0.5)
        self.play(FadeIn(highlight), run_time=0.5 / self.animation_speed)

        current = node

        # Random playout until leaf node
        path = [current]
        while current.children:
            # Randomly select a child
            next_node = random.choice(current.children)

            # Highlight the traversal lightly
            edge_key = f"{current.id}-{next_node.id}"
            if edge_key in self.edge_objects:
                self.play(
                    self.edge_objects[edge_key]
                    .animate.set_color(CATPPUCCIN_YELLOW)
                    .set_stroke_width(2),
                    run_time=0.3 / self.animation_speed,
                )

            current = next_node
            path.append(current)

        # Get the result from the leaf node (use node value directly if available)
        if hasattr(current, "value") and current.value is not None:
            result = current.value
        else:
            # Otherwise simulate a random result (0 or 1)
            result = random.randint(0, 1)

        # Highlight the final result
        result_text = Text(f"Result: {result}", font_size=16, color=CATPPUCCIN_YELLOW)
        result_text.next_to(current.manim_obj, DOWN, buff=0.2)
        self.play(FadeIn(result_text), run_time=0.5 / self.animation_speed)

        self.update_decision_box(
            f"Simulation complete\nResult: {result}", CATPPUCCIN_YELLOW
        )

        # Clean up highlights and temporary text
        self.play(
            FadeOut(highlight),
            FadeOut(result_text),
            run_time=0.5 / self.animation_speed,
        )

        return result

    def mcts_backpropagation(self, node, result):
        """Backpropagate the simulation result up the tree."""
        self.update_decision_box(
            f"Backpropagation phase\nStarting from node {node.id}\nResult: {result}",
            CATPPUCCIN_GREEN,
        )

        current = node

        # Backpropagate up the tree using parent references
        while current:
            # Update statistics
            current.visits += 1
            if result == 1:  # Assuming 1 is a win
                current.wins += 1

            # Calculate win rate
            win_rate = current.wins / current.visits

            # Visualize the update
            stats_text = Text(
                f"Visits: {current.visits}\nWins: {current.wins}\nRate: {win_rate:.2f}",
                font_size=14,
                color=CATPPUCCIN_GREEN,
            )
            stats_text.next_to(current.manim_obj, RIGHT, buff=0.2)

            # Highlight the node being updated
            highlight = current.manim_obj[1].copy()
            highlight.set_fill(CATPPUCCIN_GREEN, opacity=0.3)

            self.play(
                FadeIn(highlight),
                FadeIn(stats_text),
                run_time=0.5 / self.animation_speed,
            )

            # Update decision box
            self.update_decision_box(
                f"Updating node {current.id}\nVisits: {current.visits}\nWins: {current.wins}\nWin rate: {win_rate:.2f}",
                CATPPUCCIN_GREEN,
            )

            # Clean up before moving to parent
            self.play(
                FadeOut(highlight),
                FadeOut(stats_text),
                run_time=0.5 / self.animation_speed,
            )

            # Move to parent using direct parent reference
            current = current.parent

        self.update_decision_box("Backpropagation complete", CATPPUCCIN_GREEN)

    def get_parent_child_mapping(self):
        """Create a mapping of parent IDs to child IDs."""
        mapping = {}

        def build_mapping(node):
            child_ids = [child.id for child in node.children]
            if child_ids:
                mapping[node.id] = child_ids

            for child in node.children:
                build_mapping(child)

        build_mapping(self.root)
        return mapping

    def visualize_mcts_stats(self):
        """Visualize the final statistics for each node after MCTS."""
        self.update_decision_box(
            "Displaying final MCTS statistics for all nodes", CATPPUCCIN_LAVENDER
        )

        # Create a group to hold all the stat texts
        stats_group = VGroup()

        def add_stats_to_node(node):
            if node.visits > 0:
                win_rate = node.wins / node.visits
                stats_text = Text(
                    f"{node.visits}|{win_rate:.2f}",
                    font_size=12,
                    color=CATPPUCCIN_LAVENDER,
                )
                stats_text.next_to(node.manim_obj, LEFT, buff=0.2)
                stats_group.add(stats_text)

            for child in node.children:
                add_stats_to_node(child)

        add_stats_to_node(self.root)

        # Add all stats at once
        self.play(FadeIn(stats_group), run_time=1 / self.animation_speed)

        # Keep stats visible
        return stats_group


def parse_config(config_file):
    """Parse the configuration file."""
    with open(config_file, "r") as f:
        config = json.load(f)
    return config


def parse_tree_data(tree_file):
    """Parse the tree data file."""
    with open(tree_file, "r") as f:
        tree_data = json.load(f)
    return tree_data


def setup_argument_parser():
    """Set up command line argument parser."""
    parser = argparse.ArgumentParser(description="Game Tree Visualization Tool")
    parser.add_argument("--config", required=True, help="Path to configuration file")
    parser.add_argument("--tree", required=True, help="Path to tree data file")
    parser.add_argument(
        "--algorithm",
        default="minimax",
        choices=["minimax", "alphabeta", "mcts"],
        help="Algorithm to visualize",
    )
    return parser


def main():
    """Main function to run the visualizer."""
    # Parse command line arguments
    parser = setup_argument_parser()
    args = parser.parse_args()

    # Load configuration and tree data
    config = parse_config(args.config)
    tree_data = parse_tree_data(args.tree)

    # Add algorithm to config for easy access within the visualizer
    config["algorithm"] = args.algorithm

    # Configure algorithm-specific settings
    if args.algorithm == "minimax":
        if not config.get("pruning", False):
            config["show_alpha_beta"] = False
    elif args.algorithm == "alphabeta":
        config["pruning"] = True
        config["show_alpha_beta"] = True
    elif args.algorithm == "mcts":
        # Configure MCTS parameters
        if "mcts_iterations" not in config:
            config["mcts_iterations"] = 10  # Default number of iterations
        if "exploration_weight" not in config:
            config["exploration_weight"] = 1.4  # Default exploration constant

    # Run the visualization
    scene = GameTreeVisualizer(config, tree_data)
    scene.render()


if __name__ == "__main__":
    main()
