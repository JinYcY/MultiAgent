from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
import asyncio
import uvicorn
import os
from pathlib import Path

# ==========知识点1：FastAPI基础初始化==========
# 创建FastAPI应用实例，title设置接口文档标题，自动生成/docs接口文档页面
app = FastAPI(title="min demo fastapi")

# ==========知识点6：静态文件挂载 StaticFiles==========
# 挂载静态资源目录，访问 /static/xxx 会读取对应文件夹文件，这里仅演示挂载，文件夹自行新建
app.mount("/static", StaticFiles(directory="static"), name="static")

app.mount("/test", StaticFiles(directory="test"), name="static")

# ==========知识点8：生命周期 startup 启动事件==========
# @app.on_event("startup") 绑定服务启动事件；字符串"startup"代表：服务启动完成、接收请求前执行
@app.on_event("startup")
async def startup_init():
    # 获取当前正在运行的asyncio事件循环
    running_loop = asyncio.get_running_loop()
    print(f"【服务启动】获取事件循环: {running_loop}")
    # 业务作用：把循环保存，后续可以用这个循环创建后台异步任务


INDEX_PATH = Path(__file__).parent / "static" / "index.html"

# ==========知识点2：路由装饰器 GET/POST==========
# GET路由，访问根路径 /，返回HTML页面
@app.get("/", response_class=HTMLResponse)
async def root():
    # 返回简单html文本
    if INDEX_PATH.exists():
        # Path对象才有read_text方法
        return INDEX_PATH.read_text(encoding="utf-8")
    return "<h1>FastAPI极简Demo</h1>"

# ==========知识点3：Pydantic BaseModel 请求体模型==========
# 定义请求体结构，FastAPI自动校验json，自动生成文档
class TaskReq(BaseModel):
    msg: str

# POST路由，接收json请求体
@app.post("/api/task")
async def run_task(req: TaskReq):
    # ==========知识点9：asyncio.create_task 后台异步任务==========
    # 作用：将协程丢后台运行，接口立刻返回，不等待后台任务结束
    async def background_job(content: str):
        await asyncio.sleep(3)
        print(f"后台任务完成：{content}")
    asyncio.create_task(background_job(req.msg))
    return {"status": "任务已提交", "receive_msg": req.msg}

# ==========知识点10：WebSocket长连接==========
# websocket路由，路径参数ws_id
@app.websocket("/ws/{ws_id}")
async def ws_endpoint(websocket: WebSocket, ws_id: str):
    # 接受客户端websocket连接
    await websocket.accept()
    try:
        # 循环持续接收前端消息
        while True:
            # 接收前端文本消息
            data = await websocket.receive_text()
            # 向前端发送json消息
            await websocket.send_json({"ws_id": ws_id, "msg": f"服务端收到:{data}"})
    except WebSocketDisconnect:
        # 捕获客户端断开连接异常，做清理
        print(f"客户端 {ws_id} 断开websocket")

@app.on_event("shutdown")
async def shutdown_init():

    print(f"shutdown_init 异步函数运行成功")


# ==========知识点12：uvicorn运行服务==========
# 程序入口，直接运行此文件就启动uvicorn服务
if __name__ == "__main__":
    # host=0.0.0.0允许外部访问；port端口；reload=False关闭热重载（生产）
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)
