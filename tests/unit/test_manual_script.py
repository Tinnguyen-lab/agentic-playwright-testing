import pytest

from src.models.playwright_artifacts import ActionType, LocatorStrategy, PlaywrightAction, PlaywrightPlan
from src.services.manual_script import is_manual_script, validate_manual_script
from src.services.script_template import render_script


def _code():
    plan = PlaywrightPlan(actions=[
        PlaywrightAction(type=ActionType.GOTO, arg="https://example.test"),
        PlaywrightAction(type=ActionType.EXPECT_VISIBLE, strategy=LocatorStrategy.ROLE,
                         value="heading", role_name="Welcome"),
    ])
    return render_script(plan)


def test_manual_edit_is_tagged_and_keeps_real_assertion():
    edited = _code().replace('name="Welcome"', 'name="Home"')
    validated = validate_manual_script(edited)
    assert is_manual_script(validated)
    assert 'name="Home"' in validated
    assert validate_manual_script(validated) == validated


def test_manual_edit_cannot_remove_assertion_or_skip_run():
    code = _code()
    without_assertion = code.replace('expect(page.get_by_role("heading", name="Welcome")).to_be_visible()', 'pass')
    with pytest.raises(ValueError, match="assertion"):
        validate_manual_script(without_assertion)
    with pytest.raises(ValueError, match="run"):
        validate_manual_script(code.replace('    run()\n    print("PASSED")', '    print("PASSED")'))


def test_manual_edit_does_not_swallow_assertion_failure():
    code = _code().replace('        try:\n', '        try:\n', 1)
    code = code.replace('    print("PASSED")', '    print("PASSED")')
    code = code.replace('        finally:\n', '        except Exception:\n            pass\n        finally:\n')
    with pytest.raises(ValueError, match="bỏ qua lỗi"):
        validate_manual_script(code)
