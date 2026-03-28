
import { GoogleGenAI } from "@google/genai";

export const getGeminiResponse = async (prompt: string, history: {role: string, parts: any[]}[]) => {
  try {
    // 每次调用时初始化，确保使用最新的环境配置
    const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
    
    const response = await ai.models.generateContent({
      model: "gemini-3-flash-preview",
      contents: [
        ...history.map(h => ({ role: h.role, parts: h.parts })),
        { role: "user", parts: [{ text: prompt }] }
      ],
      config: {
        systemInstruction: "你是一个专业的宠物健康顾问，名字叫‘AI 问诊助手’。你需要根据用户提供的宠物（如金毛巴迪）的监测数据（心率、步数、行为）提供健康建议。语气要亲切、专业。如果用户询问症状，给出初步分析并建议是否需要看兽医。回答要简短精炼。",
      }
    });

    return response.text || "抱歉，我暂时无法回答。";
  } catch (error) {
    console.error("Gemini API Error:", error);
    return "抱歉，我现在无法处理您的请求。请稍后再试。";
  }
};
