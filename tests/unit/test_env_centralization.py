"""Phase D: env 加载集中化测试"""
import subprocess


class TestEnvCentralization:
    """验证 env 加载集中到 server.py，工具文件不再调用 load_dotenv"""

    def test_no_load_dotenv_in_tools(self):
        """工具文件不应包含 load_dotenv() 调用"""
        result = subprocess.run(
            ["grep", "-r", "load_dotenv", "tools/"],
            capture_output=True, text=True,
        )
        # 只允许注释中的引用，不允许实际调用
        lines = [l for l in result.stdout.splitlines() if l.strip() and not l.strip().startswith("#")]
        calls = [l for l in lines if "load_dotenv(" in l]
        assert len(calls) == 0, f"工具文件中存在 load_dotenv() 调用:\n{chr(10).join(calls)}"

    def test_server_py_has_load_dotenv(self):
        """server.py 应包含 load_dotenv 调用"""
        with open("api/server.py") as f:
            content = f.read()
        assert "load_dotenv" in content, "server.py 应包含 load_dotenv 调用"
