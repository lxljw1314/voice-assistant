"""
语音助手后端主服务
"""
from fastapi import FastAPI, WebSocket, UploadFile, File, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import tempfile
from pathlib import Path
import subprocess
import asyncio

from asr_service import ASRService
from bailian_realtime_asr_service import BailianRealtimeASRService
from tts_service import TTSService
from qwen_tts_service import QwenTTSService
from llm_service import LLMService

app = FastAPI(title="语音助手 API")

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化服务
asr_service = ASRService()
# realtime_asr_service = RealtimeASRService()  # 旧版阿里云 NLS
# 百炼实时 ASR 服务在 WebSocket 端点内按需创建，不在此处初始化
tts_service = TTSService()
qwen_tts_service = QwenTTSService()
llm_service = LLMService()

# 静态文件 - 使用绝对路径
BASE_DIR = Path(__file__).parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
async def root():
    """返回前端页面"""
    return FileResponse(str(FRONTEND_DIR / "index.html"))


@app.post("/api/asr")
async def recognize_audio(file: UploadFile = File(...)):
    """
    语音识别接口
    接收音频文件，返回识别文本
    """
    try:
        # 读取音频文件
        audio_data = await file.read()
        
        print(f" 收到音频文件，大小: {len(audio_data)} bytes, 类型: {file.content_type}")
        
        # 一律用 ffmpeg 转码成 wav（浏览器录音实际是 webm/opus）
        print("🔄 正在转码为 wav (16kHz 单声道)...")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.input') as tmp:
            tmp.write(audio_data)
            input_path = tmp.name
        
        wav_path = input_path + '.wav'
        result = subprocess.run([
            'ffmpeg', '-y', '-i', input_path,
            '-ar', '16000',
            '-ac', '1',
            '-f', 'wav',
            wav_path
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ ffmpeg 转码失败: {result.stderr}")
            return JSONResponse({"success": False, "error": "音频转码失败"}, status_code=500)
        
        with open(wav_path, 'rb') as f:
            audio_data = f.read()
        
        print(f"✅ 转码完成，wav 大小: {len(audio_data)} bytes")
        os.unlink(input_path)
        os.unlink(wav_path)
        
        # 调用 ASR 服务
        text = await asr_service.recognize(audio_data, format='wav', sample_rate=16000)
        
        if not text:
            return JSONResponse({
                "success": False,
                "error": "语音识别结果为空"
            }, status_code=400)
        
        return JSONResponse({
            "success": True,
            "text": text
        })
        
    except Exception as e:
        print(f"ASR 接口错误: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.post("/api/chat")
async def chat(message: dict):
    """
    对话接口
    接收用户文本，返回 AI 回复
    """
    try:
        user_text = message.get("text", "")
        
        if not user_text:
            return JSONResponse({
                "success": False,
                "error": "消息为空"
            }, status_code=400)
        
        # 调用 LLM
        reply = await llm_service.chat(user_text)
        
        return JSONResponse({
            "success": True,
            "reply": reply
        })
        
    except Exception as e:
        print(f"Chat 接口错误: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.post("/api/tts")
async def synthesize_speech(request: dict):
    """
    语音合成接口
    接收文本，返回音频
    """
    try:
        text = request.get("text", "")
        voice = request.get("voice", "xiaoxiao")
        rate = request.get("rate", "+30%")
        
        if not text:
            return JSONResponse({
                "success": False,
                "error": "文本为空"
            }, status_code=400)
        
        # 调用 TTS 服务
        audio_data = await tts_service.synthesize(text, voice=voice, rate=rate)
        
        if not audio_data:
            return JSONResponse({
                "success": False,
                "error": "语音合成失败"
            }, status_code=500)
        
        # 保存到临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            f.write(audio_data)
            temp_path = f.name
        
        return FileResponse(
            temp_path,
            media_type="audio/mpeg",
            filename="speech.mp3"
        )
        
    except Exception as e:
        print(f"TTS 接口错误: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.post("/api/tts/bailian")
async def synthesize_speech_bailian(request: dict):
    """
    百炼语音合成接口
    接收文本，返回音频
    """
    try:
        text = request.get("text", "")
        voice = request.get("voice", "longanhuan_v3.6")
        
        if not text:
            return JSONResponse({
                "success": False,
                "error": "文本为空"
            }, status_code=400)
        
        # 调用百炼 TTS 服务（voice 已在初始化时设置）
        output_path = qwen_tts_service.synthesize(text)
        
        if not output_path or not os.path.exists(output_path):
            return JSONResponse({
                "success": False,
                "error": "语音合成失败"
            }, status_code=500)
        
        return FileResponse(
            output_path,
            media_type="audio/mpeg",
            filename="speech.mp3"
        )
        
    except Exception as e:
        print(f"百炼 TTS 接口错误: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.post("/api/process")
async def process_voice(file: UploadFile = File(...)):
    """
    完整处理流程：语音识别 → LLM 对话 → 语音合成
    """
    try:
        # 1. 语音识别
        audio_data = await file.read()
        user_text = await asr_service.recognize(audio_data)
        
        if not user_text:
            return JSONResponse({
                "success": False,
                "error": "语音识别失败"
            }, status_code=400)
        
        # 2. LLM 对话
        ai_reply = await llm_service.chat(user_text)
        
        # 3. 语音合成
        ai_audio = await tts_service.synthesize(ai_reply)
        
        # 保存音频到临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            f.write(ai_audio)
            temp_path = f.name
        
        return JSONResponse({
            "success": True,
            "user_text": user_text,
            "ai_reply": ai_reply,
            "audio_url": f"/api/audio/{os.path.basename(temp_path)}"
        })
        
    except Exception as e:
        print(f"处理流程错误: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.get("/api/audio/{filename}")
async def get_audio(filename: str):
    """获取生成的音频文件"""
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, filename)
    
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="audio/wav")
    else:
        return JSONResponse({
            "success": False,
            "error": "音频文件不存在"
        }, status_code=404)


@app.post("/api/clear")
async def clear_history():
    """清空对话历史"""
    llm_service.clear_history()
    return JSONResponse({
        "success": True,
        "message": "对话历史已清空"
    })


@app.websocket("/ws/realtime-asr")
async def realtime_asr_websocket(websocket: WebSocket):
    """实时语音识别 WebSocket 端点 (百炼 qwen3-asr-flash-realtime)"""
    await websocket.accept()

    # 使用 asyncio.Queue 在 ASR 线程和 FastAPI 异步任务之间传递消息
    result_queue = asyncio.Queue()
    loop = asyncio.get_event_loop()

    def asr_callback(text, is_final):
        # 这个回调在 ASR 的 WebSocket 线程中执行
        # 将结果放入队列
        asyncio.run_coroutine_threadsafe(
            result_queue.put({"type": "result", "text": text, "is_final": is_final}),
            loop
        )

    # 创建百炼实时 ASR 服务实例
    asr = BailianRealtimeASRService()

    # 启动识别，传入回调
    if not asr.start(result_callback=asr_callback):
        await websocket.send_json({
            "type": "error",
            "message": "启动百炼实时识别失败"
        })
        await websocket.close()
        return

    await websocket.send_json({
        "type": "status",
        "message": "百炼实时识别已启动 (qwen3-asr-flash-realtime)"
    })

    send_task = None
    try:
        # 启动一个后台任务来监听队列并发送给前端
        async def send_results():
            while True:
                msg = await result_queue.get()
                print(f"📤 发送给前端: {msg}")
                await websocket.send_json(msg)

        send_task = asyncio.create_task(send_results())

        # 主循环接收前端发来的音频
        audio_buffer = bytearray()
        while True:
            data = await websocket.receive_bytes()
            
            # 累积音频缓冲区，每 100ms 发送一次（约 3200 bytes）
            audio_buffer.extend(data)
            if len(audio_buffer) >= 3200:
                chunk = bytes(audio_buffer[:3200])
                audio_buffer = audio_buffer[3200:]
                asr.send_audio(chunk)

    except WebSocketDisconnect:
        print("客户端断开连接")
    except Exception as e:
        print(f"WebSocket 错误: {e}")
    finally:
        if send_task:
            send_task.cancel()
        
        # 停止识别
        final_result = asr.stop()
        
        # 发送最终结果（如果连接还开着）
        try:
            await websocket.send_json({
                "type": "result",
                "text": final_result,
                "is_final": True
            })
        except:
            pass  # 连接已关闭，忽略
        
        try:
            await websocket.close()
        except:
            pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
