import yaml
from pathlib import Path

# 定义加载提示词yaml方法
def load_prompt(file_path):
    """
    加载yaml文件提示词
    :param file_path: 完成地址
    :return: 返回提示词对应dict数据
    """
    with open(file_path, "r" , encoding="utf-8") as f:
        return yaml.safe_load(f)

# 解析文件位置
root_path = Path(__file__).parent.parent

prompt_file_path = root_path / "prompt" / "prompts.yml"

prompt_config_content = load_prompt(prompt_file_path)

main_agent_config = prompt_config_content["main_agent"]
sub_agent_configs = prompt_config_content["sub_agents"]

print(main_agent_config)
print(sub_agent_configs)