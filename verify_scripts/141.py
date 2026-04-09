
"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边距离约束：调用 maps_around_search(location='116.02108,36.452701', radius='1500', keywords='洗衣店')，验证返回pois中包含 target_poi_id='B0LRD65HCQ'。
2) 用户到目标步行时间：调用 maps_search_detail('B0LRD65HCQ') 获取 poi_id，再 maps_search_detail(id=poi_id) 获取 目标坐标destination，然后调用 maps_walking_by_coordinates(origin='116.02108,36.452701', destination=目标坐标)，验证 total_duration_seconds ≤ 600（10分钟）。
3) 用户到目标骑行距离：调用 maps_bicycling_by_coordinates(origin='116.02108,36.452701', destination=目标坐标)，验证 total_distance_meters ≤ 1200。
4) 目标到"附近800米内公交站"的最小步行时间：调用 maps_around_search(location=目标坐标, radius='800', keywords='公交站') 得到公交站列表；对列表中每个公交站调用 maps_walking_by_coordinates(origin=目标坐标, destination=该站坐标)，取最小 total_duration_seconds，验证最小值 ≤ 1080（18分钟）。
5) 目标到指定公交站"滨河花园(公交站)"步行距离：在步骤4返回的公交站列表中找到 name='滨河花园(公交站)' 的站点坐标（或用 maps_text_search(keywords='滨河花园(公交站)', city='聊城') 取 poi_id，再 maps_search_detail(id=poi_id) 获取 其坐标），再调用 maps_walking_by_coordinates(origin=目标坐标, destination=该站坐标)，验证 total_distance_meters ≤ 1700。
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
    maps_text_search,
    maps_search_detail ,
    maps_bicycling_by_coordinates,
    maps_walking_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "116.02108,36.452701",
    search_radius: int = 1500,
    keywords: str = "洗衣店",
    max_walking_duration: int = 600,  # 10 minutes = 600 seconds
    max_bicycling_distance: int = 1200,  # 1200 meters
    bus_stop_search_radius: int = 800,
    bus_stop_keywords: str = "公交站",
    max_bus_stop_walking_duration: int = 1080,  # 18 minutes = 1080 seconds
    specific_bus_stop_name: str = "滨河花园(公交站)",
    specific_bus_stop_city: str = "聊城",
    max_specific_bus_stop_distance: int = 1700  # 1700 meters
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 周边距离约束：调用 maps_around_search，验证返回pois中包含目标poi_id。
    2) 用户到目标步行时间：调用 maps_search_detail 获取目标坐标，再调用 maps_walking_by_coordinates，验证 total_duration_seconds ≤ 600。
    3) 用户到目标骑行距离：调用 maps_bicycling_by_coordinates，验证 total_distance_meters ≤ 1200。
    4) 目标到"附近800米内公交站"的最小步行时间：调用 maps_around_search 得到公交站列表，对每个公交站调用 maps_walking_by_coordinates，取最小 total_duration_seconds，验证最小值 ≤ 1080。
    5) 目标到指定公交站"滨河花园(公交站)"步行距离：在步骤4返回的公交站列表中找到该站点坐标，再调用 maps_walking_by_coordinates，验证 total_distance_meters ≤ 1700。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"116.02108,36.452701"
        search_radius: 搜索半径（米），默认1500
        keywords: 搜索关键词，默认"洗衣店"
        max_walking_duration: 最大步行时长（秒），默认600（10分钟）
        max_bicycling_distance: 最大骑行距离（米），默认1200
        bus_stop_search_radius: 公交站搜索半径（米），默认800
        bus_stop_keywords: 公交站搜索关键词，默认"公交站"
        max_bus_stop_walking_duration: 到公交站最大步行时长（秒），默认1080（18分钟）
        specific_bus_stop_name: 指定公交站名称，默认"滨河花园(公交站)"
        specific_bus_stop_city: 指定公交站所在城市，默认"聊城"
        max_specific_bus_stop_distance: 到指定公交站最大步行距离（米），默认1700

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 周边距离约束
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

    # 步骤3: 用户到目标步行时间<=10分钟
    walking_result = maps_walking_by_coordinates(origin=user_location, destination=poi_location)
    if walking_result.error:
        print(f"❌ 计算步行路线失败: {walking_result.error}")
        return False

    if walking_result.total_duration_seconds is None:
        print(f"❌ 无法获取步行时长")
        return False

    walking_duration = walking_result.total_duration_seconds
    if walking_duration > max_walking_duration:
        print(f"❌ 步行时长{walking_duration}秒，超过{max_walking_duration}秒（{max_walking_duration // 60}分钟）")
        return False
    print(f"✅ 步行时长{walking_duration}秒，符合要求（<= {max_walking_duration}秒，即{max_walking_duration // 60}分钟）")

    # 步骤4: 用户到目标骑行距离<=1200米
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

    # 步骤5: 目标到"附近800米内公交站"的最小步行时间
    bus_stop_search_result = maps_around_search(
        location=poi_location,
        radius=str(bus_stop_search_radius),
        keywords=bus_stop_keywords
    )
    if bus_stop_search_result.error:
        print(f"❌ 搜索公交站失败: {bus_stop_search_result.error}")
        return False

    if not bus_stop_search_result.pois or len(bus_stop_search_result.pois) == 0:
        print(f"❌ 未找到公交站")
        return False

    print(f"✅ 找到{len(bus_stop_search_result.pois)}个公交站")

    # 计算到每个公交站的步行时间，找到最小值
    min_bus_stop_duration = None
    for bus_stop in bus_stop_search_result.pois:
        if not bus_stop.location:
            continue

        bus_stop_walking_result = maps_walking_by_coordinates(
            origin=poi_location,
            destination=bus_stop.location
        )
        if bus_stop_walking_result.error or bus_stop_walking_result.total_duration_seconds is None:
            continue

        duration = bus_stop_walking_result.total_duration_seconds
        if min_bus_stop_duration is None or duration < min_bus_stop_duration:
            min_bus_stop_duration = duration

    if min_bus_stop_duration is None:
        print(f"❌ 无法计算到公交站的步行时间")
        return False

    if min_bus_stop_duration > max_bus_stop_walking_duration:
        print(f"❌ 到最近公交站步行时长{min_bus_stop_duration}秒，超过{max_bus_stop_walking_duration}秒（{max_bus_stop_walking_duration // 60}分钟）")
        return False
    print(f"✅ 到最近公交站步行时长{min_bus_stop_duration}秒，符合要求（<= {max_bus_stop_walking_duration}秒，即{max_bus_stop_walking_duration // 60}分钟）")

    # 步骤6: 目标到指定公交站"滨河花园(公交站)"步行距离
    # 首先在步骤5返回的公交站列表中查找
    specific_bus_stop_location = None
    for bus_stop in bus_stop_search_result.pois:
        if bus_stop.name == specific_bus_stop_name:
            specific_bus_stop_location = bus_stop.location
            print(f"✅ 在公交站列表中找到{specific_bus_stop_name}，坐标: {specific_bus_stop_location}")
            break

    # 如果在列表中没找到，使用获取坐标
    if not specific_bus_stop_location:
        print(f"⚠️  在公交站列表中未找到{specific_bus_stop_name}，尝试使用地理编码获取坐标")
        bus_stop_text_result = maps_text_search(keywords=specific_bus_stop_name, city=specific_bus_stop_city)
        if bus_stop_text_result.error:
            print(f"❌ 获取{specific_bus_stop_name}坐标失败: {bus_stop_text_result.error}")
            return False

        if not bus_stop_text_result.pois or len(bus_stop_text_result.pois) == 0:
            print(f"❌ 未找到{specific_bus_stop_name}的坐标")
            return False

        first_poi_id = bus_stop_text_result.pois[0].id
        bus_stop_detail_result = maps_search_detail(id=first_poi_id)
        if bus_stop_detail_result.error:
            print(f"❌ 获取坐标失败: {bus_stop_detail_result.error}")
            return False
        if not bus_stop_detail_result.location:
            print("❌ 未获取到坐标")
            return False

        specific_bus_stop_location = bus_stop_detail_result.location
        print(f"✅ 通过地理编码获取{specific_bus_stop_name}坐标: {specific_bus_stop_location}")

    # 计算到指定公交站的步行距离
    specific_bus_stop_walking_result = maps_walking_by_coordinates(
        origin=poi_location,
        destination=specific_bus_stop_location
    )
    if specific_bus_stop_walking_result.error:
        print(f"❌ 计算到{specific_bus_stop_name}的步行路线失败: {specific_bus_stop_walking_result.error}")
        return False

    if specific_bus_stop_walking_result.total_distance_meters is None:
        print(f"❌ 无法获取到{specific_bus_stop_name}的步行距离")
        return False

    specific_bus_stop_distance = specific_bus_stop_walking_result.total_distance_meters
    if specific_bus_stop_distance > max_specific_bus_stop_distance:
        print(f"❌ 到{specific_bus_stop_name}步行距离{specific_bus_stop_distance}米，超过{max_specific_bus_stop_distance}米")
        return False
    print(f"✅ 到{specific_bus_stop_name}步行距离{specific_bus_stop_distance}米，符合要求（<= {max_specific_bus_stop_distance}米）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 789.py 文件...\\n")
    result = verify_poi(poi_id="B0LRD65HCQ")
    print(f"\n验证结果: {result}")
