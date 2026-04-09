
"""
修改任务指令：你要在附近2500米以内找一座图书馆。你希望先步行到图书馆，再从图书馆打车去金华站，所以你走到图书馆的步行距离不能超过1500米；并且从你家步行到图书馆的时间加上从图书馆开车到金华站的时间，两段加起来不能超过30分钟。另外，图书馆周边800米内必须能找到公交站，方便你临时改坐公交。你"自信、有条理、有创造力，但没有耐心。"
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边范围：调用 maps_around_search(location='119.662634,29.073312', radius='2500', keywords='图书馆')，验证其中包含 target_poi_id='B0FFHOC0LP'。
2) 获取目标点坐标：调用 maps_search_detail(id='B0FFHOC0LP')，得到目标POI坐标 destination='119.661610,29.077736'。
3) 步行距离上限：调用 maps_walking_by_coordinates(origin='119.662634,29.073312', destination='119.661610,29.077736')，验证 total_distance_meters ≤ 1500。
4) 两段总耗时上限：调用 maps_text_search(keywords='金华站', city='金华') 得到poi_id，再调用 maps_search_detail(id=poi_id) 获取金华站坐标 '119.635860,29.110764'；再调用 maps_driving_by_coordinates(origin='119.661610,29.077736', destination='119.635860,29.110764') 得到驾车时长；验证(步行total_duration_seconds + 驾车total_duration_seconds) / 60 ≤ 30。
5) 途径点附近POI类型A：调用 maps_around_search(location='119.661610,29.077736', radius='800', keywords='公交站')，验证返回pois数量≥1。
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
    maps_text_search,
    maps_driving_by_coordinates,
    maps_walking_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "119.662634,29.073312",
    search_radius: int = 2500,
    keywords: str = "图书馆",
    max_walking_distance: int = 1500,  # meters
    station_address: str = "金华站",
    station_city: str = "金华",
    max_total_time: int = 1800,  # 30 minutes = 1800 seconds
    bus_stop_search_radius: int = 800,
    bus_stop_keywords: str = "公交站"
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 周边范围：调用 maps_around_search，验证其中包含 target_poi_id。
    2) 获取目标点坐标：调用 maps_search_detail，得到目标POI坐标。
    3) 步行距离上限：调用 maps_walking_by_coordinates，验证 total_distance_meters ≤ 1500。
    4) 两段总耗时上限：获取金华站坐标，计算驾车时长，验证(步行时长 + 驾车时长) / 60 ≤ 30。
    5) 途径点附近POI类型A：调用 maps_around_search，验证返回pois数量≥1。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"119.662634,29.073312"
        search_radius: 搜索半径（米），默认2500
        keywords: 搜索关键词，默认"图书馆"
        max_walking_distance: 最大步行距离（米），默认1500
        station_address: 车站地址，默认"金华站"
        station_city: 车站所在城市，默认"金华"
        max_total_time: 最大总耗时（秒），默认1800（30分钟）
        bus_stop_search_radius: 公交站搜索半径（米），默认800
        bus_stop_keywords: 公交站搜索关键词，默认"公交站"

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 周边范围
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

    # 步骤2: 获取目标点坐标
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")

    # 步骤3: 步行距离上限
    walking_result = maps_walking_by_coordinates(origin=user_location, destination=poi_location)
    # print(f"----✅ 计算步行路线: 从{user_location}到{poi_location}")
    if walking_result.error:
        print(f"❌ 计算步行路线失败: {walking_result.error}")
        return False

    if walking_result.total_distance_meters is None:
        print(f"❌ 无法获取步行距离")
        return False

    walking_distance = walking_result.total_distance_meters
    if walking_distance > max_walking_distance:
        print(f"❌ 步行距离{walking_distance}米，超过{max_walking_distance}米")
        return False
    print(f"✅ 步行距离{walking_distance}米，符合要求（<= {max_walking_distance}米）")

    if walking_result.total_duration_seconds is None:
        print(f"❌ 无法获取步行时长")
        return False

    walking_duration = walking_result.total_duration_seconds
    print(f"✅ 步行时长{walking_duration}秒")

    # 步骤4: 两段总耗时上限
    station_text_search_result = maps_text_search(keywords=station_address, city=station_city)
    if station_text_search_result.error:
        print(f"❌ 获取车站坐标失败: {station_text_search_result.error}")
        return False

    if not station_text_search_result.pois or len(station_text_search_result.pois) == 0:
        print(f"❌ 未找到车站坐标")
        return False

    station_poi_id = station_text_search_result.pois[0].id
    station_detail_result = maps_search_detail(id=station_poi_id)
    if station_detail_result.error:
        print(f"❌ 获取车站详情失败: {station_detail_result.error}")
        return False
    if not station_detail_result.location:
        print(f"❌ 车站没有location信息")
        return False
    station_location = station_detail_result.location
    print(f"✅ 获取车站坐标: {station_location} ({station_address})")

    driving_result = maps_driving_by_coordinates(origin=poi_location, destination=station_location)
    if driving_result.error:
        print(f"❌ 计算驾车路线失败: {driving_result.error}")
        return False

    if driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取驾车时长")
        return False

    driving_duration = driving_result.total_duration_seconds
    print(f"✅ 驾车时长{driving_duration}秒")

    # 计算总耗时（分钟）
    total_time_seconds = walking_duration + driving_duration
    total_time_minutes = total_time_seconds / 60
    if total_time_seconds > max_total_time:
        print(f"❌ 总耗时{total_time_seconds}秒（{total_time_minutes:.2f}分钟），超过{max_total_time}秒（{max_total_time // 60}分钟）")
        return False
    print(f"✅ 总耗时{total_time_seconds}秒（{total_time_minutes:.2f}分钟），符合要求（<= {max_total_time}秒，即{max_total_time // 60}分钟）")

    # 步骤5: 途径点附近POI类型A
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

    print(f"✅ 找到公交站: {bus_stop_search_result.pois[0].name} (共{len(bus_stop_search_result.pois)}个)")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 853.py 文件...\\n")
    result = verify_poi(poi_id="B0FFHOC0LP")
    print(f"\n验证结果: {result}")
