import yaml
from pathlib import Path


def load_prompt(file_path):
    """Load a YAML prompt configuration file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


root_path = Path(__file__).parent.parent
prompt_file_path = root_path / "prompt" / "prompts.yml"
prompt_config_content = load_prompt(prompt_file_path)

main_agent_config = prompt_config_content["main_agent"]
sub_agent_configs = prompt_config_content["sub_agents"]
