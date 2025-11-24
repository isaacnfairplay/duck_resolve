import json
from importlib import resources

import duckdb
from playwright.sync_api import sync_playwright

from resolver_engine.app import (
    RELATION_SAMPLE_OVERRIDES,
    _build_fact_inputs,
    _load_template,
)
from resolver_engine.core.resolver_base import RESOLVER_REGISTRY
from resolver_engine.core.schema import FACT_SCHEMAS, FactSchema, register_fact_schema


RELATION_FACT = "demo.user_relation"


def setup_function(function):
    FACT_SCHEMAS.clear()
    RESOLVER_REGISTRY.clear()
    RELATION_SAMPLE_OVERRIDES.clear()


def _build_index_html(sample_rows: list[dict[str, object]] | None = None) -> str:
    if sample_rows is not None:
        RELATION_SAMPLE_OVERRIDES[RELATION_FACT] = sample_rows

    register_fact_schema(FactSchema("demo.user_name", py_type=str, description="name"))
    register_fact_schema(
        FactSchema(RELATION_FACT, py_type=duckdb.DuckDBPyRelation, description="users as relation")
    )

    template = _load_template("index.html")
    html = template.substitute(inputs_html=_build_fact_inputs(), schema_count=len(FACT_SCHEMAS))

    script = resources.files("resolver_engine.web.assets").joinpath("app.js").read_text(encoding="utf-8")
    return html.replace('<script defer src="/assets/app.js"></script>', f"<script defer>{script}</script>")


def test_relation_builder_uses_sample_rows_and_syncs_json():
    html = _build_index_html(
        sample_rows=[
            {"id": 1, "name": "Ada"},
            {"id": 2, "name": "Grace"},
        ]
    )

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html, wait_until="domcontentloaded")
        page.wait_for_function("typeof hydrateTableFields === 'function'")
        page.evaluate("hydrateTableFields()")

        page.wait_for_selector('[data-input-type="table"] [data-preview]')
        preview_text = page.text_content('[data-input-type="table"] [data-preview]') or ""
        assert "Ada" in preview_text
        assert "Grace" in preview_text

        page.click('[data-input-type="table"] details summary')
        page.click('[data-input-type="table"] [data-fill-sample]')
        textarea_value = page.eval_on_selector('textarea[data-table-rows]', 'el => el.value.trim()')
        rows = json.loads(textarea_value)
        assert rows[0]["name"] == "Ada"
        assert rows[1]["id"] == 2

        browser.close()


def test_table_builder_adds_columns_and_rows_then_updates_preview():
    html = _build_index_html(sample_rows=[])

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html, wait_until="domcontentloaded")
        page.wait_for_function("typeof hydrateTableFields === 'function'")
        page.evaluate("hydrateTableFields()")

        page.fill('[data-input-type="table"] input[data-new-column]', "city")
        page.click('[data-input-type="table"] [data-add-column]')
        page.fill('[data-input-type="table"] input[data-row="0"][data-column="city"]', "Paris")
        page.wait_for_timeout(50)

        textarea_value = page.eval_on_selector('textarea[data-table-rows]', 'el => el.value.trim()')
        rows = json.loads(textarea_value)
        assert rows == [{"city": "Paris"}]

        preview_text = page.text_content('[data-input-type="table"] [data-preview]') or ""
        assert "Paris" in preview_text

        browser.close()


def test_table_builder_removes_rows_and_resets_preview_and_json():
    html = _build_index_html(
        sample_rows=[
            {"id": 1, "name": "Ada"},
        ]
    )

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html, wait_until="domcontentloaded")
        page.wait_for_function("typeof hydrateTableFields === 'function'")
        page.evaluate("hydrateTableFields()")

        page.wait_for_selector('[data-input-type="table"] [data-preview]')
        page.click('[data-input-type="table"] details summary')
        page.click('[data-input-type="table"] [data-fill-sample]')
        page.click('[data-input-type="table"] button[data-remove-row="0"]')

        preview_text = page.text_content('[data-input-type="table"] [data-preview]') or ""
        assert "No rows added yet." in preview_text

        textarea_value = page.eval_on_selector('textarea[data-table-rows]', 'el => el.value')
        assert textarea_value.strip() == ""

        browser.close()
