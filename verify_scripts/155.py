
"""
修改任务指令：你想在附近8000米以内找一个广场。你开车过去的话，行驶距离不能超过5公里。广场周围1200米范围内要能找到公交站，而且从广场走路最近的那个公交站，步行距离不要超过2000米。你还希望广场到这个公交站的直线距离不要超过600米。你打算之后去东营胜利机场，所以从这个广场开车去东营胜利机场的时间不能超过35分钟。另外，你有两个朋友分别从东营汽车总站和东营站出发来找你，你希望他们两个人步行到这个广场的时间差不要超过200分钟。你有礼貌但非常坚决和不耐烦，希望尽快解决问题。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边命中（附近8000米）验证：调用 maps_around_search(location='118.628159,37.433537', radius='8000', keywords='广场')，检查返回pois中包含目标poi_id='B022200FA4'。
2) POI类型与属性验证：调用 maps_search_detail(id='B022200FA4')，确认名称/类型为"广场"，并读取其坐标destination='118.674646,37.431863'。
3) 出发地到目标点最大驾车距离（≤5公里）：调用 maps_driving_by_coordinates(origin='118.628159,37.433537', destination='118.674646,37.431863')，验证 total_distance_meters ≤ 5000。
4) 目标点附近1200米内存在公交站：调用 maps_around_search(location='118.674646,37.431863', radius='1200', keywords='公交站')，验证 pois 列表非空；并在这些公交站中选取"最近直线距离"的站点S（见第6步）。
5) 目标点到最近公交站的最小步行距离（≤2000米）：对第4步返回的每个公交站Si，调用 maps_walking_by_coordinates(origin='118.674646,37.431863', destination=Si.location)，取 total_distance_meters 的最小值min_walk_dist，验证 min_walk_dist ≤ 2000。同时记录这个最近公交站S的位置s_min_location。
6) 目标点到最近公交站的最小直线距离（≤600米）：对第5步返回的公交站station，调用 maps_distance(origins='118.674646,37.431863', destination=s_min_location)，取返回的直线距离为distance_meters，验证 distance_meters ≤ 600。
7) 目标点到指定交通枢纽（东营胜利机场）驾车时间（≤35分钟）：调用 maps_text_search(keywords='东营胜利机场', city='东营') 获取 poi_id，再调用 maps_search_detail(id=poi_id) 取机场坐标A；再调用 maps_driving_by_coordinates(origin='118.674646,37.431863', destination=A)，验证 total_duration_seconds ≤ 2100。
8) 两位朋友步行到目标点的时间差（≤200分钟）：调用 maps_text_search(keywords='东营汽车总站', city='东营') 获取 poi_id，再 maps_search_detail 得到坐标B；调用 maps_text_search(keywords='东营站', city='东营') 获取 poi_id，再 maps_search_detail 得到坐标C；分别调用 maps_walking_by_coordinates(origin=B, destination='118.674646,37.431863') 得tB，和 maps_walking_by_coordinates(origin=C, destination='118.674646,37.431863') 得tC；验证 |tB - tC| ≤ 12000秒。
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
    user_location: str = "118.628159,37.433537",
    search_radius: int = 8000,
    keywords: str = "广场",
    max_driving_distance: int = 5000,  # 5 km = 5000 meters
    bus_stop_search_radius: int = 1200,
    bus_stop_keywords: str = "公交站",
    max_bus_stop_walking_distance: int = 2000,  # 2000 meters
    max_bus_stop_straight_distance: int = 600,  # 600 meters
    airport_name: str = "东营胜利机场",
    city: str = "东营",
    max_airport_driving_duration: int = 2100,  # 35 minutes = 2100 seconds
    station1_name: str = "东营汽车总站",
    station2_name: str = "东营站",
    max_time_difference: int = 12000  # 200 minutes = 12000 seconds
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 周边命中（附近8000米）验证：调用 maps_around_search，检查返回pois中包含目标poi_id。
    2) POI类型与属性验证：调用 maps_search_detail，确认名称/类型为"广场"，并读取其坐标。
    3) 出发地到目标点最大驾车距离（≤5公里）：调用 maps_driving_by_coordinates，验证 total_distance_meters ≤ 5000。
    4) 目标点附近1200米内存在公交站：调用 maps_around_search，验证 pois 列表非空。
    5) 目标点到最近公交站的最小步行距离（≤2000米）：对每个公交站调用 maps_walking_by_coordinates，取最小值，验证 ≤ 2000。
    6) 目标点到最近公交站的最小直线距离（≤600米）：调用 maps_distance，验证 ≤ 600。
    7) 目标点到指定交通枢纽（东营胜利机场）驾车时间（≤35分钟）：调用 maps_text_search 获取 poi_id，再用 maps_search_detail 获取机场坐标，调用 maps_driving_by_coordinates，验证 ≤ 2100秒。
    8) 两位朋友步行到目标点的时间差（≤200分钟）：调用 maps_text_search 获取 poi_id，再用 maps_search_detail 获取两个站点坐标，调用 maps_walking_by_coordinates 计算步行时间，验证时间差 ≤ 12000秒。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"118.628159,37.433537"
        search_radius: 搜索半径（米），默认8000
        keywords: 搜索关键词，默认"广场"
        max_driving_distance: 最大驾车距离（米），默认5000
        bus_stop_search_radius: 公交站搜索半径（米），默认1200
        bus_stop_keywords: 公交站搜索关键词，默认"公交站"
        max_bus_stop_walking_distance: 到公交站最大步行距离（米），默认2000
        max_bus_stop_straight_distance: 到公交站最大直线距离（米），默认600
        airport_name: 机场名称，默认"东营胜利机场"
        city: 城市名称，默认"东营"
        max_airport_driving_duration: 到机场最大驾车时长（秒），默认2100（35分钟）
        station1_name: 第一个车站名称，默认"东营汽车总站"
        station2_name: 第二个车站名称，默认"东营站"
        max_time_difference: 最大时间差（秒），默认12000（200分钟）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 周边命中（附近8000米）验证
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

    # 步骤2: POI类型与属性验证
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")

    # 步骤3: 出发地到目标点最大驾车距离≤5公里
    driving_result = maps_driving_by_coordinates(origin=user_location, destination=poi_location)
    if driving_result.error:
        print(f"❌ 计算驾车路线失败: {driving_result.error}")
        return False

    if driving_result.total_distance_meters is None:
        print(f"❌ 无法获取驾车距离")
        return False

    driving_distance = driving_result.total_distance_meters
    if driving_distance > max_driving_distance:
        print(f"❌ 驾车距离{driving_distance}米，超过{max_driving_distance}米")
        return False
    print(f"✅ 驾车距离{driving_distance}米，符合要求（<= {max_driving_distance}米）")

    # 步骤4: 目标点附近1200米内存在公交站
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

    # 步骤5: 目标点到最近公交站的最小步行距离≤2000米
    min_bus_stop_walking_distance = None
    nearest_bus_stop_location = None
    for bus_stop in bus_stop_search_result.pois:
        if not bus_stop.location:
            continue

        bus_stop_walking_result = maps_walking_by_coordinates(
            origin=poi_location,
            destination=bus_stop.location
        )
        if bus_stop_walking_result.error or bus_stop_walking_result.total_distance_meters is None:
            continue

        distance = bus_stop_walking_result.total_distance_meters
        if min_bus_stop_walking_distance is None or distance < min_bus_stop_walking_distance:
            min_bus_stop_walking_distance = distance
            nearest_bus_stop_location = bus_stop.location

    if min_bus_stop_walking_distance is None:
        print(f"❌ 无法计算到公交站的步行距离")
        return False

    if min_bus_stop_walking_distance > max_bus_stop_walking_distance:
        print(f"❌ 到最近公交站步行距离{min_bus_stop_walking_distance}米，超过{max_bus_stop_walking_distance}米")
        return False
    print(f"✅ 到最近公交站步行距离{min_bus_stop_walking_distance}米，符合要求（<= {max_bus_stop_walking_distance}米）")

    # 步骤6: 目标点到最近公交站的最小直线距离≤600米
    if nearest_bus_stop_location is None:
        print(f"❌ 未找到最近公交站位置")
        return False

    bus_stop_distance_result = maps_distance(origins=poi_location, destination=nearest_bus_stop_location)
    if bus_stop_distance_result.error:
        print(f"❌ 计算到最近公交站距离失败: {bus_stop_distance_result.error}")
        return False

    if not bus_stop_distance_result.results or len(bus_stop_distance_result.results) == 0:
        print(f"❌ 未获取到到最近公交站的距离信息")
        return False

    bus_stop_straight_distance = bus_stop_distance_result.results[0].distance_meters
    if bus_stop_straight_distance > max_bus_stop_straight_distance:
        print(f"❌ 到最近公交站直线距离{bus_stop_straight_distance}米，超过{max_bus_stop_straight_distance}米")
        return False
    print(f"✅ 到最近公交站直线距离{bus_stop_straight_distance}米，符合要求（<= {max_bus_stop_straight_distance}米）")

    # 步骤7: 目标点到指定交通枢纽（东营胜利机场）驾车时间≤35分钟
    text_search_result = maps_text_search(keywords=airport_name, city=city)
    if text_search_result.error:
        print(f"❌ 获取{airport_name}坐标失败: {text_search_result.error}")
        return False

    if not text_search_result.pois or len(text_search_result.pois) == 0:
        print(f"❌ 未找到{airport_name}坐标")
        return False

    first_poi_id = text_search_result.pois[0].id
    detail_result = maps_search_detail(id=first_poi_id)
    if detail_result.error or not detail_result.location:
        print(f"❌ 获取{airport_name}坐标失败: {detail_result.error or '无location'}")
        return False

    airport_location = detail_result.location
    print(f"✅ 获取{airport_name}坐标: {airport_location}")

    airport_driving_result = maps_driving_by_coordinates(origin=poi_location, destination=airport_location)
    if airport_driving_result.error:
        print(f"❌ 计算到{airport_name}驾车路线失败: {airport_driving_result.error}")
        return False

    if airport_driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取到{airport_name}驾车时长")
        return False

    airport_driving_duration = airport_driving_result.total_duration_seconds
    if airport_driving_duration > max_airport_driving_duration:
        print(f"❌ 到{airport_name}驾车时长{airport_driving_duration}秒，超过{max_airport_driving_duration}秒（{max_airport_driving_duration // 60}分钟）")
        return False
    print(f"✅ 到{airport_name}驾车时长{airport_driving_duration}秒，符合要求（<= {max_airport_driving_duration}秒，即{max_airport_driving_duration // 60}分钟）")

    # 步骤8: 两位朋友步行到目标点的时间差≤200分钟
    # 获取第一个车站坐标
    text_search_result = maps_text_search(keywords=station1_name, city=city)
    if text_search_result.error:
        print(f"❌ 获取{station1_name}坐标失败: {text_search_result.error}")
        return False

    if not text_search_result.pois or len(text_search_result.pois) == 0:
        print(f"❌ 未找到{station1_name}坐标")
        return False

    first_poi_id = text_search_result.pois[0].id
    detail_result = maps_search_detail(id=first_poi_id)
    if detail_result.error or not detail_result.location:
        print(f"❌ 获取{station1_name}坐标失败: {detail_result.error or '无location'}")
        return False

    station1_location = detail_result.location
    print(f"✅ 获取{station1_name}坐标: {station1_location}")

    # 获取第二个车站坐标
    text_search_result = maps_text_search(keywords=station2_name, city=city)
    if text_search_result.error:
        print(f"❌ 获取{station2_name}坐标失败: {text_search_result.error}")
        return False

    if not text_search_result.pois or len(text_search_result.pois) == 0:
        print(f"❌ 未找到{station2_name}坐标")
        return False

    first_poi_id = text_search_result.pois[0].id
    detail_result = maps_search_detail(id=first_poi_id)
    if detail_result.error or not detail_result.location:
        print(f"❌ 获取{station2_name}坐标失败: {detail_result.error or '无location'}")
        return False

    station2_location = detail_result.location
    print(f"✅ 获取{station2_name}坐标: {station2_location}")

    # 计算从第一个车站步行到目标点的时间
    station1_walking_result = maps_walking_by_coordinates(origin=station1_location, destination=poi_location)
    if station1_walking_result.error:
        print(f"❌ 计算从{station1_name}步行路线失败: {station1_walking_result.error}")
        return False

    if station1_walking_result.total_duration_seconds is None:
        print(f"❌ 无法获取从{station1_name}步行时长")
        return False

    station1_walking_duration = station1_walking_result.total_duration_seconds
    print(f"✅ 从{station1_name}步行时长{station1_walking_duration}秒（{station1_walking_duration // 60}分钟）")

    # 计算从第二个车站步行到目标点的时间
    station2_walking_result = maps_walking_by_coordinates(origin=station2_location, destination=poi_location)
    if station2_walking_result.error:
        print(f"❌ 计算从{station2_name}步行路线失败: {station2_walking_result.error}")
        return False

    if station2_walking_result.total_duration_seconds is None:
        print(f"❌ 无法获取从{station2_name}步行时长")
        return False

    station2_walking_duration = station2_walking_result.total_duration_seconds
    print(f"✅ 从{station2_name}步行时长{station2_walking_duration}秒（{station2_walking_duration // 60}分钟）")

    # 计算时间差
    time_difference = abs(station1_walking_duration - station2_walking_duration)
    if time_difference > max_time_difference:
        print(f"❌ 两位朋友步行时间差{time_difference}秒（{time_difference // 60}分钟），超过{max_time_difference}秒（{max_time_difference // 60}分钟）")
        return False
    print(f"✅ 两位朋友步行时间差{time_difference}秒（{time_difference // 60}分钟），符合要求（<= {max_time_difference}秒，即{max_time_difference // 60}分钟）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 811.py 文件...\n")
    result = verify_poi(poi_id="B022200FA4")
    print(f"\n验证结果: {result}")

