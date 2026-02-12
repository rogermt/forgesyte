from server.app.pipeline_models.pipeline_graph_models import Pipeline, PipelineNode
from server.app.services.dag_pipeline_service import DagPipelineService


class DummyPlugin:
    def run_tool(self, tool_id, payload):
        return {"message": "hello world", **payload}


class DummyPluginManager:
    def get_plugin(self, plugin_id):
        return DummyPlugin()


class DummyRegistry:
    def get_pipeline(self, pipeline_id):
        return Pipeline(
            id="hello_world",
            name="Hello World Pipeline",
            nodes=[PipelineNode(id="echo_node", plugin_id="utils", tool_id="echo")],
            edges=[],
            entry_nodes=["echo_node"],
            output_nodes=["echo_node"],
        )


def test_hello_world_pipeline():
    registry = DummyRegistry()
    pm = DummyPluginManager()
    dag = DagPipelineService(registry, pm)

    result = dag.run_pipeline("hello_world", {"foo": "bar"})
    assert result["message"] == "hello world"
    assert result["foo"] == "bar"
