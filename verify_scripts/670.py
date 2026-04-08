"""
修改任务指令:你要找一个附近3公里内的便利店，骑共享单车过去全程不要超过8分钟。你准备办点急事，想选一家评分至少4.0分的。你还要求这家店周围1.5公里内有一个步行15分钟能到的公交站（按步行导航时间算）。你逻辑性强但没有耐心，希望高效沟通，讨厌废话。



验证方法：验证目标POI（便利店）是否符合要求
目标POI ID: B0K0OXMZMO
用户位置: 126.981897,46.643969

验证步骤：
1) 距离约束（附近3公里内）：以用户坐标126.981897,46.643969为中心，
   调用maps_around_search(location='126.981897,46.643969', radius='3000', keywords='便利店')，
   验证返回pois中包含target_poi_id=B0K0OXMZMO。

2) 骑行耗时<=8分钟：先用maps_search_detail(id='B0K0OXMZMO')获取目标POI坐标destination，
   然后调用maps_bicycling_by_coordinates(origin='126.981897,46.643969', destination=destination)，
   验证total_duration_seconds<=480。

3) 评分>=4.0：调用maps_search_detail(id='B0K0OXMZMO')，读取biz_ext.rating，验证rating>=4.0。

4) 步行15分钟内到公交站：以目标POI坐标为中心调用maps_around_search(location=destination, radius='1500', keywords='公交站')
   获取公交站poi坐标stop_loc；再调用maps_walking_by_coordinates(origin=destination, destination=stop_loc)，
   验证total_duration_seconds<=900。
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
    maps_walking_by_coordinates,
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str = "B0K0OXMZMO",
    user_location: str = "126.981897,46.643969",
    search_radius: int = 3000,  # 3km
    keywords: str = "便利店",
    max_bicycling_duration: int = 480,  # 8分钟 = 480秒
    min_rating: float = 4.0,  # 最低评分
    bus_stop_search_radius: int = 1500,  # 公交站搜索半径1500米
    bus_stop_keywords: str = "公交站",
    max_walking_to_bus_stop: int = 900,  # 步行到公交站最大15分钟 = 900秒
) -> bool:
    """
    验证POI是否符合要求
    
    Args:
        poi_id: 目标POI ID，默认 "B0K0OXMZMO"
        user_location: 用户坐标，格式为"经度,纬度"，默认 "126.981897,46.643969"
        search_radius: 搜索半径（米），默认 3000（3公里）
        keywords: 搜索关键词，默认 "便利店"
        max_bicycling_duration: 骑行最大时长（秒），默认 480（8分钟）
        min_rating: 最低评分要求，默认 4.0
        bus_stop_search_radius: 公交站搜索半径（米），默认 1500
        bus_stop_keywords: 公交站搜索关键词，默认 "公交站"
        max_walking_to_bus_stop: 步行到公交站最大时长（秒），默认 900（15分钟）
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    print("=" * 60)
    print("开始验证POI...")
    print(f"目标POI ID: {poi_id}")
    print(f"用户位置: {user_location}")
    print("=" * 60)
    
    # ==================== 步骤1: 距离约束（附近3公里内） ====================
    print("\n【步骤1】距离约束验证（附近3公里内）")
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
    
    # ==================== 步骤2: 骑行耗时<=8分钟 ====================
    print("\n【步骤2】骑行耗时验证（<=8分钟）")
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
    
    # ==================== 步骤3: 评分>=4.0 ====================
    print("\n【步骤3】评分约束验证（>=4.0分）")
    
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
    
    # ==================== 步骤4: 步行15分钟内到公交站 ====================
    print("\n【步骤4】步行到公交站验证（<=15分钟）")
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
    bus_stop_location = first_bus_stop.location
    
    print(f"  找到 {bus_stop_count} 个公交站")
    print(f"  最近的公交站: {first_bus_stop.name}")
    print(f"  公交站坐标: {bus_stop_location}")
    
    if not bus_stop_location:
        print(f"  ❌ 公交站没有location信息")
        return False
    
    # 计算步行时间
    print(f"  计算步行路线: origin={target_poi_location}, destination={bus_stop_location}")
    
    walking_result = maps_walking_by_coordinates(
        origin=target_poi_location,
        destination=bus_stop_location
    )
    
    if walking_result.error:
        print(f"  ❌ 计算步行路线失败: {walking_result.error}")
        return False
    
    if walking_result.total_duration_seconds is None:
        print(f"  ❌ 无法获取步行时长")
        return False
    
    walking_duration = walking_result.total_duration_seconds
    walking_duration_minutes = walking_duration / 60
    
    print(f"  步行到公交站时长: {walking_duration}秒（约{walking_duration_minutes:.1f}分钟）")
    
    if walking_duration > max_walking_to_bus_stop:
        print(f"  ❌ 步行时长 {walking_duration}秒 超过最大限制 {max_walking_to_bus_stop}秒（{max_walking_to_bus_stop // 60}分钟）")
        return False
    print(f"  ✅ 步行到公交站验证通过（{walking_duration}秒 <= {max_walking_to_bus_stop}秒）")
    
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
