from collections import defaultdict
import dataclasses
import typing

from . import graph
from . import registry_mem
from . import op_def
from .language_features.tagging import opdef_util


@dataclasses.dataclass
class DependencyGraph:
    # Map of inputs to outputs
    input_to_output: defaultdict[graph.Node, set[graph.Node]] = dataclasses.field(
        default_factory=lambda: defaultdict(set)
    )

    # Map from outputs to inputs
    output_to_input: defaultdict[graph.Node, set[graph.Node]] = dataclasses.field(
        default_factory=lambda: defaultdict(set)
    )

    def add_node(self: "DependencyGraph", node_to_add: graph.Node) -> None:
        if isinstance(node_to_add, graph.OutputNode):
            output_node = node_to_add
            node_inputs = list(output_node.from_op.inputs.values())
            # Add each input node to the graph and mark the output dependents
            for input_node_ndx, input_node in enumerate(node_inputs):
                if node_is_mapper(input_node):
                    # Special case for mappers - if the input is a mapper (opMap or opMapEach), then we
                    # need to connect the fn_node to the output node directly (since the tag getter can
                    # apply to either inside the map fn or to the map fn itself). We don't do this
                    # for for all lambdas (like opSort), since the lambda terminates with the execution
                    # of that op.
                    self._add_edge(get_map_fn_from_mapper_node(input_node), output_node)
                self._add_edge(input_node, output_node)
                self.add_node(input_node)

                # Special case for lambdas. Example:
                # ouput_node = opMap
                # fn_node = the lambda
                if isinstance(input_node, graph.ConstNode) and isinstance(
                    input_node.val, graph.Node
                ):
                    fn_node = input_node.val

                    # Add the node to the graph
                    self.add_node(fn_node)

                    # Get a reference to the vars:
                    vars = graph.expr_vars(fn_node)

                    # Assume that each var depends on all inputs (this is a more liberal assumption than we need)
                    for var in vars:
                        # Here, we only add the input nodes that come before the current fn param!
                        for input_node_2 in node_inputs[:input_node_ndx]:
                            self._add_edge(input_node_2, var)

    def _add_edge(self, input_node: graph.Node, output_node: graph.Node) -> None:
        self.input_to_output[input_node].add(output_node)
        self.output_to_input[output_node].add(input_node)


@dataclasses.dataclass
class TagSubscriptionManager:
    downstream_tag_subscriptions: defaultdict[
        graph.Node, defaultdict[str, set[graph.Node]]
    ] = dataclasses.field(default_factory=lambda: defaultdict(lambda: defaultdict(set)))
    node_provides_tag_for_downstream_nodes: defaultdict[
        graph.Node, set[graph.Node]
    ] = dataclasses.field(default_factory=lambda: defaultdict(set))

    def _direct_add_subscriptions_for_tag_to_node(
        self: "TagSubscriptionManager",
        sub_nodes: set[graph.Node],
        tag_name: str,
        to_node: graph.Node,
    ) -> None:
        self.downstream_tag_subscriptions[to_node][tag_name].update(sub_nodes)

    def _direct_merge_subscriptions_into_node_from_downstream_node(
        self: "TagSubscriptionManager", node: graph.Node, downstream_node: graph.Node
    ) -> None:
        for tag_name, tag_subscriptions in self.downstream_tag_subscriptions[
            downstream_node
        ].items():
            self._direct_add_subscriptions_for_tag_to_node(
                tag_subscriptions, tag_name, node
            )

    def rollup_tags(
        self: "TagSubscriptionManager",
        curr_node: graph.Node,
        downstream_nodes: set[graph.Node],
        dg: DependencyGraph,
    ) -> None:
        for downstream_node in downstream_nodes:
            tag_get_name = node_gets_tag_by_name(downstream_node)
            if tag_get_name:
                # If the current node is a tag getter, then it adds itself
                self.downstream_tag_subscriptions[curr_node][tag_get_name].add(
                    downstream_node
                )
            else:
                # else, rollup the downstream tag subscriptions
                # Merge the downstream tag subscriptions
                self._direct_merge_subscriptions_into_node_from_downstream_node(
                    curr_node, downstream_node
                )

        # If the current node provides a tag, then we need to connect the wormholes
        # and update the downstream tag subscriptions
        provider_result = node_provides_tag(curr_node)
        if provider_result:
            subscriptions_to_provided_tag = self.downstream_tag_subscriptions[
                curr_node
            ][provider_result.tag_name]
            self.downstream_tag_subscriptions[curr_node][
                provider_result.tag_name
            ] = set()
            for provider in provider_result.tag_providers:
                for sub_node in subscriptions_to_provided_tag:
                    self.node_provides_tag_for_downstream_nodes[provider].add(sub_node)
                    self.rollup_tags(provider, dg.output_to_input[sub_node], dg)
                    # self._direct_merge_subscriptions_into_node_from_downstream_node(provided_by, sub_node)


@dataclasses.dataclass
class StitchGraph2:
    _subscription_manager: TagSubscriptionManager
    _dependency_graph: DependencyGraph

    def get_combined_outputs(self, node: graph.Node) -> set[graph.Node]:
        direct_outputs = self._dependency_graph.input_to_output[node]
        tag_subscriptions = (
            self._subscription_manager.node_provides_tag_for_downstream_nodes[node]
        )

        return direct_outputs.union(tag_subscriptions)


def stitch_2(nodes: list[graph.Node]) -> StitchGraph2:
    """
    Stitch2 is a new version of the stitcher that uses a bottom-up traversal, similar
    to Weave0. Here, we start at the leaf nodes, and collect "tag getters" along the way.
    """
    # Tag subscription manager
    tag_subscription_manager = TagSubscriptionManager()

    # First we need to create a dependency graph (basically a forward graph in our old terminology)
    dependency_graph = DependencyGraph()
    for node in nodes:
        dependency_graph.add_node(node)

    # Next, we basically do BFS on the nodes
    frontier = [n for n in nodes]
    visited = set()
    while frontier:
        # Standard BFS bookkeeping
        curr_node = frontier.pop()
        if curr_node in visited:
            continue
        visited.add(curr_node)

        # Add nodes to the frontier
        ## Add the node's inputs to the frontier if all their dependents have been visited
        for input_node in dependency_graph.output_to_input[curr_node]:
            if all(
                output_of_input in visited
                for output_of_input in dependency_graph.input_to_output[input_node]
            ):
                frontier.append(input_node)

        ## Special case for lambdas
        if isinstance(curr_node, graph.ConstNode) and isinstance(
            curr_node.val, graph.Node
        ):
            fn_node = curr_node.val
            if all(
                output_of_input in visited
                for output_of_input in dependency_graph.input_to_output[fn_node]
            ):
                frontier.append(fn_node)

        # Now we can process the node
        tag_subscription_manager.rollup_tags(
            curr_node, dependency_graph.input_to_output[curr_node], dependency_graph
        )

    return StitchGraph2(tag_subscription_manager, dependency_graph)


def node_gets_tag_by_name(node: graph.Node) -> typing.Optional[str]:
    if isinstance(node, graph.OutputNode):
        op = registry_mem.memory_registry.get_op(node.from_op.name)
        if is_get_tag_op(op):
            return get_tag_name_from_tag_getter_op(op)
        elif is_mapped_get_tag_op(op):
            return get_tag_name_from_mapped_tag_getter_op(op)
    return None


def node_is_mapper(node: graph.Node) -> bool:
    return isinstance(node, graph.OutputNode) and (
        node.from_op.name.endswith("map") or node.from_op.name.endswith("mapEach")
    )


def get_map_fn_from_mapper_node(node: graph.OutputNode) -> graph.Node:
    return list(node.from_op.inputs.values())[1].val


def get_group_fn_from_mapper_node(node: graph.OutputNode) -> graph.Node:
    return list(node.from_op.inputs.values())[1].val


def get_joinall_fn_from_mapper_node(node: graph.OutputNode) -> graph.Node:
    return list(node.from_op.inputs.values())[1].val


def get_join_2_fn_from_mapper_node(node: graph.OutputNode) -> list[graph.Node]:
    inputs = list(node.from_op.inputs.values())
    return [inputs[2].val, inputs[3].val]


@dataclasses.dataclass
class TagProviderResult:
    tag_name: str
    tag_providers: list[graph.Node]


def node_provides_tag(node: graph.Node) -> typing.Optional[TagProviderResult]:
    if isinstance(node, graph.OutputNode):
        op = registry_mem.memory_registry.get_op(node.from_op.name)
        if (
            op.derived_from
            and op.derived_from.derived_ops.get("mapped")
            and opdef_util.should_tag_op_def_outputs(op.derived_from)
        ) or opdef_util.should_tag_op_def_outputs(op):
            first_input_key, first_input_node = list(node.from_op.inputs.items())[0]
            return TagProviderResult(first_input_key, first_input_node)
        elif node.from_op.name.endswith("groupby"):
            return TagProviderResult("groupKey", [get_group_fn_from_mapper_node(node)])
        elif node.from_op.name.endswith("joinAll"):
            return TagProviderResult("joinKey", [get_joinall_fn_from_mapper_node(node)])
        elif node.from_op.name.endswith("join"):
            return TagProviderResult("joinKey", get_join_2_fn_from_mapper_node(node))
    return None


def is_mapped_get_tag_op(op: op_def.OpDef) -> bool:
    if op.derived_from and op.derived_from.derived_ops.get("mapped") == op:
        return is_get_tag_op(op.derived_from)
    return False


def is_get_tag_op(op: op_def.OpDef) -> bool:
    return op._gets_tag_by_name != None


def get_tag_name_from_tag_getter_op(op: op_def.OpDef) -> str:
    assert (
        op._gets_tag_by_name != None
    ), "Caller should verify that this is a tag getter op"
    return op._gets_tag_by_name  # type: ignore


def get_tag_name_from_mapped_tag_getter_op(op: op_def.OpDef) -> str:
    assert (
        op.derived_from != None
    ), "Caller should verify that this is a mapped tag getter op"
    return get_tag_name_from_tag_getter_op(op.derived_from)  # type: ignore
