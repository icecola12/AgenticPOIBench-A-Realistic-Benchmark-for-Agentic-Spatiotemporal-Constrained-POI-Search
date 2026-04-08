"""
修改任务指令：你要在附近3000米以内找一家酒店。你打算骑车过去，所以骑行距离不能超过2000米，同时步行过去的距离也不能超过2500米。你还希望开车过去也别太远，驾车距离控制在2.5公里以内。酒店要离一个你们常用的公交站"青山湖区政府西门(公交站)"不超过5000米直线距离。并且酒店附近1200米内要能找到地铁站，酒店走到这些地铁站里最近的那个，步行时间不能超过15分钟。最后你要从酒店打车去南昌昌北国际机场，车程时间不要超过30分钟。你说话时会夹杂英语单词，有些不耐烦。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 附近3000米酒店：调用 maps_around_search(location='115.933816,28.708441', radius='3000', keywords='酒店')，验证返回pois中包含 target_poi_id='B0JUCZ10JY'。
2) 酒店类型与评分：调用 maps_search_detail(id='B0JUCZ10JY')， biz_ext.rating >= 4.6（该POI为4.6）。
3) 骑行距离≤2000米：用 maps_search_detail 取酒店坐标destination='115.920828,28.705862'；调用 maps_bicycling_by_coordinates(origin='115.933816,28.708441', destination='115.920828,28.705862')，验证 total_distance_meters <= 2000（实际1920m）。
4) 步行距离≤2500米：调用 maps_walking_by_coordinates(origin='115.933816,28.708441', destination='115.920828,28.705862')，验证 total_distance_meters <= 2500（实际1920m）。
5) 驾车距离≤2.5公里：调用 maps_driving_by_coordinates(origin='115.933816,28.708441', destination='115.920828,28.705862')，验证 total_distance_meters <= 2500（实际1920m）。
6) 到指定公交站直线距离≤5000米：调用 maps_geo(address='青山湖区政府西门(公交站)', city='南昌') 得到站点坐标 '115.960510,28.683555'；再调用 maps_distance(origins='115.960510,28.683555', destination='115.920828,28.705862')，验证 distance_meters <= 5000（实际4602m）。
7) 附近1200米内有地铁站：调用 maps_around_search(location='115.920828,28.705862', radius='1200', keywords='地铁站')。
8) 到最近地铁站步行时间≤15分钟：对步骤7返回的每个地铁站poi，取其location分别调用 maps_walking_by_coordinates(origin='115.920828,28.705862', destination=station_location)，取最小 total_duration_seconds，验证 <= 900秒（到七里站520秒，到起凤路站843秒，最小520秒）。
9) 到机场驾车时间≤30分钟：调用 maps_geo(address='南昌昌北国际机场', city='南昌') 得到 '115.911718,28.858250'；调用 maps_driving_by_coordinates(origin='115.920828,28.705862', destination='115.911718,28.858250')，验证 total_duration_seconds <= 1800秒（实际1757秒）。
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
    maps_walking_by_coordinates,
    maps_driving_by_coordinates,
    maps_geo,
    maps_distance,
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "115.933816,28.708441",
    hotel_location: str = "115.920828,28.705862",
    search_radius: int = 3000,
    keywords: str = "酒店",
    min_rating: float = 4.6,
    max_bicycling_distance: int = 2000,
    max_walking_distance: int = 2500,
    max_driving_distance: int = 2500,
    bus_station_address: str = "青山湖区政府西门(公交站)",
    city: str = "南昌",
    max_bus_station_distance: int = 5000,
    subway_search_radius: int = 1200,
    subway_keywords: str = "地铁站",
    max_walking_duration_to_subway: int = 900,  # 15分钟 = 900秒
    airport_address: str = "南昌昌北国际机场",
    max_driving_duration_to_airport: int = 1800,  # 30分钟 = 1800秒
) -> bool:
    """
    验证POI（酒店）是否符合要求。

    验证步骤：
    1) 附近3000米酒店：maps_around_search，验证返回pois中包含目标poi_id。
    2) 酒店类型与评分：maps_search_detail，biz_ext.rating >= 4.6。
    3) 骑行距离≤2000米：maps_bicycling_by_coordinates，total_distance_meters <= 2000。
    4) 步行距离≤2500米：maps_walking_by_coordinates，total_distance_meters <= 2500。
    5) 驾车距离≤2.5公里：maps_driving_by_coordinates，total_distance_meters <= 2500。
    6) 到指定公交站直线距离≤5000米：maps_geo 得公交站坐标，maps_distance <= 5000。
    7) 附近1200米内有地铁站：maps_around_search 以酒店为中心搜地铁站。
    8) 到最近地铁站步行时间≤15分钟：对步骤7各地铁站分别算步行时间，取最小 <= 900秒。
    9) 到机场驾车时间≤30分钟：maps_geo 得机场坐标，maps_driving_by_coordinates <= 1800秒。

    Args:
        poi_id: POI ID，默认"B0JUCZ10JY"
        user_location: 用户坐标，默认"115.933816,28.708441"
        hotel_location: 酒店坐标（可从 detail 覆盖），默认"115.920828,28.705862"
        search_radius: 搜索半径（米），默认3000
        keywords: 搜索关键词，默认"酒店"
        min_rating: 最小评分，默认4.6
        max_bicycling_distance: 最大骑行距离（米），默认2000
        max_walking_distance: 最大步行距离（米），默认2500
        max_driving_distance: 最大驾车距离（米），默认2500
        bus_station_address: 公交站地址，默认"青山湖区政府西门(公交站)"
        city: 城市，默认"南昌"
        max_bus_station_distance: 酒店到公交站最大直线距离（米），默认5000
        subway_search_radius: 地铁站搜索半径（米），默认1200
        subway_keywords: 地铁站搜索关键词，默认"地铁站"
        max_walking_duration_to_subway: 到最近地铁站最大步行时间（秒），默认900（15分钟）
        airport_address: 机场地址，默认"南昌昌北国际机场"
        max_driving_duration_to_airport: 酒店到机场最大驾车时间（秒），默认1800（30分钟）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 附近3000米酒店
    # 注意：首个约束应该为"你想找一个附近指定距离的poi点"，而非"你想找一个离你不超过指定距离的poi点"
    print(f"【步骤1】验证附近范围（{search_radius}米范围内，关键词：{keywords}）")
    print("-" * 80)
    around_search_result = maps_around_search(
        location=user_location,
        radius=str(search_radius),
        keywords=keywords
    )
    if around_search_result.error:
        print(f"❌ 搜索附近POI失败: {around_search_result.error}")
        return False

    if not around_search_result.pois:
        print(f"❌ 未找到符合条件的POI")
        return False

    poi_found = False
    for poi in around_search_result.pois:
        if poi.id == poi_id:
            poi_found = True
            print(f"✅ 在{search_radius}米范围内找到目标POI: {poi.name} (ID: {poi_id})")
            break

    if not poi_found:
        print(f"❌ 目标POI {poi_id} 不在{search_radius}米范围内的{keywords}列表中")
        return False

    # 步骤2: 酒店类型与评分，并获取酒店坐标
    print(f"\n【步骤2】验证评分（>={min_rating}分）")
    print("-" * 80)
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if poi_detail.location:
        hotel_location = poi_detail.location
        print(f"✅ 获取酒店坐标: {hotel_location} ({poi_detail.name})")
    else:
        print(f"⚠️  POI详情中没有location信息，使用默认坐标: {hotel_location}")

    if poi_detail.biz_ext:
        rating = poi_detail.biz_ext.get("rating")
        if rating is not None:
            try:
                rating_value = float(rating)
                if rating_value < min_rating:
                    print(f"❌ POI评分{rating_value}，低于要求的最小评分{min_rating}")
                    return False
                print(f"✅ POI评分{rating_value}，满足要求（>={min_rating}）")
            except (ValueError, TypeError):
                print(f"⚠️  无法解析rating值: {rating}，跳过评分验证")
        else:
            print(f"⚠️  POI没有rating信息，跳过评分验证")
    else:
        print(f"⚠️  POI没有biz_ext信息，跳过评分验证")

    # 步骤3: 骑行距离≤2000米
    print(f"\n【步骤3】验证骑行距离（≤{max_bicycling_distance}米）")
    print("-" * 80)
    bicycling_result = maps_bicycling_by_coordinates(
        origin=user_location,
        destination=hotel_location
    )
    if bicycling_result.error:
        print(f"❌ 计算骑行路线失败: {bicycling_result.error}")
        return False

    if bicycling_result.total_distance_meters is None:
        print(f"❌ 无法获取骑行距离")
        return False

    if bicycling_result.total_distance_meters > max_bicycling_distance:
        print(f"❌ 骑行距离{bicycling_result.total_distance_meters}米，超过{max_bicycling_distance}米")
        return False
    print(f"✅ 骑行距离{bicycling_result.total_distance_meters}米，符合要求（≤{max_bicycling_distance}米）")

    # 步骤4: 步行距离≤2500米
    print(f"\n【步骤4】验证步行距离（≤{max_walking_distance}米）")
    print("-" * 80)
    walking_result = maps_walking_by_coordinates(
        origin=user_location,
        destination=hotel_location
    )
    if walking_result.error:
        print(f"❌ 计算步行路线失败: {walking_result.error}")
        return False

    if walking_result.total_distance_meters is None:
        print(f"❌ 无法获取步行距离")
        return False

    if walking_result.total_distance_meters > max_walking_distance:
        print(f"❌ 步行距离{walking_result.total_distance_meters}米，超过{max_walking_distance}米")
        return False
    print(f"✅ 步行距离{walking_result.total_distance_meters}米，符合要求（≤{max_walking_distance}米）")

    # 步骤5: 驾车距离≤2.5公里
    print(f"\n【步骤5】验证驾车距离（≤{max_driving_distance}米，即2.5公里）")
    print("-" * 80)
    driving_result = maps_driving_by_coordinates(
        origin=user_location,
        destination=hotel_location
    )
    if driving_result.error:
        print(f"❌ 计算驾车路线失败: {driving_result.error}")
        return False

    if driving_result.total_distance_meters is None:
        print(f"❌ 无法获取驾车距离")
        return False

    if driving_result.total_distance_meters > max_driving_distance:
        print(f"❌ 驾车距离{driving_result.total_distance_meters}米，超过{max_driving_distance}米")
        return False
    print(f"✅ 驾车距离{driving_result.total_distance_meters}米，符合要求（≤{max_driving_distance}米）")

    # 步骤6: 到指定公交站直线距离≤5000米
    print(f"\n【步骤6】验证到公交站直线距离（≤{max_bus_station_distance}米）")
    print("-" * 80)
    geo_bus = maps_geo(address=bus_station_address, city=city)
    if geo_bus.error or not geo_bus.results:
        print(f"❌ 地理编码公交站失败: {geo_bus.error or '无结果'}")
        return False

    bus_station_location = geo_bus.results[0].location
    print(f"✅ 公交站坐标: {bus_station_location}")

    dist_bus = maps_distance(origins=bus_station_location, destination=hotel_location)
    if dist_bus.error or not dist_bus.results:
        print(f"❌ 计算到公交站直线距离失败: {dist_bus.error or '无结果'}")
        return False

    bus_distance = dist_bus.results[0].distance_meters
    if bus_distance > max_bus_station_distance:
        print(f"❌ 到公交站直线距离{bus_distance}米，超过{max_bus_station_distance}米")
        return False
    print(f"✅ 到公交站直线距离{bus_distance}米，符合要求（≤{max_bus_station_distance}米）")

    # 步骤7: 附近1200米内有地铁站
    print(f"\n【步骤7】验证酒店附近{subway_search_radius}米内有地铁站")
    print("-" * 80)
    subway_search_result = maps_around_search(
        location=hotel_location,
        radius=str(subway_search_radius),
        keywords=subway_keywords
    )
    if subway_search_result.error:
        print(f"❌ 搜索地铁站失败: {subway_search_result.error}")
        return False

    if not subway_search_result.pois or len(subway_search_result.pois) == 0:
        print(f"❌ 酒店{subway_search_radius}米范围内未找到地铁站")
        return False

    print(f"✅ 找到{len(subway_search_result.pois)}个地铁站")

    # 步骤8: 到最近地铁站步行时间≤15分钟
    print(f"\n【步骤8】验证到最近地铁站步行时间（≤{max_walking_duration_to_subway}秒，即15分钟）")
    print("-" * 80)
    min_walk_duration = None
    for station in subway_search_result.pois:
        if not station.location:
            continue
        walk_result = maps_walking_by_coordinates(
            origin=hotel_location,
            destination=station.location
        )
        if walk_result.error or walk_result.total_duration_seconds is None:
            continue
        d = walk_result.total_duration_seconds
        if min_walk_duration is None or d < min_walk_duration:
            min_walk_duration = d

    if min_walk_duration is None:
        print(f"❌ 无法计算到任一地铁站的步行时间")
        return False

    if min_walk_duration > max_walking_duration_to_subway:
        print(f"❌ 到最近地铁站步行时间{min_walk_duration}秒，超过{max_walking_duration_to_subway}秒（15分钟）")
        return False
    print(f"✅ 到最近地铁站步行时间{min_walk_duration}秒，符合要求（≤{max_walking_duration_to_subway}秒）")

    # 步骤9: 到机场驾车时间≤30分钟
    print(f"\n【步骤9】验证到机场驾车时间（≤{max_driving_duration_to_airport}秒，即30分钟）")
    print("-" * 80)
    geo_airport = maps_geo(address=airport_address, city=city)
    if geo_airport.error or not geo_airport.results:
        print(f"❌ 地理编码机场失败: {geo_airport.error or '无结果'}")
        return False

    airport_location = geo_airport.results[0].location
    print(f"✅ 机场坐标: {airport_location}")

    drive_airport_result = maps_driving_by_coordinates(
        origin=hotel_location,
        destination=airport_location
    )
    if drive_airport_result.error:
        print(f"❌ 计算到机场驾车路线失败: {drive_airport_result.error}")
        return False

    if drive_airport_result.total_duration_seconds is None:
        print(f"❌ 无法获取到机场驾车时长")
        return False

    if drive_airport_result.total_duration_seconds > max_driving_duration_to_airport:
        print(f"❌ 到机场驾车时长{drive_airport_result.total_duration_seconds}秒，超过{max_driving_duration_to_airport}秒（30分钟）")
        return False
    print(f"✅ 到机场驾车时长{drive_airport_result.total_duration_seconds}秒，符合要求（≤{max_driving_duration_to_airport}秒）")

    print(f"\n✅ 所有验证通过！")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python 760.py <poi_id> [user_location]")
        print("示例: python 760.py B0JUCZ10JY")
        print("示例: python 760.py B0JUCZ10JY 115.933816,28.708441")
        print("未传参，使用示例默认值运行。")
        poi_id = "B0JUCZ10JY"
        user_location = "115.933816,28.708441"
    else:
        poi_id = sys.argv[1]
        user_location = sys.argv[2] if len(sys.argv) > 2 else "115.933816,28.708441"
        

    print(f"开始验证POI: {poi_id}")
    print(f"用户坐标: {user_location}")
    print("=" * 80)

    result = verify_poi(poi_id, user_location=user_location)

    print("=" * 80)
    print(f"验证结果: {'通过' if result else '失败'}")
