from app.utils.json_utils import parse_json_response


def test_valid_json():
    response = '{"name": "MindMate", "status": "working"}'

    result = parse_json_response(response)

    assert result["name"] == "MindMate"
    assert result["status"] == "working"

    print("Test 1 passed: Valid JSON parsed successfully!")


def test_json_with_markdown():
    response = """```json
{
    "name": "MindMate",
    "status": "working"
}
```"""

    result = parse_json_response(response)

    assert result["name"] == "MindMate"

    print("Test 2 passed: Markdown-wrapped JSON parsed successfully!")


def test_invalid_json():
    response = '{"name": "MindMate", "status": '

    try:
        parse_json_response(response)

    except ValueError:
        print("Test 3 passed: Invalid JSON handled correctly!")

    else:
        raise AssertionError("Invalid JSON was not detected.")


def test_non_object_json():
    response = '["MindMate", "working"]'

    try:
        parse_json_response(response)

    except ValueError:
        print("Test 4 passed: Non-object JSON rejected correctly!")

    else:
        raise AssertionError("A JSON array should have been rejected.")


if __name__ == "__main__":
    test_valid_json()
    test_json_with_markdown()
    test_invalid_json()
    test_non_object_json()

    print("\nAll JSON utility tests passed!")