
"""
修改任务指令：你想找一个附近2.5km内的政务服务中心。你到那里的步行时间必须不超过15分钟。另外它得在附近2公里内有一个地铁站并且步行12分钟之内能到。你思路混乱，可能会混淆信息，让对话难以跟进。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 用 maps_around_search(location=用户坐标116.367032,39.924774, radius=2500, keywords=政务服务中心) 验证 target_poi_id 在返回列表中（满足"附近2.5km内"）。
2) 用 maps_search_detail(id=target_poi_id) 获取该POI坐标 destination。
3) 用 maps_walking_by_coordinates(origin=116.367032,39.924774, destination=POI坐标) 得到 total_duration_seconds，验证 total_duration_seconds<=900（步行不超过15分钟）。
4) 用 maps_around_search(location=116.367032,39.924774, radius=2000, keywords=地铁站) 获取附近地铁站列表；选择其中"西四(地铁站)" location=116.373332,39.924206。
5) 用 maps_walking_by_coordinates(origin=116.373332,39.924206, destination=POI坐标) 得到 total_duration_seconds，验证 total_duration_seconds<=720（地铁站步行12分钟内可达）。
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
    maps_walking_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "116.367032,39.924774",
    max_walking_duration_from_user: int = 900,  # 15 minutes = 900 seconds
    search_radius: int = 2500,  # 2.5km
    keywords: str = "政务服务中心",
    subway_search_radius: int = 2000,  # 2km
    subway_keywords: str = "地铁站",
    subway_station_name: str = "西四(地铁站)",
    subway_station_location: str = "116.373332,39.924206",
    max_walking_duration_from_subway: int = 720  # 12 minutes = 720 seconds
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 用 maps_around_search 验证 target_poi_id 在返回列表中（满足"附近2.5km内"）。
    2) 用 maps_search_detail 获取该POI坐标 destination。
    3) 用 maps_walking_by_coordinates 得到 total_duration_seconds，验证 total_duration_seconds<=900（步行不超过15分钟）。
    4) 用 maps_around_search 获取附近地铁站列表；选择其中"西四(地铁站)"。
    5) 用 maps_walking_by_coordinates 得到 total_duration_seconds，验证 total_duration_seconds<=720（地铁站步行12分钟内可达）。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"116.367032,39.924774"
        max_walking_duration_from_user: 从用户位置到POI的最大步行时长（秒），默认900（15分钟）
        search_radius: 搜索半径（米），默认2500（2.5公里）
        keywords: 搜索关键词，默认"政务服务中心"
        subway_search_radius: 地铁站搜索半径（米），默认2000（2公里）
        subway_keywords: 地铁站搜索关键词，默认"地铁站"
        subway_station_name: 地铁站名称，默认"西四(地铁站)"
        subway_station_location: 地铁站坐标，格式为"经度,纬度"，默认"116.373332,39.924206"
        max_walking_duration_from_subway: 从地铁站到POI的最大步行时长（秒），默认720（12分钟）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 距离约束（附近2.5公里）
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

    # 步骤2: 获取目标POI坐标
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")

    # 步骤3: 从用户位置到POI的步行时间<=15分钟
    walking_result_from_user = maps_walking_by_coordinates(origin=user_location, destination=poi_location)
    if walking_result_from_user.error:
        print(f"❌ 计算从用户位置到POI的步行路线失败: {walking_result_from_user.error}")
        return False

    if walking_result_from_user.total_duration_seconds is None:
        print(f"❌ 无法获取从用户位置到POI的步行时长")
        return False

    walking_duration_from_user = walking_result_from_user.total_duration_seconds
    if walking_duration_from_user > max_walking_duration_from_user:
        print(f"❌ 从用户位置到POI的步行时长{walking_duration_from_user}秒，超过{max_walking_duration_from_user}秒（{max_walking_duration_from_user // 60}分钟）")
        return False
    print(f"✅ 从用户位置到POI的步行时长{walking_duration_from_user}秒，符合要求（<= {max_walking_duration_from_user}秒，即{max_walking_duration_from_user // 60}分钟）")

    # 步骤4: 搜索附近地铁站，验证"西四(地铁站)"存在
    subway_search_result = maps_around_search(
        location=user_location,
        radius=str(subway_search_radius),
        keywords=subway_keywords
    )
    if subway_search_result.error:
        print(f"❌ 搜索地铁站失败: {subway_search_result.error}")
        return False

    if not subway_search_result.pois or len(subway_search_result.pois) == 0:
        print(f"❌ 未找到地铁站")
        return False

    # 验证"西四(地铁站)"是否在列表中
    subway_found = False
    for subway in subway_search_result.pois:
        if subway_station_name in subway.name:
            subway_found = True
            print(f"✅ 找到地铁站: {subway.name} (共{len(subway_search_result.pois)}个地铁站)")
            break

    if not subway_found:
        print(f"❌ 未找到{subway_station_name}")
        return False

    # 步骤5: 从地铁站到POI的步行时间<=12分钟
    walking_result_from_subway = maps_walking_by_coordinates(origin=subway_station_location, destination=poi_location)
    if walking_result_from_subway.error:
        print(f"❌ 计算从地铁站到POI的步行路线失败: {walking_result_from_subway.error}")
        return False

    if walking_result_from_subway.total_duration_seconds is None:
        print(f"❌ 无法获取从地铁站到POI的步行时长")
        return False

    walking_duration_from_subway = walking_result_from_subway.total_duration_seconds
    if walking_duration_from_subway > max_walking_duration_from_subway:
        print(f"❌ 从地铁站到POI的步行时长{walking_duration_from_subway}秒，超过{max_walking_duration_from_subway}秒（{max_walking_duration_from_subway // 60}分钟）")
        return False
    print(f"✅ 从地铁站到POI的步行时长{walking_duration_from_subway}秒，符合要求（<= {max_walking_duration_from_subway}秒，即{max_walking_duration_from_subway // 60}分钟）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 718.py 文件...\n")
    result = verify_poi(poi_id="B0FFL1PL0J")
    print(f"\n验证结果: {result}")
