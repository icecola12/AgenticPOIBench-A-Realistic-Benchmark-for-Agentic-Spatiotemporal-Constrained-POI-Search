
"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 附近搜索：调用 maps_around_search(location='105.299048,27.309886', radius='5000', keywords='网吧')；验证其中包含目标poi_id，并获取目标poi坐标。
2) 从出发点步行距离≤2000米：调用 maps_walking_by_coordinates(origin='105.299048,27.309886', destination='105.305963,27.296854')，验证 total_distance_meters ≤ 2000。
3) 网吧300米内存在公交站：调用 maps_around_search(location='105.305963,27.296854', radius='300', keywords='公交站')，验证返回pois数量≥1。
4) 最近公交站步行时间≤8分钟：对第4步返回的每个公交站POI，分别调用 maps_walking_by_coordinates(origin='105.305963,27.296854', destination=<公交站location>)，取最小 total_duration_seconds，验证 ≤ 480秒。（例如可用BV11678294，destination='105.305551,27.295907'，其步行361秒。）
5) 网吧到毕节站驾车时间≤23分钟：调用 maps_text_search(keywords='毕节站', city='毕节市') 得到poi_id，再调用 maps_search_detail(id=poi_id) 获取毕节站坐标destination='105.419026,27.262094'；再调用 maps_driving_by_coordinates(origin='105.305963,27.296854', destination='105.419026,27.262094')，验证 total_duration_seconds ≤ 1380秒。
6) 绕行增加时间≤5分钟：
a) 直接去毕节站：maps_driving_by_coordinates(origin='105.299048,27.309886', destination='105.419026,27.262094') 得到 t_direct。
b) 先去网吧再去毕节站：t_via = maps_driving_by_coordinates(origin='105.299048,27.309886', destination='105.305963,27.296854').total_duration_seconds + maps_driving_by_coordinates(origin='105.305963,27.296854', destination='105.419026,27.262094').total_duration_seconds。
验证 (t_via - t_direct) ≤ 300秒。
7) 不在电影院500米附近：调用 maps_around_search(location='105.305963,27.296854', radius='500', keywords='电影院')，验证返回pois数量为0。
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
    user_location: str = "105.299048,27.309886",
    search_radius: int = 5000,
    keywords: str = "网吧",
    max_walking_distance: int = 2000,  # 2000 meters
    bus_stop_search_radius: int = 300,
    bus_stop_keywords: str = "公交站",
    min_bus_stop_count: int = 1,
    max_bus_stop_walking_duration: int = 480,  # 8 minutes = 480 seconds
    station_name: str = "毕节站",
    city: str = "毕节市",
    max_station_driving_duration: int = 1380,  # 23 minutes = 1380 seconds
    max_detour_increment: int = 300,  # 5 minutes = 300 seconds
    cinema_search_radius: int = 500,
    cinema_keywords: str = "电影院",
    max_cinema_count: int = 0
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 附近搜索：调用 maps_around_search，验证其中包含目标poi_id，并获取目标poi坐标。
    2) 从出发点步行距离≤2000米：调用 maps_walking_by_coordinates，验证 total_distance_meters ≤ 2000。
    3) 网吧300米内存在公交站：调用 maps_around_search，验证返回pois数量≥1。
    4) 最近公交站步行时间≤8分钟：对每个公交站POI调用 maps_walking_by_coordinates，取最小值，验证 ≤ 480秒。
    5) 网吧到毕节站驾车时间≤23分钟：调用 maps_text_search + maps_search_detail 和 maps_driving_by_coordinates，验证 total_duration_seconds ≤ 1380秒。
    6) 绕行增加时间≤5分钟：计算直接路线和绕行路线的时间差，验证 ≤ 300秒。
    7) 不在电影院500米附近：调用 maps_around_search，验证返回pois数量为0。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"105.299048,27.309886"
        search_radius: 搜索半径（米），默认5000
        keywords: 搜索关键词，默认"网吧"
        max_walking_distance: 最大步行距离（米），默认2000
        bus_stop_search_radius: 公交站搜索半径（米），默认300
        bus_stop_keywords: 公交站搜索关键词，默认"公交站"
        min_bus_stop_count: 最小公交站数量，默认1
        max_bus_stop_walking_duration: 到公交站最大步行时长（秒），默认480（8分钟）
        station_name: 车站名称，默认"毕节站"
        city: 城市名称，默认"毕节市"
        max_station_driving_duration: 到车站最大驾车时长（秒），默认1380（23分钟）
        max_detour_increment: 最大绕行增加时间（秒），默认300（5分钟）
        cinema_search_radius: 电影院搜索半径（米），默认500
        cinema_keywords: 电影院搜索关键词，默认"电影院"
        max_cinema_count: 最大电影院数量，默认0

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 附近搜索
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

    # 获取目标POI坐标
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")

    # 步骤2: 从出发点步行距离≤2000米
    walking_result = maps_walking_by_coordinates(origin=user_location, destination=poi_location)
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

    # 步骤3: 网吧300米内存在公交站
    bus_stop_search_result = maps_around_search(
        location=poi_location,
        radius=str(bus_stop_search_radius),
        keywords=bus_stop_keywords
    )
    if bus_stop_search_result.error:
        print(f"❌ 搜索公交站失败: {bus_stop_search_result.error}")
        return False

    bus_stop_count = len(bus_stop_search_result.pois) if bus_stop_search_result.pois else 0
    if bus_stop_count < min_bus_stop_count:
        print(f"❌ 网吧周边{bus_stop_search_radius}米内找到{bus_stop_count}个公交站，少于{min_bus_stop_count}个")
        return False
    print(f"✅ 网吧周边{bus_stop_search_radius}米内找到{bus_stop_count}个公交站，符合要求（>= {min_bus_stop_count}个）")

    # 步骤4: 最近公交站步行时间≤8分钟
    min_bus_stop_walking_duration = None
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
        if min_bus_stop_walking_duration is None or duration < min_bus_stop_walking_duration:
            min_bus_stop_walking_duration = duration

    if min_bus_stop_walking_duration is None:
        print(f"❌ 无法计算到公交站的步行时间")
        return False

    if min_bus_stop_walking_duration > max_bus_stop_walking_duration:
        print(f"❌ 到最近公交站步行时长{min_bus_stop_walking_duration}秒，超过{max_bus_stop_walking_duration}秒（{max_bus_stop_walking_duration // 60}分钟）")
        return False
    print(f"✅ 到最近公交站步行时长{min_bus_stop_walking_duration}秒，符合要求（<= {max_bus_stop_walking_duration}秒，即{max_bus_stop_walking_duration // 60}分钟）")

    # 步骤5: 网吧到毕节站驾车时间≤23分钟
    station_text_search_result = maps_text_search(keywords=station_name, city=city)
    if station_text_search_result.error:
        print(f"❌ 获取{station_name}坐标失败: {station_text_search_result.error}")
        return False

    if not station_text_search_result.pois or len(station_text_search_result.pois) == 0:
        print(f"❌ 未找到{station_name}坐标")
        return False

    station_poi_id = station_text_search_result.pois[0].id
    station_detail_result = maps_search_detail(id=station_poi_id)
    if station_detail_result.error:
        print(f"❌ 获取{station_name}详情失败: {station_detail_result.error}")
        return False
    if not station_detail_result.location:
        print(f"❌ {station_name}没有location信息")
        return False
    station_location = station_detail_result.location
    print(f"✅ 获取{station_name}坐标: {station_location}")

    poi_to_station_driving_result = maps_driving_by_coordinates(origin=poi_location, destination=station_location)
    if poi_to_station_driving_result.error:
        print(f"❌ 计算到{station_name}驾车路线失败: {poi_to_station_driving_result.error}")
        return False

    if poi_to_station_driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取到{station_name}驾车时长")
        return False

    poi_to_station_duration = poi_to_station_driving_result.total_duration_seconds
    if poi_to_station_duration > max_station_driving_duration:
        print(f"❌ 到{station_name}驾车时长{poi_to_station_duration}秒，超过{max_station_driving_duration}秒（{max_station_driving_duration // 60}分钟）")
        return False
    print(f"✅ 到{station_name}驾车时长{poi_to_station_duration}秒，符合要求（<= {max_station_driving_duration}秒，即{max_station_driving_duration // 60}分钟）")

    # 步骤6: 绕行增加时间≤5分钟
    # 计算直接路线：用户位置→毕节站
    direct_driving_result = maps_driving_by_coordinates(origin=user_location, destination=station_location)
    if direct_driving_result.error:
        print(f"❌ 计算直接到{station_name}驾车路线失败: {direct_driving_result.error}")
        return False

    if direct_driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取直接到{station_name}驾车时长")
        return False

    direct_duration = direct_driving_result.total_duration_seconds
    print(f"✅ 直接到{station_name}驾车时长{direct_duration}秒")

    # 计算绕行路线：用户位置→网吧→毕节站
    user_to_poi_driving_result = maps_driving_by_coordinates(origin=user_location, destination=poi_location)
    if user_to_poi_driving_result.error:
        print(f"❌ 计算到网吧驾车路线失败: {user_to_poi_driving_result.error}")
        return False

    if user_to_poi_driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取到网吧驾车时长")
        return False

    user_to_poi_duration = user_to_poi_driving_result.total_duration_seconds
    via_duration = user_to_poi_duration + poi_to_station_duration
    print(f"✅ 绕行路线时长{via_duration}秒（用户→网吧: {user_to_poi_duration}秒 + 网吧→{station_name}: {poi_to_station_duration}秒）")

    detour_increment = via_duration - direct_duration
    if detour_increment > max_detour_increment:
        print(f"❌ 绕行增加时间{detour_increment}秒（{detour_increment / 60:.2f}分钟），超过{max_detour_increment}秒（{max_detour_increment // 60}分钟）")
        return False
    print(f"✅ 绕行增加时间{detour_increment}秒（{detour_increment / 60:.2f}分钟），符合要求（<= {max_detour_increment}秒，即{max_detour_increment // 60}分钟）")

    # 步骤7: 不在电影院500米附近
    cinema_search_result = maps_around_search(
        location=poi_location,
        radius=str(cinema_search_radius),
        keywords=cinema_keywords
    )
    if cinema_search_result.error:
        print(f"❌ 搜索电影院失败: {cinema_search_result.error}")
        return False

    cinema_count = len(cinema_search_result.pois) if cinema_search_result.pois else 0
    if cinema_count > max_cinema_count:
        print(f"❌ 网吧周边{cinema_search_radius}米内找到{cinema_count}个电影院，超过{max_cinema_count}个")
        return False
    print(f"✅ 网吧周边{cinema_search_radius}米内找到{cinema_count}个电影院，符合要求（<= {max_cinema_count}个）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 845.py 文件...\n")
    result = verify_poi(poi_id="B0LRYAVQ76")
    print(f"\n验证结果: {result}")

