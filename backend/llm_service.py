"""
LLM 对话服务
"""
from openai import OpenAI
from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL


class LLMService:
    def __init__(self):
        self.client = OpenAI(
            api_key=LLM_API_KEY,
            base_url=LLM_BASE_URL
        )
        self.model = LLM_MODEL
        self.conversation_history = []
        print(f"✅ LLM 初始化: model={LLM_MODEL}, base_url={LLM_BASE_URL}")
        
    async def chat(self, user_message: str) -> str:
        """
        与 LLM 对话
        :param user_message: 用户输入
        :return: AI 回复
        """
        try:
            # 添加用户消息到历史
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })
            
            # 调用 LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history
            )
            
            # 获取回复
            reply = response.choices[0].message.content
            
            # 添加 AI 回复到历史
            self.conversation_history.append({
                "role": "assistant",
                "content": reply
            })
            
            # 保留最近 10 轮对话
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            return reply
            
        except Exception as e:
            print(f"LLM 对话错误: {e}")
            return "抱歉，我遇到了一些问题，请稍后再试。"
    
    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []
