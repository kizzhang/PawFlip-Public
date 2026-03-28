import React, { useState, useEffect } from 'react';
import api from '../services/api';

const ApiTestView: React.FC = () => {
  const [results, setResults] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const log = (message: string, type: 'info' | 'success' | 'error' = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    const prefix = type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️';
    setResults(prev => [...prev, `[${timestamp}] ${prefix} ${message}`]);
    console.log(`[ApiTest] ${message}`);
  };

  const clearResults = () => {
    setResults([]);
  };

  const testBasicConnection = async () => {
    log('开始测试基础连接...');
    try {
      const response = await fetch('http://localhost:8003/health');
      if (response.ok) {
        const data = await response.json();
        log(`健康检查成功: ${JSON.stringify(data)}`, 'success');
      } else {
        log(`健康检查失败: HTTP ${response.status}`, 'error');
      }
    } catch (error: any) {
      log(`连接错误: ${error.message}`, 'error');
    }
  };

  const testRegistration = async () => {
    log('开始测试注册功能...');
    setIsLoading(true);
    
    const testData = {
      email: `test_${Date.now()}@example.com`,
      password: '123456',
      username: '测试用户'
    };

    try {
      log(`测试数据: ${JSON.stringify(testData, null, 2)}`);
      log('调用注册 API...');
      
      const result = await api.auth.register(
        testData.email,
        testData.password,
        testData.username
      );
      
      log(`注册成功: ${JSON.stringify(result, null, 2)}`, 'success');
      log(`令牌已保存: ${api.auth.isLoggedIn() ? '是' : '否'}`, 'success');
      
    } catch (error: any) {
      log(`注册失败: ${error.message}`, 'error');
      log(`错误类型: ${error.constructor.name}`, 'error');
      if (error.stack) {
        log(`错误堆栈: ${error.stack}`, 'error');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const testApiService = async () => {
    log('开始测试 API 服务...');
    try {
      log(`API 对象: ${JSON.stringify(Object.keys(api))}`);
      log(`认证 API: ${JSON.stringify(Object.keys(api.auth))}`);
      log('API 服务测试完成', 'success');
    } catch (error: any) {
      log(`API 服务测试失败: ${error.message}`, 'error');
    }
  };

  useEffect(() => {
    // 页面加载时自动运行基础测试
    setTimeout(() => {
      testApiService();
      testBasicConnection();
    }, 1000);
  }, []);

  return (
    <div className="flex flex-col h-full bg-[#f6f8f8] px-8 pt-12">
      <header className="mb-10">
        <h1 className="text-3xl font-bold text-[#111814] mb-2">API 连接测试</h1>
        <p className="text-gray-500 font-medium">测试前端与后端 API 的连接</p>
      </header>

      <div className="flex flex-wrap gap-4 mb-6">
        <button 
          onClick={testBasicConnection}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
        >
          测试基础连接
        </button>
        
        <button 
          onClick={testApiService}
          className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
        >
          测试 API 服务
        </button>
        
        <button 
          onClick={testRegistration}
          disabled={isLoading}
          className="px-4 py-2 bg-[#31d2e8] text-white rounded-lg hover:bg-[#2bb8cc] transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {isLoading && <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>}
          测试注册功能
        </button>
        
        <button 
          onClick={clearResults}
          className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
        >
          清除结果
        </button>
      </div>

      <div className="flex-1 bg-white rounded-2xl p-6 shadow-sm">
        <h2 className="text-lg font-bold mb-4">测试结果</h2>
        <div className="bg-gray-50 rounded-lg p-4 h-96 overflow-y-auto">
          {results.length === 0 ? (
            <p className="text-gray-500 text-center">点击按钮开始测试...</p>
          ) : (
            <pre className="text-sm font-mono whitespace-pre-wrap">
              {results.join('\n')}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
};

export default ApiTestView;