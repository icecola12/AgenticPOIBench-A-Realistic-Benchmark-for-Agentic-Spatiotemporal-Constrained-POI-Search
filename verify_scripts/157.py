
"""
修改任务指令：你要在附近1200米以内找一家民宿，走路过去不要超过15分钟。另外你希望这家民宿离"台州实验小学(公交站)"步行不超过15分钟；同时民宿周围1200米内必须能搜到公交站，并且民宿到这些公交站里最近的一个直线距离不超过300米。你还想让民宿周围600米内能找到青年旅舍。最后，你计划先去附近一家叫"弎野精酿鲜啤打酒站"的酒吧拿东西，所以从那家酒吧开车到民宿的时间要控制在5分钟以内。你有礼貌但非常坚决和不耐烦，希望尽快解决问题。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 附近1200米以内：调用maps_around_search(location='121.441477,28.654039', radius='1200', keywords='民宿')，验证返回列表包含target_poi_id='B0LUNXCFKP'。
2) 走路到民宿≤15分钟：调用maps_search_detail('B0LUNXCFKP')取location='121.441325,28.655675'；调用maps_walking_by_coordinates(origin='121.441477,28.654039', destination='121.441325,28.655675')，验证total_duration_seconds=531≤900。
3) 民宿到指定公交站"台州实验小学(公交站)"步行≤15分钟：调用maps_text_search(keywords='台州实验小学(公交站)', city='台州', citylimit='true')得到id='BV10201601'；调用maps_search_detail('BV10201601')得location='121.438842,28.655631'；调用maps_walking_by_coordinates(origin='121.441325,28.655675', destination='121.438842,28.655631')，验证total_duration_seconds=813≤900。
4) 民宿周围1200米内有公交站：调用maps_around_search(location='121.441325,28.655675', radius='1200', keywords='公交站')，验证pois数量>0。
5) 民宿到最近公交站直线距离≤300米：从步骤4返回的公交站POI中选取若干个（或全部）坐标，调用maps_distance(origins='公交站1|公交站2|...', destination='121.441325,28.655675')，取最小distance_meters，验证≤300。（例如对台州实验小学/椒江交警大队/景元花园三站测得最小值为242米≤300。）
6) 民宿周围600米内有青年旅舍：调用maps_around_search(location='121.441325,28.655675', radius='600', keywords='青年旅舍')，验证pois数量>0（例如返回"爱家青年公寓"）。
7) 从附近酒吧到民宿开车≤5分钟：调用。maps_search_detail('B0LUNXCFKP')取location='121.442530,28.649773'）；调用maps_driving_by_coordinates(origin='121.442530,28.649773', destination='121.441325,28.655675')，验证total_duration_seconds=68≤300。
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
    user_location: str = "121.441477,28.654039",
    search_radius: int = 1200,
    keywords: str = "民宿",
    max_walking_duration: int = 900,  # 15 minutes = 900 seconds
    bus_stop_name: str = "台州实验小学(公交站)",
    city: str = "台州",
    max_bus_stop_walking_duration: int = 900,  # 15 minutes = 900 seconds
    bus_stop_search_radius: int = 1200,
    bus_stop_keywords: str = "公交站",
    max_bus_stop_straight_distance: int = 300,  # 300 meters
    hostel_search_radius: int = 600,
    hostel_keywords: str = "青年旅舍",
    bar_name: str = "弎野精酿鲜啤打酒站",
    max_bar_driving_duration: int = 300  # 5 minutes = 300 seconds
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 附近1200米以内：调用 maps_around_search，验证返回列表包含target_poi_id。
    2) 走路到民宿≤15分钟：调用 maps_search_detail 取location，调用 maps_walking_by_coordinates，验证 total_duration_seconds ≤ 900。
    3) 民宿到指定公交站步行≤15分钟：调用 maps_text_search 得到公交站，调用 maps_search_detail 得location，调用 maps_walking_by_coordinates，验证 total_duration_seconds ≤ 900。
    4) 民宿周围1200米内有公交站：调用 maps_around_search，验证pois数量>0。
    5) 民宿到最近公交站直线距离≤300米：调用 maps_distance，取最小distance_meters，验证≤300。
    6) 民宿周围600米内有青年旅舍：调用 maps_around_search，验证pois数量>0。
    7) 从附近酒吧到民宿开���≤5分钟：调用 maps_text_search 获取酒吧坐标，调用 maps_driving_by_coordinates，验证 total_duration_seconds ≤ 300。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"121.441477,28.654039"
        search_radius: 搜索半径（米），默认1200
        keywords: 搜索关键词，默认"民宿"
        max_walking_duration: 最大步行时长（秒），默认900（15分钟）
        bus_stop_name: 公交站名称，默认"台州实验小学(公交站)"
        city: 城市名称，默认"台州"
        max_bus_stop_walking_duration: 到公交站最大步行时长（秒），默认900（15分钟）
        bus_stop_search_radius: 公交站搜索半径（米），默认1200
        bus_stop_keywords: 公交站搜索关键词，默认"公交站"
        max_bus_stop_straight_distance: 到公交站最大直线距离（米），默认300
        hostel_search_radius: 青年旅舍搜索半径（米），默认600
        hostel_keywords: 青年旅舍搜索关键词，默认"青年旅舍"
        bar_name: 酒吧名称，默认"弎野精酿鲜啤打酒站"
        max_bar_driving_duration: 从酒吧最大驾车时长（秒），默认300（5分钟）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 附近1200米以内
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

    # 步骤3: 走路到民宿≤15分钟
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

    # 步骤4: 民宿到指定公交站步行≤15分钟
    bus_stop_search_result = maps_text_search(
        keywords=bus_stop_name,
        city=city,
        citylimit="true"
    )
    if bus_stop_search_result.error:
        print(f"❌ 搜索{bus_stop_name}失败: {bus_stop_search_result.error}")
        return False

    if not bus_stop_search_result.pois or len(bus_stop_search_result.pois) == 0:
        print(f"❌ 未找到{bus_stop_name}")
        return False

    # 获取公交站详情以获取坐标
    bus_stop_id = bus_stop_search_result.pois[0].id
    bus_stop_detail = maps_search_detail(id=bus_stop_id)
    if bus_stop_detail.error:
        print(f"❌ 获取{bus_stop_name}详情失败: {bus_stop_detail.error}")
        return False

    if not bus_stop_detail.location:
        print(f"❌ {bus_stop_name}没有location信息")
        return False

    bus_stop_location = bus_stop_detail.location
    print(f"✅ 获取{bus_stop_name}坐标: {bus_stop_location}")

    bus_stop_walking_result = maps_walking_by_coordinates(origin=poi_location, destination=bus_stop_location)
    if bus_stop_walking_result.error:
        print(f"❌ 计算到{bus_stop_name}步行路线失败: {bus_stop_walking_result.error}")
        return False

    if bus_stop_walking_result.total_duration_seconds is None:
        print(f"❌ 无法获取到{bus_stop_name}步行时长")
        return False

    bus_stop_walking_duration = bus_stop_walking_result.total_duration_seconds
    if bus_stop_walking_duration > max_bus_stop_walking_duration:
        print(f"❌ 到{bus_stop_name}步行时长{bus_stop_walking_duration}秒，超过{max_bus_stop_walking_duration}秒（{max_bus_stop_walking_duration // 60}分钟）")
        return False
    print(f"✅ 到{bus_stop_name}步行时长{bus_stop_walking_duration}秒，符合要求（<= {max_bus_stop_walking_duration}秒，即{max_bus_stop_walking_duration // 60}分钟）")

    # 步骤5: 民宿周围1200米内有公交站
    nearby_bus_stop_search_result = maps_around_search(
        location=poi_location,
        radius=str(bus_stop_search_radius),
        keywords=bus_stop_keywords
    )
    if nearby_bus_stop_search_result.error:
        print(f"❌ 搜索公交站失败: {nearby_bus_stop_search_result.error}")
        return False

    if not nearby_bus_stop_search_result.pois or len(nearby_bus_stop_search_result.pois) == 0:
        print(f"❌ 未找到公交站")
        return False

    print(f"✅ 找到{len(nearby_bus_stop_search_result.pois)}个公交站")

    # 步骤6: 民宿到最近公交站直线距离≤300米
    # 将所有公交站坐标拼成origins
    bus_stop_locations = []
    for bus_stop in nearby_bus_stop_search_result.pois:
        if bus_stop.location:
            bus_stop_locations.append(bus_stop.location)

    if len(bus_stop_locations) == 0:
        print(f"❌ 没有公交站有坐标信息")
        return False

    origins_str = "|".join(bus_stop_locations)
    distance_result = maps_distance(origins=origins_str, destination=poi_location)
    if distance_result.error:
        print(f"❌ 计算距离失败: {distance_result.error}")
        return False

    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 未获取到距离信息")
        return False

    # 找到最小直线距离
    min_straight_distance = None
    for result in distance_result.results:
        if min_straight_distance is None or result.distance_meters < min_straight_distance:
            min_straight_distance = result.distance_meters

    if min_straight_distance is None:
        print(f"❌ 无法计算最小直线距离")
        return False

    if min_straight_distance > max_bus_stop_straight_distance:
        print(f"❌ 最近公交站直线距离{min_straight_distance}米，超过{max_bus_stop_straight_distance}米")
        return False
    print(f"✅ 最近公交站直线距离{min_straight_distance}米，符合要求（<= {max_bus_stop_straight_distance}米）")

    # 步骤7: 民宿周围600米内有青年旅舍
    hostel_search_result = maps_around_search(
        location=poi_location,
        radius=str(hostel_search_radius),
        keywords=hostel_keywords
    )
    if hostel_search_result.error:
        print(f"❌ 搜索青年旅舍失败: {hostel_search_result.error}")
        return False

    if not hostel_search_result.pois or len(hostel_search_result.pois) == 0:
        print(f"❌ 未找到青年旅舍")
        return False

    print(f"✅ 找到{len(hostel_search_result.pois)}个青年旅舍")
    print(f"   示例青年旅舍: {hostel_search_result.pois[0].name} (ID: {hostel_search_result.pois[0].id})")

    # 步骤8: 从附近酒吧到民宿开车≤5分钟
    bar_search_result = maps_text_search(
        keywords=bar_name,
        city=city,
        citylimit="true"
    )
    if bar_search_result.error:
        print(f"❌ 搜索{bar_name}失败: {bar_search_result.error}")
        return False

    if not bar_search_result.pois or len(bar_search_result.pois) == 0:
        print(f"❌ 未找到{bar_name}")
        return False

    # 获取酒吧详情以获取坐标
    bar_id = bar_search_result.pois[0].id
    bar_detail = maps_search_detail(id=bar_id)
    if bar_detail.error:
        print(f"❌ 获取{bar_name}详情失败: {bar_detail.error}")
        return False

    if not bar_detail.location:
        print(f"❌ {bar_name}没有location信息")
        return False

    bar_location = bar_detail.location
    print(f"✅ 获取{bar_name}坐标: {bar_location}")

    bar_driving_result = maps_driving_by_coordinates(origin=bar_location, destination=poi_location)
    if bar_driving_result.error:
        print(f"❌ 计算从{bar_name}驾车路线失败: {bar_driving_result.error}")
        return False

    if bar_driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取从{bar_name}驾车时长")
        return False

    bar_driving_duration = bar_driving_result.total_duration_seconds
    if bar_driving_duration > max_bar_driving_duration:
        print(f"❌ 从{bar_name}驾车时长{bar_driving_duration}秒，超过{max_bar_driving_duration}秒（{max_bar_driving_duration // 60}分钟）")
        return False
    print(f"✅ 从{bar_name}驾车时长{bar_driving_duration}秒，符合要求（<= {max_bar_driving_duration}秒，即{max_bar_driving_duration // 60}分钟）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 815.py 文件...\n")
    result = verify_poi(poi_id="B0LUNXCFKP")
    print(f"\n验证结果: {result}")

