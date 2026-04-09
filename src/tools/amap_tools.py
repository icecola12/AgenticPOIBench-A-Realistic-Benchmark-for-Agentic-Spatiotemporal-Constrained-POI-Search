import os
import sys
import argparse
import json
import asyncio
import time
import threading
import hashlib
import random
import math
from typing import Any, Dict, List, Optional, TypedDict, Tuple
from urllib.parse import urlencode

# 添加项目根目录到 sys.path，以便导入 utils 模块
_current_file_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_file_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import requests
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP
from fastmcp import Client
from langchain_core.tools import tool


# 用于动态替换的当前 API Key（由 QPS 管理器使用）
_current_api_key: Optional[str] = None

# 与 src/config/config.yaml env.amap_key_env 及 agent.md §5.1 对齐；保留旧名以便迁移
_AMAP_KEY_ENV_NAMES = (
    "AMAP_MCP_KEY",
    "AMAP_API_KEY",
    "AMAP_KEY",
    "GAODE_API_KEY",
)


def get_amap_default_key() -> str:
    """从环境变量读取高德 Web 服务 Key，禁止在代码中硬编码。"""
    for name in _AMAP_KEY_ENV_NAMES:
        v = os.environ.get(name)
        if v and str(v).strip():
            return str(v).strip()
    raise RuntimeError(
        "未设置高德 API Key。请设置环境变量 AMAP_MCP_KEY（或与 config.yaml 中 env.amap_key_env 一致）。"
    )


def http_get_with_retry(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    wait_before_request: Optional[Any] = None,
    max_retries: int = 5,
    timeout: int = 60,
) -> Any:
    """带可选限流与指数退避的 GET，返回 requests.Response。"""
    last_exc: Optional[Exception] = None
    for attempt in range(max_retries):
        if wait_before_request is not None:
            wait_before_request()
        try:
            return requests.get(url, params=params, timeout=timeout)
        except requests.exceptions.RequestException as e:
            last_exc = e
            if attempt >= max_retries - 1:
                raise
            time.sleep(min(2**attempt, 30.0))
    assert last_exc is not None
    raise last_exc


def get_amap_api_key() -> str:
    """
    Get the Amap Maps API key from configuration file or dynamic override.

    If _current_api_key is set (by QPS manager), use it.
    Otherwise, get from environment variables.
    """
    if _current_api_key is not None:
        return _current_api_key
    return get_amap_default_key()

mcp = FastMCP("amap-maps-refine")


class QPSLimiter:
    """QPS限制器，用于控制API请求频率"""
    
    def __init__(self, qps: float = 1.0):
        """
        初始化QPS限制器
        
        Args:
            qps: 每秒允许的请求数，默认1.0（每秒1个请求）
        """
        self.qps = qps
        self.min_interval = 1.0 / qps if qps > 0 else 0  # 每个请求的最小间隔（秒）
        self.last_request_time = 0.0
        self.lock = threading.Lock()
    
    def wait_if_needed(self):
        """如果需要，等待直到可以发送请求（线程安全）"""
        if self.min_interval <= 0:
            return
        
        with self.lock:
            current_time = time.time()
            elapsed = current_time - self.last_request_time
            
            if elapsed < self.min_interval:
                wait_time = self.min_interval - elapsed
                time.sleep(wait_time)
            
            self.last_request_time = time.time()

# 全局QPS限制器实例，QPS限制为1
_qps_limiter = QPSLimiter(qps=1.0)


def _amap_http_get(url: str, params: Optional[Dict[str, Any]] = None):
    """Amap GET with MCP concurrency cap (config.yaml mcp.max_concurrent_mcp), QPS limiter, and retries."""
    from concurrency import get_mcp_sync_semaphore

    with get_mcp_sync_semaphore():
        return http_get_with_retry(
            url,
            params=params,
            wait_before_request=_qps_limiter.wait_if_needed,
        )

def _safe_get_string(data: dict, key: str, default: str = "") -> str:
    """
    安全地获取字符串字段，处理高德API可能返回空列表[]的情况
    
    Args:
        data: 数据字典
        key: 要获取的键
        default: 默认值，如果键不存在或值不是字符串时返回
        
    Returns:
        字符串值，如果原始值不是字符串（如空列表[]），则返回默认值
    """
    value = data.get(key, default)
    if not isinstance(value, str):
        return default
    return value

class RegeocodeResult(BaseModel):
    """逆地理编码结果"""
    formatted_address: Optional[str] = Field(
        default=None,
        description="完整格式化地址"
    )
    province: Optional[str] = Field(
        default=None,
        description="省份名称"
    )
    city: Optional[str] = Field(
        default=None,
        description="城市名称"
    )
    district: Optional[str] = Field(
        default=None,
        description="区县名称"
    )
    township: Optional[str] = Field(
        default=None,
        description="乡镇街道名称"
    )
    error: Optional[str] = Field(
        default=None,
        description="错误信息，仅在失败时存在"
    )

class GeoResultItem(BaseModel):
    """单条地理编码结果"""
    formatted_address: str = Field(description="完整格式化地址")
    country: str = Field(default="", description="国家")
    province: str = Field(default="", description="省份")
    city: str = Field(default="", description="城市")
    citycode: str = Field(default="", description="城市编码")
    district: str = Field(default="", description="区域")
    street: str = Field(default="", description="街道")
    number: str = Field(default="", description="门牌")
    adcode: str = Field(default="", description="区域编码")
    location: str = Field(description="经纬度坐标，格式为'经度,纬度'")
    level: str = Field(default="", description="匹配级别")

class GeoResult(BaseModel):
    """地理编码服务返回结果"""
    results: Optional[List[GeoResultItem]] = Field(
        default=None,
        description="地理编码结果列表，成功时包含"
    )
    error: Optional[str] = Field(
        default=None,
        description="错误信息，仅在失败时存在"
    )

class BicyclingStep(BaseModel):
    """骑行路线中的单步导航信息"""
    instruction: str = Field(description="导航指示，描述当前步骤的行驶方向")
    road: str = Field(description="道路名称，如果为空则显示'无名道路'")
    distance_meters: int = Field(description="当前步骤的行驶距离（米）")
    duration_seconds: int = Field(description="当前步骤的预计行驶时间（秒）")
    action: Optional[str] = Field(default=None, description="导航动作类型")
    assistant_action: Optional[str] = Field(default=None, description="辅助导航动作")
    from_coordinates: str = Field(description="步骤起点坐标，格式为'经度,纬度'")
    to_coordinates: str = Field(description="步骤终点坐标，格式为'经度,纬度'（可能是途经点或最终目的地）")

class BicyclingRouteResult(BaseModel):
    """骑行路线规划结果"""
    total_distance_meters: Optional[int] = Field(default=None, description="路线总距离（米），成功时包含")
    total_duration_seconds: Optional[int] = Field(default=None, description="路线总预计时间（秒），成功时包含")
    origin_coordinates: Optional[str] = Field(default=None, description="起点坐标，格式为'经度,纬度'，成功时包含")
    destination_coordinates: Optional[str] = Field(default=None, description="终点坐标，格式为'经度,纬度'，成功时包含")
    origin_address: Optional[str] = Field(default=None, description="起点地址，成功时包含")
    destination_address: Optional[str] = Field(default=None, description="终点地址，成功时包含")
    steps: Optional[List[BicyclingStep]] = Field(default=None, description="分步导航信息列表，成功时包含")
    error: Optional[str] = Field(default=None, description="错误信息，仅在失败时存在")

class DrivingStep(BaseModel):
    """驾车路线中的单步导航信息"""
    instruction: str = Field(description="导航指示，描述当前步骤的行驶方向")
    road: Optional[str] = Field(default=None, description="道路名称")
    distance_meters: int = Field(description="当前步骤的行驶距离（米）")
    duration_seconds: int = Field(description="当前步骤的预计行驶时间（秒）")
    orientation: Optional[str] = Field(default=None, description="方向，如'东'、'南'、'西'、'北'等")
    from_coordinates: str = Field(description="步骤起点坐标，格式为'经度,纬度'")
    to_coordinates: str = Field(description="步骤终点坐标，格式为'经度,纬度'（可能是途经点或最终目的地）")

class DrivingRouteResult(BaseModel):
    """驾车路线规划结果"""
    total_distance_meters: Optional[int] = Field(default=None, description="路线总距离（米），成功时包含")
    total_duration_seconds: Optional[int] = Field(default=None, description="路线总预计时间（秒），成功时包含")
    origin_coordinates: Optional[str] = Field(default=None, description="起点坐标，格式为'经度,纬度'，成功时包含")
    destination_coordinates: Optional[str] = Field(default=None, description="终点坐标，格式为'经度,纬度'，成功时包含")
    origin_address: Optional[str] = Field(default=None, description="起点地址，成功时包含")
    destination_address: Optional[str] = Field(default=None, description="终点地址，成功时包含")
    steps: Optional[List[DrivingStep]] = Field(default=None, description="分步导航信息列表，成功时包含")
    error: Optional[str] = Field(default=None, description="错误信息，仅在失败时存在")

class WalkingStep(BaseModel):
    """步行路线中的单步导航信息"""
    instruction: str = Field(description="导航指示，描述当前步骤的行驶方向")
    road: str = Field(description="道路名称，如果为空则显示'无名道路'")
    distance_meters: int = Field(description="当前步骤的行驶距离（米）")
    duration_seconds: int = Field(description="当前步骤的预计行驶时间（秒）")
    action: Optional[str] = Field(default=None, description="导航动作类型")
    assistant_action: Optional[str] = Field(default=None, description="辅助导航动作")
    from_coordinates: str = Field(description="步骤起点坐标，格式为'经度,纬度'")
    to_coordinates: str = Field(description="步骤终点坐标，格式为'经度,纬度'（可能是途经点或最终目的地）")

class WalkingRouteResult(BaseModel):
    """步行路线规划结果"""
    total_distance_meters: Optional[int] = Field(default=None, description="路线总距离（米），成功时包含")
    total_duration_seconds: Optional[int] = Field(default=None, description="路线总预计时间（秒），成功时包含")
    origin_coordinates: Optional[str] = Field(default=None, description="起点坐标，格式为'经度,纬度'，成功时包含")
    destination_coordinates: Optional[str] = Field(default=None, description="终点坐标，格式为'经度,纬度'，成功时包含")
    origin_address: Optional[str] = Field(default=None, description="起点地址，成功时包含")
    destination_address: Optional[str] = Field(default=None, description="终点地址，成功时包含")
    steps: Optional[List[WalkingStep]] = Field(default=None, description="分步导航信息列表，成功时包含")
    error: Optional[str] = Field(default=None, description="错误信息，仅在失败时存在")

class DistanceResultItem(BaseModel):
    """单个距离测量结果"""
    origin_id: int = Field(description="起点坐标序列号（从1开始）")
    dest_id: int = Field(description="终点坐标序列号（从1开始）")
    distance_meters: int = Field(description="路径距离（米）")

class DistanceResult(BaseModel):
    """距离测量结果"""
    results: Optional[List[DistanceResultItem]] = Field(default=None, description="距离信息列表，成功时包含")
    error: Optional[str] = Field(default=None, description="错误信息，仅在失败时存在")
    error_code: Optional[str] = Field(default=None, description="错误代码，仅在失败时存在")

class TextSearchCitySuggestion(BaseModel):
    """文本搜索城市建议"""
    name: str = Field(description="城市名称")
    num: Optional[int] = Field(default=None, description="该城市内符合要求的结果数量（仅在泛词搜索时返回）")

class TextSearchPOI(BaseModel):
    """文本搜索POI结果"""
    id: str = Field(description="POI ID")
    name: str = Field(description="POI名称")
    address: Optional[str] = Field(default=None, description="POI地址")

class TextSearchResult(BaseModel):
    """文本搜索结果"""
    suggestion: Optional[Dict[str, Any]] = Field(default=None, description="搜索建议信息，包含关键词建议和城市建议")
    pois: Optional[List[TextSearchPOI]] = Field(default=None, description="POI结果列表")
    error: Optional[str] = Field(default=None, description="错误信息，仅在失败时存在")

class AroundSearchPOI(BaseModel):
    """周边搜索POI结果"""
    id: str = Field(description="POI ID")
    name: str = Field(description="POI名称")
    address: Optional[str] = Field(default=None, description="POI地址")
    location: Optional[str] = Field(default=None, description="POI坐标，格式为'经度,纬度'")

class AroundSearchResult(BaseModel):
    """周边搜索结果"""
    pois: Optional[List[AroundSearchPOI]] = Field(default=None, description="POI结果列表")
    error: Optional[str] = Field(default=None, description="错误信息，仅在失败时存在")

class PolygonSearchPOI(BaseModel):
    """多边形搜索POI结果"""
    id: str = Field(description="POI ID")
    name: str = Field(description="POI名称")
    address: Optional[str] = Field(default=None, description="POI地址")
    location: Optional[str] = Field(default=None, description="POI坐标，格式为'经度,纬度'")

class PolygonSearchResult(BaseModel):
    """多边形搜索结果"""
    pois: Optional[List[PolygonSearchPOI]] = Field(default=None, description="POI结果列表")
    count: Optional[str] = Field(default=None, description="本次查询结果总数（API 返回）")
    error: Optional[str] = Field(default=None, description="错误信息，仅在失败时存在")

class InputTipItem(BaseModel):
    """输入提示单条结果"""
    id: str = Field(description="数据 ID，POI 为 POI ID，bus 为 bus id，busline 为 busline id")
    name: str = Field(description="提示名称")
    district: str = Field(default="", description="所属区域，省+市+区")
    adcode: str = Field(default="", description="区域编码，六位区县编码")
    location: Optional[str] = Field(default=None, description="中心点坐标，busline 类型不返回")
    address: Optional[str] = Field(default=None, description="详细地址")

class InputTipsResult(BaseModel):
    """输入提示接口返回结果"""
    count: Optional[int] = Field(default=None, description="返回结果总数目")
    tips: Optional[List[InputTipItem]] = Field(default=None, description="建议提示列表")
    error: Optional[str] = Field(default=None, description="错误信息，仅在失败时存在")

class POIDetailResult(BaseModel):
    """POI详细信息结果"""
    id: Optional[str] = Field(default=None, description="POI ID")
    name: Optional[str] = Field(default=None, description="POI名称")
    location: Optional[str] = Field(default=None, description="POI坐标，格式为'经度,纬度'")
    address: Optional[str] = Field(default=None, description="POI地址")
    business_area: Optional[str] = Field(default=None, description="商圈信息")
    city: Optional[str] = Field(default=None, description="城市名称")
    alias: Optional[str] = Field(default=None, description="POI别名")
    biz_ext: Optional[Dict[str, Any]] = Field(default=None, description="扩展信息，包含营业时间、评分、价格等")
    error: Optional[str] = Field(default=None, description="错误信息，仅在失败时存在")
    tel: Optional[str] = Field(default=None, description="POI电话")
    entr_location: Optional[str] = Field(default=None, description="POI入口坐标，格式为'经度,纬度'")
    parking_type: Optional[str] = Field(default=None, description="仅在停车场类型POI的时候显示该字段，展示停车场类型，包括地下，地面，路边")

# inputs for langchain
class RegeocodeInput(BaseModel):
    """逆地理编码工具输入参数"""
    location: str = Field(
        description="经纬度坐标。规则：经度在前，纬度在后，用英文逗号','分割。例如：'116.481488,39.990464'"
    )

class GeoInput(BaseModel):
    """地理编码工具输入参数"""
    address: str = Field(
        description="结构化地址信息。规则遵循：国家、省份、城市、区县、城镇、乡村、街道、门牌号码。例如：'北京市朝阳区阜通东大街6号'"
    )
    city: Optional[str] = Field(
        default=None,
        description="指定查询的城市。可选内容包括：中文（如'北京'）、中文全拼（'beijing'）、citycode（'010'）、adcode（'110000'）。如果为空，则在全国范围内进行搜索。"
    )

class BicyclingRouteInput(BaseModel):
    """骑行路线规划工具输入参数"""
    origin: str = Field(
        description="起点坐标，格式为 '经度,纬度'。规则：经度在前，纬度在后，用英文逗号','分隔。经纬度小数点不超过6位。例如：'116.481028,39.989643'"
    )
    destination: str = Field(
        description="终点坐标，格式为 '经度,纬度'。规则：经度在前，纬度在后，用英文逗号','分隔。经纬度小数点不超过6位。例如：'116.465302,40.004717'"
    )

class DrivingRouteInput(BaseModel):
    """驾车路线规划工具输入参数"""
    origin: str = Field(
        description="起点坐标，格式为 '经度,纬度'。规则：经度在前，纬度在后，用英文逗号','分隔。经纬度小数点不超过6位。例如：'116.481028,39.989643'"
    )
    destination: str = Field(
        description="终点坐标，格式为 '经度,纬度'。规则：经度在前，纬度在后，用英文逗号','分隔。经纬度小数点不超过6位。例如：'116.465302,40.004717'"
    )

class WalkingRouteInput(BaseModel):
    """步行路线规划工具输入参数"""
    origin: str = Field(
        description="起点坐标，格式为 '经度,纬度'。规则：经度在前，纬度在后，用英文逗号','分隔。经纬度小数点不超过6位。例如：'116.481028,39.989643'"
    )
    destination: str = Field(
        description="终点坐标，格式为 '经度,纬度'。规则：经度在前，纬度在后，用英文逗号','分隔。经纬度小数点不超过6位。例如：'116.465302,40.004717'"
    )

class DistanceInput(BaseModel):
    """距离测量工具输入参数"""
    origins: str = Field(
        description="出发点坐标，支持最多100个坐标对。格式：坐标对用'|'分隔，经度和纬度用','分隔。例如：'116.481028,39.989643|114.481028,39.989643'"
    )
    destination: str = Field(
        description="目的地坐标，单个坐标点。格式：'经度,纬度'，例如：'114.465302,40.004717'。经纬度小数点不超过6位"
    )

class TextSearchInput(BaseModel):
    """文本搜索工具输入参数"""
    keywords: str = Field(
        description="查询关键字。规则：只支持一个关键字。必填。"
    )
    city: str = Field(
        default="",
        description="查询城市。可选值：城市中文、citycode、adcode。例如：北京/010/110000。填入此参数后，会尽量优先返回此城市数据，但是不一定仅局限此城市结果，若仅需要某个城市数据请调用 citylimit 参数。可选若为空则在全国范围内搜索。"
    )
    citylimit: str = Field(
        default="false",
        description="仅返回指定城市数据。可选值：true/false。可选，默认 false。"
    )

class AroundSearchInput(BaseModel):
    """周边搜索工具输入参数"""
    location: str = Field(
        description="中心点坐标。规则：经度和纬度用','分割，经度在前，纬度在后，经纬度小数点后不得超过6位。必填。例如：'116.481488,39.990464'"
    )
    radius: str = Field(
        default="5000",
        description="查询半径。取值范围:0-50000。规则：大于50000按默认值，单位：米。可选，默认 5000。"
    )
    keywords: str = Field(
        default="",
        description="查询关键字。规则：只支持一个关键字。可选，无（不指定关键词时返回周边所有POI）。"
    )

class POIDetailInput(BaseModel):
    """POI详情查询工具输入参数"""
    id: str = Field(
        description="AOI唯一标识。最多可以传入1个id，传入目标区域的poiid即可。必填。"
    )

class PolygonSearchInput(BaseModel):
    """多边形搜索工具输入参数"""
    polygon: str = Field(
        description="多边形顶点坐标。规则：经度和纬度用英文逗号','分割，经度在前纬度在后；多个坐标对用竖线'|'分割；经纬度小数点后不得超过6位。矩形时可只传左上、右下两顶点；其他多边形首尾坐标对需相同。例如：'116.460988,40.006919|116.48231,40.007381|116.47516,39.99713|116.460988,40.006919'"
    )
    keywords: str = Field(
        default="",
        description="查询关键字。规则：只支持一个关键字。可选，不指定关键词时返回区域内默认类型 POI（商务住宅、交通设施等）。"
    )

class InputTipsInput(BaseModel):
    """输入提示工具输入参数"""
    keywords: str = Field(
        description="查询关键词。必填。"
    )
    type: str = Field(
        default="",
        description="POI 分类。可选：POI 分类名称或分类代码，多个用 '|' 分隔。建议使用分类代码。"
    )
    location: str = Field(
        default="",
        description="坐标，格式为 '经度,纬度'，不可包含空格。建议传入以在附近优先返回结果；在 city 不为空时生效。"
    )
    city: str = Field(
        default="",
        description="搜索城市。可选：citycode 或 adcode，如 010/110000。填入后优先返回该城市数据，不保证仅限该城市。"
    )
    citylimit: str = Field(
        default="false",
        description="仅返回指定城市数据。可选：true/false。默认 false。"
    )
    datatype: str = Field(
        default="all",
        description="返回数据类型。可选：all（全部）、poi、bus、busline，多种用 '|' 分隔。默认 all。"
    )

@mcp.tool()
def regeocode_amap_location(location: str) -> RegeocodeResult:
    """高德地图逆地理编码服务。
    
    根据提供的经纬度坐标，查询其对应的结构化地址信息，如省、市、区和详细地址。
    
    Args:
        location: 经纬度坐标。规则：经度在前，纬度在后，用英文逗号","分割。
            例如："116.481488,39.990464"
    
    Returns:
        RegeocodeResult: 包含地址信息的对象。成功时包含以下字段：
            - formatted_address (str): 完整格式化地址
            - province (str): 省份名称
            - city (str): 城市名称
            - district (str): 区县名称
            - township (str): 乡镇街道名称
            失败时包含 error (str) 字段。
    """
    base_url = "https://restapi.amap.com/v3/geocode/regeo"
    params = {
        "key": get_amap_api_key(),
        "location": location,
        # 根据要求，只使用必选参数。其他参数如 'extensions' 均为默认值 'base'。
        # 这里是因为其他参数返回的功能过于强大且上下文过于长  在这里使用原子工具即可
    }

    try:
        response = _amap_http_get(base_url, params=params)
        data = response.json()

        # 检查高德API返回的状态
        if data.get("status") != "1":
            error_info = data.get('info', '未知错误')
            return RegeocodeResult(error=f"高德API请求失败: {error_info}")

        # 安全地提取数据
        regeocode_data = data.get("regeocode", {})
        address_comp = regeocode_data.get("addressComponent", {})
        
        # 使用辅助函数安全地获取可能返回空列表的字符串字段
        return RegeocodeResult(
            formatted_address=_safe_get_string(regeocode_data, "formatted_address", ""),
            province=_safe_get_string(address_comp, "province", ""),
            city=_safe_get_string(address_comp, "city", ""),
            district=_safe_get_string(address_comp, "district", ""),
            township=_safe_get_string(address_comp, "township", ""),
        )
    
    except requests.exceptions.RequestException as e:
        return RegeocodeResult(error=f"网络请求异常: {str(e)}")
    except Exception as e:
        return RegeocodeResult(error=f"处理过程中发生未知错误: {str(e)}")

def maps_geo(address: str, city: Optional[str] = None) -> GeoResult:
    """高德地图地理编码服务（地址转坐标）。

    将结构化地址或地标名称转换为高德经纬度坐标。

    Args:
        address: 结构化地址或地标，如「北京市朝阳区阜通东大街6号」或「宝鸡南站」。
        city: 指定查询城市，如「北京」「宝鸡」，可选；为空时在全国范围检索。

    Returns:
        GeoResult: 成功时 results 为 GeoResultItem 列表（含 location 等）；失败时 error 为原因。
    """
    base_url = "https://restapi.amap.com/v3/geocode/geo"
    params = {
        "key": get_amap_api_key(),
        "address": address,
        "output": "json",
    }
    if city:
        params["city"] = city

    try:
        response = _amap_http_get(base_url, params=params)
        data = response.json()

        if data.get("status") != "1":
            error_info = data.get("info", "未知错误")
            return GeoResult(error=f"高德API请求失败: {error_info}")

        geocodes = data.get("geocodes") or []
        if not geocodes:
            return GeoResult(error="未找到匹配的地址")

        results = []
        for g in geocodes:
            if isinstance(g, dict):
                fa = _safe_get_string(g, "formatted_address", "")
                if not fa:
                    parts = [
                        _safe_get_string(g, "province", ""),
                        _safe_get_string(g, "city", ""),
                        _safe_get_string(g, "district", ""),
                        _safe_get_string(g, "street", ""),
                        _safe_get_string(g, "number", ""),
                    ]
                    fa = "".join(p for p in parts if p)
                results.append(
                    GeoResultItem(
                        formatted_address=fa or address,
                        country=_safe_get_string(g, "country", ""),
                        province=_safe_get_string(g, "province", ""),
                        city=_safe_get_string(g, "city", ""),
                        citycode=_safe_get_string(g, "citycode", ""),
                        district=_safe_get_string(g, "district", ""),
                        street=_safe_get_string(g, "street", ""),
                        number=_safe_get_string(g, "number", ""),
                        adcode=_safe_get_string(g, "adcode", ""),
                        location=_safe_get_string(g, "location", ""),
                        level=_safe_get_string(g, "level", ""),
                    )
                )
        return GeoResult(results=results if results else None)
    except requests.exceptions.RequestException as e:
        return GeoResult(error=f"网络请求异常: {str(e)}")
    except Exception as e:
        return GeoResult(error=f"处理过程中发生未知错误: {str(e)}")

@mcp.tool()
def maps_bicycling_by_coordinates(origin: str, destination: str) -> BicyclingRouteResult:
    """
    根据经纬度坐标规划骑行路线。
    返回总距离，总时长等信息。

    
    Args:
        origin (str): 起点坐标，格式为 "经度,纬度"。
                      规则：经度在前，纬度在后，用英文逗号","分隔。
                      经纬度小数点不超过6位。
                      例如："116.481028,39.989643"
        destination (str): 终点坐标，格式为 "经度,纬度"。
                          规则：经度在前，纬度在后，用英文逗号","分隔。
                          经纬度小数点不超过6位。
                          例如："116.465302,40.004717"
    
    Returns:
        BicyclingRouteResult: 包含路线信息的对象。
                              成功时包含以下字段：
                              - total_distance_meters (int): 路线总距离（米）
                              - total_duration_seconds (int): 路线总预计时间（秒）
                              - origin_coordinates (str): 起点坐标，格式为'经度,纬度'
                              - destination_coordinates (str): 终点坐标，格式为'经度,纬度'
                              - origin_address (str|None): 起点地址，可能为None
                              - destination_address (str|None): 终点地址，可能为None
                              - steps (List[BicyclingStep]): 分步导航信息列表，每个步骤包含：
                                * instruction (str): 导航指示，描述当前步骤的行驶方向
                                * road (str): 道路名称，如果为空则显示'无名道路'
                                * distance_meters (int): 当前步骤的行驶距离（米）
                                * duration_seconds (int): 当前步骤的预计行驶时间（秒）
                                * action (str|None): 导航动作类型（如"直行"、"左转"、"右转"、"到达"），可能为None
                                * assistant_action (str|None): 辅助导航动作，可能为None
                                * from_coordinates (str): 步骤起点坐标，格式为'经度,纬度'
                                * to_coordinates (str): 步骤终点坐标，格式为'经度,纬度'（可能是途经点或最终目的地）
                              失败时包含 error (str) 字段，描述错误信息。
    """
    try:
        # 解析坐标
        origin_lat, origin_lng = parse_coordinates(origin)
        dest_lat, dest_lng = parse_coordinates(destination)
        
        # 生成种子
        seed = generate_seed(origin_lat, origin_lng, dest_lat, dest_lng)
        
        # 生成确定性参数
        params = generate_deterministic_params(seed, max_waypoints=3)
        
        # 生成途经点
        waypoint_coords = []
        for i, offset_info in enumerate(params['waypoint_offsets']):
            progress = (i + 1) / (params['num_waypoints'] + 1)
            wp_lat, wp_lng = calculate_waypoint(
                origin_lat, origin_lng, dest_lat, dest_lng,
                offset_info['offset_lat'], offset_info['offset_lng'],
                offset_info['direction'], progress
            )
            waypoint_coords.append((wp_lat, wp_lng))
        
        # 生成速度
        speed = generate_speed(seed, 'bicycling')
        
        # 构建路径点列表（起点 + 途经点 + 终点）
        path_points = [(origin_lat, origin_lng)]
        path_points.extend(waypoint_coords)
        path_points.append((dest_lat, dest_lng))
        
        # 使用 maps_distance 计算每一步的距离
        steps_list = []
        total_distance = 0
        total_duration = 0
        
        for i in range(len(path_points) - 1):
            from_point = path_points[i]
            to_point = path_points[i + 1]
            
            # 构建 origins 字符串（单个起点）
            origins_str = format_coordinates(from_point[0], from_point[1])
            destination_str = format_coordinates(to_point[0], to_point[1])
            
            # 调用 maps_distance
            distance_result = maps_distance(origins_str, destination_str)
            
            if distance_result.error or not distance_result.results:
                return BicyclingRouteResult(error=f"计算距离失败: {distance_result.error or '未找到结果'}")
            
            # 获取距离
            step_distance = distance_result.results[0].distance_meters
            step_duration = int(step_distance / speed)  # 根据距离和速度计算时间
            
            total_distance += step_distance
            total_duration += step_duration
            
            # 生成导航指示
            instruction = generate_instruction(i, len(path_points) - 1, from_point, to_point)
            
            # 生成道路名称（使用确定性随机数）
            seed_for_road = seed + str(i)
            road_seed = int(hashlib.sha256(seed_for_road.encode()).hexdigest()[:8], 16)
            road_rng = random.Random(road_seed)
            road_names = ["无名道路", "主路", "辅路", "小路", "街道"]
            road = road_rng.choice(road_names)
            
            # 生成动作类型
            actions = ["直行", "左转", "右转", "直行"]
            action = actions[i % len(actions)] if i < len(path_points) - 2 else "到达"
            
            steps_list.append({
                "instruction": instruction,
                "road": road,
                "distance_meters": step_distance,
                "duration_seconds": step_duration,
                "action": action if i < len(path_points) - 2 else None,
                "assistant_action": None,
                "from_coordinates": origins_str,
                "to_coordinates": destination_str
            })
        
        # 转换 steps 列表为 BicyclingStep 对象列表
        steps = []
        for step_dict in steps_list:
            steps.append(BicyclingStep(**step_dict))
        
        return BicyclingRouteResult(
            total_distance_meters=total_distance,
            total_duration_seconds=total_duration,
            origin_coordinates=origin,
            destination_coordinates=destination,
            origin_address=None,
            destination_address=None,
            steps=steps
        )
        
    except Exception as e:
        return BicyclingRouteResult(error=f"规划路线时发生意外错误: {e}")

@mcp.tool()
def maps_driving_by_coordinates(origin: str, destination: str) -> DrivingRouteResult:
    """
    根据经纬度坐标规划驾车路线。
    返回总距离，总时长等信息。

    
    Args:
        origin (str): 起点坐标，格式为 "经度,纬度"。
                      规则：经度在前，纬度在后，用英文逗号","分隔。
                      经纬度小数点不超过6位。
                      例如："116.481028,39.989643"
        destination (str): 终点坐标，格式为 "经度,纬度"。
                          规则：经度在前，纬度在后，用英文逗号","分隔。
                          经纬度小数点不超过6位。
                          例如："116.465302,40.004717"
    
    Returns:
        DrivingRouteResult: 包含路线信息的对象。
                            成功时包含以下字段：
                            - total_distance_meters (int): 路线总距离（米）
                            - total_duration_seconds (int): 路线总预计时间（秒）
                            - origin_coordinates (str): 起点坐标，格式为'经度,纬度'
                            - destination_coordinates (str): 终点坐标，格式为'经度,纬度'
                            - origin_address (str|None): 起点地址，可能为None
                            - destination_address (str|None): 终点地址，可能为None
                            - steps (List[DrivingStep]): 分步导航信息列表，每个步骤包含：
                              * instruction (str): 导航指示，描述当前步骤的行驶方向
                              * road (str|None): 道路名称，可能为None
                              * distance_meters (int): 当前步骤的行驶距离（米）
                              * duration_seconds (int): 当前步骤的预计行驶时间（秒）
                              * orientation (str|None): 方向，如'东'、'南'、'西'、'北'、'东北'、'东南'、'西南'、'西北'等，可能为None
                              * from_coordinates (str): 步骤起点坐标，格式为'经度,纬度'
                              * to_coordinates (str): 步骤终点坐标，格式为'经度,纬度'（可能是途经点或最终目的地）
                            失败时包含 error (str) 字段，描述错误信息。
    """
    try:
        # 解析坐标
        origin_lat, origin_lng = parse_coordinates(origin)
        dest_lat, dest_lng = parse_coordinates(destination)
        
        # 生成种子
        seed = generate_seed(origin_lat, origin_lng, dest_lat, dest_lng)
        
        # 生成确定性参数
        params = generate_deterministic_params(seed, max_waypoints=3)
        
        # 生成途经点
        waypoint_coords = []
        for i, offset_info in enumerate(params['waypoint_offsets']):
            progress = (i + 1) / (params['num_waypoints'] + 1)
            wp_lat, wp_lng = calculate_waypoint(
                origin_lat, origin_lng, dest_lat, dest_lng,
                offset_info['offset_lat'], offset_info['offset_lng'],
                offset_info['direction'], progress
            )
            waypoint_coords.append((wp_lat, wp_lng))
        
        # 生成速度
        speed = generate_speed(seed, 'driving')
        
        # 构建路径点列表（起点 + 途经点 + 终点）
        path_points = [(origin_lat, origin_lng)]
        path_points.extend(waypoint_coords)
        path_points.append((dest_lat, dest_lng))
        
        # 使用 maps_distance 计算每一步的距离
        steps_list = []
        total_distance = 0
        total_duration = 0
        
        for i in range(len(path_points) - 1):
            from_point = path_points[i]
            to_point = path_points[i + 1]
            
            # 构建 origins 字符串（单个起点）
            origins_str = format_coordinates(from_point[0], from_point[1])
            destination_str = format_coordinates(to_point[0], to_point[1])
            
            # 调用 maps_distance
            distance_result = maps_distance(origins_str, destination_str)
            
            if distance_result.error or not distance_result.results:
                return DrivingRouteResult(error=f"计算距离失败: {distance_result.error or '未找到结果'}")
            
            # 获取距离
            step_distance = distance_result.results[0].distance_meters
            step_duration = int(step_distance / speed)  # 根据距离和速度计算时间
            
            total_distance += step_distance
            total_duration += step_duration
            
            # 生成导航指示
            instruction = generate_instruction(i, len(path_points) - 1, from_point, to_point)
            
            # 生成道路名称（使用确定性随机数）
            seed_for_road = seed + str(i)
            road_seed = int(hashlib.sha256(seed_for_road.encode()).hexdigest()[:8], 16)
            road_rng = random.Random(road_seed)
            road_names = ["主路", "辅路", "高速", "环路", "街道", None]
            road = road_rng.choice(road_names)
            
            # 生成方向
            lat1, lng1 = from_point
            lat2, lng2 = to_point
            lat_diff = lat2 - lat1
            lng_diff = lng2 - lng1
            angle = math.degrees(math.atan2(lng_diff, lat_diff))
            if angle < 0:
                angle += 360
            
            orientations = ["东", "南", "西", "北", "东北", "东南", "西南", "西北"]
            orientation_index = int(angle / 45) % 8
            orientation = orientations[orientation_index]
            
            steps_list.append({
                "instruction": instruction,
                "road": road,
                "distance_meters": step_distance,
                "duration_seconds": step_duration,
                "orientation": orientation,
                "from_coordinates": origins_str,
                "to_coordinates": destination_str
            })
        
        # 转换 steps 列表为 DrivingStep 对象列表
        steps = []
        for step_dict in steps_list:
            steps.append(DrivingStep(**step_dict))
        
        return DrivingRouteResult(
            total_distance_meters=total_distance,
            total_duration_seconds=total_duration,
            origin_coordinates=origin,
            destination_coordinates=destination,
            origin_address=None,
            destination_address=None,
            steps=steps
        )
        
    except Exception as e:
        return DrivingRouteResult(error=f"规划路线时发生意外错误: {e}")

@mcp.tool()
def maps_walking_by_coordinates(origin: str, destination: str) -> WalkingRouteResult:
    """
    根据经纬度坐标规划步行路线。
    返回总距离，总时长等信息

    
    Args:
        origin (str): 起点坐标，格式为 "经度,纬度"。
                      规则：经度在前，纬度在后，用英文逗号","分隔。
                      经纬度小数点不超过6位。
                      例如："116.481028,39.989643"
        destination (str): 终点坐标，格式为 "经度,纬度"。
                          规则：经度在前，纬度在后，用英文逗号","分隔。
                          经纬度小数点不超过6位。
                          例如："116.465302,40.004717"
    
    Returns:
        WalkingRouteResult: 包含路线信息的对象。
                            成功时包含以下字段：
                            - total_distance_meters (int): 路线总距离（米）
                            - total_duration_seconds (int): 路线总预计时间（秒）
                            - origin_coordinates (str): 起点坐标，格式为'经度,纬度'
                            - destination_coordinates (str): 终点坐标，格式为'经度,纬度'
                            - origin_address (str|None): 起点地址，可能为None
                            - destination_address (str|None): 终点地址，可能为None
                            - steps (List[WalkingStep]): 分步导航信息列表，每个步骤包含：
                              * instruction (str): 导航指示，描述当前步骤的行驶方向
                              * road (str): 道路名称，如果为空则显示'无名道路'
                              * distance_meters (int): 当前步骤的行驶距离（米）
                              * duration_seconds (int): 当前步骤的预计行驶时间（秒）
                              * action (str|None): 导航动作类型（如"直行"、"左转"、"右转"、"到达"），可能为None
                              * assistant_action (str|None): 辅助导航动作，可能为None
                              * from_coordinates (str): 步骤起点坐标，格式为'经度,纬度'
                              * to_coordinates (str): 步骤终点坐标，格式为'经度,纬度'（可能是途经点或最终目的地）
                            失败时包含 error (str) 字段，描述错误信息。
    """
    try:
        # 解析坐标
        origin_lat, origin_lng = parse_coordinates(origin)
        dest_lat, dest_lng = parse_coordinates(destination)
        
        # 生成种子
        seed = generate_seed(origin_lat, origin_lng, dest_lat, dest_lng)
        
        # 生成确定性参数
        params = generate_deterministic_params(seed, max_waypoints=3)
        
        # 生成途经点
        waypoint_coords = []
        for i, offset_info in enumerate(params['waypoint_offsets']):
            progress = (i + 1) / (params['num_waypoints'] + 1)
            wp_lat, wp_lng = calculate_waypoint(
                origin_lat, origin_lng, dest_lat, dest_lng,
                offset_info['offset_lat'], offset_info['offset_lng'],
                offset_info['direction'], progress
            )
            waypoint_coords.append((wp_lat, wp_lng))
        
        # 生成速度
        speed = generate_speed(seed, 'walking')
        
        # 构建路径点列表（起点 + 途经点 + 终点）
        path_points = [(origin_lat, origin_lng)]
        path_points.extend(waypoint_coords)
        path_points.append((dest_lat, dest_lng))
        
        # 使用 maps_distance 计算每一步的距离
        steps_list = []
        total_distance = 0
        total_duration = 0
        
        for i in range(len(path_points) - 1):
            from_point = path_points[i]
            to_point = path_points[i + 1]
            
            # 构建 origins 字符串（单个起点）
            origins_str = format_coordinates(from_point[0], from_point[1])
            destination_str = format_coordinates(to_point[0], to_point[1])
            
            # 调用 maps_distance
            distance_result = maps_distance(origins_str, destination_str)
            
            if distance_result.error or not distance_result.results:
                return WalkingRouteResult(error=f"计算距离失败: {distance_result.error or '未找到结果'}")
            
            # 获取距离
            step_distance = distance_result.results[0].distance_meters
            step_duration = int(step_distance / speed)  # 根据距离和速度计算时间
            
            total_distance += step_distance
            total_duration += step_duration
            
            # 生成导航指示
            instruction = generate_instruction(i, len(path_points) - 1, from_point, to_point)
            
            # 生成道路名称（使用确定性随机数）
            seed_for_road = seed + str(i)
            road_seed = int(hashlib.sha256(seed_for_road.encode()).hexdigest()[:8], 16)
            road_rng = random.Random(road_seed)
            road_names = ["无名道路", "人行道", "小路", "街道", "步道"]
            road = road_rng.choice(road_names)
            
            # 生成动作类型
            actions = ["直行", "左转", "右转", "直行"]
            action = actions[i % len(actions)] if i < len(path_points) - 2 else "到达"
            
            steps_list.append({
                "instruction": instruction,
                "road": road,
                "distance_meters": step_distance,
                "duration_seconds": step_duration,
                "action": action if i < len(path_points) - 2 else None,
                "assistant_action": None,
                "from_coordinates": origins_str,
                "to_coordinates": destination_str
            })
        
        # 转换 steps 列表为 WalkingStep 对象列表
        steps = []
        for step_dict in steps_list:
            steps.append(WalkingStep(**step_dict))
        
        return WalkingRouteResult(
            total_distance_meters=total_distance,
            total_duration_seconds=total_duration,
            origin_coordinates=origin,
            destination_coordinates=destination,
            origin_address=None,
            destination_address=None,
            steps=steps
        )
        
    except Exception as e:
        return WalkingRouteResult(error=f"规划路线时发生意外错误: {e}")

# Version for the algorithm
ALGORITHM_VERSION = "v2.0"

def generate_seed(lat1: float, lng1: float, lat2: float, lng2: float, version: str = ALGORITHM_VERSION) -> str:
    """
    第一层：种子生成器
    将两个浮点数（lat1, lng1, lat2, lng2）变成一个固定字符串
    
    Args:
        lat1: 起点纬度
        lng1: 起点经度
        lat2: 终点纬度
        lng2: 终点经度
        version: 算法版本号，用于算法升级时强制改变所有路径
    
    Returns:
        固定字符串种子
    """
    # 规范化坐标对：确保 (A, B) 和 (B, A) 生成相同的 seed
    coord1 = (lat1, lng1)
    coord2 = (lat2, lng2)
    
    # 对坐标对进行排序（先比较纬度，再比较经度）
    if coord1 > coord2:
        coord1, coord2 = coord2, coord1
    
    # 使用排序后的坐标生成 seed（保留6位小数）
    seed_str = f"{version}:{coord1[0]:.6f},{coord1[1]:.6f}:{coord2[0]:.6f},{coord2[1]:.6f}"
    # 使用SHA256生成哈希值
    seed_hash = hashlib.sha256(seed_str.encode('utf-8')).hexdigest()
    return seed_hash

def generate_deterministic_params(seed: str, max_waypoints: int = 3) -> Dict[str, Any]:
    """
    第二层：确定性参数工厂
    用种子生成路径的"设计参数"
    
    Args:
        seed: 种子字符串
        max_waypoints: 最大途经点数量（最多3个）
    
    Returns:
        包含路径参数的字典
    """
    # 使用种子初始化随机数生成器
    seed_int = int(seed[:16], 16)  # 使用前16个字符转换为整数
    rng = random.Random(seed_int)
    
    # 生成途经点数量（1-3）
    num_waypoints = rng.randint(1, max_waypoints)
    
    # 生成每个途经点的偏移量和方向
    waypoint_offsets = []
    for i in range(num_waypoints):
        # 偏移量：0.001-0.01度（约100米-1公里）
        offset_lat = rng.uniform(0.001, 0.01)
        offset_lng = rng.uniform(0.001, 0.01)
        # 方向：随机角度（0-360度）
        direction = rng.uniform(0, 360)
        waypoint_offsets.append({
            'offset_lat': offset_lat,
            'offset_lng': offset_lng,
            'direction': direction
        })
    
    # 路径曲折程度（0-1）
    path_complexity = rng.uniform(0.3, 0.7)
    
    # 速度（m/s）- 这个会在调用时根据交通方式确定范围
    speed_seed = rng.uniform(0, 1)
    
    return {
        'num_waypoints': num_waypoints,
        'waypoint_offsets': waypoint_offsets,
        'path_complexity': path_complexity,
        'speed_seed': speed_seed
    }

def generate_speed(seed: str, transport_mode: str) -> float:
    """
    根据种子和交通方式生成确定性速度
    
    Args:
        seed: 种子字符串
        transport_mode: 交通方式（'walking', 'bicycling', 'driving'）
    
    Returns:
        速度（m/s）
    """
    seed_int = int(seed[16:32], 16)  # 使用中间16个字符
    rng = random.Random(seed_int)
    speed_seed = rng.uniform(0, 1)
    
    if transport_mode == 'walking':
        # 步行：0.8-2 m/s
        return 0.8 + speed_seed * 1.2
    elif transport_mode == 'bicycling':
        # 骑行：3-5 m/s
        return 3.0 + speed_seed * 2.0
    elif transport_mode == 'driving':
        # 驾车：6-12 m/s（约22-43 km/h，考虑城市交通）
        return 6.0 + speed_seed * 6.0
    else:
        return 0.8 + speed_seed * 1.2  # 默认步行速度

def calculate_waypoint(origin_lat: float, origin_lng: float, 
                      dest_lat: float, dest_lng: float,
                      offset_lat: float, offset_lng: float, 
                      direction: float, progress: float) -> Tuple[float, float]:
    """
    计算途经点坐标
    
    Args:
        origin_lat: 起点纬度
        origin_lng: 起点经度
        dest_lat: 终点纬度
        dest_lng: 终点经度
        offset_lat: 纬度偏移量
        offset_lng: 经度偏移量
        direction: 方向角度（度）
        progress: 在路径上的进度（0-1）
    
    Returns:
        途经点坐标 (纬度, 经度)
    """
    # 计算起点到终点的向量
    lat_diff = dest_lat - origin_lat
    lng_diff = dest_lng - origin_lng
    
    # 在路径上的基础位置
    base_lat = origin_lat + lat_diff * progress
    base_lng = origin_lng + lng_diff * progress
    
    # 应用偏移量（根据方向）
    rad = math.radians(direction)
    offset_lat_final = offset_lat * math.cos(rad) * (1 - progress)
    offset_lng_final = offset_lng * math.sin(rad) * (1 - progress)
    
    waypoint_lat = base_lat + offset_lat_final
    waypoint_lng = base_lng + offset_lng_final
    
    return waypoint_lat, waypoint_lng

def parse_coordinates(coord_str: str) -> Tuple[float, float]:
    """
    解析坐标字符串 "经度,纬度" 为 (纬度, 经度)
    
    Args:
        coord_str: 坐标字符串，格式为 "经度,纬度"
    
    Returns:
        (纬度, 经度) 元组
    """
    parts = coord_str.split(',')
    lng = float(parts[0].strip())
    lat = float(parts[1].strip())
    return lat, lng

def format_coordinates(lat: float, lng: float) -> str:
    """
    格式化坐标为字符串 "经度,纬度"
    
    Args:
        lat: 纬度
        lng: 经度
    
    Returns:
        坐标字符串 "经度,纬度"
    """
    return f"{lng:.6f},{lat:.6f}"

def generate_instruction(step_index: int, total_steps: int, 
                        from_coord: Tuple[float, float],
                        to_coord: Tuple[float, float]) -> str:
    """
    生成导航指示
    
    Args:
        step_index: 步骤索引（从0开始）
        total_steps: 总步骤数
        from_coord: 起点坐标 (纬度, 经度)
        to_coord: 终点坐标 (纬度, 经度)
    
    Returns:
        导航指示字符串
    """
    lat1, lng1 = from_coord
    lat2, lng2 = to_coord
    
    # 计算方向
    lat_diff = lat2 - lat1
    lng_diff = lng2 - lng1
    
    # 计算角度
    angle = math.degrees(math.atan2(lng_diff, lat_diff))
    
    # 转换为方向描述
    if angle < 0:
        angle += 360
    
    if 22.5 <= angle < 67.5:
        direction = "东北"
    elif 67.5 <= angle < 112.5:
        direction = "东"
    elif 112.5 <= angle < 157.5:
        direction = "东南"
    elif 157.5 <= angle < 202.5:
        direction = "南"
    elif 202.5 <= angle < 247.5:
        direction = "西南"
    elif 247.5 <= angle < 292.5:
        direction = "西"
    elif 292.5 <= angle < 337.5:
        direction = "西北"
    else:
        direction = "北"
    
    if step_index == 0:
        return f"从起点向{direction}方向出发"
    elif step_index == total_steps - 1:
        return f"向{direction}方向到达终点"
    else:
        return f"继续向{direction}方向行驶"

@mcp.tool()
def maps_distance(origins: str, destination: str) -> DistanceResult:
    """
    测量两个或多个经纬度坐标之间的距离。
    
    Args:
        origins (str): 出发点坐标，支持最多100个坐标对。
                       格式：坐标对用"|"分隔，经度和纬度用","分隔。
                       例如："116.481028,39.989643|114.481028,39.989643"
        destination (str): 目的地坐标，单个坐标点。
                          格式："经度,纬度"，例如："114.465302,40.004717"
                          经纬度小数点不超过6位

    Returns:
        DistanceResult: 包含距离测量结果的对象。
                        成功时包含 results 字段（距离信息列表）。 
                             - origin_id 起点坐标，起点坐标序列号（从1开始）
                             - dest_id 终点坐标，终点坐标序列号（从1开始）
                             - distance 距离（米）
                        失败时包含 error 和 error_code 字段。
    """
    base_url = "https://restapi.amap.com/v3/distance"
    params = {
        "key": get_amap_api_key(),
        "origins": origins,
        "destination": destination,
        "type": "0"
    }

    try:
        response = _amap_http_get(base_url, params=params)
        data = response.json()

        # 检查高德API返回的业务状态码
        if data.get("status") != "1":
            error_info = data.get("info", "未知错误")
            error_code = data.get("code", "")
            # 根据文档，info字段在出错时显示错误原因
            return DistanceResult(
                error=f"高德API错误: {error_info}",
                error_code=error_code if error_code else None
            )

        # 检查结果数据是否存在
        if not data.get("results"):
            return DistanceResult(error="未找到距离测量结果")

        # 格式化结果列表
        results_list = []
        for result in data["results"]:
            # 检查result中是否有错误信息
            if result.get("info"):
                error_info = result.get("info", "未知错误")
                error_code = result.get("code", "")
                return DistanceResult(
                    error=f"距离计算错误: {error_info}",
                    error_code=error_code if error_code else None
                )
            
            results_list.append(DistanceResultItem(
                origin_id=int(result.get("origin_id", 0)),
                dest_id=int(result.get("dest_id", 0)),
                distance_meters=int(result.get("distance", 0))
            ))

        return DistanceResult(results=results_list)

    except requests.exceptions.RequestException as e:
        return DistanceResult(error=f"网络请求失败: {e}")
    except (KeyError, IndexError, TypeError, ValueError) as e:
        return DistanceResult(error=f"解析API响应失败: {e}")
    except Exception as e:
        return DistanceResult(error=f"发生未知错误: {e}")

@mcp.tool()
def maps_text_search(keywords: str, city: str = "", citylimit: str = "false") -> TextSearchResult:
    """高德地图关键词搜索服务。
    
    根据用户输入的关键字进行 POI 搜索，并返回相关的信息。
    
    规则说明：
    - 只支持一个关键字
    - 若不指定 city，并且搜索的为泛词（例如"美食"）的情况下，返回的内容为城市列表以及此城市内有多少结果符合要求
    - keyword 参数必填
    
    Args:
        keywords: 查询关键字。规则：只支持一个关键字。必填。
        city: 查询城市。可选值：城市中文、citycode、adcode。
             例如：北京/010/110000。
             填入此参数后，会尽量优先返回此城市数据，但是不一定仅局限此城市结果，
             若仅需要某个城市数据请调用 citylimit 参数。
             city参数能够接收 citycode和 adcode，citycode仅能精确到城市，而adcode却能够精确到区县。
             例如：北京，citycode：010，adcode：110000。
             北京-海淀区，citycode：010，adcode：110108。
             所以使用citycode仅能在北京范围内搜索，而adcode能够制定在海淀区搜索。
             如：在深圳市搜天安门，返回北京天安门结果。
             可选，若为空则在全国范围内搜索。
        citylimit: 仅返回指定城市数据。可选值：true/false。可选，默认 false。
    
    Returns:
        TextSearchResult: 包含搜索结果的对象。
                         成功时包含 suggestion（搜索建议，包含关键词建议和城市建议）和 pois（POI结果列表）字段。
                         Suggestion，城市建议列表，当搜索的文本关键字在限定城市中没有返回时会返回建议城市列表；
                         - keywords 关键字
                         - cities 城市列表
                           - name 名称
                           - num 该城市包含此关键字的个数
                           - citycode 该城市的citycode
                           - adcode 该城市的adcode
                         搜索成功时，pois列表中包括以下字段：
                         - id (str): POI唯一标识
                         - name (str): POI名称
                         - address (str): 地址
                         失败时包含 error 字段。
    """
    try:
        response = _amap_http_get(
            "https://restapi.amap.com/v3/place/text",
            params={
                "key": get_amap_api_key(),
                "keywords": keywords,
                "city": city,
                "citylimit": citylimit
            }
        )
        data = response.json()
        
        if data.get("status") != "1":
            error_info = data.get('info', '未知错误')
            return TextSearchResult(error=f"高德API文本搜索失败: {error_info}")
        
        # 处理城市建议列表
        suggestion_cities = []
        if data.get("suggestion", {}).get("cities"):
            for city_item in data["suggestion"]["cities"]:
                city_suggestion = {
                    "name": _safe_get_string(city_item, "name", "")
                }
                # 如果存在 num 字段（泛词搜索时返回的结果数量），也包含进去
                if "num" in city_item:
                    num_value = city_item.get("num")
                    # 确保 num 是整数类型
                    try:
                        city_suggestion["num"] = int(num_value) if num_value is not None else None
                    except (ValueError, TypeError):
                        city_suggestion["num"] = None
                suggestion_cities.append(city_suggestion)
        
        # 处理POI列表
        pois = []
        for poi in data.get("pois", []):
            # 安全地获取字符串字段，处理可能返回空列表的情况
            address = poi.get("address")
            pois.append(TextSearchPOI(
                id=_safe_get_string(poi, "id", ""),
                name=_safe_get_string(poi, "name", ""),
                address=_safe_get_string(poi, "address") if address is not None else None,
            ))
        
        # 构建返回结果
        suggestion_data = {}
        if data.get("suggestion"):
            suggestion_data["keywords"] = data["suggestion"].get("keywords")
            suggestion_data["cities"] = suggestion_cities
        
        return TextSearchResult(
            suggestion=suggestion_data if suggestion_data else None,
            pois=pois if pois else None
        )
        
    except requests.exceptions.RequestException as e:
        return TextSearchResult(error=f"网络请求失败: {str(e)}")
    except Exception as e:
        return TextSearchResult(error=f"处理过程中发生未知错误: {str(e)}")

@mcp.tool()
def maps_around_search(location: str, radius: str = "5000", keywords: str = "") -> AroundSearchResult:
    """高德地图周边搜索服务。
    当用户需要"找附近/周边X米/公里内的餐厅/加油站/厕所等"时，**必须直接调用此函数**，无需其他距离验证。
    
    禁止先大范围搜索再用 maps_distance 逐个验证的低效做法
    
    根据用户传入的关键词以及坐标位置，搜索指定半径范围内的 POI。
    
    Args:
        location: 中心点坐标。规则：经度和纬度用","分割，经度在前，纬度在后，经纬度小数点后不得超过6位。必填。
                  例如："116.481488,39.990464"
        radius: 查询半径。取值范围:0-50000。规则：大于50000按默认值，单位：米。可选，默认 5000。
        keywords: 查询关键字。规则：只支持一个关键字。可选，不指定关键词时返回周边所有POI。
    
    Returns:
        AroundSearchResult: 包含搜索结果的对象。
                         成功时包含 suggestion（搜索建议，包含关键词建议和城市建议）和 pois（POI结果列表）字段。
                         Suggestion，城市建议列表，当搜索的文本关键字在限定城市中没有返回时会返回建议城市列表；
                         - keywords 关键字
                         - cities 城市列表
                           - name 名称
                           - num 该城市包含此关键字的个数
                           - citycode 该城市的citycode
                           - adcode 该城市的adcode
                         搜索成功时，pois列表中包括以下字段：
                         - id (str): POI唯一标识
                         - name (str): POI名称
                         - address (str): 地址
                         - location (str): POI坐标，格式为"经度,纬度"
                         失败时包含 error 字段。
    """
    try:
        try:
            radius_int = int(radius)
            if radius_int > 50000:
                radius = "5000"
        except (ValueError, TypeError):
            radius = "5000"

        pois = []
        for page in range(1, 6):
            params = {
                "key": get_amap_api_key(),
                "location": location,
                "radius": radius,
                "page": page,
                "offset": 20,
            }
            if keywords:
                params["keywords"] = keywords
            response = _amap_http_get(
                "https://restapi.amap.com/v3/place/around", params=params
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") != "1":
                return AroundSearchResult(error=f"高德API周边搜索失败: {data.get('info', '未知错误')}")
            for poi in data.get("pois", []):
                addr = poi.get("address")
                loc = poi.get("location")
                pois.append(AroundSearchPOI(
                    id=_safe_get_string(poi, "id", ""),
                    name=_safe_get_string(poi, "name", ""),
                    address=_safe_get_string(poi, "address") if addr is not None else None,
                    location=_safe_get_string(poi, "location") if loc is not None else None,
                ))

        seen = set()
        deduped = []
        for p in pois:
            if p.id and p.id not in seen:
                seen.add(p.id)
                deduped.append(p)
            elif not p.id:
                deduped.append(p)
        return AroundSearchResult(pois=deduped if deduped else None)

    except requests.exceptions.RequestException as e:
        return AroundSearchResult(error=f"网络请求失败: {str(e)}")
    except Exception as e:
        return AroundSearchResult(error=f"处理过程中发生未知错误: {str(e)}")

@mcp.tool()
def maps_search_detail(id: str) -> POIDetailResult:
    """高德地图POI详情查询服务。
    
    查询通过关键词搜索或周边搜索获取到的POI ID的详细信息。
    
    Args:
        id: AOI唯一标识。最多可以传入1个id，传入目标区域的poiid即可。必填。
    
    Returns:
        POIDetailResult: 包含POI详细信息的对象。
                         成功时包含id、name、location、address、business_area、city、alias、biz_ext等字段。
                         biz_ext字段包含扩展信息，如营业时间、评分、价格等。
                         失败时包含 error 字段。
    """
    try:
        response = _amap_http_get(
            "https://restapi.amap.com/v3/place/detail",
            params={
                "key": get_amap_api_key(),
                "id": id
            }
        )
        data = response.json()
        
        if data.get("status") != "1":
            error_info = data.get('info', '未知错误')
            return POIDetailResult(error=f"高德API POI详情查询失败: {error_info}")
        
        if not data.get("pois") or len(data.get("pois", [])) == 0:
            return POIDetailResult(error="未找到POI信息")
        
        poi = data["pois"][0]
        
        # 使用辅助函数安全地获取可能返回空列表的字符串字段
        # 对于 Optional 字段，如果不是字符串则返回 None
        business_area_val = poi.get("business_area")
        business_area = _safe_get_string(poi, "business_area") if business_area_val is not None else None
        
        alias_val = poi.get("alias")
        alias = _safe_get_string(poi, "alias") if alias_val is not None else None
        
        # 提取基本信息
        id_val = poi.get("id")
        name_val = poi.get("name")
        location_val = poi.get("location")
        address_val = poi.get("address")
        city_val = poi.get("cityname")
        tel_val = poi.get("tel")
        entr_location_val = poi.get("entr_location")
        parking_type_val = poi.get("parking_type")
        
        # 提取扩展信息（biz_ext），归一化 rating 为 float 或移除无效值
        biz_ext = None
        if poi.get("biz_ext"):
            biz_ext = dict(poi["biz_ext"])
            if "rating" in biz_ext:
                raw = biz_ext["rating"]
                if isinstance(raw, list):
                    raw = raw[0] if raw else None
                try:
                    if raw is not None and raw != "":
                        biz_ext["rating"] = float(raw)
                    else:
                        del biz_ext["rating"]
                except (TypeError, ValueError):
                    del biz_ext["rating"]

        return POIDetailResult(
            id=_safe_get_string(poi, "id") if id_val is not None else None,
            name=_safe_get_string(poi, "name") if name_val is not None else None,
            location=_safe_get_string(poi, "location") if location_val is not None else None,
            address=_safe_get_string(poi, "address") if address_val is not None else None,
            business_area=business_area,
            city=_safe_get_string(poi, "cityname") if city_val is not None else None,
            alias=alias,
            tel=_safe_get_string(poi, "tel") if tel_val is not None else None,
            biz_ext=biz_ext,
            entr_location=_safe_get_string(poi, "entr_location") if entr_location_val is not None else None,
            parking_type=_safe_get_string(poi, "parking_type") if parking_type_val is not None else None
        )
        
    except requests.exceptions.RequestException as e:
        return POIDetailResult(error=f"网络请求失败: {str(e)}")
    except Exception as e:
        return POIDetailResult(error=f"处理过程中发生未知错误: {str(e)}")

@mcp.tool()
def maps_polygon_search(polygon: str, keywords: str = "") -> PolygonSearchResult:
    """高德地图多边形区域内 POI 搜索服务。

    根据用户传入的多边形顶点坐标（或矩形左上、右下两顶点），在区域内搜索 POI。
    适用于「某块区域内的餐厅/学校/加油站」等按范围筛选的场景。

    Args:
        polygon: 多边形顶点坐标。规则：经度和纬度用","分割，经度在前纬度在后，坐标对用"|"分割；矩形时可只传左上、右下两顶点；非矩形时首尾坐标对需相同。必填。
                 例如："116.460988,40.006919|116.48231,40.007381|116.47516,39.99713|116.460988,40.006919"
        keywords: 查询关键字。规则：只支持一个关键字。可选，不指定关键词时返回区域内默认类型 POI。

    Returns:
        PolygonSearchResult: 包含搜索结果的对象。
                            成功时包含 pois（POI 列表，含 id、name、address、location）和 count（总数）；
                            失败时包含 error 字段。
    """
    try:
        params = {
            "key": get_amap_api_key(),
            "polygon": polygon,
            "offset": "20",
            "page": "1",
            "extensions": "base",
        }
        if keywords:
            params["keywords"] = keywords

        response = _amap_http_get("https://restapi.amap.com/v3/place/polygon", params=params)
        data = response.json()

        if data.get("status") != "1":
            error_info = data.get("info", "未知错误")
            return PolygonSearchResult(error=f"高德API多边形搜索失败: {error_info}")

        pois = []
        for poi in data.get("pois", []):
            addr = poi.get("address")
            loc = poi.get("location")
            pois.append(
                PolygonSearchPOI(
                    id=_safe_get_string(poi, "id", ""),
                    name=_safe_get_string(poi, "name", ""),
                    address=_safe_get_string(poi, "address") if addr is not None else None,
                    location=_safe_get_string(poi, "location") if loc is not None else None,
                )
            )

        count = data.get("count")
        if isinstance(count, str):
            count_val = count
        elif count is not None:
            count_val = str(count)
        else:
            count_val = None

        return PolygonSearchResult(
            pois=pois if pois else None,
            count=count_val,
        )
    except requests.exceptions.RequestException as e:
        return PolygonSearchResult(error=f"网络请求失败: {str(e)}")
    except Exception as e:
        return PolygonSearchResult(error=f"处理过程中发生未知错误: {str(e)}")

@mcp.tool()
def amap_input_tips(
    keywords: str,
    type: str = "",
    location: str = "",
    city: str = "",
    citylimit: str = "false",
    datatype: str = "all",
) -> InputTipsResult:
    """高德地图输入提示服务。

    根据用户输入的关键词返回建议列表，适用于输入联想场景（如输入「仙林」后出现相关提示）。

    Args:
        keywords: 查询关键词。必填。
        type: POI 分类。可选：分类名称或分类代码，多个用「|」分隔，建议使用分类代码。
        location: 坐标，格式「经度,纬度」。可选，传入后在附近优先返回；在 city 不为空时生效。
        city: 搜索城市。可选：citycode 或 adcode，如 010/110000。填入后优先返回该城市数据。
        citylimit: 仅返回指定城市数据。可选：true/false。默认 false。
        datatype: 返回数据类型。可选：all、poi、bus、busline，多种用「|」分隔。默认 all。

    Returns:
        InputTipsResult: 成功时包含 count（结果总数）和 tips（提示列表，每项含 id、name、district、adcode、location、address）；
                        失败时包含 error。
    """
    try:
        params = {
            "key": get_amap_api_key(),
            "keywords": keywords,
        }
        if type:
            params["type"] = type
        if location:
            params["location"] = location
        if city:
            params["city"] = city
        if citylimit:
            params["citylimit"] = citylimit
        if datatype and datatype != "all":
            params["datatype"] = datatype

        response = _amap_http_get(
            "https://restapi.amap.com/v3/assistant/inputtips",
            params=params,
        )
        data = response.json()

        status = data.get("status")
        if status != "1" and status != 1:
            error_info = data.get("info", "未知错误")
            return InputTipsResult(error=f"高德输入提示失败: {error_info}")

        count_val = data.get("count", 0)
        try:
            count_int = int(count_val) if count_val is not None else 0
        except (TypeError, ValueError):
            count_int = 0

        tips_list = []
        for tip in data.get("tips", []):
            loc_str = _safe_get_string(tip, "location", "")
            addr_str = _safe_get_string(tip, "address", "")
            tips_list.append(
                InputTipItem(
                    id=_safe_get_string(tip, "id", ""),
                    name=_safe_get_string(tip, "name", ""),
                    district=_safe_get_string(tip, "district", ""),
                    adcode=_safe_get_string(tip, "adcode", ""),
                    location=loc_str or None,
                    address=addr_str or None,
                )
            )

        return InputTipsResult(
            count=count_int if count_int else None,
            tips=tips_list if tips_list else None,
        )
    except requests.exceptions.RequestException as e:
        return InputTipsResult(error=f"网络请求失败: {str(e)}")
    except Exception as e:
        return InputTipsResult(error=f"处理过程中发生未知错误: {str(e)}")


class CoordinateConvertResult(BaseModel):
    """坐标转换结果"""
    locations: Optional[str] = Field(
        default=None,
        description="转换后的高德坐标。多个坐标用分号';'分隔，单个坐标为'经度,纬度'。"
    )
    error: Optional[str] = Field(
        default=None,
        description="错误信息，仅在失败时存在"
    )


class CoordinateConvertInput(BaseModel):
    """坐标转换工具输入参数"""
    locations: str = Field(
        description="待转换的坐标点。经度和纬度用英文逗号','分割，经度在前、纬度在后，小数点后不得超过6位；多个坐标对之间用竖线'|'分隔，最多40对。例如：'116.481028,39.989643' 或 '116.481028,39.989643|114.481028,39.989643'"
    )
    coordsys: str = Field(
        default="gps",
        description="原坐标系。可选值：gps（GPS 坐标）、mapbar（mapbar 坐标）、baidu（百度坐标）、autonavi（高德坐标，不转换）。可选，默认 gps。"
    )


@mcp.tool()
def amap_coordinate_convert(locations: str, coordsys: str = "gps") -> CoordinateConvertResult:
    """高德地图坐标转换服务。

    将非高德坐标（GPS、mapbar、百度）转换为高德坐标，便于后续使用高德逆地理、路径规划等服务。

    Args:
        locations: 坐标点。经度、纬度用英文逗号分隔，经度在前纬度在后，小数点后不超过6位；多组坐标用竖线'|'分隔，最多40对。例如："116.481028,39.989643" 或 "116.481028,39.989643|114.481028,39.989643"。
        coordsys: 原坐标系。可选：gps、mapbar、baidu、autonavi（不转换）。默认 gps。

    Returns:
        CoordinateConvertResult: 成功时 locations 为转换后的高德坐标（多组用分号';'分隔）；失败时 error 为错误原因。
    """
    base_url = "https://restapi.amap.com/v3/assistant/coordinate/convert"
    params = {
        "key": get_amap_api_key(),
        "locations": locations,
        "coordsys": coordsys,
        "output": "json",
    }

    try:
        response = _amap_http_get(base_url, params=params)
        data = response.json()

        if data.get("status") != "1":
            error_info = data.get("info", "未知错误")
            return CoordinateConvertResult(error=f"高德坐标转换失败: {error_info}")

        result_locations = data.get("locations")
        if result_locations is None:
            return CoordinateConvertResult(error="接口未返回转换后的坐标")
        if not isinstance(result_locations, str):
            return CoordinateConvertResult(error="接口返回的 locations 格式异常")

        return CoordinateConvertResult(locations=result_locations.strip())

    except requests.exceptions.RequestException as e:
        return CoordinateConvertResult(error=f"网络请求异常: {str(e)}")
    except Exception as e:
        return CoordinateConvertResult(error=f"处理过程中发生未知错误: {str(e)}")


class StaticMapResult(BaseModel):
    """静态地图结果"""
    image_url: Optional[str] = Field(default=None, description="地图图片URL，成功时包含")
    image_data: Optional[bytes] = Field(default=None, description="地图图片二进制数据，成功时包含")
    error: Optional[str] = Field(default=None, description="错误信息，仅在失败时存在")

class StaticMapInput(BaseModel):
    """静态地图工具输入参数"""
    location: str = Field(
        description="地图中心点坐标。规则：经度在前，纬度在后，用英文逗号','分隔。例如：'116.481488,39.990464'"
    )
    zoom: Optional[str] = Field(
        default="10",
        description="地图缩放级别。可选值：1-18。可选，默认10。"
    )
    size: Optional[str] = Field(
        default="400*400",
        description="图片尺寸。格式：宽*高，例如：'400*400'。可选，默认'400*400'。"
    )
    markers: Optional[str] = Field(
        default=None,
        description="标注点标记。格式：标注样式|标注位置|标注内容，多个标注用'|'分隔。可选。"
    )
    labels: Optional[str] = Field(
        default=None,
        description="文本标签。格式：标签样式|标签位置|标签内容，多个标签用'|'分隔。可选。"
    )
    paths: Optional[str] = Field(
        default=None,
        description="折线。格式：折线样式|折线坐标点，多个折线用'|'分隔。可选。"
    )

class LiveWeatherItem(BaseModel):
    """实况天气单条"""
    province: str = Field(default="", description="省份名")
    city: str = Field(default="", description="城市名")
    adcode: str = Field(default="", description="区域编码")
    weather: str = Field(default="", description="天气现象（汉字描述）")
    temperature: str = Field(default="", description="实时气温，单位：摄氏度")
    winddirection: str = Field(default="", description="风向描述")
    windpower: str = Field(default="", description="风力级别，单位：级")
    humidity: str = Field(default="", description="空气湿度")

class ForecastCastItem(BaseModel):
    """预报单日（casts 中一项）"""
    date: str = Field(default="", description="日期")
    week: str = Field(default="", description="星期几")
    dayweather: str = Field(default="", description="白天天气现象")
    nightweather: str = Field(default="", description="晚上天气现象")
    daytemp: str = Field(default="", description="白天温度")
    nighttemp: str = Field(default="", description="晚上温度")
    daywind: str = Field(default="", description="白天风向")
    nightwind: str = Field(default="", description="晚上风向")
    daypower: str = Field(default="", description="白天风力")
    nightpower: str = Field(default="", description="晚上风力")

class ForecastItem(BaseModel):
    """预报天气一组（某城市多日）"""
    city: str = Field(default="", description="城市名称")
    adcode: str = Field(default="", description="城市编码")
    province: str = Field(default="", description="省份名称")
    casts: List[ForecastCastItem] = Field(default_factory=list, description="当天起连续几日预报")

class WeatherResult(BaseModel):
    """天气查询结果"""
    lives: Optional[List[LiveWeatherItem]] = Field(
        default=None,
        description="实况天气（extensions=base 时返回）"
    )
    forecasts: Optional[List[ForecastItem]] = Field(
        default=None,
        description="预报天气（extensions=all 时返回）"
    )
    error: Optional[str] = Field(default=None, description="错误信息，仅在失败时存在")

class WeatherQueryInput(BaseModel):
    """天气查询工具输入参数"""
    city: str = Field(
        description="城市编码，即 adcode。可参考高德城市编码表。必填。例如：110000（北京）"
    )
    extensions: str = Field(
        default="base",
        description="气象类型。base：返回实况天气；all：返回预报天气（当天及未来几日）。可选，默认 base。"
    )

@mcp.tool()
def amap_weather_query(city: str, extensions: str = "base") -> WeatherResult:
    """高德地图天气查询服务。

    根据城市 adcode 查询该区域当前实况天气或未来几日预报天气。

    Args:
        city: 城市编码（adcode），必填。如 110000（北京）。
        extensions: 气象类型。base：实况天气；all：预报天气（含当天及未来几日）。默认 base。

    Returns:
        WeatherResult: 成功时 lives 为实况列表（base）或 forecasts 为预报列表（all）；失败时 error 为错误原因。
    """
    base_url = "https://restapi.amap.com/v3/weather/weatherInfo"
    params = {
        "key": get_amap_api_key(),
        "city": city,
        "extensions": extensions,
        "output": "json",
    }

    try:
        response = _amap_http_get(base_url, params=params)
        data = response.json()

        if data.get("status") != "1":
            error_info = data.get("info", "未知错误")
            return WeatherResult(error=f"高德天气查询失败: {error_info}")

        lives_out: Optional[List[LiveWeatherItem]] = None
        forecasts_out: Optional[List[ForecastItem]] = None

        raw_lives = data.get("lives")
        if isinstance(raw_lives, list) and len(raw_lives) > 0:
            lives_out = []
            for item in raw_lives:
                if not isinstance(item, dict):
                    continue
                lives_out.append(LiveWeatherItem(
                    province=_safe_get_string(item, "province"),
                    city=_safe_get_string(item, "city"),
                    adcode=_safe_get_string(item, "adcode"),
                    weather=_safe_get_string(item, "weather"),
                    temperature=_safe_get_string(item, "temperature"),
                    winddirection=_safe_get_string(item, "winddirection"),
                    windpower=_safe_get_string(item, "windpower"),
                    humidity=_safe_get_string(item, "humidity"),
                ))

        raw_forecasts = data.get("forecasts")
        if isinstance(raw_forecasts, list) and len(raw_forecasts) > 0:
            forecasts_out = []
            for f in raw_forecasts:
                if not isinstance(f, dict):
                    continue
                raw_casts = f.get("casts") or []
                casts_list: List[ForecastCastItem] = []
                if isinstance(raw_casts, list):
                    for c in raw_casts:
                        if not isinstance(c, dict):
                            continue
                        casts_list.append(ForecastCastItem(
                            date=_safe_get_string(c, "date"),
                            week=_safe_get_string(c, "week"),
                            dayweather=_safe_get_string(c, "dayweather"),
                            nightweather=_safe_get_string(c, "nightweather"),
                            daytemp=_safe_get_string(c, "daytemp"),
                            nighttemp=_safe_get_string(c, "nighttemp"),
                            daywind=_safe_get_string(c, "daywind"),
                            nightwind=_safe_get_string(c, "nightwind"),
                            daypower=_safe_get_string(c, "daypower"),
                            nightpower=_safe_get_string(c, "nightpower"),
                        ))
                forecasts_out.append(ForecastItem(
                    city=_safe_get_string(f, "city"),
                    adcode=_safe_get_string(f, "adcode"),
                    province=_safe_get_string(f, "province"),
                    casts=casts_list,
                ))

        if lives_out is None and forecasts_out is None:
            return WeatherResult(error="接口未返回天气数据")

        return WeatherResult(lives=lives_out, forecasts=forecasts_out)

    except requests.exceptions.RequestException as e:
        return WeatherResult(error=f"网络请求异常: {str(e)}")
    except Exception as e:
        return WeatherResult(error=f"处理过程中发生未知错误: {str(e)}")


class IpLocationResult(BaseModel):
    """IP 定位结果"""
    province: Optional[str] = Field(
        default=None,
        description="省份名称。直辖市显示直辖市名；局域网 IP 返回「局域网」；非法或国外 IP 为空。"
    )
    city: Optional[str] = Field(
        default=None,
        description="城市名称。直辖市显示直辖市名；局域网/非法/国外 IP 为空。"
    )
    adcode: Optional[str] = Field(
        default=None,
        description="城市 adcode 编码，可参考高德城市编码表。"
    )
    rectangle: Optional[str] = Field(
        default=None,
        description="所在城市矩形区域范围，左下右上坐标对。"
    )
    error: Optional[str] = Field(
        default=None,
        description="错误信息，仅在失败时存在"
    )

class IpLocationInput(BaseModel):
    """IP 定位工具输入参数"""
    ip: str = Field(
        default="",
        description="待定位的 IPv4 地址（仅支持国内）。不填则使用请求方 IP 定位。可选。"
    )

@mcp.tool()
def amap_ip_location(ip: str = "") -> IpLocationResult:
    """高德地图 IP 定位服务。

    根据 IPv4 地址查询其所在省份、城市、adcode 及城市矩形范围。仅支持国内 IP；局域网返回「局域网」，非法或国外 IP 省/市为空。

    Args:
        ip: 待定位的 IPv4 地址（仅国内）。不填则使用请求方 IP。可选。

    Returns:
        IpLocationResult: 成功时包含 province、city、adcode、rectangle；失败时 error 为错误原因。
    """
    base_url = "https://restapi.amap.com/v3/ip"
    params = {
        "key": get_amap_api_key(),
        "output": "json",
    }
    if ip and ip.strip():
        params["ip"] = ip.strip()

    try:
        response = _amap_http_get(base_url, params=params)
        data = response.json()

        if data.get("status") != "1":
            error_info = data.get("info", "未知错误")
            return IpLocationResult(error=f"高德 IP 定位失败: {error_info}")

        def _s(v: str) -> Optional[str]:
            if v is None or (isinstance(v, str) and not v.strip()):
                return None
            return v.strip() if isinstance(v, str) else None

        province = _s(data.get("province"))
        city = _s(data.get("city"))
        adcode = _s(data.get("adcode"))
        rectangle = _s(data.get("rectangle"))

        return IpLocationResult(
            province=province,
            city=city,
            adcode=adcode,
            rectangle=rectangle,
        )

    except requests.exceptions.RequestException as e:
        return IpLocationResult(error=f"网络请求异常: {str(e)}")
    except Exception as e:
        return IpLocationResult(error=f"处理过程中发生未知错误: {str(e)}")


class BusLineItem(BaseModel):
    """途经该站的公交线路一条"""
    id: str = Field(default="", description="公交线路唯一 id")
    location: str = Field(default="", description="线路途径此站的经纬度")
    name: str = Field(default="", description="线路名称")
    start_stop: str = Field(default="", description="首发站")
    end_stop: str = Field(default="", description="末站")

class BusStopItem(BaseModel):
    """公交站信息"""
    id: str = Field(default="", description="公交站 id")
    name: str = Field(default="", description="公交站名")
    location: str = Field(default="", description="经纬度")
    adcode: str = Field(default="", description="城市 adcode")
    citycode: str = Field(default="", description="城市 citycode")
    buslines: List[BusLineItem] = Field(default_factory=list, description="途径此站的公交路线列表")

class BusStopResult(BaseModel):
    """公交站 ID 查询结果"""
    busstops: List[BusStopItem] = Field(default_factory=list, description="公交车站信息列表")
    error: Optional[str] = Field(default=None, description="错误信息，仅在失败时存在")

class BusStopInput(BaseModel):
    """公交站 ID 查询工具输入参数"""
    id: str = Field(
        description="公交站 id。必填。例如：BV10006672"
    )


@mcp.tool()
def amap_bus_stop_id(id: str) -> BusStopResult:
    """高德地图公交站 ID 查询服务。

    通过公交站点 ID 查询该站详细信息，包括站名、经纬度、adcode、citycode 及途径此站的所有公交线路（线路名、首末站等）。

    Args:
        id: 公交站 id，必填。例如 BV10006672。

    Returns:
        BusStopResult: 成功时 busstops 为公交站信息列表，每站含 id、name、location、adcode、citycode、buslines（线路列表）；失败时 error 为错误原因。
    """
    base_url = "https://restapi.amap.com/v3/bus/stopid"
    params = {
        "key": get_amap_api_key(),
        "id": id.strip(),
        "output": "json",
        "extensions": "base",
    }

    try:
        response = _amap_http_get(base_url, params=params)
        data = response.json()

        if data.get("status") != "1":
            error_info = data.get("info", "未知错误")
            return BusStopResult(error=f"高德公交站 ID 查询失败: {error_info}")

        raw_busstops = data.get("busstops")
        if not isinstance(raw_busstops, list):
            return BusStopResult(busstops=[])

        busstops_out: List[BusStopItem] = []
        for stop in raw_busstops:
            if not isinstance(stop, dict):
                continue
            raw_buslines = stop.get("buslines") or []
            buslines_list: List[BusLineItem] = []
            if isinstance(raw_buslines, list):
                for bl in raw_buslines:
                    if not isinstance(bl, dict):
                        continue
                    buslines_list.append(BusLineItem(
                        id=_safe_get_string(bl, "id"),
                        location=_safe_get_string(bl, "location"),
                        name=_safe_get_string(bl, "name"),
                        start_stop=_safe_get_string(bl, "start_stop"),
                        end_stop=_safe_get_string(bl, "end_stop"),
                    ))
            busstops_out.append(BusStopItem(
                id=_safe_get_string(stop, "id"),
                name=_safe_get_string(stop, "name"),
                location=_safe_get_string(stop, "location"),
                adcode=_safe_get_string(stop, "adcode"),
                citycode=_safe_get_string(stop, "citycode"),
                buslines=buslines_list,
            ))

        return BusStopResult(busstops=busstops_out)

    except requests.exceptions.RequestException as e:
        return BusStopResult(error=f"网络请求异常: {str(e)}")
    except Exception as e:
        return BusStopResult(error=f"处理过程中发生未知错误: {str(e)}")


class BusStopInLine(BaseModel):
    """线路途径站一条"""
    id: str = Field(default="", description="公交站 ID")
    name: str = Field(default="", description="公交站名")
    location: str = Field(default="", description="公交站经纬度")
    sequence: str = Field(default="", description="公交站序号")


class BusRouteItem(BaseModel):
    """公交线路详情（公交路线 ID 查询单条）"""
    id: str = Field(default="", description="公交线路 id")
    type: str = Field(default="", description="公交类型，如普通公交、地铁、轻轨等")
    name: str = Field(default="", description="线路名称")
    polyline: str = Field(default="", description="坐标串")
    citycode: str = Field(default="", description="城市 citycode")
    start_stop: str = Field(default="", description="首发站")
    end_stop: str = Field(default="", description="末站")
    start_time: str = Field(default="", description="首班车时间")
    end_time: str = Field(default="", description="末班车时间")
    uicolor: str = Field(default="", description="线路 UI 颜色")
    timedesc: str = Field(default="", description="线路详细时间，JSON 串")
    distance: str = Field(default="", description="全程里程，单位：公里")
    loop: str = Field(default="", description="是否环线，0 否 1 是")
    status: str = Field(default="", description="线路状态，0 停运 1 正常 2 规划中 3 在建")
    direc: str = Field(default="", description="反向线路 id")
    company: str = Field(default="", description="所属公司")
    basic_price: str = Field(default="", description="起步价，单位：元")
    total_price: str = Field(default="", description="全程票价，单位：元")
    bounds: str = Field(default="", description="矩形区域")
    busstops: List[BusStopInLine] = Field(default_factory=list, description="途径站，extensions=all 时返回")


class BusLineResult(BaseModel):
    """公交路线 ID 查询结果"""
    buslines: List[BusRouteItem] = Field(default_factory=list, description="公交线路信息列表")
    error: Optional[str] = Field(default=None, description="错误信息，仅在失败时存在")


class BusLineInput(BaseModel):
    """公交路线 ID 查询工具输入参数"""
    id: str = Field(
        description="公交线路 id。必填。例如：131000010042"
    )
    extensions: str = Field(
        default="base",
        description="返回范围。base：基本信息；all：基本+途径站点、首末班时间等。可选，默认 base。"
    )


@mcp.tool()
def amap_bus_line_id(id: str, extensions: str = "base") -> BusLineResult:
    """高德地图公交路线 ID 查询服务。

    通过公交线路 ID 查询该线路详细信息，包括线路名、类型、首末站、首末班时间、票价、途径站点（extensions=all 时）等。

    Args:
        id: 公交线路 id，必填。例如 131000010042。
        extensions: base 返回基本信息；all 返回基本+途径站点、首末班车时间等。默认 base。

    Returns:
        BusLineResult: 成功时 buslines 为线路列表，每项含 id、type、name、start_stop、end_stop、start_time、end_time、distance、busstops 等；失败时 error 为错误原因。
    """
    base_url = "https://restapi.amap.com/v3/bus/lineid"
    params = {
        "key": get_amap_api_key(),
        "id": id.strip(),
        "output": "json",
        "extensions": (extensions or "base").strip().lower(),
    }
    if params["extensions"] not in ("base", "all"):
        params["extensions"] = "base"

    try:
        response = _amap_http_get(base_url, params=params)
        data = response.json()

        if data.get("status") != "1":
            error_info = data.get("info", "未知错误")
            return BusLineResult(error=f"高德公交路线 ID 查询失败: {error_info}")

        raw_buslines = data.get("buslines")
        if not isinstance(raw_buslines, list):
            return BusLineResult(buslines=[])

        buslines_out: List[BusRouteItem] = []
        for line in raw_buslines:
            if not isinstance(line, dict):
                continue
            raw_stops = line.get("busstops") or []
            stops_list: List[BusStopInLine] = []
            if isinstance(raw_stops, list):
                for s in raw_stops:
                    if not isinstance(s, dict):
                        continue
                    stops_list.append(BusStopInLine(
                        id=_safe_get_string(s, "id"),
                        name=_safe_get_string(s, "name"),
                        location=_safe_get_string(s, "location"),
                        sequence=_safe_get_string(s, "sequence"),
                    ))
            buslines_out.append(BusRouteItem(
                id=_safe_get_string(line, "id"),
                type=_safe_get_string(line, "type"),
                name=_safe_get_string(line, "name"),
                polyline=_safe_get_string(line, "polyline"),
                citycode=_safe_get_string(line, "citycode"),
                start_stop=_safe_get_string(line, "start_stop"),
                end_stop=_safe_get_string(line, "end_stop"),
                start_time=_safe_get_string(line, "start_time"),
                end_time=_safe_get_string(line, "end_time"),
                uicolor=_safe_get_string(line, "uicolor"),
                timedesc=_safe_get_string(line, "timedesc"),
                distance=_safe_get_string(line, "distance"),
                loop=_safe_get_string(line, "loop"),
                status=_safe_get_string(line, "status"),
                direc=_safe_get_string(line, "direc"),
                company=_safe_get_string(line, "company"),
                basic_price=_safe_get_string(line, "basic_price"),
                total_price=_safe_get_string(line, "total_price"),
                bounds=_safe_get_string(line, "bounds"),
                busstops=stops_list,
            ))

        return BusLineResult(buslines=buslines_out)

    except requests.exceptions.RequestException as e:
        return BusLineResult(error=f"网络请求异常: {str(e)}")
    except Exception as e:
        return BusLineResult(error=f"处理过程中发生未知错误: {str(e)}")


class BusLineKeywordResult(BaseModel):
    """公交路线关键字查询结果"""
    buslines: List[BusRouteItem] = Field(default_factory=list, description="公交线路信息列表")
    error: Optional[str] = Field(default=None, description="错误信息，仅在失败时存在")


class BusLineKeywordInput(BaseModel):
    """公交路线关键字查询工具输入参数"""
    keywords: str = Field(
        description="查询关键字，只支持一个关键字。必填。"
    )
    city: str = Field(
        description="城市。可选值：城市中文/全拼、citycode、adcode。不填默认全国。必填。例如：110000"
    )
    offset: str = Field(
        default="20",
        description="每页记录数，大于 100 按默认值。可选，默认 20。"
    )
    page: str = Field(
        default="1",
        description="当前页数，最大翻页数 10。可选，默认 1。"
    )
    extensions: str = Field(
        default="base",
        description="返回范围。base：基本信息；all：基本+途径站点、首末班时间等。可选，默认 base。"
    )


@mcp.tool()
def amap_bus_line_keyword(
    keywords: str,
    city: str,
    offset: str = "20",
    page: str = "1",
    extensions: str = "base",
) -> BusLineKeywordResult:
    """高德地图公交路线关键字查询服务。

    通过公交线路名称（关键字）查询该线路的详细信息，支持分页。返回线路 id、类型、名称、首末站、坐标串等；extensions=all 时含途径站点、首末班时间等。

    Args:
        keywords: 查询关键字，只支持一个。必填。
        city: 城市，城市名/citycode/adcode。必填。例如 110000（北京）。
        offset: 每页记录数，默认 20，大于 100 按默认。可选。
        page: 当前页，默认 1，最大 10。可选。
        extensions: base 基本信息；all 基本+途径站点、首末班时间等。默认 base。可选。

    Returns:
        BusLineKeywordResult: 成功时 buslines 为线路列表，每项结构同公交路线 ID 查询；失败时 error 为错误原因。
    """
    base_url = "https://restapi.amap.com/v3/bus/linename"
    params = {
        "key": get_amap_api_key(),
        "keywords": keywords.strip(),
        "city": city.strip(),
        "offset": (offset or "20").strip(),
        "page": (page or "1").strip(),
        "extensions": (extensions or "base").strip().lower(),
        "output": "json",
    }
    if params["extensions"] not in ("base", "all"):
        params["extensions"] = "base"

    try:
        response = _amap_http_get(base_url, params=params)
        data = response.json()

        if data.get("status") != "1":
            error_info = data.get("info", "未知错误")
            return BusLineKeywordResult(error=f"高德公交路线关键字查询失败: {error_info}")

        raw_buslines = data.get("buslines")
        if not isinstance(raw_buslines, list):
            return BusLineKeywordResult(buslines=[])

        buslines_out: List[BusRouteItem] = []
        for line in raw_buslines:
            if not isinstance(line, dict):
                continue
            raw_stops = line.get("busstops") or []
            stops_list: List[BusStopInLine] = []
            if isinstance(raw_stops, list):
                for s in raw_stops:
                    if not isinstance(s, dict):
                        continue
                    stops_list.append(BusStopInLine(
                        id=_safe_get_string(s, "id"),
                        name=_safe_get_string(s, "name"),
                        location=_safe_get_string(s, "location"),
                        sequence=_safe_get_string(s, "sequence"),
                    ))
            buslines_out.append(BusRouteItem(
                id=_safe_get_string(line, "id"),
                type=_safe_get_string(line, "type"),
                name=_safe_get_string(line, "name"),
                polyline=_safe_get_string(line, "polyline"),
                citycode=_safe_get_string(line, "citycode"),
                start_stop=_safe_get_string(line, "start_stop"),
                end_stop=_safe_get_string(line, "end_stop"),
                start_time=_safe_get_string(line, "start_time"),
                end_time=_safe_get_string(line, "end_time"),
                uicolor=_safe_get_string(line, "uicolor"),
                timedesc=_safe_get_string(line, "timedesc"),
                distance=_safe_get_string(line, "distance"),
                loop=_safe_get_string(line, "loop"),
                status=_safe_get_string(line, "status"),
                direc=_safe_get_string(line, "direc"),
                company=_safe_get_string(line, "company"),
                basic_price=_safe_get_string(line, "basic_price"),
                total_price=_safe_get_string(line, "total_price"),
                bounds=_safe_get_string(line, "bounds"),
                busstops=stops_list,
            ))

        return BusLineKeywordResult(buslines=buslines_out)

    except requests.exceptions.RequestException as e:
        return BusLineKeywordResult(error=f"网络请求异常: {str(e)}")
    except Exception as e:
        return BusLineKeywordResult(error=f"处理过程中发生未知错误: {str(e)}")



def get_amap_tools():
    """
    获取高德地图工具列表

    Returns:
        List[Tool]: LangChain 工具列表
    """
    # 基础工具
    regeocode_tool = tool(regeocode_amap_location, args_schema=RegeocodeInput)
    bicycling_route_tool = tool(maps_bicycling_by_coordinates, args_schema=BicyclingRouteInput)
    driving_route_tool = tool(maps_driving_by_coordinates, args_schema=DrivingRouteInput)
    walking_route_tool = tool(maps_walking_by_coordinates, args_schema=WalkingRouteInput)
    distance_tool = tool(maps_distance, args_schema=DistanceInput)
    text_search_tool = tool(maps_text_search, args_schema=TextSearchInput)
    around_search_tool = tool(maps_around_search, args_schema=AroundSearchInput)
    polygon_search_tool = tool(maps_polygon_search, args_schema=PolygonSearchInput)
    poi_detail_tool = tool(maps_search_detail, args_schema=POIDetailInput)

    # 扩展工具（坐标转换、天气、IP 定位、智能硬件定位、公交、静态地图等）
    extra_tools = get_amap_extra_tools()

    amap_tools = [
        regeocode_tool,
        bicycling_route_tool,
        driving_route_tool,
        walking_route_tool,
        distance_tool,
        text_search_tool,
        around_search_tool,
        polygon_search_tool,
        poi_detail_tool,
        *extra_tools,
    ]

    return amap_tools


def get_amap_extra_tools():
    """
    获取高德地图扩展工具列表（坐标转换、天气查询、IP 定位、智能硬件定位、公交站/路线 ID 与关键字查询、静态地图等）。

    Returns:
        List[Tool]: LangChain 工具列表
    """
    return [
        tool(amap_input_tips, args_schema=InputTipsInput),
        tool(amap_coordinate_convert, args_schema=CoordinateConvertInput),
        tool(amap_weather_query, args_schema=WeatherQueryInput),
        tool(amap_ip_location, args_schema=IpLocationInput),
        tool(amap_bus_stop_id, args_schema=BusStopInput),
        tool(amap_bus_line_id, args_schema=BusLineInput),
        tool(amap_bus_line_keyword, args_schema=BusLineKeywordInput),
    ]

# --- 主程序入口：根据 @mcp.tool() 装饰的工具生成 amap_tools_descriptions.json ---
async def _generate_tool_descriptions_json():
    """
    生成工具描述 JSON 文件。
    收集所有用 @mcp.tool() 装饰的工具的描述信息，并保存到 JSON 文件中。
    """
    def serialize_schema(schema):
        """序列化 schema 对象为字典"""
        if schema is None:
            return {}
        if hasattr(schema, 'model_dump'):
            return schema.model_dump()
        if hasattr(schema, 'dict'):
            return schema.dict()
        if isinstance(schema, dict):
            return schema
        return {}
    
    try:
        # 获取所有工具
        tools = await mcp.list_tools()
        
        # 构建工具描述列表
        tools_descriptions = []
        for tool in tools:
            tool_info = {
                "name": tool.name,
                "description": tool.description or "",
                "inputSchema": serialize_schema(tool.inputSchema),
            }
            
            # 添加可选字段
            if hasattr(tool, 'title') and tool.title:
                tool_info["title"] = tool.title
            if hasattr(tool, 'outputSchema') and tool.outputSchema:
                tool_info["outputSchema"] = serialize_schema(tool.outputSchema)
            if hasattr(tool, 'annotations') and tool.annotations:
                annotations = tool.annotations
                if hasattr(annotations, 'model_dump'):
                    tool_info["annotations"] = annotations.model_dump()
                elif hasattr(annotations, 'dict'):
                    tool_info["annotations"] = annotations.dict()
                elif isinstance(annotations, dict):
                    tool_info["annotations"] = annotations
            
            tools_descriptions.append(tool_info)
        
        # 构建最终输出结构
        output_data = {
            "tools": tools_descriptions,
            "total_count": len(tools_descriptions),
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 输出文件路径
        output_file = os.path.join(_current_file_dir, "amap_tools_descriptions.json")
        
        # 保存到 JSON 文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 成功生成工具描述文件: {output_file}")
        print(f"✓ 共包含 {len(tools_descriptions)} 个工具")
        
        # 打印工具列表
        print("\n工具列表:")
        for i, tool_info in enumerate(tools_descriptions, 1):
            desc = tool_info['description']
            desc_preview = desc[:60] + "..." if len(desc) > 60 else desc
            print(f"  {i}. {tool_info['name']}: {desc_preview}")
        
        return output_data
        
    except Exception as e:
        print(f"✗ 生成工具描述文件时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # 生成工具描述 JSON 文件
    asyncio.run(_generate_tool_descriptions_json())
    # print(maps_around_search(location="116.481488,39.990464", radius=1000, keywords="网吧"))