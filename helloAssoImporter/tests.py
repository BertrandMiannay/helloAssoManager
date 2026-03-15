from django.test import TestCase
from unittest.mock import MagicMock, patch

from common.api.helloAssoApi import HelloAssoApi

SIMPLE_SCHEMA = {
    "type": "object",
    "required": ["data"],
    "properties": {
        "data": {"type": "array"}
    }
}


class CheckFormDataFormatTest(TestCase):

    def setUp(self):
        with patch.object(HelloAssoApi, '__init__', return_value=None):
            self.api = HelloAssoApi()

    def _mock_response(self, ok=True, json_data=None, raises_json=False, status_code=200, text=""):
        mock = MagicMock()
        mock.ok = ok
        mock.status_code = status_code
        mock.text = text
        if raises_json:
            mock.json.side_effect = ValueError("not JSON")
        else:
            mock.json.return_value = json_data
        return mock

    def test_returns_empty_on_http_error(self):
        raw = self._mock_response(ok=False, status_code=500, text="Internal Server Error")
        result = self.api.check_form_data_format(raw, SIMPLE_SCHEMA)
        self.assertEqual(result, [])

    def test_returns_empty_on_non_json_response(self):
        raw = self._mock_response(ok=True, raises_json=True)
        result = self.api.check_form_data_format(raw, SIMPLE_SCHEMA)
        self.assertEqual(result, [])

    def test_returns_empty_on_schema_validation_failure(self):
        raw = self._mock_response(ok=True, json_data={"wrong_key": []})
        result = self.api.check_form_data_format(raw, SIMPLE_SCHEMA)
        self.assertEqual(result, [])

    def test_returns_data_on_valid_response(self):
        data = [{"id": 1}, {"id": 2}]
        raw = self._mock_response(ok=True, json_data={"data": data})
        result = self.api.check_form_data_format(raw, SIMPLE_SCHEMA)
        self.assertEqual(result, data)

    def test_returns_empty_list_when_data_is_empty(self):
        raw = self._mock_response(ok=True, json_data={"data": []})
        result = self.api.check_form_data_format(raw, SIMPLE_SCHEMA)
        self.assertEqual(result, [])
