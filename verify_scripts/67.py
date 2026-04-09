
"""
修改任务指令：你想找一家附近3公里内的超市，骑车过去的路程别超过2.5公里。你打算先在超市买完东西，再开车去附近的停车场取车，所以这家超市到附近最近的停车场距离要在300米以内。另外，你从你这里直接开车到这家超市的时间别超过5分钟。你虽然心情不好，但仍然保持礼貌和独立的姿态。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 调用 maps_around_search(location="110.145403,22.639682", radius="3000", keywords="超市")，验证返回pois中包含 target_poi_id= B0FFI152Q6（证明目标超市在3km周边范围内）。
2) 调用 maps_search_detail(id="B0FFI152Q6") 获取目标POI的 location（记为 L_poi）。
3) 调用 maps_bicycling_by_coordinates(origin="110.145403,22.639682", destination=L_poi)，验证 total_distance_meters <= 2500（骑行距离不超过2.5km）。
4) 调用 maps_around_search(location=L_poi, radius="300", keywords="停车场")，验证返回pois列表中数量>0（证明超市附近300米内有停车场）。取最近的停车场POI的 location 记为 L_parking
5) 调用 maps_driving_by_coordinates(origin="110.145403,22.639682", destination=L_poi)，验证 total_duration_seconds <= 300（从你当前位置驾车到超市不超过5分钟）。
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
    maps_driving_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "110.145403,22.639682",
    search_radius: int = 3000,  # 3km
    keywords: str = "超市",
    max_bicycling_distance: int = 2500,  # 2.5km
    parking_search_radius: int = 300,  # 300 meters
    parking_keywords: str = "停车场",
    max_driving_duration: int = 300  # 5 minutes = 300 seconds
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 验证返回pois中包含 target_poi_id（证明目标超市在3km周边范围内）
    2) 获取目标POI的 location（记为 L_poi）
    3) 验证 total_distance_meters <= 2500（骑行距离不超过2.5km）
    4) 验证返回pois列表中数量>0（证明超市附近300米内有停车场）
    5) 验证 total_duration_seconds <= 300（从你当前位置驾车到超市不超过5分钟）

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"110.145403,22.639682"
        search_radius: 搜索半径（米），默认3000（3公里）
        keywords: 搜索关键词，默认"超市"
        max_bicycling_distance: 最大骑行距离（米），默认2500（2.5公里）
        parking_search_radius: 停车场搜索半径（米），默认300
        parking_keywords: 停车场搜索关键词，默认"停车场"
        max_driving_duration: 最大驾车时长（秒），默认300（5分钟）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 周边检索（附近3公里内的超市）
    around_search_result = maps_around_search(
        location=user_location,
        radius=str(search_radius),
        keywords=keywords
    )
    if around_search_result.error:
        print(f"❌ 搜索周边POI失败: {around_search_result.error}")
        return False

    if not around_search_result.pois or len(around_search_result.pois) == 0:
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

    # 步骤2: 获取目标POI的location
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")

    # 步骤3: 骑行距离验证（<= 2.5公里）
    bicycling_result = maps_bicycling_by_coordinates(origin=user_location, destination=poi_location)
    if bicycling_result.error:
        print(f"❌ 计算骑行路线失败: {bicycling_result.error}")
        return False

    if bicycling_result.total_distance_meters is None:
        print(f"❌ 无法获取骑行距离")
        return False

    bicycling_distance = bicycling_result.total_distance_meters
    if bicycling_distance > max_bicycling_distance:
        print(f"❌ 骑行距离{bicycling_distance}米，超过{max_bicycling_distance}米")
        return False
    print(f"✅ 骑行距离{bicycling_distance}米，符合要求（<= {max_bicycling_distance}米）")

    # 步骤4: 停车场邻近验证（300米内有停车场）
    parking_search_result = maps_around_search(
        location=poi_location,
        radius=str(parking_search_radius),
        keywords=parking_keywords
    )
    if parking_search_result.error:
        print(f"❌ 搜索周边停车场失败: {parking_search_result.error}")
        return False

    if not parking_search_result.pois or len(parking_search_result.pois) == 0:
        print(f"❌ {parking_search_radius}米范围内未找到停车场")
        return False

    parking_count = len(parking_search_result.pois)
    print(f"✅ {parking_search_radius}米范围内找到{parking_count}个停车场，符合要求")

    # 取最近的停车场（第一个）
    nearest_parking = parking_search_result.pois[0]
    print(f"✅ 最近的停车场: {nearest_parking.name} (ID: {nearest_parking.id})")

    # 步骤5: 驾车时间验证（<= 5分钟）
    driving_result = maps_driving_by_coordinates(origin=user_location, destination=poi_location)
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

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 638.py 文件...\n")
    result = verify_poi(poi_id="B0FFI152Q6")
    print(f"\n验证结果: {result}")
