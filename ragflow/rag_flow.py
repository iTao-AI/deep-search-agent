from ragflow_sdk import RAGFlow
from ragflow.config import _load_ragflow_env
import os

from ragflow_sdk import RAGFlow
from config import _load_ragflow_env
from typing_extensions import Annotated

def create_knowledge_base(kb_name: str, description: str = "") -> str:
    """
    创建 RAGFlow 知识库
    参数：
        kb_name: 知识库名称（必填，唯一）
        description: 知识库描述（可选）
    返回：知识库 ID（后续文档上传/检索需用到）
    """
    api_key , base_url = _load_ragflow_env()

    if not api_key or not base_url:
        return "错误：没有配置ragflow的key和url"

    try:
        rag = RAGFlow(api_key, base_url)
        #  新版 0.23+ 名词：  知识库（KB）= 数据集（Dataset）  创建知识库 = create_dataset
        kb  = rag.create_dataset(name=kb_name,description="ragflow的知识库，导入中国刑法！！")
        print("知识库创建成功：id = " ,kb.id , kb)
    except Exception as e:
        print(e)

def upload_documents(kb_id: str, file_paths: list) -> str:
    """
    批量上传文档到指定RAGFlow知识库
    Args:
        kb_id: 知识库ID（用于定位要上传的目标数据集）
        file_paths: 待上传文件的本地路径列表
    Returns:
        str: 上传结果（成功/失败提示）
    """
    # 加载RAGFlow环境变量（API密钥和基础地址）
    api_key, base_url = _load_ragflow_env()
    if not api_key or not base_url:
        return "错误：未配置环境变量"

    # 校验文件是否存在，过滤有效文件
    valid_files = []
    for file_path in file_paths:
        if not os.path.exists(file_path):
            return f"错误：文件不存在 → {file_path}"
        valid_files.append(file_path)

    # 无有效文件时直接返回错误
    if not valid_files:
        return "错误：没有有效的上传文件"

    try:
        # 初始化RAGFlow客户端
        rag = RAGFlow(api_key=api_key, base_url=base_url)

        # 1. 根据知识库ID查询对应的数据集（分页参数：第1页，每页10条）
        datasets = rag.list_datasets(id=kb_id, page=1, page_size=10)
        if not datasets:
            return f"错误：未找到 ID 为 {kb_id} 的知识库"
        dataset = datasets[0]  # 取第一个匹配的数据集

        # 2. 准备上传文件数据：读取文件二进制内容，构造文档列表
        document_list = []
        for file_path in valid_files:
            file_name = os.path.basename(file_path)  # 提取文件名（不含路径）
            with open(file_path, "rb") as f:
                blob = f.read()  # 读取文件二进制流
                document_list.append({
                    "display_name": file_name,  # 展示名称
                    "name": file_name,          # 文件名
                    "blob": blob                # 文件二进制内容
                })

        # 3. 执行文档上传操作
        dataset.upload_documents(document_list)

        # 4. 构造并返回成功提示
        uploaded_names = [d["display_name"] for d in document_list]
        return f"成功上传 {len(uploaded_names)} 个文档：{', '.join(uploaded_names)}"

    except Exception as e:
        # 捕获所有异常，打印堆栈信息（便于调试），返回错误提示
        import traceback
        traceback.print_exc()
        return f"上传文档失败：{str(e)}"


def get_assistant_list(
        dummy_arg: Annotated[str, "不需要输入参数，直接调用即可"] = "",
):
    """
    获取RAGFlow平台中所有聊天助手的信息
    工具说明：
        用于查询当前RAGFlow中已创建的所有助手，包含助手名称、功能介绍、关联知识库
        适合Agent在不知道有哪些可用助手时调用
    参数：
        dummy_arg: 占位参数（LangChain工具要求至少一个参数），无需传值
    返回：
        str: 格式化的助手列表字符串，格式为「助手名称：xxx； 功能介绍：xxx； 知识库：xxx」
             若出错则返回错误提示信息
    """
    # 上报工具调用日志（自定义监控）
    # 加载RAGFlow配置
    api_key, base_url = _load_ragflow_env()

    # 校验环境变量配置
    if not api_key or not base_url:
        return "RAGFlow 环境变量未配置：请设置 RAGFLOW_API_URL 与 RAGFLOW_API_KEY。"

    # 校验RAGFlow SDK是否正常导入
    if RAGFlow is None:
        return "Error: 'ragflow_sdk' or 'ragflow' library is not installed."

    # 初始化返回结果字符串
    result = ""
    try:
        # 初始化RAGFlow客户端
        rag_object = RAGFlow(api_key=api_key, base_url=base_url)

        # 遍历所有聊天助手（list_chats()返回所有已创建的助手列表）
        for assistant in rag_object.list_chats():
            # 初始化当前助手关联的知识库名称列表
            kb_names = []
            # 校验助手关联的数据集（知识库）是否为有效列表
            if assistant.datasets and isinstance(assistant.datasets, list):
                # 遍历每个关联的数据集，提取名称
                for dataset in assistant.datasets:
                    if isinstance(dataset, dict) and "name" in dataset:
                        kb_names.append(dataset["name"])

            # 拼接知识库名称（用顿号分隔，无则显示"无"）
            kb_names_str = "、".join(kb_names) if kb_names else "无"
            # 拼接当前助手的信息到结果字符串
            result += (
                f"助手名称：{assistant.name}； 功能介绍：{assistant.description}； 知识库：{kb_names_str}\n"
            )

        # 移除结果末尾多余的换行符
        if result:
            result = result.rstrip("\n")
    except Exception as e:
        # 捕获异常并记录错误信息
        result = f"获取助手列表时出错: {str(e)}"

    return result


def create_ask_delete(
        assistant_name: Annotated[str, "必填：目标聊天助手的名称"],
        question: Annotated[str, "必填：要向助手提问的问题"],
) -> str:
    """
    【工具功能】向指定 RAGFlow 助手发起单次提问（临时会话，用完即删）
    适用场景：Agent 需单次查询某个助手，无需保留会话记录时调用
    特点：创建临时会话→流式接收答案→自动删除会话，无数据残留
    """
    # 埋点监控：记录提问信息
    api_key, base_url = _load_ragflow_env()

    # 步骤1：服务健康检查（提前确认服务可达）
    try:
        import requests
        test_response = requests.get(f"{base_url}/health", timeout=5)
        if test_response.status_code != 200:
            return f"错误：RAGFlow 服务健康检查失败（状态码：{test_response.status_code}）"
    except requests.RequestException as e:
        return f"错误：连接 RAGFlow 服务失败 → {str(e)}"

    # 步骤2：核心提问逻辑
    try:
        rag = RAGFlow(api_key=api_key, base_url=base_url)

        # 按名称筛选目标助手（取第一个匹配结果）
        assistants = rag.list_chats(name=assistant_name)
        if not assistants:
            return f"错误：未找到名为「{assistant_name}」的聊天助手"
        assistant = assistants[0]

        session = None  # 初始化会话对象（用于后续删除）
        try:
            # 创建临时会话（名称自定义，便于识别）
            session = assistant.create_session(name="temp_session_for_single_ask")

            # 流式提问（stream=True 逐段接收答案，避免等待全量结果）
            response_generator = session.ask(question, stream=True)

            # 收集流式响应（适配 SDK 格式：part.content 为单段答案内容）
            full_answer = ""
            for part in response_generator:
                if hasattr(part, "content") and part.content:
                    full_answer = part.content  # 覆盖更新为完整答案（流式最后一段是完整内容）
            # 自动删除临时会话（核心：避免会话堆积）
            if session and hasattr(session, "id"):
                assistant.delete_sessions(ids=[session.id])

            return full_answer if full_answer else "未获取到助手的回答"

        except Exception as e:
            return f"提问过程失败：{str(e)}"

    except Exception as e:
        return f"RAGFlow 操作失败：{str(e)}"


if __name__ == "__main__":
    # create_knowledge_base(kb_name="法律文件知识库")
    # 8a4cfe10106211f188755e0656eb9057
    #result = upload_documents(kb_id="8a4cfe10106211f188755e0656eb9057",file_paths=["./人力面试18道必问真题.docx"])
    #print(result)
    result =  get_assistant_list()
    print(result)

    re = create_ask_delete("查询公司信息","面试必问面试题")
    print(re)