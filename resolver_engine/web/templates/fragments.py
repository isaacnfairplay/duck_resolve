from __future__ import annotations

import html
import json
from enum import StrEnum


class InputFragment(StrEnum):
    TEXT = (
        """
        <div class=\"field\" data-fact-id=\"{fact_id}\" data-input-type=\"text\">\
            <div class=\"field-label\">\
                <span class=\"pill\">Fact</span>\
                <label for=\"{fact_id}\">{fact_id}</label>\
            </div>\
            <p class=\"hint\">{hint} <span class=\"type\">({python_type})</span></p>\
            <input id=\"{fact_id}\" name=\"{fact_id}\" data-fact-id=\"{fact_id}\" placeholder=\"Enter {placeholder}\" />\
        </div>
        """
    )

    TABLE = (
        """
        <div class=\"field table-field\" data-fact-id=\"{fact_id}\" data-input-type=\"table\" data-sample='{sample_rows}'>\
            <div class=\"field-label\">\
                <span class=\"pill\">Relation</span>\
                <label for=\"{fact_id}\">{fact_id}</label>\
            </div>\
            <p class=\"hint\">{hint} <span class=\"type\">({python_type})</span></p>\
            <div class=\"table-input\">\
                <div class=\"table-builder\" data-table-builder>\
                    <div class=\"builder-header\">\
                        <div class=\"builder-columns\" data-column-list></div>\
                        <div class=\"builder-actions\">\
                            <input type=\"text\" placeholder=\"Add column name\" data-new-column />\
                            <button type=\"button\" class=\"ghost compact\" data-add-column>Add column</button>\
                            <button type=\"button\" class=\"ghost compact\" data-add-row>Add row</button>\
                        </div>\
                    </div>\
                    <div class=\"builder-grid\" data-table-editor></div>\
                </div>\
                <details class=\"json-fallback\">\
                    <summary>Paste JSON rows instead</summary>\
                    <p class=\"subtle\">Provide an array of objects. Any edits here will sync to the table builder.</p>\
                    <textarea id=\"{fact_id}-table\" name=\"{fact_id}\" data-table-rows placeholder=\"{placeholder}\"></textarea>\
                    <div class=\"table-actions\">\
                        <button type=\"button\" class=\"ghost compact\" data-fill-sample>Use sample rows</button>\
                        <span class=\"muted\">Rows will be converted into a DuckDB relation automatically.</span>\
                    </div>\
                </details>\
                <div class=\"table-preview\" data-preview>\
                    <p class=\"muted\">No rows added yet.</p>\
                </div>\
            </div>\
        </div>
        """
    )

    @staticmethod
    def serialize_sample_rows(rows: list[dict[str, object]]) -> str:
        return html.escape(json.dumps(rows), quote=True)
