"""
Supabase 数据库连接模块
提供数据库客户端和常用操作封装
"""

from supabase import create_client, Client
from typing import Optional, Dict, Any, List
import logging

from config import settings

logger = logging.getLogger(__name__)

# ===========================================
# Supabase 客户端初始化
# ===========================================

_supabase_client: Optional[Client] = None


def get_supabase() -> Client:
    """
    获取 Supabase 客户端单例
    优先使用 service_role key（可绕过 RLS）
    """
    global _supabase_client
    
    if _supabase_client is None:
        if not settings.SUPABASE_URL:
            raise ValueError(
                "Supabase 配置缺失！请设置 SUPABASE_URL 环境变量"
            )
        
        # 优先使用 service_role key（后端推荐）
        api_key = settings.SUPABASE_SERVICE_KEY or settings.SUPABASE_KEY
        
        if not api_key:
            raise ValueError(
                "Supabase API Key 缺失！请设置 SUPABASE_KEY 或 SUPABASE_SERVICE_KEY 环境变量"
            )
        
        # 检查 key 格式
        if not api_key.startswith("eyJ"):
            logger.warning(
                "⚠️ Supabase Key 格式可能不正确！"
                "正确的 key 应该以 'eyJ' 开头（JWT 格式）。"
                "请从 Supabase 控制台 Settings -> API 获取正确的 key。"
            )
        
        _supabase_client = create_client(
            settings.SUPABASE_URL,
            api_key
        )
        
        key_type = "service_role" if settings.SUPABASE_SERVICE_KEY else "anon"
        logger.info(f"Supabase 客户端初始化成功 (使用 {key_type} key)")
    
    return _supabase_client


# ===========================================
# 数据库表名常量
# ===========================================

class Tables:
    """数据库表名定义"""
    USERS = "users"
    PETS = "pets"
    DIARY_ENTRIES = "diary_entries"
    HEALTH_RECORDS = "health_records"
    SOCIAL_POSTS = "social_posts"
    NOTIFICATIONS = "notifications"
    DEVICES = "devices"
    VIDEO_JOBS = "video_jobs"


# ===========================================
# 通用数据库操作封装
# ===========================================

class DatabaseService:
    """
    数据库服务类
    封装常用的 CRUD 操作
    """
    
    def __init__(self):
        self.client = get_supabase()
    
    async def insert(
        self, 
        table: str, 
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        插入单条记录
        
        Args:
            table: 表名
            data: 要插入的数据
            
        Returns:
            插入后的记录（包含自动生成的字段）
        """
        try:
            result = self.client.table(table).insert(data).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"插入数据失败 [{table}]: {e}")
            raise
    
    async def select(
        self,
        table: str,
        columns: str = "*",
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        查询记录
        
        Args:
            table: 表名
            columns: 要查询的列，默认全部
            filters: 过滤条件 {column: value}
            order_by: 排序字段 (如 "created_at.desc")
            limit: 限制返回数量
            
        Returns:
            查询结果列表
        """
        try:
            query = self.client.table(table).select(columns)
            
            # 应用过滤条件
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            # 应用排序
            if order_by:
                parts = order_by.split(".")
                column = parts[0]
                desc = len(parts) > 1 and parts[1] == "desc"
                query = query.order(column, desc=desc)
            
            # 应用限制
            if limit:
                query = query.limit(limit)
            
            result = query.execute()
            return result.data or []
        except Exception as e:
            logger.error(f"查询数据失败 [{table}]: {e}")
            raise
    
    async def select_one(
        self,
        table: str,
        filters: Dict[str, Any],
        columns: str = "*"
    ) -> Optional[Dict[str, Any]]:
        """
        查询单条记录
        """
        results = await self.select(table, columns, filters, limit=1)
        return results[0] if results else None
    
    async def update(
        self,
        table: str,
        filters: Dict[str, Any],
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        更新记录
        
        Args:
            table: 表名
            filters: 过滤条件
            data: 要更新的数据
            
        Returns:
            更新后的记录
        """
        try:
            query = self.client.table(table).update(data)
            
            for key, value in filters.items():
                query = query.eq(key, value)
            
            result = query.execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"更新数据失败 [{table}]: {e}")
            raise
    
    async def delete(
        self,
        table: str,
        filters: Dict[str, Any]
    ) -> bool:
        """
        删除记录
        
        Args:
            table: 表名
            filters: 过滤条件
            
        Returns:
            是否删除成功
        """
        try:
            query = self.client.table(table).delete()
            
            for key, value in filters.items():
                query = query.eq(key, value)
            
            query.execute()
            return True
        except Exception as e:
            logger.error(f"删除数据失败 [{table}]: {e}")
            raise
    
    async def upsert(
        self,
        table: str,
        data: Dict[str, Any],
        on_conflict: str = "id"
    ) -> Dict[str, Any]:
        """
        插入或更新记录
        
        Args:
            table: 表名
            data: 数据
            on_conflict: 冲突检测字段
            
        Returns:
            操作后的记录
        """
        try:
            result = self.client.table(table).upsert(
                data, 
                on_conflict=on_conflict
            ).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Upsert 失败 [{table}]: {e}")
            raise


# 导出数据库服务实例
db = DatabaseService()
