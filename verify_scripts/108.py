
"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 距离约束(附近2km)：用 maps_around_search(location=107.970090,26.569880; radius=2000; keywords=政务服务中心) 搜索，验证返回pois中包含 target_poi_id=B0FFHFZNOY。
2) 骑行距离<=1.8km：对 target_poi_id 调用 maps_search_detail 得到目标location=107.980538,26.568962；调用 maps_bicycling_by_coordinates(origin=107.970090,26.569880, destination=107.980538,26.568962)，验证 total_distance_meters<=1800。
3) 步行时间<=30分钟：调用 maps_walking_by_coordinates(origin=107.970090,26.569880, destination=107.980538,26.568962)，验证 total_duration_seconds<=1800。
4) 到凯里站驾车时间<=8分钟：调用 maps_text_search(keywords=station_address, city=station_city) 取 poi_id，再 maps_search_detail(id=poi_id) 得到 凯里站坐标；调用 maps_driving_by_coordinates，验证 total_duration_seconds<=480。
5) 绕行增量时间<=8分钟：
a) 直接去凯里站：maps_driving_by_coordinates(origin=107.970090,26.569880, destination=107.975951,26.602770) 得到T_direct。
b) 先去政务中心再去凯里站：maps_driving_by_coordinates(origin=107.970090,26.569880, destination=107.980538,26.568962) 得到T_leg1；再 maps_driving_by_coordinates(origin=107.980538,26.568962, destination=107.975951,26.602770) 得到T_leg2；计算T_via=T_leg1+T_leg2。
c) 验证 (T_via - T_direct) <= 480秒。
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
    maps_search_detail,
    maps_bicycling_by_coordinates,
    maps_walking_by_coordinates ,
    maps_driving_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "107.970090,26.569880",
    search_radius: int = 2000,  # 2km
    keywords: str = "政务服务中心",
    max_bicycling_distance: int = 1800,  # 1.8km
    max_walking_duration: int = 1800,  # 30 minutes = 1800 seconds
    station_address: str = "凯里站",
    station_city: str = "黔东南",
    max_driving_duration_to_station: int = 480,  # 8 minutes = 480 seconds
    max_detour_duration: int = 480  # 8 minutes = 480 seconds
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 距离约束(附近2km)：用 maps_around_search 搜索，验证返回pois中包含 target_poi_id。
    2) 骑行距离<=1.8km：调用 maps_search_detail 得到目标location；调用 maps_bicycling_by_coordinates，验证 total_distance_meters<=1800。
    3) 步行时间<=30分钟：调用 maps_walking_by_coordinates，验证 total_duration_seconds<=1800。
    4) 到凯里站驾车时间<=8分钟：调用得到凯里站坐标；调用 maps_driving_by_coordinates，验证 total_duration_seconds<=480。
    5) 绕行增量时间<=8分钟：计算直接路线和绕行路线的时间差，验证 (T_via - T_direct) <= 480秒。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"107.970090,26.569880"
        search_radius: 搜索半径（米），默认2000（2公里）
        keywords: 搜索关键词，默认"政务服务中心"
        max_bicycling_distance: 最大骑行距离（米），默认1800（1.8公里）
        max_walking_duration: 最大步行时长（秒），默认1800（30分钟）
        station_address: 车站地址，默认"凯里站"
        station_city: 车站所在城市，默认"黔东南"
        max_driving_duration_to_station: 到车站的最大驾车时长（秒），默认480（8分钟）
        max_detour_duration: 最大绕行增量时间（秒），默认480（8分钟）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 距离约束（附近2公里）
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

    # 步骤3: 骑行距离<=1.8km
    bicycling_result = maps_bicycling_by_coordinates(origin=user_location, destination=poi_location)
    if bicycling_result.error:
        print(f"❌ 计算骑行路线失败: {bicycling_result.error}")
        return False

    if bicycling_result.total_distance_meters is None:
        print(f"❌ 无法获取骑行距离")
        return False

    bicycling_distance = bicycling_result.total_distance_meters
    if bicycling_distance > max_bicycling_distance:
        print(f"❌ 骑行距离{bicycling_distance}米，超过{max_bicycling_distance}米（{max_bicycling_distance / 1000}公里）")
        return False
    print(f"✅ 骑行距离{bicycling_distance}米，符合要求（<= {max_bicycling_distance}米，即{max_bicycling_distance / 1000}公里）")

    # 步骤4: 步行时间<=30分钟
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

    # 步骤5: 获取车站坐标（用 maps_text_search + maps_search_detail 替代 maps_geo）
    station_text_result = maps_text_search(keywords=station_address, city=station_city)
    if station_text_result.error:
        print(f"❌ 获取车站坐标失败: {station_text_result.error}")
        return False

    if not station_text_result.pois or len(station_text_result.pois) == 0:
        print(f"❌ 未找到车站坐标")
        return False

    first_poi_id = station_text_result.pois[0].id
    station_detail_result = maps_search_detail(id=first_poi_id)
    if station_detail_result.error:
        print(f"❌ 获取坐标失败: {station_detail_result.error}")
        return False
    if not station_detail_result.location:
        print("❌ 未获取到坐标")
        return False

    station_location = station_detail_result.location
    print(f"✅ 获取车站坐标: {station_location} ({station_address})")

    # 步骤6: 到车站驾车时间<=8分钟
    driving_result_to_station = maps_driving_by_coordinates(origin=poi_location, destination=station_location)
    if driving_result_to_station.error:
        print(f"❌ 计算从POI到车站的驾车路线失败: {driving_result_to_station.error}")
        return False

    if driving_result_to_station.total_duration_seconds is None:
        print(f"❌ 无法获取从POI到车站的驾车时长")
        return False

    driving_duration_to_station = driving_result_to_station.total_duration_seconds
    if driving_duration_to_station > max_driving_duration_to_station:
        print(f"❌ 从POI到车站的驾车时长{driving_duration_to_station}秒，超过{max_driving_duration_to_station}秒（{max_driving_duration_to_station // 60}分钟）")
        return False
    print(f"✅ 从POI到车站的驾车时长{driving_duration_to_station}秒，符合要求（<= {max_driving_duration_to_station}秒，即{max_driving_duration_to_station // 60}分钟）")

    # 步骤7: 绕行增量时间<=8分钟
    # a) 直接去车站
    driving_result_direct = maps_driving_by_coordinates(origin=user_location, destination=station_location)
    if driving_result_direct.error:
        print(f"❌ 计算从用户位置直接到车站的驾车路线失败: {driving_result_direct.error}")
        return False

    if driving_result_direct.total_duration_seconds is None:
        print(f"❌ 无法获取从用户位置直接到车站的驾车时长")
        return False

    t_direct = driving_result_direct.total_duration_seconds
    print(f"✅ 从用户位置直接到车站的驾车时长: {t_direct}秒")

    # b) 先去POI再去车站
    driving_result_leg1 = maps_driving_by_coordinates(origin=user_location, destination=poi_location)
    if driving_result_leg1.error:
        print(f"❌ 计算从用户位置到POI的驾车路线失败: {driving_result_leg1.error}")
        return False

    if driving_result_leg1.total_duration_seconds is None:
        print(f"❌ 无法获取从用户位置到POI的驾车时长")
        return False

    t_leg1 = driving_result_leg1.total_duration_seconds
    print(f"✅ 从用户位置到POI的驾车时长: {t_leg1}秒")

    driving_result_leg2 = maps_driving_by_coordinates(origin=poi_location, destination=station_location)
    if driving_result_leg2.error:
        print(f"❌ 计算从POI到车站的驾车路线失败: {driving_result_leg2.error}")
        return False

    if driving_result_leg2.total_duration_seconds is None:
        print(f"❌ 无法获取从POI到车站的驾车时长")
        return False

    t_leg2 = driving_result_leg2.total_duration_seconds
    print(f"✅ 从POI到车站的驾车时长: {t_leg2}秒")

    t_via = t_leg1 + t_leg2
    detour_time = t_via - t_direct
    print(f"✅ 绕行路线总时长: {t_via}秒，绕行增量时间: {detour_time}秒")

    if detour_time > max_detour_duration:
        print(f"❌ 绕行增量时间{detour_time}秒，超过{max_detour_duration}秒（{max_detour_duration // 60}分钟）")
        return False
    print(f"✅ 绕行增量时间{detour_time}秒，符合要求（<= {max_detour_duration}秒，即{max_detour_duration // 60}分钟）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 717.py 文件...\n")
    result = verify_poi(poi_id="B0FFHFZNOY")
    print(f"\n验证结果: {result}")
