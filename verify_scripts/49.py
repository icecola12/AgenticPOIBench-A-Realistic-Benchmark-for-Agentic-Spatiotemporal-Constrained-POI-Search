"""
修改任务指令：你要在附近2.5公里内找一个充电桩站点。你打算骑车过去，骑行距离不能超过1公里，同时你也需要确认开车过去不超过5分钟。这个充电站附近300米内必须能找到药店，方便你顺路买点常用药。你情绪化，时而冷静时而愤怒，态度变化快。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 调用 maps_around_search(location=用户坐标, radius=2500, keywords=充电站)，验证返回pois里包含 target_poi_id。
2) 调用 maps_search_detail(id=target_poi_id) 获取目标POI坐标 destination。
3) 调用 maps_bicycling_by_coordinates(origin=用户坐标, destination=destination)，验证 total_distance_meters <= 1000。
4) 调用 maps_driving_by_coordinates(origin=用户坐标, destination=destination)，验证 total_duration_seconds <= 300。
5) 调用 maps_distance(origins=用户坐标, destination=destination)，验证 distance <= 1000（直线距离不超过1公里）。
6) 调用 maps_around_search(location=destination, radius=300, keywords=药店)，验证返回pois数量>=1（附近300米内存在药店）。
"""

import os
import sys

# 将 src 加入 sys.path，以便从 src/tools/amap_tools 导入
_current_file_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_file_dir)
_src_dir = os.path.join(_project_root, "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

# 导入高德地图工具函数
from tools.amap_tools import (
    maps_search_detail,
    maps_bicycling_by_coordinates,
    maps_driving_by_coordinates,
    maps_distance
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "113.902675,35.294147",
    poi_location: str = None,
    search_radius: int = 2500,
    keywords: str = "充电站",
    max_bicycling_distance: int = 1000,  # 1公里 = 1000米
    max_driving_duration: int = 300,  # 5分钟 = 300秒
    max_straight_distance: int = 1000,  # 1公里 = 1000米
    pharmacy_search_radius: int = 300,
    pharmacy_keywords: str = "药店",
    min_pharmacy_count: int = 1
) -> bool:
    """
    验证POI是否符合要求
    
    验证步骤：
    1) 调用 maps_around_search，验证返回pois里包含目标poi_id。
    2) 调用 maps_search_detail 获取目标POI坐标 destination。
    3) 调用 maps_bicycling_by_coordinates，验证 total_distance_meters <= 1000。
    4) 调用 maps_driving_by_coordinates，验证 total_duration_seconds <= 300。
    5) 调用 maps_distance，验证 distance <= 1000（直线距离不超过1公里）。
    6) 调用 maps_around_search，验证返回pois数量>=1（附近300米内存在药店）。
    
    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"113.902675,35.294147"
        poi_location: POI坐标，格式为"经度,纬度"，如果为None则从详情中获取
        search_radius: 搜索半径（米），默认2500（2.5公里）
        keywords: 搜索关键词，默认"充电站"
        max_bicycling_distance: 最大骑行距离（米），默认1000（1公里）
        max_driving_duration: 最大驾车时长（秒），默认300（5分钟）
        max_straight_distance: 最大直线距离（米），默认1000（1公里）
        pharmacy_search_radius: 药店搜索半径（米），默认300
        pharmacy_keywords: 药店搜索关键词，默认"药店"
        min_pharmacy_count: 最小药店数量，默认1
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 验证返回pois里包含target_poi_id
    print(f"【步骤1】验证周边搜索（{search_radius}米范围内，关键词：{keywords}）")
    print("-" * 80)
    around_search_result = maps_around_search(
        location=user_location,
        radius=str(search_radius),
        keywords=keywords
    )
    if around_search_result.error:
        print(f"❌ 搜索周边POI失败: {around_search_result.error}")
        return False
    
    if not around_search_result.pois:
        print(f"❌ 未找到符合条件的POI")
        return False
    
    # 检查返回列表中是否包含目标POI ID
    poi_found = False
    for poi in around_search_result.pois:
        if poi.id == poi_id:
            poi_found = True
            print(f"✅ 在{search_radius}米范围内找到目标POI: {poi.name} (ID: {poi_id})")
            break
    
    if not poi_found:
        print(f"❌ 目标POI {poi_id} 不在{search_radius}米范围内的{keywords}列表中")
        return False
    
    # 步骤2: 获取目标POI坐标
    print(f"\n【步骤2】获取目标POI坐标")
    print("-" * 80)
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False
    
    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False
    
    destination = poi_detail.location
    print(f"✅ 获取POI坐标: {destination} ({poi_detail.name})")
    
    # 步骤3: 验证骑行距离不超过1公里
    print(f"\n【步骤3】验证骑行距离（<={max_bicycling_distance}米，即{max_bicycling_distance // 1000}公里）")
    print("-" * 80)
    bicycling_result = maps_bicycling_by_coordinates(
        origin=user_location,
        destination=destination
    )
    if bicycling_result.error:
        print(f"❌ 计算骑行路线失败: {bicycling_result.error}")
        return False
    
    if bicycling_result.total_distance_meters is None:
        print(f"❌ 无法获取骑行距离")
        return False
    
    bicycling_distance = bicycling_result.total_distance_meters
    if bicycling_distance > max_bicycling_distance:
        print(f"❌ 骑行距离{bicycling_distance}米，超过{max_bicycling_distance}米（{max_bicycling_distance // 1000}公里）")
        return False
    print(f"✅ 骑行距离{bicycling_distance}米，符合要求（<= {max_bicycling_distance}米，即{max_bicycling_distance // 1000}公里）")
    
    # 步骤4: 验证驾车时间不超过5分钟
    print(f"\n【步骤4】验证驾车时间（<={max_driving_duration}秒，即{max_driving_duration // 60}分钟）")
    print("-" * 80)
    driving_result = maps_driving_by_coordinates(
        origin=user_location,
        destination=destination
    )
    if driving_result.error:
        print(f"❌ 计算驾车路线失败: {driving_result.error}")
        return False
    
    if driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取驾车时长")
        return False
    
    driving_duration = driving_result.total_duration_seconds
    if driving_duration > max_driving_duration:
        print(f"❌ 驾车时长{driving_duration}秒，超过{max_driving_duration}秒（{max_driving_duration // 60}分钟）")
        return False
    print(f"✅ 驾车时长{driving_duration}秒，符合要求（<= {max_driving_duration}秒，即{max_driving_duration // 60}分钟）")
    
    # 步骤5: 验证直线距离不超过1公里
    print(f"\n【步骤5】验证直线距离（<={max_straight_distance}米，即{max_straight_distance // 1000}公里）")
    print("-" * 80)
    distance_result = maps_distance(
        origins=user_location,
        destination=destination
    )
    if distance_result.error:
        print(f"❌ 计算直线距离失败: {distance_result.error}")
        return False
    
    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 未找到距离测量结果")
        return False
    
    straight_distance = distance_result.results[0].distance_meters
    if straight_distance > max_straight_distance:
        print(f"❌ 直线距离{straight_distance}米，超过{max_straight_distance}米（{max_straight_distance // 1000}公里）")
        return False
    print(f"✅ 直线距离{straight_distance}米，符合要求（<= {max_straight_distance}米，即{max_straight_distance // 1000}公里）")
    
    # 步骤6: 验证附近300米内存在药店
    print(f"\n【步骤6】验证附近{pharmacy_search_radius}米内存在{pharmacy_keywords}（数量>={min_pharmacy_count}）")
    print("-" * 80)
    pharmacy_search_result = maps_around_search(
        location=destination,
        radius=str(pharmacy_search_radius),
        keywords=pharmacy_keywords
    )
    if pharmacy_search_result.error:
        print(f"❌ 搜索{pharmacy_keywords}失败: {pharmacy_search_result.error}")
        return False
    
    if not pharmacy_search_result.pois or len(pharmacy_search_result.pois) < min_pharmacy_count:
        print(f"❌ 未找到{pharmacy_keywords}或数量不足（找到{len(pharmacy_search_result.pois) if pharmacy_search_result.pois else 0}个，需要>={min_pharmacy_count}个）")
        return False
    
    print(f"✅ 找到{pharmacy_keywords}: {pharmacy_search_result.pois[0].name} (共{len(pharmacy_search_result.pois)}个)")
    
    print(f"\n✅ 所有验证通过！")
    return True


if __name__ == "__main__":
    # 测试用例
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python 592.py <poi_id> [user_location] [poi_location]")
        print("示例: python 592.py <poi_id>")
        print("示例: python 592.py <poi_id> 113.902675,35.294147")
        print("示例: python 592.py <poi_id> 113.902675,35.294147 113.902675,35.294147")
        print("未传参，使用示例默认值运行。")
        poi_id = "<poi_id>"
        user_location = "113.902675,35.294147"
    else:
        poi_id = sys.argv[1]
        user_location = sys.argv[2] if len(sys.argv) > 2 else "113.902675,35.294147"
        poi_location = sys.argv[3] if len(sys.argv) > 3 else None
        

    print(f"开始验证POI: {poi_id}")
    print(f"用户坐标: {user_location}")
    if poi_location:
        print(f"POI坐标: {poi_location}")
    print("=" * 80)
    
    result = verify_poi(poi_id, user_location=user_location, poi_location=poi_location)
    
    print("=" * 80)
    print(f"验证结果: {'通过' if result else '失败'}")
