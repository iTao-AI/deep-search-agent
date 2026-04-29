# RAGFlow 核心实战

## 一、环境准备与核心概念

### 1.1 什么是 RAGFlow？

RAGFlow 是字节跳动开源的 RAG（检索增强生成）框架，核心能力：

- 文档解析（支持 PDF/Word/Markdown 等 20+ 格式）

- 知识库管理（创建 / 删除 / 文档上传）

- 语义检索（精准匹配问题与文档片段）

- 聊天助手（绑定知识库，支持会话交互）

- 大模型集成（支持自定义大模型，生成带引用的答案）

### 1.1 本地部署RAGFlow

【部署文件】

### 1.2 环境配置

#### 1.2.1 配置 .env 文件

在项目根目录创建 .env 文件，填入 RAGFlow 服务信息：

<img src="assets/image-20260209110534502.png" alt="image-20260209110534502" style="zoom: 33%;" />

```python
RAGFLOW_API_URL=http://129.211.218.165  # 你的 RAGFlow 服务地址
RAGFLOW_API_KEY=ragflow-IyZjA4NzBlMDU2NDExZjE4NzJiNGE1NT  # 你的 API 密钥
```

#### 1.2.2 安装依赖

```python
# 核心依赖（SDK+环境变量+请求库）
pip install ragflow_sdk python-dotenv requests
# LangChain 集成依赖（适配 Agent 工具调用）
pip install langchain-core typing-extensions
```

#### 1.2.3 加载环境变量工具函数

创建 [config.py](http://config.py)，封装环境变量加载逻辑（后续所有功能复用）：

```python
import os
from dotenv import load_dotenv
from typing import Tuple, Optional

def _load_ragflow_env() -> Tuple[Optional[str], Optional[str]]:
    """
    加载 RAGFlow 环境变量（优先读取项目根目录 .env，兼容系统环境变量）
    返回值：(api_key, base_url) → 缺失则返回 None
    """
    # 优先加载项目根目录的 .env 文件
    current_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(current_dir, ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        load_dotenv()  # 无则加载系统环境变量

    api_key = os.getenv("RAGFLOW_API_KEY")
    base_url = os.getenv("RAGFLOW_API_URL")
    return api_key, base_url
```

## 二、核心功能入门

### 2.1 功能 1：创建知识库

所有文档需归属到「知识库」，先创建知识库再上传文档。

https://www.ragflow.io/docs/python_api_reference#update-dataset

#### 代码示例

```python
from ragflow_sdk import RAGFlow
from config import _load_ragflow_env

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

if __name__ == "__main__":
    create_knowledge_base(kb_name="法律文件知识库")
```

#### 核心知识点

- RAGFlow(api_key=, base_url=)：初始化客户端，是所有操作的入口
- 知识库 ID 需保存：后续上传文档、检索都依赖该 ID

### 2.2 功能 2：上传文档到知识库

支持本地文件（PDF/Word/TXT/Markdown 等）批量上传，自动解析切分。

#### 代码示例

```python
from ragflow_sdk import RAGFlow
from config import _load_ragflow_env
import os

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

# 测试调用
if __name__ == "__main__":
    # create_knowledge_base(kb_name="法律文件知识库")
    # 8a4cfe10106211f188755e0656eb9057
    result = upload_documents(kb_id="8a4cfe10106211f188755e0656eb9057",file_paths=["./人力面试18道必问真题.docx"])
    print(result)
```

## 三、项目实战功能

基于你提供的项目代码，补充「聊天助手、会话创建 / 删除」等实战功能，适配 Agent 工具调用场景。

### 3.1 功能 1：查询所有聊天助手及关联知识库

获取 RAGFlow 中已创建的所有聊天助手，解析每个助手绑定的知识库。

#### 代码示例（LangChain Tool 格式）

```python
from langchain_core.tools import tool
from typing import Annotated
from ragflow_sdk import RAGFlow
from config import _load_ragflow_env
from api.monitor import monitor  # 你的项目埋点工具

@tool
def get_assistant_list(
    dummy_arg: Annotated[str, "不需要输入参数，直接调用即可"] = "",
) -> str:
    """
    【工具功能】获取 RAGFlow 中所有聊天助手信息
    适用场景：Agent 需要确认当前有哪些可用助手，及每个助手绑定的知识库范围时调用
    返回：结构化字符串（助手名称+功能介绍+关联知识库）
    """
    # 埋点监控：记录工具调用行为
    monitor.report_tool("RAGFlow助手列表查询")
    api_key, base_url = _load_ragflow_env()

    # 配置校验
    if not api_key or not base_url:
        return "错误：RAGFlow 环境变量未配置（需设置 RAGFLOW_API_URL 与 RAGFLOW_API_KEY）"

    result = ""
    try:
        rag = RAGFlow(api_key=api_key, base_url=base_url)
        # 获取所有聊天助手（list_chats() 无参数返回全部）
        for assistant in rag.list_chats():
            # 解析助手关联的知识库名称（assistant.datasets 是知识库列表）
            kb_names = []
            if assistant.datasets and isinstance(assistant.datasets, list):
                for dataset in assistant.datasets:
                    if isinstance(dataset, dict) and "name" in dataset:
                        kb_names.append(dataset["name"])
            
            # 格式化知识库名称（无则显示"无"）
            kb_names_str = "、".join(kb_names) if kb_names else "无"
            # 结构化拼接助手信息
            result += f"助手名称：{assistant.name}； 功能介绍：{assistant.description}； 关联知识库：{kb_names_str}\n"

        # 移除末尾多余换行符
        return result.rstrip("\n") if result else "未找到任何聊天助手"
    except Exception as e:
        return f"获取助手列表失败：{str(e)}"

# 测试调用（Agent 可直接调用该工具）
if __name__ == "__main__":
    print(get_assistant_list())
```

#### 核心知识点

- rag.list_chats()：获取所有聊天助手，支持按名称筛选（rag.list_chats(name="助手名称")）

- assistant.datasets：每个助手绑定的知识库列表（字典格式，核心字段 name/id）

- 工具格式：适配 LangChain @tool 装饰器，返回字符串格式（便于 Agent 解析）

### 3.2 功能 2：临时会话提问（创建→提问→删除）

创建临时会话向指定助手提问，获取答案后自动删除会话（避免冗余会话堆积）。

#### 代码示例（LangChain Tool 格式）

```python
@tool
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
    monitor.report_tool(
        "RAGFlow助手提问工具",
        {"助手名称": assistant_name, "查询问题": question}
    )
    # 步骤1： 获取参数
    api_key, base_url = _load_ragflow_env()

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

            # 埋点监控：记录返回的答案
            monitor.report_tool(
                "RAGFlow助手回答记录",
                {"助手名称": assistant_name, "问题": question, "答案": full_answer}
            )
            
            # 自动删除临时会话（核心：避免会话堆积）
            if session and hasattr(session, "id"):
                assistant.delete_sessions(ids=[session.id])
            
            return full_answer if full_answer else "未获取到助手的回答"

        except Exception as e:
            return f"提问过程失败：{str(e)}"

    except Exception as e:
        return f"RAGFlow 操作失败：{str(e)}"

# 测试调用
if __name__ == "__main__":
    result = create_ask_delete(
        assistant_name="产品咨询助手",
        question="产品支持哪些操作系统？"
    )
    print(result)
```

#### 核心知识点

- 服务健康检查：base_url/health 接口，提前判断服务是否可用（避免无效调用）

- assistant.create_session()：创建助手专属会话（每个会话独立存储聊天历史）

- 流式响应：session.ask(stream=True) 逐段返回答案，适合大文本回答场景

- 会话删除：assistant.delete_sessions(ids=[session.id]) 批量删除会话（支持多个 ID）

### 3.3 功能 3：扩展功能（查询会话 / 批量删除会话）

#### 3.3.1 查询指定助手的所有会话

```python
@tool
def list_assistant_sessions(
    assistant_name: Annotated[str, "必填：聊天助手的名称"]
) -> str:
    """
    【工具功能】查询指定 RAGFlow 助手的所有会话列表
    适用场景：Agent 需要查看助手的历史会话时调用
    返回：会话 ID+名称+创建时间
    """
    monitor.report_tool("RAGFlow会话列表查询", {"助手名称": assistant_name})
    api_key, base_url = _load_ragflow_env()

    if not api_key or not base_url:
        return "错误：未配置 RAGFlow 环境变量"

    try:
        rag = RAGFlow(api_key=api_key, base_url=base_url)
        assistants = rag.list_chats(name=assistant_name)
        if not assistants:
            return f"错误：未找到助手「{assistant_name}」"
        
        assistant = assistants[0]
        # 获取助手的所有会话
        sessions = assistant.list_sessions()
        
        result = f"助手【{assistant_name}】的会话列表（共 {len(sessions)} 个）：\n"
        for s in sessions:
            result += f"会话ID：{s.id}； 会话名称：{s.name}； 创建时间：{s.created_at}\n"
        
        return result.rstrip("\n") if sessions else f"助手【{assistant_name}】无任何会话"
    except Exception as e:
        return f"查询会话失败：{str(e)}"
```

#### 3.3.2 批量删除助手的会话

```python
# 工具装饰器（标识该函数为Agent可调用的工具）
@tool
def batch_delete_sessions(
    assistant_name: Annotated[str, "必填：聊天助手的名称"],
    session_ids: Annotated[str, "必填：会话ID列表（逗号分隔，如：s1,s2,s3）"]
) -> str:
    """
    【工具功能】批量删除指定 RAGFlow 助手的会话
    适用场景：Agent 需要清理助手的历史会话时调用
    返回值：删除结果的文本提示（成功/失败信息）
    """
    # 上报工具调用日志（便于追踪Agent操作）
    monitor.report_tool(
        "RAGFlow批量删除会话",
        {"助手名称": assistant_name, "会话ID列表": session_ids}
    )
    
    # 加载RAGFlow的API密钥和基础地址（从环境变量读取）
    api_key, base_url = _load_ragflow_env()
    # 校验环境变量是否配置
    if not api_key or not base_url:
        return "错误：未配置 RAGFlow 环境变量"

    # 解析会话ID列表：按逗号分割，去除空值和首尾空格
    session_id_list = [s.strip() for s in session_ids.split(",") if s.strip()]
    # 校验解析后的会话ID是否有效
    if not session_id_list:
        return "错误：请传入有效的会话ID（逗号分隔）"

    try:
        # 初始化RAGFlow客户端
        rag = RAGFlow(api_key=api_key, base_url=base_url)
        
        # 根据助手名称查询对应的聊天助手实例
        assistants = rag.list_chats(name=assistant_name)
        if not assistants:
            return f"错误：未找到助手「{assistant_name}」"
        
        # 取第一个匹配的助手（名称唯一时直接使用）
        assistant = assistants[0]
        # 调用SDK批量删除指定ID的会话
        assistant.delete_sessions(ids=session_id_list)
        
        # 构造成功提示信息
        return f"成功删除助手【{assistant_name}】的 {len(session_id_list)} 个会话：{','.join(session_id_list)}"
    
    # 捕获所有异常，返回友好的错误提示
    except Exception as e:
        return f"批量删除会话失败：{str(e)}"
```

## 四、常见问题与注意事项

### 4.1 环境配置类问题

- 问题：未配置 RAGFlow 环境变量 → 检查 .env 文件是否存在，RAGFLOW_API_URL 和 RAGFLOW_API_KEY 是否填写正确

- 问题：连接 RAGFlow 服务失败 → 检查服务地址是否可达（浏览器访问 base_url/health 应返回 200），网络是否有防火墙限制

### 4.2 功能使用类问题

- 问题：未找到名为XXX的助手 → 确认助手名称拼写正确，或调用 get_assistant_list 工具查看所有可用助手

- 问题：检索不到相关内容 → 检查知识库是否上传文档，调整 top_k（增大）或 score_threshold（降低至 0.3）

- 问题：流式响应无内容 → 确认 ragflow_sdk 版本与服务端兼容（建议使用最新版本），检查 part.content 是否为 SDK 正确的字段名
