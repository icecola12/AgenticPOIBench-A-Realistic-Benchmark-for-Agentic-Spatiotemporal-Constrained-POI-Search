
"""
修改任务指令：你要在附近2000米以内找一个广场。你希望这个广场是24小时开放的。它的评分要在4.0分及以上。广场旁边400米内得有公交站，另外你希望从广场走到最近的公交站不要超过10分钟。你还希望：从海口东站开车到你这里，再接着去广场，这一段总用时比海口东站直接开到广场，最多只多20分钟。最后，这个广场不要在海口东站直线距离500米范围内。你虽然心情不好，但仍然保持礼貌和独立的姿态。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 附近2000米：调用 maps_around_search(location='110.322878,20.048017', radius='2000', keywords='广场')，验证返回pois中包含 target_poi_id=B0FFL6O7PG。
2) 24小时开放：调用 maps_search_detail(id='B0FFL6O7PG')，验证 biz_ext.open_time 包含 '24小时' 或 biz_ext.opentime2 覆盖 00:00-24:00。
3) 评分≥4.0：调用 maps_search_detail(id='B0FFL6O7PG')，验证 biz_ext.rating >= 4.0。
4) 广场400米内有公交站：调用 maps_around_search(location=广场坐标, radius='400', keywords='公交站')，验证 pois 数量>0。
5) 走到最近公交站≤10分钟：对(4)中返回的每个公交站POI，调用 maps_walking_by_coordinates(origin=广场坐标, destination=公交站坐标)，取最小 total_duration_seconds，验证 <= 600。
6) 绕行增量≤20分钟：用 maps_text_search(keywords='海口东站', city='海口') 得到poi_id，再调用 maps_search_detail(id=poi_id) 获取东站坐标A；用 maps_driving_by_coordinates(origin=A, destination=用户坐标U) 得到 t_AU；用 maps_driving_by_coordinates(origin=U, destination=广场坐标P) 得到 t_UP；用 maps_driving_by_coordinates(origin=A, destination=P) 得到 t_AP；验证 (t_AU+t_UP - t_AP) <= 1200秒。
7) 不在海口东站500米范围内：调用 maps_text_search + maps_search_detail 得到A后，调用 maps_distance(origins=A, destination=P) 得到直线距离d，验证 d > 500米。
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
    maps_distance,
    maps_driving_by_coordinates,
    maps_walking_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "110.322878,20.048017",
    search_radius: int = 2000,
    keywords: str = "广场",
    min_rating: float = 4.0,
    bus_stop_search_radius: int = 400,
    bus_stop_keywords: str = "公交站",
    min_bus_stop_count: int = 1,
    max_bus_stop_walking_duration: int = 600,  # 10 minutes = 600 seconds
    station_name: str = "海口东站",
    city: str = "海口",
    max_detour_increment: int = 1200,  # 20 minutes = 1200 seconds
    min_station_distance: int = 500  # 500 meters
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 附近2000米：调用 maps_around_search，验证返回pois中包含目标poi_id。
    2) 24小时开放：调用 maps_search_detail，验证 biz_ext.open_time 包含 '24小时' 或 biz_ext.opentime2 覆盖 00:00-24:00。
    3) 评分≥4.0：调用 maps_search_detail，验证 biz_ext.rating >= 4.0。
    4) 广场400米内有公交站：调用 maps_around_search，验证 pois 数量>0。
    5) 走到最近公交站≤10分钟：对每个公交站POI调用 maps_walking_by_coordinates，取最小值，验证 <= 600秒。
    6) 绕行增量≤20分钟：计算 (A→U→P) - (A→P)，验证 <= 1200秒。
    7) 不在海口东站500米范围内：调用 maps_distance，验证 d > 500米。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"110.322878,20.048017"
        search_radius: 搜索半径（米），默认2000
        keywords: 搜索关键词，默认"广场"
        min_rating: 最低评分，默认4.0
        bus_stop_search_radius: 公交站搜索半径（米），默认400
        bus_stop_keywords: 公交站搜索关键词，默认"公交站"
        min_bus_stop_count: 最小公交站数量，默认1
        max_bus_stop_walking_duration: 到公交站最大步行时长（秒），默认600（10分钟）
        station_name: 车站名称，默认"海口东站"
        city: 城市名称，默认"海口"
        max_detour_increment: 最大绕行增加时间（秒），默认1200（20分钟）
        min_station_distance: 到车站最小距离（米），默认500

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 附近2000米
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

    # 步骤2: 获取POI详情并验证24小时开放和评分
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")

    # 验证24小时开放
    is_24_hours = False
    if poi_detail.biz_ext:
        # 检查 open_time 字段
        if 'open_time' in poi_detail.biz_ext and poi_detail.biz_ext['open_time']:
            open_time = poi_detail.biz_ext['open_time']
            if '24小时' in open_time or '24 小时' in open_time:
                is_24_hours = True
                print(f"✅ POI为24小时开放（open_time: {open_time}）")

        # 检查 opentime2 字段
        if not is_24_hours and 'opentime2' in poi_detail.biz_ext and poi_detail.biz_ext['opentime2']:
            opentime2 = poi_detail.biz_ext['opentime2']
            # 检查是否覆盖 00:00-24:00 或类似的全天时间
            if '00:00' in opentime2 and ('24:00' in opentime2 or '23:59' in opentime2):
                is_24_hours = True
                print(f"✅ POI为24小时开放（opentime2: {opentime2}）")

    if not is_24_hours:
        print(f"❌ POI不是24小时开放")
        return False

    # 步骤3: 验证评分≥4.0
    if poi_detail.biz_ext and 'rating' in poi_detail.biz_ext:
        rating = float(poi_detail.biz_ext['rating'])
        if rating < min_rating:
            print(f"❌ POI评分{rating}分，低于{min_rating}分")
            return False
        print(f"✅ POI评分{rating}分，符合要求（>= {min_rating}分）")
    else:
        print(f"❌ POI没有评分信息")
        return False

    # 步骤4: 广场400米内有公交站
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
        print(f"❌ 广场周边{bus_stop_search_radius}米内找到{bus_stop_count}个公交站，少于{min_bus_stop_count}个")
        return False
    print(f"✅ 广场周边{bus_stop_search_radius}米内找到{bus_stop_count}个公交站，符合要求（>= {min_bus_stop_count}个）")

    # 步骤5: 走到最近公交站≤10分钟
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

    # 步骤6: 绕行增量≤20分钟
    # 获取海口东站坐标
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

    # 计算 A→U (海口东站→用户位置)
    station_to_user_driving_result = maps_driving_by_coordinates(origin=station_location, destination=user_location)
    if station_to_user_driving_result.error:
        print(f"❌ 计算{station_name}到用户位置驾车路线失败: {station_to_user_driving_result.error}")
        return False

    if station_to_user_driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取{station_name}到用户位置驾车时长")
        return False

    t_AU = station_to_user_driving_result.total_duration_seconds
    print(f"✅ {station_name}到用户位置驾车时长{t_AU}秒")

    # 计算 U→P (用户位置→广场)
    user_to_poi_driving_result = maps_driving_by_coordinates(origin=user_location, destination=poi_location)
    if user_to_poi_driving_result.error:
        print(f"❌ 计算用户位置到广场驾车路线失败: {user_to_poi_driving_result.error}")
        return False

    if user_to_poi_driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取用户位置到广场驾车时长")
        return False

    t_UP = user_to_poi_driving_result.total_duration_seconds
    print(f"✅ 用户位置到广场驾车时长{t_UP}秒")

    # 计算 A→P (海口东站→广场，直接路线)
    station_to_poi_driving_result = maps_driving_by_coordinates(origin=station_location, destination=poi_location)
    if station_to_poi_driving_result.error:
        print(f"❌ 计算{station_name}到广场驾车路线失败: {station_to_poi_driving_result.error}")
        return False

    if station_to_poi_driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取{station_name}到广场驾车时长")
        return False

    t_AP = station_to_poi_driving_result.total_duration_seconds
    print(f"✅ {station_name}到广场驾车时长{t_AP}秒")

    # 计算绕行增量
    detour_increment = (t_AU + t_UP) - t_AP
    if detour_increment > max_detour_increment:
        print(f"❌ 绕行增加时间{detour_increment}秒（{detour_increment / 60:.2f}分钟），超过{max_detour_increment}秒（{max_detour_increment // 60}分钟）")
        return False
    print(f"✅ 绕行增加时间{detour_increment}秒（{detour_increment / 60:.2f}分钟），符合要求（<= {max_detour_increment}秒，即{max_detour_increment // 60}分钟）")

    # 步骤7: 不在海口东站500米范围内
    distance_result = maps_distance(origins=station_location, destination=poi_location)
    if distance_result.error:
        print(f"❌ 计算到{station_name}距离失败: {distance_result.error}")
        return False

    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 未获取到到{station_name}的距离信息")
        return False

    station_distance = distance_result.results[0].distance_meters
    if station_distance <= min_station_distance:
        print(f"❌ 到{station_name}直线距离{station_distance}米，不大于{min_station_distance}米")
        return False
    print(f"✅ 到{station_name}直线距离{station_distance}米，符合要求（> {min_station_distance}米）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 847.py 文件...\n")
    result = verify_poi(poi_id="B0FFL6O7PG")
    print(f"\n验证结果: {result}")

