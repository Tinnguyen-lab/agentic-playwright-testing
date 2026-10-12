from src.agents.test_design_agent import SYSTEM_PROMPT
from src.services.test_design_policy import TEST_DESIGN_RUNTIME_POLICY, load_test_design_policy


def test_runtime_policy_is_loaded_from_the_project_skill():
    policy = load_test_design_policy()
    assert "Analyse before generating" in policy
    assert policy == TEST_DESIGN_RUNTIME_POLICY


def test_test_design_system_prompt_includes_runtime_skill_policy():
    assert "CHÍNH SÁCH RUNTIME TỪ SKILL" in SYSTEM_PROMPT
    assert "coverage map" in SYSTEM_PROMPT
