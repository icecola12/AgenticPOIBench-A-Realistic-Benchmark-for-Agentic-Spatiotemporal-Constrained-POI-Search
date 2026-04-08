"""
修改任务指令：你要找一个附近2公里内的充电站，骑车过去全程不要超过10分钟。你希望这家充电站在高德上的评分至少有4.8分。另外为了等人更方便，充电站周边300米内要有公交站。你没有耐心，说话直接

验证方法：验证目标POI（充电站）是否符合要求
目标POI ID: B0L1PM55A3
用户位置: 103.747149,29.605968

验证步骤：
1) 距离约束（附近2公里内）：调用 maps_around_search(location="103.747149,29.605968", radius="2000", keywords="充电站")，
   验证返回pois中包含 target_poi_id=B0L1PM55A3。

2) 骑行时间约束（<=10分钟）：对 target_poi_id 调用 maps_search_detail(id="B0L1PM55A3") 获取其 destination 坐标；
   再调用 maps_bicycling_by_coordinates(origin="103.747149,29.605968", destination=destination)，
   验证 total_duration_seconds <= 600。

3) 评分约束（>=4.8分）：调用 maps_search_detail(id="B0L1PM55A3")，读取 biz_ext.rating，验证 rating >= 4.8。

4) 公交站近邻约束（300米内有公交站）：用 maps_search_detail(id="B0L1PM55A3") 获取其 location；
   调用 maps_around_search(location=该location, radius="300", keywords="公交站")，验证返回pois数量>0。
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
    maps_bicycling_by_coordinates,
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str = "B0L1PM55A3",
    user_location: str = "103.747149,29.605968",
    search_radius: int = 2000,  # 2km
    keywords: str = "充电站",
    max_bicycling_duration: int = 600,  # 10分钟 = 600秒
    min_rating: float = 4.8,  # 最低评分
    bus_stop_search_radius: int = 300,  # 公交站搜索半径300米
    bus_stop_keywords: str = "公交站",
) -> bool:
    """
    验证POI是否符合要求
    
    Args:
        poi_id: 目标POI ID，默认 "B0L1PM55A3"
        user_location: 用户坐标，格式为"经度,纬度"，默认 "103.747149,29.605968"
        search_radius: 搜索半径（米），默认 2000（2公里）
        keywords: 搜索关键词，默认 "充电站"
        max_bicycling_duration: 骑行最大时长（秒），默认 600（10分钟）
        min_rating: 最低评分要求，默认 4.8
        bus_stop_search_radius: 公交站搜索半径（米），默认 300
        bus_stop_keywords: 公交站搜索关键词，默认 "公交站"
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    print("=" * 60)
    print("开始验证POI...")
    print(f"目标POI ID: {poi_id}")
    print(f"用户位置: {user_location}")
    print("=" * 60)
    
    # ==================== 步骤1: 距离约束（附近2公里内） ====================
    print("\n【步骤1】距离约束验证（附近2公里内）")
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
    
    # ==================== 步骤2: 骑行时间约束（<=10分钟） ====================
    print("\n【步骤2】骑行时间约束验证（<=10分钟）")
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
    
    # 计算骑行时间
    print(f"  计算骑行路线: origin={user_location}, destination={target_poi_location}")
    
    bicycling_result = maps_bicycling_by_coordinates(
        origin=user_location,
        destination=target_poi_location
    )
    
    if bicycling_result.error:
        print(f"  ❌ 计算骑行路线失败: {bicycling_result.error}")
        return False
    
    if bicycling_result.total_duration_seconds is None:
        print(f"  ❌ 无法获取骑行时长")
        return False
    
    bicycling_duration = bicycling_result.total_duration_seconds
    bicycling_duration_minutes = bicycling_duration / 60
    
    print(f"  骑行时长: {bicycling_duration}秒（约{bicycling_duration_minutes:.1f}分钟）")
    
    if bicycling_duration > max_bicycling_duration:
        print(f"  ❌ 骑行时长 {bicycling_duration}秒 超过最大限制 {max_bicycling_duration}秒（{max_bicycling_duration // 60}分钟）")
        return False
    print(f"  ✅ 骑行时间验证通过（{bicycling_duration}秒 <= {max_bicycling_duration}秒）")
    
    # ==================== 步骤3: 评分约束（>=4.8分） ====================
    print("\n【步骤3】评分约束验证（>=4.8分）")
    
    # 获取评分（已经从步骤2获取了poi_detail）
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
    
    # ==================== 步骤4: 公交站近邻约束（300米内有公交站） ====================
    print("\n【步骤4】公交站近邻约束验证（300米内有公交站）")
    print(f"  搜索参数: location={target_poi_location}, radius={bus_stop_search_radius}, keywords={bus_stop_keywords}")
    
    bus_stop_search_result = maps_around_search(
        location=target_poi_location,
        radius=str(bus_stop_search_radius),
        keywords=bus_stop_keywords
    )
    
    if bus_stop_search_result.error:
        print(f"  ❌ 搜索周边公交站失败: {bus_stop_search_result.error}")
        return False
    
    if not bus_stop_search_result.pois or len(bus_stop_search_result.pois) == 0:
        print(f"  ❌ {bus_stop_search_radius}米内未找到公交站")
        return False
    
    bus_stop_count = len(bus_stop_search_result.pois)
    first_bus_stop = bus_stop_search_result.pois[0]
    print(f"  找到 {bus_stop_count} 个公交站")
    print(f"  最近的公交站: {first_bus_stop.name}")
    print(f"  ✅ 公交站近邻验证通过（{bus_stop_search_radius}米内有 {bus_stop_count} 个公交站）")
    
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
