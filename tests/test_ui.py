from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from resolver_engine.app import create_app
from resolver_engine.core.schema import FACT_SCHEMAS, register_fact_schema, FactSchema
from resolver_engine.core.resolver_base import BaseResolver, ResolverSpec, ResolverOutput, RESOLVER_REGISTRY
from resolver_engine.core.state import LineContext


class DemoFacts:
    USER_NAME = "demo.user_name"
    USER_ID = "demo.user_id"


def setup_function(function):
    FACT_SCHEMAS.clear()
    RESOLVER_REGISTRY.clear()


def _setup_app_with_demo():
    register_fact_schema(FactSchema(DemoFacts.USER_NAME, py_type=str, description="name"))
    register_fact_schema(FactSchema(DemoFacts.USER_ID, py_type=int, description="id"))

    @BaseResolver.register(
        ResolverSpec(
            name="UserIdResolver",
            description="maps name to id",
            input_facts={DemoFacts.USER_NAME},
            output_facts={DemoFacts.USER_ID},
            impact={DemoFacts.USER_ID: 1.0},
        )
    )
    class UserIdResolver(BaseResolver):
        def run(self, ctx: LineContext):
            return [ResolverOutput(DemoFacts.USER_ID, len(ctx.state[DemoFacts.USER_NAME].value))]

    return create_app()


def test_index_page_renders_form_with_registered_facts():
    app = _setup_app_with_demo()
    client = TestClient(app)

    resp = client.get("/")
    assert resp.status_code == 200
    soup = BeautifulSoup(resp.text, "html.parser")
    inputs = {inp.get("name") for inp in soup.find_all("input")}
    assert DemoFacts.USER_NAME in inputs


def test_client_side_history_rendering(tmp_path):
    app = _setup_app_with_demo()
    client = TestClient(app)

    # simulate running report and rendering history script
    report_resp = client.get("/report.html?demo.user_name=Alice")
    assert report_resp.status_code == 200
    from resolver_engine.web.static.history import apply_history_script

    store = {}
    apply_history_script(store, report_resp.text)
    history = store.get("resolverHistory")
    assert history is not None
    assert "demo.user_name" in history


def test_transpose_tables_for_narrow_viewports():
    from resolver_engine.web.static.transpose import transpose_table_html

    html = """
    <table class='data-table'>
        <tr><th>A</th><th>B</th></tr>
        <tr><td>1</td><td>2</td></tr>
    </table>
    """
    transposed = transpose_table_html(html)
    soup = BeautifulSoup(transposed, "html.parser")
    table = soup.find("table")
    assert "transposed" in table.get("class")
    rows = table.find_all("tr")
    assert rows[0].find_all("td")[0].text.strip() == "A"
    assert rows[1].find_all("td")[0].text.strip() == "B"
