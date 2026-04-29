# RAGFlow

## 第一章 RAGFlow的介绍

### 1 .1 RAGFlow的概念

​	RAGFlow是一种结合了检索增强生成(Retrieval-Augmented Generation, RAG)技术的工作流程框架。它主要用于构建和优化基于大型语言模型(LLM)的知识密集型应用系统。

RAGFlow的核心概念包括：

- **检索增强生成(RAG)**: 这是一种将外部知识库检索与生成式AI模型相结合的技术。通过先检索相关信息，再让模型基于这些信息生成回答，从而提高回答的准确性和可靠性。

- **工作流程化**: RAGFlow将RAG的各个环节(文档处理、索引构建、检索、生成等)组织成可配置的工作流程，使开发者能够灵活定制和优化每个环节。

- **模块化设计**: 包含文档加载器、文档处理器、嵌入模型、向量存储、检索器和生成器等模块，每个模块可以独立配置和替换。

- **可视化与监控**: 提供工作流程的可视化界面和性能监控工具，帮助开发者理解和优化系统。

- **评估与优化**: 内置评估框架，可以对RAG系统的各个环节进行评估和优化。

  RAGFlow的应用场景包括企业知识库问答、文档智能搜索、个性化推荐系统等需要结合外部知识的AI应用。

### 1.2 使用RAGFlow的意义

​	在之前的大模型开发中，大家一定了解过RAG的概念，以及尝试了使用向量数据库作为知识库的使用。当进行一些深入思考的时候可能会发现，向量数据库的构建和使用并不是很轻松简单，尤其是在处理多种文档、多种数据类型的时候，我们可能需要分门别类地根据文档类型去编写多种不同的提取脚本，根据不同的文档内容进行划分、清洗、多模态分析。这无疑是一个很复杂且耗费精力的过程。

​	在企业的知识库开发中，往往都是会有很多非规整格式化的文档需要导入知识库中，比如Excel文件、doc文件、pdf文件、ppt文件等多种领域多种内容的文档。我们亟需一个统一的方案去解决这个化散为整的过程，RAGFlow提供了一套简单高效的解决方案！

​	通过使用RAGFlow，可以自由创建多种独立的知识库空间，并可以通过可视化界面的方式去上传、删除知识库中的知识文档。这些知识问答可以是任何常见的文件类型，RAGFlow会自动分析其内容，并自动解析进行存储。当知识库创建完毕后，可以创建知识助手去掌握不同的知识库，打造企业级的行业知识专家。可以通过与知识助手展开会话的方式进行知识库的查询。

## 第二章 RAGFlow的安装及配置

​	RAGFlow需要安装在docker中，我们这里可以租用云服务器，也可以在本地的虚拟机上去部署，但是RAGFlow的配置要求为：

- CPU：至少4核心 (x86架构)

- 内存：至少16GB RAM

- 存储空间：至少50GB磁盘空间

  虽然配置略低于此最低要求也是可以运行的，但是可能会在后续的使用中出现问题。此教案编写的期间进行过相关的测试，当硬件配置低于要求的时候，响应速度相比满足其要求的服务器会低很多。此外，之后还需要拉取RAGFlow的文件大约7.6GB，教室的网络资源会很吃力。所以推荐去租用云服务器进行学习使用。我们可以选择租用一个腾讯云服务器。

### 2.1 租用腾讯云服务器

点击下方链接进入购买页面，选择竞价实例

​	https://buy.cloud.tencent.com/cvm?tab=custom&step=1&devPayMode=spotpaid&regionId=4&wanIp=0&templateCreateMode=createLt&isBackup=false&backupDiskType=ALL&backupDiskCustomizeValue=&backupQuotaSegment=1&backupQuota=1

![image-20250619102651808](./RAGFlow.assets/image-20250619102651808.png)

​	地域随便选一个，然后选4核16GB的。这里建议同学按小组为单位，一组选择一个区的，不要全班都集中在某个区。因为我们使用的是竞价实例，只要有人租长期的服务器就有可能把你的服务器踢掉，为了避免全班被某些大客户一锅端，我们要分散开去租用。当然，实例被竞价释放也是有解决办法的，后续会去讲。

![image-20250619102817297](./RAGFlow.assets/image-20250619102817297.png)

镜像选择CentOS核Ubuntu都可以，文档里使用了Ubuntu。选择后点击下一步。

![image-20250619103252815](./RAGFlow.assets/image-20250619103252815.png)

![image-20250619103307728](./RAGFlow.assets/image-20250619103307728.png)

拉满带宽上限，新建安全组，把常用的端口都开启

![image-20250619103457368](./RAGFlow.assets/image-20250619103457368.png)

命名实例，设置密码，进行下一步

![image-20250619103548187](./RAGFlow.assets/image-20250619103548187.png)

开通

![image-20250619103615844](./RAGFlow.assets/image-20250619103615844.png)

创建好了，通过这个公网IP，端口使用22，账号ubuntu，密码使用你设置的密码。使用你的远程连接工具连接即可

![image-20250619103844777](./RAGFlow.assets/image-20250619103844777.png)

### 2.2 安装docker

​	RAGFlow需要运行在docker上，我们安装一下吧

```bash
#更新软件包
sudo apt update
sudo apt upgrade -y
#安装docker依赖
sudo apt-get install ca-certificates curl gnupg lsb-release
#添加Docker官方GPG密钥
curl -fsSL http://mirrors.aliyun.com/docker-ce/linux/ubuntu/gpg | sudo apt-key add -
#添加Docker软件源（输入后根据提示按Enter）
sudo add-apt-repository "deb [arch=amd64] http://mirrors.aliyun.com/docker-ce/linux/ubuntu $(lsb_release -cs) stable"
#安装docker
sudo apt-get install docker-ce docker-ce-cli containerd.io
```

如果安装docker 的时候出现这个界面，直接回车就可以！	![001](RAGFlow.assets\001.png)

安装完毕，启动docker，并查看状态

```bash
sudo systemctl start docker
sudo systemctl status docker
```

​	如图所示即为启动成功

![](./RAGFlow.assets/image-20250619104758997.png)

### 2.3 安装RAGFlow

```bash
sudo vim /etc/sysctl.conf
```

添加如下参数

```bash
vm.max_map_count = 262144
```

![image-20250619105104648](./RAGFlow.assets/image-20250619105104648.png)

执行命令重新加载内核参数

```bash
sysctl -p
```

配置成功

![image-20250619105258790](./RAGFlow.assets/image-20250619105258790.png)

```bash
sudo mkdir /opt/mirrors
cd /opt/mirrors
```

在此目录下上传这些文件

![image-20250619110235982](./RAGFlow.assets/image-20250619110235982.png)

首先要使用root用户

```bash
sudo passwd root
```

自己设置一下密码，然后

```bash
su root
```

输入密码登陆root

腾讯云对FTP上传文件有一些限制，我们需要进行更改才能上传文件

![image-20250619112542899](./RAGFlow.assets/image-20250619112542899.png)

![image-20250619112558136](./RAGFlow.assets/image-20250619112558136.png)

![image-20250619112615974](./RAGFlow.assets/image-20250619112615974.png)

![image-20250619112659812](./RAGFlow.assets/image-20250619112659812.png)

然后回到终端，vim /etc/ssh/sshd_config

这两项去掉注释符号，变成yes

![image-20250619112847346](./RAGFlow.assets/image-20250619112847346.png)

```bash
service sshd restart
```

然后修改一下用户身份，登陆默认使用root

![image-20250619113345673](./RAGFlow.assets/image-20250619113345673.png)

重新登陆即可上传文件了

上传完成后，解压

```bash
unzip ragflow-main.zip -d /opt/
```

导入镜像

```》bash
docker load -i elasticsearch.tar
docker load -i infinity.tar
docker load -i minio.tar
docker load -i mysql.tar 
docker load -i valkey.tar
```

> infinity : **字节的开源高分辨率图像生成模型**
>
> valkey: **是一个高性能的开源键值存储系统，主要用于缓存、消息队列和主数据库等多种工作负载**

使用查看镜像

```bash
docker images
```

导入成功

![image-20250619115614270](./RAGFlow.assets/image-20250619115614270.png)

现在只差最后一步就可以安装完成，修改一个镜像的标签，我这里提供的镜像标签与配置文件中的不一样，如果不修改会进行漫长的下载，所以我们操作一下

进入该配置文件

```bash
 vim /opt/ragflow-main/docker/docker-compose-base.yml 
```

将es01的image替换为

```bash
image: docker.elastic.co/elasticsearch/elasticsearch:8.11.3
```

![image-20250619120100518](./RAGFlow.assets/image-20250619120100518.png)

```bash
# 在这个目录下/opt/ragflow-main/docker 执行vim 命令
vim .env
```

删除这里华为云的注释符 105行

![image-20250619134514861](./RAGFlow.assets/image-20250619134514861.png)

现在配置全部搞定，在docker目录下开始启动

![image-20250619134637133](./RAGFlow.assets/image-20250619134637133.png)

```bash
docker compose up -d
```

如果提示链接超时，修改加速器执行命令

vim /etc/docker/daemon.json

```json
{
  "registry-mirrors" : [
    "https://docker.m.daocloud.io",
    "https://mirror.aliyuncs.com"
  ],
  "insecure-registries" : [
    "docker.mirrors.ustc.edu.cn"
  ],
  "debug": true,
  "experimental": false
}
```

等待拉取

![image-20250619134716042](./RAGFlow.assets/image-20250619134716042.png)

安装完毕

![image-20250619135921801](./RAGFlow.assets/image-20250619135921801.png)

### 2.3 配置RAGFlow知识库

直接复制公网ip，到浏览器进行访问即可进入页面

![image-20250619135912891](./RAGFlow.assets/image-20250619135912891.png)

先注册一个账号

![image-20250619140313102](./RAGFlow.assets/image-20250619140313102.png)

![image-20250619140339250](./RAGFlow.assets/image-20250619140339250.png)

然后登陆

![image-20250619140358858](./RAGFlow.assets/image-20250619140358858.png)

设置一下中文

![image-20250619140428425](./RAGFlow.assets/image-20250619140428425.png)

去开通自己的阿里百炼平台API-KEY

[大模型服务平台百炼控制台](https://bailian.console.aliyun.com/?utm_content=se_1021227512&tab=model#/api-key)

复制自己的API-KEY

![image-20250619140855488](./RAGFlow.assets/image-20250619140855488.png)

点击模型供应商，下滑寻找Tongyi-Qianwen

![image-20250619140605716](./RAGFlow.assets/image-20250619140605716.png)

点击添加模型，然后把自己的API-KEY粘贴进去

设置默认模型

![image-20250619141933424](./RAGFlow.assets/image-20250619141933424.png)

设置自己的模型，千问系列的优点是模型十分全面，大语言模型、多模态模型、重排模型、向量化模型都可以使用，只需要配置其API就可以完成大多数任务需求。

![image-20250619142044389](./RAGFlow.assets/image-20250619142044389.png)

设置完成后，就需要开始配置自己的知识库了。这里准备好了一些测试使用的知识库文件，大家可以直接使用，也可以根据自己的兴趣去寻找收集其他知识文档。

![image-20250619144708406](./RAGFlow.assets/image-20250619144708406.png)

创建知识库

![image-20250619144741192](./RAGFlow.assets/image-20250619144741192.png)

划到最下面点击保存即创建成功

![image-20250619144812672](./RAGFlow.assets/image-20250619144812672.png)

新增文件，把准备好的文件进行上传，**上传后务必点击解析进行文档解析！**这里的pdf是调用多模态模型进行分析，可能会耗时比较长，请耐心等待

![image-20250619144958440](./RAGFlow.assets/image-20250619144958440.png)

解析成功，如果解析失败了就一个一个再重新解析。

![image-20250619145801880](./RAGFlow.assets/image-20250619145801880.png)

创建知识助手

**注意，这里的助理描述一定要详细填写，否则在后续调用API的时候会出现无法灵活处理问题的情况**

![image-20250619150034877](./RAGFlow.assets/image-20250619150034877.png)

​	这里创建完成后新建一个对话，做出一个简单的相关问题提问，回答中会给出每一条信息的来源标识，并且会给出源文件。可见，其并不是靠着自己的强大模型能力完成的，而是根据知识库的信息检索输出的。

![image-20250619150230019](./RAGFlow.assets/image-20250619150230019.png)

![image-20250619150315666](./RAGFlow.assets/image-20250619150315666.png)

之后将这几种数据文件全部新建知识库，并且创建知识助手。可以让一个助手掌握一个或多个知识库，根据具体情况灵活调整即可。

依次创建成功

![image-20250619152749961](./RAGFlow.assets/image-20250619152749961.png)

创建出助手进行测试

![image-20250619153004516](./RAGFlow.assets/image-20250619153004516.png)

在完成了上述知识助手的创建之后，我们还需要去创建一个**通用知识助手**来完成一些不依靠知识库的通用知识处理。

```
无法被用来解决任何问题的知识助手，永远不要使用该助手
```

![image-20250620105319201](./RAGFlow.assets/image-20250620105319201.png)

这里建议给通用知识助手的模型选择一个性能比较好的，否则可能产生幻觉效果

```
无论用户如何提问，都要向用户回答“我是一个通用知识助手，无法根据解答你的任何专业问题”，之后用50字以内简答用户的问题
```

![image-20250620105521620](./RAGFlow.assets/image-20250620105521620.png)

删除关键字

![image-20250620105701633](./RAGFlow.assets/image-20250620105701633.png)

## 第三章 RAGFlow的安装及配置

​	RAGFlow需要安