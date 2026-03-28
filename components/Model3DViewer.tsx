import React, { useEffect, useRef, useState } from 'react';

interface Model3DViewerProps {
  modelUrl: string;
  fallbackImage?: string;
}

const Model3DViewer: React.FC<Model3DViewerProps> = ({ modelUrl, fallbackImage }) => {
  const [error, setError] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [loading, setLoading] = useState(true);
  const viewerRef = useRef<any>(null);

  // 调试：打印 props
  useEffect(() => {
    console.log('🔍 Model3DViewer 组件挂载');
    console.log('📦 modelUrl:', modelUrl);
    console.log('🖼️ fallbackImage:', fallbackImage);
    
    // 检查 model-viewer 是否已定义
    if (customElements.get('model-viewer')) {
      console.log('✅ model-viewer 自定义元素已注册');
    } else {
      console.log('⏳ model-viewer 自定义元素未注册，等待中...');
      customElements.whenDefined('model-viewer').then(() => {
        console.log('✅ model-viewer 自定义元素注册完成');
      });
    }
  }, [modelUrl, fallbackImage]);

  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer) {
      console.log('⚠️ viewerRef.current 为 null');
      return;
    }

    console.log('🎬 设置 model-viewer 事件监听器');
    setLoading(true);
    setError(false);

    const handleLoad = () => {
      console.log('✅ 3D 模型加载成功:', modelUrl);
      setLoaded(true);
      setError(false);
      setLoading(false);
    };

    const handleError = (e: any) => {
      console.error('❌ 3D 模型加载失败:', modelUrl, e);
      console.error('错误详情:', e.detail || e.message);
      setError(true);
      setLoading(false);
    };

    const handleProgress = (e: any) => {
      const progress = Math.round(e.detail.totalProgress * 100);
      console.log(`⏳ 加载进度: ${progress}%`);
    };

    viewer.addEventListener('load', handleLoad);
    viewer.addEventListener('error', handleError);
    viewer.addEventListener('progress', handleProgress);

    return () => {
      console.log('🧹 清理 model-viewer 事件监听器');
      viewer.removeEventListener('load', handleLoad);
      viewer.removeEventListener('error', handleError);
      viewer.removeEventListener('progress', handleProgress);
    };
  }, [modelUrl]);

  if (error && fallbackImage) {
    // 如果加载失败，显示备用图片
    return (
      <div className="w-full h-full flex items-center justify-center bg-gray-100 rounded-3xl overflow-hidden">
        <img src={fallbackImage} alt="Model Preview" className="w-full h-full object-cover" />
      </div>
    );
  }

  return (
    <div className="w-full h-full relative">
      {/* @ts-ignore - model-viewer 是自定义 Web Component */}
      <model-viewer
        ref={viewerRef}
        src={modelUrl}
        alt="3D Pet Model"
        poster={fallbackImage}
        camera-controls
        auto-rotate
        shadow-intensity="1"
        style={{
          width: '100%',
          height: '100%',
          background: 'transparent'
        }}
      >
        {/* 加载中提示 */}
        {loading && !loaded && !error && (
          <div 
            slot="poster" 
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              textAlign: 'center',
              zIndex: 10,
              background: 'rgba(255,255,255,0.9)',
              padding: '20px',
              borderRadius: '10px'
            }}
          >
            <div style={{
              border: '4px solid #f3f3f3',
              borderTop: '4px solid #31d2e8',
              borderRadius: '50%',
              width: '40px',
              height: '40px',
              animation: 'spin 1s linear infinite',
              margin: '0 auto 10px'
            }}></div>
            <p style={{ color: '#666', fontSize: '12px', margin: 0 }}>加载 3D 模型...</p>
          </div>
        )}
      {/* @ts-ignore */}
      </model-viewer>
      
      {/* 错误提示 */}
      {error && (
        <div style={{
          position: 'absolute',
          top: '10px',
          left: '10px',
          right: '10px',
          background: 'rgba(255,0,0,0.1)',
          color: '#c62828',
          padding: '10px',
          borderRadius: '8px',
          fontSize: '12px',
          zIndex: 20
        }}>
          ⚠️ 3D 模型加载失败，显示预览图
        </div>
      )}
      
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default Model3DViewer;
