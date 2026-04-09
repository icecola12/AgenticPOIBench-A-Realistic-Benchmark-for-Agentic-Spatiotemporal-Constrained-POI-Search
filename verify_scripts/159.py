
"""
修改任务指令：你想在附近1200米内找一家美术馆。你希望它离你步行过去的路程不要超过1300米，骑车过去的路程也别超过1500米，开车过去的距离不超过2公里。另外，你约了朋友在和平门地铁站碰头，所以这家美术馆到和平门地铁站的步行时间要在15分钟以内。你之后还得赶去北京南站坐车，所以从美术馆开车到北京南站不要超过8分钟。最后，你希望从你这边走过去的路上中存在一个途径点周围800米内能找到洗衣店，方便顺路办事。你有礼貌但很固执，坚持自己的要求不让步。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 附近1200米内（首要约束）
- 调用 maps_around_search(location=U, radius=1200, keywords='美术馆')，验证返回pois列表中包含 target_poi_id='B000A8UL4T'。

2) 步行路程≤1300米
- 调用 maps_search_detail('B000A8UL4T') 获取P坐标。
- 调用 maps_walking_by_coordinates(origin=U, destination=P.location)，验证 total_distance_meters ≤ 1300。

3) 骑行路程≤1500米
- 调用 maps_bicycling_by_coordinates(origin=U, destination=P.location)，验证 total_distance_meters ≤ 1500。

4) 驾车距离≤2公里
- 调用 maps_driving_by_coordinates(origin=U, destination=P.location)，验证 total_distance_meters ≤ 2000。

5) 到指定公交/地铁站点的距离限制：到【和平门地铁站】步行时间≤15分钟
- 调用 maps_text_search(keywords='和平门(地铁站)', city='北京') 获取 poi_id，再调用 maps_search_detail(id=poi_id) 得到S坐标。
- 调用 maps_walking_by_coordinates(origin=P.location, destination=S.location)，验证 total_duration_seconds ≤ 900。

6) 到特定交通枢纽：到【北京南站】驾车时间≤8分钟
- 调用 maps_text_search(keywords='北京南站', city='北京') 获取 poi_id，再调用 maps_search_detail(id=poi_id) 得到N坐标。
- 调用 maps_driving_by_coordinates(origin=P.location, destination=N.location)，验证 total_duration_seconds ≤ 480。

7) 途径点附近POI类型A：路中点M附近800米内有【洗衣店】
- 在步骤2的 maps_walking_by_coordinates 返回steps中，取包括起点终点的中间所有途径点to_coordinates）
- 逐个调用 maps_around_search(location=M, radius=800, keywords='洗衣店')，验证其中存在一个点的 pois 不为空（≥1）。
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
    maps_bicycling_by_coordinates,
    maps_walking_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "116.376186,39.902373",
    search_radius: int = 1200,
    keywords: str = "美术馆",
    max_walking_distance: int = 1300,  # 1300 meters
    max_bicycling_distance: int = 1500,  # 1500 meters
    max_driving_distance: int = 2000,  # 2 km = 2000 meters
    subway_station_name: str = "和平门(地铁站)",
    city: str = "北京",
    max_subway_walking_duration: int = 900,  # 15 minutes = 900 seconds
    train_station_name: str = "北京南站",
    max_train_station_driving_duration: int = 480,  # 8 minutes = 480 seconds
    laundry_search_radius: int = 800,
    laundry_keywords: str = "洗衣店"
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 附近1200米内：调用 maps_around_search，验证返回pois数量≥8，且列表中包含target_poi_id。
    2) 步行路程≤1300米：调用 maps_search_detail 获取P坐标，调用 maps_walking_by_coordinates，验证 total_distance_meters ≤ 1300。
    3) 骑行路程≤1500米：调用 maps_bicycling_by_coordinates，验证 total_distance_meters ≤ 1500。
    4) 驾车距离≤2公里：调用 maps_driving_by_coordinates，验证 total_distance_meters ≤ 2000。
    5) 到和平门地铁站步行时间≤15分钟：调用 maps_text_search 获取 poi_id，再用 maps_search_detail 得到S坐标，调用 maps_walking_by_coordinates，验证 total_duration_seconds ≤ 900。
    6) 到北京南站驾车时间≤8分钟：调用 maps_text_search 获取 poi_id，再用 maps_search_detail 得到N坐标，调用 maps_driving_by_coordinates，验证 total_duration_seconds ≤ 480。
    7) 途径点附近有洗衣店：在步行路线steps中取途径点，调用 maps_around_search，验证存在一个点的pois不为空。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"116.397428,39.90923"
        search_radius: 搜索半径（米），默认1200
        keywords: 搜索关键词，默认"美术馆"
        max_walking_distance: 最大步行距离（米），默认1300
        max_bicycling_distance: 最大骑行距离（米），默认1500
        max_driving_distance: 最大驾车距离（米），默认2000
        subway_station_name: 地铁站名称，默认"和平门(地铁站)"
        city: 城市名称，默认"北京"
        max_subway_walking_duration: 到地铁站最大步行时长（秒），默认900（15分钟）
        train_station_name: 火车站名称，默认"北京南站"
        max_train_station_driving_duration: 到火车站最大驾车时长（秒），默认480（8分钟）
        laundry_search_radius: 洗衣店搜索半径（米），默认800
        laundry_keywords: 洗衣店搜索关键词，默认"洗衣店"

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 附近1200米内
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

    # 步骤3: 步行路程≤1300米
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

    # 步骤4: 骑行路程≤1500米
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

    # 步骤5: 驾车距离≤2公里
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

    # 步骤6: 到和平门地铁站步行时间≤15分钟
    text_search_result = maps_text_search(keywords=subway_station_name, city=city)
    if text_search_result.error:
        print(f"❌ 获取{subway_station_name}坐标失败: {text_search_result.error}")
        return False

    if not text_search_result.pois or len(text_search_result.pois) == 0:
        print(f"❌ 未找到{subway_station_name}坐标")
        return False

    first_poi_id = text_search_result.pois[0].id
    detail_result = maps_search_detail(id=first_poi_id)
    if detail_result.error or not detail_result.location:
        print(f"❌ 获取{subway_station_name}坐标失败: {detail_result.error or '无location'}")
        return False

    subway_location = detail_result.location
    print(f"✅ 获取{subway_station_name}坐标: {subway_location}")

    subway_walking_result = maps_walking_by_coordinates(origin=poi_location, destination=subway_location)
    if subway_walking_result.error:
        print(f"❌ 计算到{subway_station_name}步行路线失败: {subway_walking_result.error}")
        return False

    if subway_walking_result.total_duration_seconds is None:
        print(f"❌ 无法获取到{subway_station_name}步行时长")
        return False

    subway_walking_duration = subway_walking_result.total_duration_seconds
    if subway_walking_duration > max_subway_walking_duration:
        print(f"❌ 到{subway_station_name}步行时长{subway_walking_duration}秒，超过{max_subway_walking_duration}秒（{max_subway_walking_duration // 60}分钟）")
        return False
    print(f"✅ 到{subway_station_name}步行时长{subway_walking_duration}秒，符合要求（<= {max_subway_walking_duration}秒，即{max_subway_walking_duration // 60}分钟）")

    # 步骤7: 到北京南站驾车时间≤8分钟
    text_search_result = maps_text_search(keywords=train_station_name, city=city)
    if text_search_result.error:
        print(f"❌ 获取{train_station_name}坐标失败: {text_search_result.error}")
        return False

    if not text_search_result.pois or len(text_search_result.pois) == 0:
        print(f"❌ 未找到{train_station_name}坐标")
        return False

    first_poi_id = text_search_result.pois[0].id
    detail_result = maps_search_detail(id=first_poi_id)
    if detail_result.error or not detail_result.location:
        print(f"❌ 获取{train_station_name}坐标失败: {detail_result.error or '无location'}")
        return False

    train_station_location = detail_result.location
    print(f"✅ 获取{train_station_name}坐标: {train_station_location}")

    train_station_driving_result = maps_driving_by_coordinates(origin=poi_location, destination=train_station_location)
    if train_station_driving_result.error:
        print(f"❌ 计算到{train_station_name}驾车路线失败: {train_station_driving_result.error}")
        return False

    if train_station_driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取到{train_station_name}驾车时长")
        return False

    train_station_driving_duration = train_station_driving_result.total_duration_seconds
    if train_station_driving_duration > max_train_station_driving_duration:
        print(f"❌ 到{train_station_name}驾车时长{train_station_driving_duration}秒，超过{max_train_station_driving_duration}秒（{max_train_station_driving_duration // 60}分钟）")
        return False
    print(f"✅ 到{train_station_name}驾车时长{train_station_driving_duration}秒，符合要求（<= {max_train_station_driving_duration}秒，即{max_train_station_driving_duration // 60}分钟）")

    # 步骤8: 途径点附近有洗衣店
    if not walking_result.steps or len(walking_result.steps) == 0:
        print(f"❌ 步行路线没有步骤信息")
        return False

    print(f"✅ 步行路线共有{len(walking_result.steps)}个步骤")

    # 检查每个途经点周围是否有洗衣店
    laundry_found = False
    for i, step in enumerate(walking_result.steps):
        waypoint_location = step.to_coordinates
        laundry_search_result = maps_around_search(
            location=waypoint_location,
            radius=str(laundry_search_radius),
            keywords=laundry_keywords
        )

        if laundry_search_result.error:
            continue

        if laundry_search_result.pois and len(laundry_search_result.pois) > 0:
            laundry_found = True
            print(f"✅ 在途经点{i+1}（坐标: {waypoint_location}）周围{laundry_search_radius}米内找到{len(laundry_search_result.pois)}个洗衣店")
            print(f"   示例洗衣店: {laundry_search_result.pois[0].name} (ID: {laundry_search_result.pois[0].id})")
            break

    if not laundry_found:
        print(f"❌ 所有途经点周围{laundry_search_radius}米内都没有找到洗衣店")
        return False

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 818.py 文件...\n")
    result = verify_poi(poi_id="B000A8UL4T")
    print(f"\n验证结果: {result}")

