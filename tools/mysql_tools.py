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


@tool
def list_sql_tables() -> str:
    """Query all available tables in the database."""
    monitor.report_tool("数据库获取表名工具！")
    config = get_db_config()

    try:
        if not all([config["user"], config["password"], config["host"], config["port"], config["database"]]):
            return "错误: 数据库连接必要配置确实，查询失败！"
        with connect(**config) as conn:
            with conn.cursor() as cursor:
                cursor.execute("show tables;")
                tables = cursor.fetchall()
                if not tables:
                    return "数据库没有查询到任何表！"
                table_names = [table[0] for table in tables]
                return f"可用数据表:{','.join(table_names)}"
    except Error as e:
        return f"查询可用表名失败:{e}"


@tool
def get_table_data(table_name: str) -> str:
    """Query first 100 rows of a table, returned as CSV."""
    monitor.report_tool("数据库内容浏览工具", {"读取读取的表": table_name})
    config = get_db_config()
    if not all([config["user"], config["password"], config["host"], config["port"], config["database"]]):
        return "错误: 数据库配置缺失（检查账号，数据库名和密码必要配置！）"

    try:
        with connect(**config) as conn:
            with conn.cursor() as cursor:
                safe_table_name = table_name.replace("`", "").replace(";", "").split()[0]
                cursor.execute(f"select * from {safe_table_name} limit 100")
                if not cursor.description:
                    return f"数据表 {table_name}为空或者表名无效！"
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                result = [",".join(map(str, row)) for row in rows]
                header = ",".join(columns)
                return f"{header}\n" + "\n".join(result)
    except Error as e:
        return f"读取数据表：{table_name} 失败!{str(e)}"

@tool
def execute_sql_query(query: str) -> str:
    """Execute a custom SQL query."""
    monitor.report_tool("数据库查询工具")
    config = get_db_config()
    try:
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
                rows_t = [",".join(map(str, row)) for row in rows]
                header_str = ",".join(columns)
                return f"{header_str}\n" + "\n".join(rows_t)
    except Error as e:
        return f"执行自定义语句{query}失败，错误!{str(e)}"


