"""
修改任务指令：你想找一个附近2公里内的自习室。你打算骑行过去，骑行时间必须在8分钟以内；同时你也考虑打车备选，所以从你这里出发驾车过去不能超过25分钟。为了方便转地铁，那个自习室附近800米需要至少有一个地铁站。你"自信、有条理、有创造力，但没有耐心。"

验证任务说明：
验证目标POI（自习室）是否符合以下要求：

目标POI ID: B0K3S7G0OE
用户位置: 113.646377,34.769937
目标POI坐标: 113.652738,34.774369

验证步骤：
1) 周边候选集验证：调用 maps_around_search(location="113.646377,34.769937", radius="2000", keywords="自习室")，
   确认返回pois数量>=8，且目标poi_id=B0K3S7G0OE 在pois列表中。

2) POI详情与评分（若有）：调用 maps_search_detail(id="B0K3S7G0OE") 获取目标POI的location。

3) 骑行时间验证：调用 maps_bicycling_by_coordinates(origin="113.646377,34.769937", destination="113.652738,34.774369")，
   验证 total_duration_seconds <= 480（8分钟）。

4) 驾车时间验证：调用 maps_driving_by_coordinates(origin="113.646377,34.769937", destination="113.652738,34.774369")，
   验证 total_duration_seconds <= 1500（25分钟）。

5) 地铁站距离验证：以目标POI的location为中心，调用 maps_around_search(location="113.652738,34.774369", radius="800", keywords="地铁站")，
   验证返回的pois数量>=1（即存在至少一个800米内的地铁站）。
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
    maps_driving_by_coordinates,
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str = "B0K3S7G0OE",
    user_location: str = "113.646377,34.769937",
    poi_location: str = "113.652738,34.774369",  # 目标POI坐标
    search_radius: int = 2000,  # 2000米
    keywords: str = "自习室",
    min_pois_count: int = 8,  # 最少POI数量
    max_bicycling_duration_seconds: int = 480,  # 骑行最大时间8分钟=480秒
    max_driving_duration_seconds: int = 1500,  # 驾车最大时间25分钟=1500秒
    subway_search_radius: int = 800,  # 地铁站搜索半径800米
) -> bool:
    """
    验证POI是否符合要求
    
    Args:
        poi_id: 目标POI ID，默认 "B0K3S7G0OE"
        user_location: 用户坐标，格式为"经度,纬度"，默认 "113.646377,34.769937"
        poi_location: 目标POI坐标，格式为"经度,纬度"，默认 "113.652738,34.774369"
        search_radius: 搜索半径（米），默认 2000
        keywords: 搜索关键词，默认 "自习室"
        min_pois_count: 最少POI数量要求，默认 8
        max_bicycling_duration_seconds: 骑行最大时间（秒），默认 480（8分钟）
        max_driving_duration_seconds: 驾车最大时间（秒），默认 1500（25分钟）
        subway_search_radius: 地铁站搜索半径（米），默认 800
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    print("=" * 60)
    print("开始验证POI...")
    print(f"目标POI ID: {poi_id}")
    print(f"用户位置: {user_location}")
    print(f"目标POI坐标: {poi_location}")
    print("=" * 60)
    
    # ==================== 步骤1: 周边候选集验证 ====================
    print("\n【步骤1】周边候选集验证（2000米内，POI数量>=8）")
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
    
    # 验证POI数量>=8
    if pois_count < min_pois_count:
        print(f"  ❌ POI数量 {pois_count} 少于要求的 {min_pois_count}")
        return False
    print(f"  ✅ POI数量验证通过（{pois_count} >= {min_pois_count}）")
    
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
    
    # ==================== 步骤2: POI详情与评分（若有） ====================
    print("\n【步骤2】POI详情获取")
    print(f"  获取POI详情: id={poi_id}")
    
    poi_detail = maps_search_detail(id=poi_id)
    
    if poi_detail.error:
        print(f"  ❌ 获取POI详情失败: {poi_detail.error}")
        return False
    
    print(f"  POI名称: {poi_detail.name}")
    print(f"  POI地址: {poi_detail.address}")
    print(f"  POI坐标: {poi_detail.location}")
    
    # 获取评分（若有）
    if poi_detail.biz_ext:
        rating_str = poi_detail.biz_ext.get("rating", "")
        if rating_str:
            print(f"  POI评分: {rating_str}")
        else:
            print(f"  POI评分: 未提供")
    else:
        print(f"  biz_ext信息: 未提供")
    
    # 使用从详情获取的location，如果没有则使用预设的poi_location
    target_poi_location = poi_detail.location if poi_detail.location else poi_location
    print(f"  ✅ POI详情获取成功，坐标: {target_poi_location}")
    
    # ==================== 步骤3: 骑行时间验证（<=8分钟） ====================
    print("\n【步骤3】骑行时间验证（<=8分钟）")
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
    
    bicycling_duration_seconds = bicycling_result.total_duration_seconds
    bicycling_duration_minutes = bicycling_duration_seconds / 60
    
    print(f"  骑行时长: {bicycling_duration_seconds}秒（约{bicycling_duration_minutes:.2f}分钟）")
    
    if bicycling_duration_seconds > max_bicycling_duration_seconds:
        print(f"  ❌ 骑行时长 {bicycling_duration_seconds}秒 超过最大限制 {max_bicycling_duration_seconds}秒（{max_bicycling_duration_seconds // 60}分钟）")
        return False
    print(f"  ✅ 骑行时间验证通过（{bicycling_duration_seconds}秒 <= {max_bicycling_duration_seconds}秒）")
    
    # ==================== 步骤4: 驾车时间验证（<=25分钟） ====================
    print("\n【步骤4】驾车时间验证（<=25分钟）")
    print(f"  计算驾车路线: origin={user_location}, destination={target_poi_location}")
    
    driving_result = maps_driving_by_coordinates(
        origin=user_location,
        destination=target_poi_location
    )
    
    if driving_result.error:
        print(f"  ❌ 计算驾车路线失败: {driving_result.error}")
        return False
    
    if driving_result.total_duration_seconds is None:
        print(f"  ❌ 无法获取驾车时长")
        return False
    
    driving_duration_seconds = driving_result.total_duration_seconds
    driving_duration_minutes = driving_duration_seconds / 60
    
    print(f"  驾车时长: {driving_duration_seconds}秒（约{driving_duration_minutes:.2f}分钟）")
    
    if driving_duration_seconds > max_driving_duration_seconds:
        print(f"  ❌ 驾车时长 {driving_duration_seconds}秒 超过最大限制 {max_driving_duration_seconds}秒（{max_driving_duration_seconds // 60}分钟）")
        return False
    print(f"  ✅ 驾车时间验证通过（{driving_duration_seconds}秒 <= {max_driving_duration_seconds}秒）")
    
    # ==================== 步骤5: 地铁站距离验证 ====================
    print("\n【步骤5】地铁站距离验证（800米内至少1个地铁站）")
    print(f"  搜索参数: location={target_poi_location}, radius={subway_search_radius}, keywords=地铁站")
    
    subway_search_result = maps_around_search(
        location=target_poi_location,
        radius=str(subway_search_radius),
        keywords="地铁站"
    )
    
    if subway_search_result.error:
        print(f"  ❌ 搜索周边地铁站失败: {subway_search_result.error}")
        return False
    
    if not subway_search_result.pois or len(subway_search_result.pois) == 0:
        print(f"  ❌ {subway_search_radius}米内未找到地铁站")
        return False
    
    subway_count = len(subway_search_result.pois)
    first_subway = subway_search_result.pois[0]
    
    print(f"  找到 {subway_count} 个地铁站")
    print(f"  最近的地铁站: {first_subway.name}")
    print(f"  地铁站坐标: {first_subway.location}")
    
    if subway_count < 1:
        print(f"  ❌ 地铁站数量 {subway_count} 少于要求的 1 个")
        return False
    print(f"  ✅ 地铁站验证通过（{subway_count} >= 1）")
    
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
