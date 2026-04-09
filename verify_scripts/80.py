"""
修改任务指令：你要找一家附近2km以内的百货商店，走路过去不超过22分钟。你需要它离“水口医院公交站”很近，直线距离不要超过500米。另外这家店的评分要在4.0分及以上。你情绪化，时而冷静时而愤怒，态度变化快。


验证方法：验证目标POI（百货商店）是否符合要求
目标POI ID: B0FFIL2UR5
用户位置: 114.444459,23.111859

验证步骤：
1) 用 maps_around_search 以用户坐标(114.444459,23.111859)、半径2000米、关键词"百货商店"检索，
   验证返回pois里包含目标poi_id=B0FFIL2UR5。

2) 用 maps_search_detail(B0FFIL2UR5) 获取评分rating与坐标location，验证 rating>=4.0。

3) 用 maps_text_search(keywords="水口医院", city="惠州") 拿到 poi_id，再 maps_search_detail(poi_id) 获取"水口医院(公交站)"坐标；
   再用 maps_distance(origins=公交站坐标, destination=目标POI坐标) 验证直线距离<=500米。

4) 用 maps_walking_by_coordinates(origin=用户坐标, destination=目标POI坐标) 验证步行总时长<=22分钟(1320秒)。
"""

import sys
import os

# 将 src 加入 sys.path，以便从 src/tools/amap_tools 导入
_current_file_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_file_dir)
_src_dir = os.path.join(_project_root, "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from tools.amap_tools import (
    maps_search_detail,
    maps_text_search,
    maps_walking_by_coordinates,
    maps_distance,
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str = "B0FFIL2UR5",
    user_location: str = "114.444459,23.111859",
    search_radius: int = 2000,  # 2km
    keywords: str = "百货商店",
    min_rating: float = 4.0,  # 最低评分
    bus_stop_address: str = "水口医院",
    bus_stop_city: str = "惠州",
    max_distance_to_bus_stop: int = 500,  # 到公交站最大距离500米
    max_walking_duration: int = 1320,  # 22分钟 = 1320秒
) -> bool:
    """
    验证POI是否符合要求
    
    Args:
        poi_id: 目标POI ID，默认 "B0FFIL2UR5"
        user_location: 用户坐标，格式为"经度,纬度"，默认 "114.444459,23.111859"
        search_radius: 搜索半径（米），默认 2000（2公里）
        keywords: 搜索关键词，默认 "百货商店"
        min_rating: 最低评分要求，默认 4.0
        bus_stop_address: 公交站地址，默认 "水口医院"
        bus_stop_city: 公交站所在城市，默认 "惠州"
        max_distance_to_bus_stop: 到公交站的最大直线距离（米），默认 500
        max_walking_duration: 步行最大时长（秒），默认 1320（22分钟）
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    print("=" * 60)
    print("开始验证POI...")
    print(f"目标POI ID: {poi_id}")
    print(f"用户位置: {user_location}")
    print("=" * 60)
    
    # ==================== 步骤1: 周边搜索验证 ====================
    print("\n【步骤1】周边搜索验证")
    print(f"  搜索参数: location={user_location}, radius={search_radius}, keywords={keywords}")
    
    around_search_result = maps_around_search(
        location=user_location,
        radius=str(search_radius),
        keywords=keywords
    )
    
    if around_search_result.error:
        print(f"  ❌ 搜索周边POI失败: {around_search_result.error}")
        return False
    
    if not around_search_result.pois:
        print(f"  ❌ 未找到符合条件的POI")
        return False
    
    pois_count = len(around_search_result.pois)
    print(f"  找到 {pois_count} 个{keywords}")
    
    # 验证目标POI在列表中
    poi_found = False
    for poi in around_search_result.pois:
        if poi.id == poi_id:
            poi_found = True
            print(f"  ✅ 在{search_radius}米范围内找到目标POI: {poi.name} (ID: {poi_id})")
            break
    
    if not poi_found:
        print(f"  ❌ 目标POI {poi_id} 不在{search_radius}米范围内的{keywords}列表中")
        return False
    
    # ==================== 步骤2: POI评分验证 ====================
    print("\n【步骤2】POI评分验证")
    print(f"  获取POI详情: id={poi_id}")
    
    poi_detail = maps_search_detail(id=poi_id)
    
    if poi_detail.error:
        print(f"  ❌ 获取POI详情失败: {poi_detail.error}")
        return False
    
    print(f"  POI名称: {poi_detail.name}")
    print(f"  POI地址: {poi_detail.address}")
    
    if not poi_detail.location:
        print(f"  ❌ POI没有location信息")
        return False
    
    target_poi_location = poi_detail.location
    print(f"  POI坐标: {target_poi_location}")
    
    # 获取评分
    rating = None
    if poi_detail.biz_ext:
        rating_str = poi_detail.biz_ext.get("rating", "")
        if rating_str:
            try:
                rating = float(rating_str)
            except (ValueError, TypeError):
                rating = None
        print(f"  POI评分: {rating_str if rating_str else '未提供'}")
    else:
        print(f"  未找到biz_ext信息")
    
    if rating is None:
        print(f"  ❌ 无法获取POI评分")
        return False
    
    if rating < min_rating:
        print(f"  ❌ POI评分 {rating} 低于要求的 {min_rating}")
        return False
    print(f"  ✅ 评分验证通过（{rating} >= {min_rating}）")
    
    # ==================== 步骤3: 到公交站距离验证 ====================
    print("\n【步骤3】到公交站距离验证")
    print(f"  获取公交站坐标: keywords={bus_stop_address}, city={bus_stop_city}")
    
    text_search_result = maps_text_search(keywords=bus_stop_address, city=bus_stop_city)
    
    if text_search_result.error:
        print(f"  ❌ 获取公交站坐标失败: {text_search_result.error}")
        return False
    
    if not text_search_result.pois or len(text_search_result.pois) == 0:
        print(f"  ❌ 未找到公交站坐标")
        return False
    
    bus_stop_poi_id = text_search_result.pois[0].id
    bus_stop_detail_result = maps_search_detail(id=bus_stop_poi_id)
    if bus_stop_detail_result.error:
        print(f"  ❌ 获取公交站详情失败: {bus_stop_detail_result.error}")
        return False
    if not bus_stop_detail_result.location:
        print(f"  ❌ 公交站无坐标信息")
        return False
    bus_stop_location = bus_stop_detail_result.location
    bus_stop_formatted_address = bus_stop_detail_result.address or bus_stop_detail_result.name or ""
    print(f"  公交站地址: {bus_stop_formatted_address}")
    print(f"  公交站坐标: {bus_stop_location}")
    
    # 计算直线距离
    print(f"  计算距离: origins={bus_stop_location}, destination={target_poi_location}")
    
    distance_result = maps_distance(
        origins=bus_stop_location,
        destination=target_poi_location
    )
    
    if distance_result.error:
        print(f"  ❌ 计算距离失败: {distance_result.error}")
        return False
    
    if not distance_result.results or len(distance_result.results) == 0:
        print(f"  ❌ 未获取到距离结果")
        return False
    
    distance_to_bus_stop = distance_result.results[0].distance_meters
    print(f"  到公交站的直线距离: {distance_to_bus_stop}米")
    
    if distance_to_bus_stop > max_distance_to_bus_stop:
        print(f"  ❌ 直线距离 {distance_to_bus_stop}米 超过最大限制 {max_distance_to_bus_stop}米")
        return False
    print(f"  ✅ 距离验证通过（{distance_to_bus_stop}米 <= {max_distance_to_bus_stop}米）")
    
    # ==================== 步骤4: 步行可达性验证 ====================
    print("\n【步骤4】步行可达性验证（步行<=22分钟）")
    print(f"  计算步行路线: origin={user_location}, destination={target_poi_location}")
    
    walking_result = maps_walking_by_coordinates(
        origin=user_location,
        destination=target_poi_location
    )
    
    if walking_result.error:
        print(f"  ❌ 计算步行路线失败: {walking_result.error}")
        return False
    
    if walking_result.total_duration_seconds is None:
        print(f"  ❌ 无法获取步行时长")
        return False
    
    walking_duration = walking_result.total_duration_seconds
    walking_duration_minutes = walking_duration / 60
    
    print(f"  步行时长: {walking_duration}秒（约{walking_duration_minutes:.1f}分钟）")
    
    if walking_duration > max_walking_duration:
        print(f"  ❌ 步行时长 {walking_duration}秒 超过最大限制 {max_walking_duration}秒（{max_walking_duration // 60}分钟）")
        return False
    print(f"  ✅ 步行可达性验证通过（{walking_duration}秒 <= {max_walking_duration}秒）")
    
    # ==================== 所有验证通过 ====================
    print("\n" + "=" * 60)
    print("✅ 所有验证通过！")
    print("=" * 60)
    return True


if __name__ == "__main__":
    # 执行验证
    result = verify_poi()
    print(f"\n最终验证结果: {'通过 ✅' if result else '失败 ❌'}")
    sys.exit(0 if result else 1)
