import os
from dotenv import load_dotenv
from langchain_core.tools import tool
from mysql.connector import connect, Error

from api.monitor import monitor

load_dotenv()

# 定义加载配置的函数
def get_db_config():
    """
    获取数据库配置文件
    :return:
    """
    config = {
        "user": os.getenv("MYSQL_USER"),
        "password": os.getenv("MYSQL_PASSWORD"),
        "host": os.getenv("MYSQL_HOST"),
        "port": os.getenv("MYSQL_PORT"),
        "database": os.getenv("MYSQL_DATABASE"),
        "autocommit": True
    }
    return config



# 定义查看数据库表的工具
"""
【mysql.connector 核心 API 说明（针对 connect/cursor）】
1. connect 函数：
   - 作用：建立与 MySQL 数据库的连接，返回一个 Connection 对象；
   - 使用方式：connect(**config)，config 为包含 host/user/password 等的字典；
   - 上下文管理器：推荐用 with 语句（with connect(**config) as conn），自动关闭连接，避免资源泄露；
   - 核心属性/方法：
     - conn.cursor(): 创建游标对象（执行 SQL 的核心）；
     - conn.commit(): 提交事务（autocommit=True 时无需手动调用）；
     - conn.close(): 关闭连接（with 语句自动执行）。
2. cursor 游标对象：
   - 作用：执行 SQL 语句、获取查询结果的核心对象；
   - 创建方式：conn.cursor()；
   - 上下文管理器：with conn.cursor() as cursor，自动关闭游标；
   - 核心方法：
     - cursor.execute(sql): 执行单条 SQL 语句（如 SHOW TABLES/SELECT/INSERT）；
     - cursor.executemany(sql, params): 批量执行 SQL 语句（如批量插入）；
     - cursor.close(): 关闭游标（with 语句自动执行）。
3. 【重点】cursor 执行 DQL/DML 后的结果解析：
   ▶ DQL（数据查询语言，如 SELECT/SHOW）：查询类操作，返回「数据结果集」
     - 核心方法：
       1. cursor.fetchall(): 获取所有结果（返回列表，每个元素是元组，如 [(1, '张三'), (2, '李四')]）；
       2. cursor.fetchone(): 获取一条结果（返回元组，如 (1, '张三')，多次调用可遍历所有结果）；
       3. cursor.fetchmany(n): 获取前 n 条结果（返回列表）；
       4. cursor.column_names: 获取查询结果的列名（列表，如 ['id', 'name']）；
     - 解析技巧：将「列名 + 元组结果」转为字典（更易读），如 {'id': 1, 'name': '张三'}。
   ▶ DML（数据操作语言，如 INSERT/UPDATE/DELETE）：修改类操作，无「数据结果集」
     - 核心属性：
       1. cursor.rowcount: 返回受影响的行数（整数，如 INSERT 1 条返回 1，UPDATE 3 条返回 3）；
       2. cursor.lastrowid: INSERT 操作后，返回新增记录的自增 ID（仅对有自增主键的表有效）；
     - 解析技巧：通过 rowcount 判断操作是否生效，lastrowid 获取新增数据的主键。
4. 异常处理：
   - Error: mysql.connector 专属异常类，捕获所有数据库操作异常（如连接失败、SQL 语法错误）；
   - 推荐方式：try-except Error as e 捕获异常，返回友好提示。
"""

# 查询表名，让模型明确表名！
@tool
def list_sql_tables() -> str:
    """
    查询对应库中的所有可用表
    核心用途 agent需要查看数据库有那些表，为后续执行提供基础数据信息
    :return: 成功时返回,固定格式的表名，格式为："可用数据表:表1,表2,...."
    """
    monitor.report_tool("数据库获取表名工具！")
    config = get_db_config()

    try:
        if not all([config["user"], config["password"], config["host"], config["port"], config["database"]]):
            return "错误: 数据库连接必要配置确实，查询失败！"
        # 建立连接
        with connect(**config) as conn:
            with conn.cursor() as cursor:
                # 执行DQL查询数据库表
                cursor.execute("show tables;")
                # 获取返回结果
                # [(表名,),(表名,),()]
                tables = cursor.fetchall()
                if not tables:
                    return "数据库没有查询到任何表！"
                table_names = [table[0] for table in tables]
                return f"可用数据表:{','.join(table_names)}"
    except Error as e:
        return f"查询可用表名失败:{e}"


# 查询指定表名数据，拼接成csv格式
@tool
def get_table_data(table_name:str) -> str:
    """
    查询指定表名 table_name的数据，返回前100条数据，拼接成cvs格式！
    :param table_name: 要查询表名，表名需要通过get_sql_tables工具进行校验的！
    :return: 返回拼接结果的cvs数据！ 1.列使用 英文逗号分割 , 2. 行使用 换行符风格 \n 3. 第一行是列名  4. 第二行还是是数据
    """
    monitor.report_tool("数据库内容浏览工具",{"读取读取的表":table_name})
    config = get_db_config()
    if not all([config["user"], config["password"], config["host"], config["port"], config["database"]]):
        return "错误: 数据库配置缺失（检查账号，数据库名和密码必要配置！）"

    try:
        with connect(**config) as conn:
            with conn.cursor() as cursor:
                safe_table_name = table_name.replace("`","").replace(";","").split()[0]
                cursor.execute(f"select * from {safe_table_name} limit 100")
                if not cursor.description:
                    return f"数据表 {table_name}为空或者表名无效！"
                print(cursor.description)
                # 解析列名集合
                columns = [desc[0] for desc in cursor.description]
                print(f"处理后的列名集合：{columns}")
                # 解析数据
                rows = cursor.fetchall()
                # rows 示例结果： [(),(),()]
                result = [",".join(map(str,row)) for row in rows]
                header = ",".join(columns)
                return f"{header}\n" + "\n".join(result)
    except Error as e:
        return f"读取数据表：{table_name} 失败!{str(e)}"

@tool
def execute_sql_query(
        query:str
)-> str:
    """
    执行自定义sql语句，用于复杂或者关联查询！
    :param query: 自定义sql语句
    :return: 查询结果
    """
    monitor.report_tool("数据库查询工具")
    config = get_db_config()
    try:
        # 前置校验：确保核心数据库配置（账号、密码、库名）完整
        if not all([config.get("user"), config.get("password"), config.get("database")]):
            return "错误：数据库配置缺失（请检查账号、密码、数据库名）。"
        with connect(**config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                if not cursor.description:
                    return f"SQL 执行成功，受影响行数：{cursor.rowcount}"
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                if not rows:
                    return f"查询执行成功，无数据返回。涉及列名：{', '.join(columns)}"
                # 拼接结果
                rows_t = [",".join(map(str,row)) for row in rows ]
                header_str = ",".join(columns)
                return f"{header_str}\n" + "\n".join(rows_t)
    except Error as e:
        return f"执行自定义语句{query}失败，错误!{str(e)}"


