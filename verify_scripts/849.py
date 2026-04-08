
"""
修改任务指令：你要在附近2000米以内找一家酒店。酒店评分至少4.8分。另外你想避开人多的景点，所以这家酒店不能在许昌动物园直线距离500米范围内。你朋友从许昌火车站打车过来，你从当前位置先步行去酒店，你们都要再去胖东来时代广场碰头，所以"许昌火车站→酒店→胖东来时代广场"的总开车时间要在6分钟以内，并且相比"许昌火车站直接开到胖东来时代广场"，增加的时间不能超过3分钟。你还希望这家酒店离许昌火车站步行20分钟以内。最后你担心现金不够，酒店周围400米内必须能找到ATM。你逻辑性强但没有耐心，希望高效沟通，讨厌废话。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边约束：调用 maps_around_search(location='113.822816,34.023623', radius='2000', keywords='酒店')，结果中必须包含 target_poi_id。
2) 评分约束：调用 maps_search_detail(id='B017600QGN')，取 biz_ext.rating，验证 rating>=4.8。
3) 不在其他地点附近：调用 maps_search_detail(id='B017600QGN') 得到酒店坐标H；调用 maps_search_detail(id='B0FFH3XL11') 得到"许昌动物园"坐标Z；调用 maps_distance(origins=H, destination=Z)，验证距离>500米。
4) 交通枢纽可达性(步行)：调用 maps_text_search(keywords='许昌火车站', city='许昌') 得到poi_id，再调用 maps_search_detail(id=poi_id) 获取坐标S；调用 maps_walking_by_coordinates(origin=H, destination=S)，验证步行总时长<=1200秒。
5) A经由目标到B的总行程时间(驾车)：调用 maps_text_search(keywords='胖东来时代广场', city='许昌') 得到poi_id，再调用 maps_search_detail(id=poi_id) 获取坐标B；调用 maps_driving_by_coordinates(origin=S, destination=H) 得到t1；调用 maps_driving_by_coordinates(origin=H, destination=B) 得到t2；验证(t1+t2)<=360秒。
6) 绕行增量时间：调用 maps_driving_by_coordinates(origin=S, destination=B) 得到t0；验证((t1+t2)-t0)<=180秒。
7) 途径点附近有POI类型A：在步骤5得到的驾车路线 steps 中，取每个 step.to_coordinates 和起点、终点组成途径点集合P；对每个p∈P调用 maps_around_search(location=p, radius='400', keywords='ATM')，至少存在一个途径点返回pois非空。
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
    user_location: str = "113.822816,34.023623",
    search_radius: int = 2000,
    keywords: str = "酒店",
    min_rating: float = 4.8,
    zoo_name: str = "许昌动物园",
    min_exclusion_distance: int = 500,
    station_address: str = "许昌火车站",
    plaza_address: str = "胖东来时代广场",
    city: str = "许昌",
    max_walking_duration: int = 1200,  # 20 minutes = 1200 seconds
    max_total_driving_duration: int = 360,  # 6 minutes = 360 seconds
    max_detour_increment: int = 180,  # 3 minutes = 180 seconds
    atm_search_radius: int = 400,
    atm_keywords: str = "ATM"
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 周边约束：调用 maps_around_search，结果中必须包含 target_poi_id。
    2) 评分约束：调用 maps_search_detail，验证 rating>=4.8。
    3) 不在其他地点附近：验证距离>500米。
    4) 交通枢纽可达性(步行)：验证步行总时长<=1200秒。
    5) A经由目标到B的总行程时间(驾车)：验证(t1+t2)<=360秒。
    6) 绕行增量时间：验证((t1+t2)-t0)<=180秒。
    7) 途径点附近有POI类型A：至少存在一个途径点返回pois非空。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"113.822816,34.023623"
        search_radius: 搜索半径（米），默认2000
        keywords: 搜索关键词，默认"酒店"
        min_rating: 最低评分，默认4.8
        zoo_name: 动物园名称，默认"许昌动物园"
        min_exclusion_distance: 最小排除距离（米），默认500
        station_address: 火车站地址，默认"许昌火车站"
        plaza_address: 广场地址，默认"胖东来时代广场"
        city: 城市名称，默认"许昌"
        max_walking_duration: 最大步行时间（秒），默认1200（20分钟）
        max_total_driving_duration: 最大总驾车时间（秒），默认360（6分钟）
        max_detour_increment: 最大绕行增加时间（秒），默认180（3分钟）
        atm_search_radius: ATM搜索半径（米），默认400
        atm_keywords: ATM搜索关键词，默认"ATM"

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 周边约束
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

    # 步骤2: 评分约束
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    hotel_location = poi_detail.location
    print(f"✅ 获取酒店坐标: {hotel_location}")

    # 验证评分
    if poi_detail.biz_ext and 'rating' in poi_detail.biz_ext:
        rating = float(poi_detail.biz_ext['rating'])
        if rating < min_rating:
            print(f"❌ POI评分{rating}分，低于{min_rating}分")
            return False
        print(f"✅ POI评分{rating}分，符合要求（>= {min_rating}分）")
    else:
        print(f"❌ POI没有评分信息")
        return False

    # 步骤3: 不在其他地点附近（许昌动物园）
    # 首先搜索动物园
    zoo_search_result = maps_text_search(
        keywords=zoo_name,
        city=city,
        citylimit="true"
    )
    if zoo_search_result.error:
        print(f"❌ 搜索{zoo_name}失败: {zoo_search_result.error}")
        return False

    if not zoo_search_result.pois or len(zoo_search_result.pois) == 0:
        print(f"❌ 未找到{zoo_name}")
        return False

    # 获取动物园POI ID
    zoo_poi_id = zoo_search_result.pois[0].id
    print(f"✅ 找到{zoo_name}，POI ID: {zoo_poi_id}")

    # 获取动物园详情以获取坐标
    zoo_detail = maps_search_detail(id=zoo_poi_id)
    if zoo_detail.error:
        print(f"❌ 获取{zoo_name}详情失败: {zoo_detail.error}")
        return False

    if not zoo_detail.location:
        print(f"❌ {zoo_name}没有location信息")
        return False

    zoo_location = zoo_detail.location
    print(f"✅ 获取{zoo_name}坐标: {zoo_location}")

    # 计算直线距离
    distance_result = maps_distance(origins=hotel_location, destination=zoo_location)
    if distance_result.error:
        print(f"❌ 计算到{zoo_name}距离失败: {distance_result.error}")
        return False

    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 未获取到到{zoo_name}的距离信息")
        return False

    zoo_distance = distance_result.results[0].distance_meters
    if zoo_distance <= min_exclusion_distance:
        print(f"❌ 到{zoo_name}直线距离{zoo_distance}米，不大于{min_exclusion_distance}米")
        return False
    print(f"✅ 到{zoo_name}直线距离{zoo_distance}米，符合要求（> {min_exclusion_distance}米）")

    # 步骤4: 交通枢纽可达性(步行) - 获取火车站坐标
    station_text_search_result = maps_text_search(keywords=station_address, city=city)
    if station_text_search_result.error:
        print(f"❌ 获取{station_address}坐标失败: {station_text_search_result.error}")
        return False

    if not station_text_search_result.pois or len(station_text_search_result.pois) == 0:
        print(f"❌ 未找到{station_address}坐标")
        return False

    station_poi_id = station_text_search_result.pois[0].id
    station_detail_result = maps_search_detail(id=station_poi_id)
    if station_detail_result.error:
        print(f"❌ 获取{station_address}详情失败: {station_detail_result.error}")
        return False
    if not station_detail_result.location:
        print(f"❌ {station_address}没有location信息")
        return False
    station_location = station_detail_result.location
    print(f"✅ 获取{station_address}坐标: {station_location}")

    # 验证从酒店步行到火车站时间<=1200秒
    walking_result = maps_walking_by_coordinates(origin=hotel_location, destination=station_location)
    # print(hotel_location, station_location) #########

    if walking_result.error:
        print(f"❌ 计算从酒店步行到{station_address}失败: {walking_result.error}")
        return False

    if walking_result.total_duration_seconds is None:
        print(f"❌ 无法获取从酒店步行到{station_address}的时长")
        return False

    walking_duration = walking_result.total_duration_seconds
    if walking_duration > max_walking_duration:
        print(f"❌ 从酒店步行到{station_address}时长{walking_duration}秒（{walking_duration / 60:.2f}分钟），超过{max_walking_duration}秒（{max_walking_duration // 60}分钟）")
        return False
    print(f"✅ 从酒店步行到{station_address}时长{walking_duration}秒（{walking_duration / 60:.2f}分钟），符合要求（<= {max_walking_duration}秒，即{max_walking_duration // 60}分钟）")

    # 步骤5: A经由目标到B的总行程时间(驾车) - 获取广场坐标
    plaza_text_search_result = maps_text_search(keywords=plaza_address, city=city)
    if plaza_text_search_result.error:
        print(f"❌ 获取{plaza_address}坐标失败: {plaza_text_search_result.error}")
        return False

    if not plaza_text_search_result.pois or len(plaza_text_search_result.pois) == 0:
        print(f"❌ 未找到{plaza_address}坐标")
        return False

    plaza_poi_id = plaza_text_search_result.pois[0].id
    plaza_detail_result = maps_search_detail(id=plaza_poi_id)
    if plaza_detail_result.error:
        print(f"❌ 获取{plaza_address}详情失败: {plaza_detail_result.error}")
        return False
    if not plaza_detail_result.location:
        print(f"❌ {plaza_address}没有location信息")
        return False
    plaza_location = plaza_detail_result.location
    print(f"✅ 获取{plaza_address}坐标: {plaza_location}")

    # 计算火车站→酒店的驾车时间
    driving_station_to_hotel_result = maps_driving_by_coordinates(origin=station_location, destination=hotel_location)
    if driving_station_to_hotel_result.error:
        print(f"❌ 计算从{station_address}到酒店驾车路线失败: {driving_station_to_hotel_result.error}")
        return False

    if driving_station_to_hotel_result.total_duration_seconds is None:
        print(f"❌ 无法获取从{station_address}到酒店驾车时长")
        return False

    t1 = driving_station_to_hotel_result.total_duration_seconds
    print(f"✅ 从{station_address}到酒店驾车时长{t1}秒（{t1 / 60:.2f}分钟）")

    # 计算酒店→广场的驾车时间
    driving_hotel_to_plaza_result = maps_driving_by_coordinates(origin=hotel_location, destination=plaza_location)
    if driving_hotel_to_plaza_result.error:
        print(f"❌ 计算从酒店到{plaza_address}驾车路线失败: {driving_hotel_to_plaza_result.error}")
        return False

    if driving_hotel_to_plaza_result.total_duration_seconds is None:
        print(f"❌ 无法获取从酒店到{plaza_address}驾车时长")
        return False

    t2 = driving_hotel_to_plaza_result.total_duration_seconds
    print(f"✅ 从酒店到{plaza_address}驾车时长{t2}秒（{t2 / 60:.2f}分钟）")

    # 验证总行程时间<=360秒
    total_driving_duration = t1 + t2
    if total_driving_duration > max_total_driving_duration:
        print(f"❌ 总行程时间{total_driving_duration}秒（{total_driving_duration / 60:.2f}分钟），超过{max_total_driving_duration}秒（{max_total_driving_duration // 60}分钟）")
        return False
    print(f"✅ 总行程时间{total_driving_duration}秒（{total_driving_duration / 60:.2f}分钟），符合要求（<= {max_total_driving_duration}秒，即{max_total_driving_duration // 60}分钟）")

    # 步骤6: 绕行增量时间
    direct_driving_result = maps_driving_by_coordinates(origin=station_location, destination=plaza_location)
    if direct_driving_result.error:
        print(f"❌ 计算从{station_address}直接到{plaza_address}驾车路线失败: {direct_driving_result.error}")
        return False

    if direct_driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取从{station_address}直接到{plaza_address}驾车时长")
        return False

    t0 = direct_driving_result.total_duration_seconds
    print(f"✅ 从{station_address}直接到{plaza_address}驾车时长{t0}秒（{t0 / 60:.2f}分钟）")

    detour_increment = total_driving_duration - t0
    if detour_increment > max_detour_increment:
        print(f"❌ 绕行增加时间{detour_increment}秒（{detour_increment / 60:.2f}分钟），超过{max_detour_increment}秒（{max_detour_increment // 60}分钟）")
        return False
    print(f"✅ 绕行增加时间{detour_increment}秒（{detour_increment / 60:.2f}分钟），符合要求（<= {max_detour_increment}秒，即{max_detour_increment // 60}分钟）")

    # 步骤7: 途径点附近有POI类型A（ATM）
    # 收集所有途径点坐标：起点、终点、以及路线中的所有step.to_coordinates
    waypoints = []

    # 添加起点（火车站）
    waypoints.append(station_location)

    # 从火车站→酒店路线中提取途径点
    if driving_station_to_hotel_result.steps:
        for step in driving_station_to_hotel_result.steps:
            if step.to_coordinates:
                waypoints.append(step.to_coordinates)

    # 从酒店→广场路线中提取途径点
    if driving_hotel_to_plaza_result.steps:
        for step in driving_hotel_to_plaza_result.steps:
            if step.to_coordinates:
                waypoints.append(step.to_coordinates)

    # 添加终点（广场）
    waypoints.append(plaza_location)

    print(f"✅ 收集到{len(waypoints)}个途径点")

    # 检查是否至少有一个途径点附近有ATM
    found_atm_waypoint = False
    for i, waypoint in enumerate(waypoints):
        atm_search_result = maps_around_search(
            location=waypoint,
            radius=str(atm_search_radius),
            keywords=atm_keywords
        )
        if not atm_search_result.error and atm_search_result.pois and len(atm_search_result.pois) > 0:
            print(f"✅ 途径点{i+1}（{waypoint}）附近{atm_search_radius}米内找到{len(atm_search_result.pois)}个ATM")
            found_atm_waypoint = True
            break

    if not found_atm_waypoint:
        print(f"❌ 所有途径点附近{atm_search_radius}米内均未找到ATM")
        return False

    print(f"✅ 至少存在一个途径点附近有ATM，符合要求")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 849.py 文件...\n")
    result = verify_poi(poi_id="B017600QGN")
    print(f"\n验证结果: {result}")

