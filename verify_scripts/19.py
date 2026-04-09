"""
修改任务指令：你想在附近2000米内找一家餐厅，评分不低于4.5，人均消费不超过80元，并且能吃到毛血旺。
餐厅不能在宝鸡火车站500米范围内。你步行去餐厅的路上，要有一个地方离胜利桥南公交站直线距离不超过350米。
餐厅附近300米内得有一个公交站，走过去步行距离不超过350米。你打算从家走到餐厅，然后骑车去宝鸡市中心医院，
整个过程不超过30分钟。另外，你朋友从宝鸡火车站开车到餐厅的时间，和你步行到餐厅的时间差不能超过10分钟。

🎯 目标POI ID: B039500197
📍 用户位置坐标: 107.130999,34.354942
🏠 用户地址: 陕西省宝鸡市渭滨区神农镇宝鸡城市快速干线绿城·逸水苑小区南区

🔍 验证方法:
1. 调用 maps_search_detail('B039500197') 获取餐厅详细信息。
2. 验证 biz_ext.rating ≥ 4.5。
3. 验证 biz_ext.cost 字段存在且人均消费 ≤ 80元（实际为51元）。
4. 验证 tag 字段包含 '毛血旺'。
5. 调用 maps_around_search('107.130999,34.354942', '餐厅', 2000) 验证目标餐厅在搜索结果中。
6. 调用 maps_text_search('宝鸡火车站', '宝鸡') 获取火车站POI ID，再调用 maps_search_detail 获取坐标。
7. 调用 maps_distance('107.135470,34.359067', '107.152717,34.372500') 计算餐厅到火车站直线距离，验证 > 500米。
8. 调用 maps_walking_by_coordinates('107.130999,34.354942', '107.135470,34.359067') 获取步行路线，遍历每个步骤的 from_coordinates 和 to_coordinates，计算到胜利桥南公交站坐标 (107.135647,34.359701) 的直线距离，验证至少有一个点距离 < 350米。
9. 调用 maps_around_search('107.135470,34.359067', '公交站', 300) 获取餐厅附近300米内的公交站列表。
10. 对每个公交站坐标，调用 maps_walking_by_coordinates('107.135470,34.359067', '公交站坐标') 计算步行距离，验证至少有一个公交站步行距离 ≤ 350米。
11. 调用 maps_walking_by_coordinates('107.130999,34.354942', '107.135470,34.359067') 获取步行时间 t1（秒）。
12. 调用 maps_bicycling_by_coordinates('107.135470,34.359067', '107.111837,34.357240') 获取骑行时间 t2（秒）。
13. 验证 t1 + t2 ≤ 1800秒（30分钟）。
14. 调用 maps_driving_by_coordinates('107.152717,34.372500', '107.135470,34.359067') 获取驾车时间 t3（秒）。
15. 验证 |t3 - t1| < 600秒（10分钟）。
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
    maps_around_search,
    maps_search_detail,
    maps_text_search,
    maps_distance,
    maps_walking_by_coordinates,
    maps_bicycling_by_coordinates,
    maps_driving_by_coordinates
)


def verify_poi(
    poi_id: str = "B039500197",
    user_location: str = "107.130999,34.354942",
    search_radius: int = 2000,
    min_rating: float = 4.5,
    max_cost: int = 80,
    required_tag: str = "毛血旺",
    train_station_name: str = "宝鸡火车站",
    train_station_city: str = "宝鸡",
    min_distance_to_station: int = 500,  # 距离火车站最小距离（米）
    shengliqiaonan_bus_location: str = "107.135647,34.359701",  # 胜利桥南公交站坐标
    max_distance_to_shengliqiao: int = 350,  # 途经点距离胜利桥南公交站最大距离（米）
    bus_search_radius: int = 300,  # 公交站搜索半径（米）
    max_walking_distance_to_bus: int = 350,  # 到公交站最大步行距离（米）
    hospital_location: str = "107.111837,34.357240",  # 宝鸡市中心医院坐标
    max_total_time: int = 1800,  # 总时间最大值（秒），30分钟
    max_time_diff: int = 600  # 时间差最大值（秒），10分钟
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 验证餐厅评分≥4.5、人均消费≤80元、tag包含'毛血旺'
    2) 验证目标餐厅在周边2000米搜索结果中
    3) 验证餐厅距离宝鸡火车站>500米
    4) 验证步行途中有一个点距离胜利桥南公交站<350米
    5) 验证餐厅附近300米内有公交站，且步行距离≤350米
    6) 验证步行到餐厅+骑行到医院的总时间≤30分钟
    7) 验证朋友驾车到餐厅的时间与用户步行到餐厅的时间差≤10分钟

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    print(f"开始验证 POI ID: {poi_id}")
    print(f"用户位置: {user_location}")
    print("=" * 60)

    # 步骤1: 获取餐厅详情，验证评分、人均消费和标签
    print(f"\n⭐ 步骤1: 验证餐厅评分≥{min_rating}、人均消费≤{max_cost}元、tag包含'{required_tag}'")
    detail_result = maps_search_detail(id=poi_id)
    if detail_result.error:
        print(f"❌ 获取POI详情失败: {detail_result.error}")
        return False

    # 获取餐厅坐标
    if not detail_result.location:
        print(f"❌ POI没有location信息")
        return False
    restaurant_location = detail_result.location
    print(f"   餐厅坐标: {restaurant_location}")
    print(f"   餐厅名称: {detail_result.name}")

    # 验证评分
    rating = None
    if detail_result.biz_ext and 'rating' in detail_result.biz_ext:
        try:
            rating = float(detail_result.biz_ext['rating'])
        except (ValueError, TypeError):
            pass

    if rating is None:
        print(f"⚠️  无法获取评分信息，跳过评分验证")
    elif rating < min_rating:
        print(f"❌ 餐厅评分{rating}，低于要求的{min_rating}")
        return False
    else:
        print(f"✅ 餐厅评分{rating}，符合要求（≥{min_rating}）")

    # 验证人均消费
    cost = None
    if detail_result.biz_ext and 'cost' in detail_result.biz_ext:
        try:
            cost = float(detail_result.biz_ext['cost'])
        except (ValueError, TypeError):
            pass

    if cost is None:
        print(f"⚠️  无法获取人均消费信息，跳过人均消费验证")
    elif cost > max_cost:
        print(f"❌ 餐厅人均消费{cost}元，超过要求的{max_cost}元")
        return False
    else:
        print(f"✅ 餐厅人均消费{cost}元，符合要求（≤{max_cost}元）")

    # 验证标签包含'毛血旺'
    tag = None
    if detail_result.biz_ext and 'tag' in detail_result.biz_ext:
        tag = detail_result.biz_ext['tag']

    if tag is None:
        print(f"⚠️  无法获取标签信息，跳过标签验证")
    elif required_tag not in tag:
        print(f"❌ 餐厅标签'{tag}'不包含'{required_tag}'")
        return False
    else:
        print(f"✅ 餐厅标签'{tag}'包含'{required_tag}'")

    # 步骤2: 验证目标餐厅在周边2000米搜索结果中
    print(f"\n🍽️  步骤2: 验证目标餐厅在周边{search_radius}米搜索结果中")
    around_result = maps_around_search(location=user_location, keywords='餐厅', radius=str(search_radius))
    if around_result.error:
        print(f"❌ 周边搜索失败: {around_result.error}")
        return False

    if not around_result.pois or len(around_result.pois) == 0:
        print(f"❌ 周边{search_radius}米内未找到餐厅")
        return False

    found_target_poi = False
    for poi in around_result.pois:
        if poi.id == poi_id:
            found_target_poi = True
            print(f"   找到目标餐厅: {poi.name} (ID: {poi.id})")
            break

    if not found_target_poi:
        print(f"❌ 目标餐厅 {poi_id} 不在周边{search_radius}米搜索结果中")
        return False
    print(f"✅ 目标餐厅 {poi_id} 在周边{search_radius}米范围内")

    # 步骤3: 获取宝鸡火车站坐标，验证餐厅距离火车站>500米
    print(f"\n🚉 步骤3: 验证餐厅距离{train_station_name}>{min_distance_to_station}米")

    # 搜索火车站
    station_search = maps_text_search(keywords=train_station_name, city=train_station_city)
    if station_search.error:
        print(f"❌ 搜索{train_station_name}失败: {station_search.error}")
        return False
    if not station_search.pois or len(station_search.pois) == 0:
        print(f"❌ 未找到{train_station_name}")
        return False

    station_poi_id = station_search.pois[0].id
    print(f"   {train_station_name} POI ID: {station_poi_id}")

    # 获取火车站详情
    station_detail = maps_search_detail(id=station_poi_id)
    if station_detail.error:
        print(f"❌ 获取{train_station_name}详情失败: {station_detail.error}")
        return False
    if not station_detail.location:
        print(f"❌ {train_station_name}没有location信息")
        return False
    station_location = station_detail.location
    print(f"   {train_station_name}坐标: {station_location}")

    # 计算餐厅到火车站的距离
    distance_result = maps_distance(origins=restaurant_location, destination=station_location)
    if distance_result.error:
        print(f"❌ 计算到{train_station_name}的距离失败: {distance_result.error}")
        return False

    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 未找到到{train_station_name}的距离信息")
        return False

    distance_to_station = distance_result.results[0].distance_meters
    if distance_to_station <= min_distance_to_station:
        print(f"❌ 餐厅距离{train_station_name}{distance_to_station}米，不大于{min_distance_to_station}米")
        return False
    print(f"✅ 餐厅距离{train_station_name}{distance_to_station}米，符合要求（>{min_distance_to_station}米）")

    # 步骤4: 验证步行途中有一个点距离胜利桥南公交站<350米
    print(f"\n🚶 步骤4: 验证步行途中有一个点距离胜利桥南公交站<{max_distance_to_shengliqiao}米")
    walking_to_restaurant = maps_walking_by_coordinates(origin=user_location, destination=restaurant_location)
    if walking_to_restaurant.error:
        print(f"❌ 获取步行路线失败: {walking_to_restaurant.error}")
        return False

    if not walking_to_restaurant.steps or len(walking_to_restaurant.steps) == 0:
        print(f"❌ 未找到步行路线步骤")
        return False

    # 检查每个步骤的起点和终点坐标与胜利桥南公交站的距离
    found_close_point = False
    min_distance_found = float('inf')
    for step in walking_to_restaurant.steps:
        # 检查起点坐标
        from_distance_result = maps_distance(origins=step.from_coordinates, destination=shengliqiaonan_bus_location)
        if not from_distance_result.error and from_distance_result.results:
            from_distance = from_distance_result.results[0].distance_meters
            if from_distance < min_distance_found:
                min_distance_found = from_distance
            if from_distance < max_distance_to_shengliqiao:
                found_close_point = True
                print(f"   找到符合条件的点: 步骤起点{step.from_coordinates}距离胜利桥南公交站{from_distance}米")
                break

        # 检查终点坐标
        to_distance_result = maps_distance(origins=step.to_coordinates, destination=shengliqiaonan_bus_location)
        if not to_distance_result.error and to_distance_result.results:
            to_distance = to_distance_result.results[0].distance_meters
            if to_distance < min_distance_found:
                min_distance_found = to_distance
            if to_distance < max_distance_to_shengliqiao:
                found_close_point = True
                print(f"   找到符合条件的点: 步骤终点{step.to_coordinates}距离胜利桥南公交站{to_distance}米")
                break

    if not found_close_point:
        print(f"❌ 步行途中没有点距离胜利桥南公交站<{max_distance_to_shengliqiao}米（最近距离: {min_distance_found}米）")
        return False
    print(f"✅ 步行途中有点距离胜利桥南公交站<{max_distance_to_shengliqiao}米")

    # 步骤5: 验证餐厅附近300米内有公交站，且步行距离≤350米
    print(f"\n🚌 步骤5: 验证餐厅附近{bus_search_radius}米内有公交站，且步行距离≤{max_walking_distance_to_bus}米")
    bus_result = maps_around_search(location=restaurant_location, keywords='公交站', radius=str(bus_search_radius))
    if bus_result.error:
        print(f"❌ 搜索公交站失败: {bus_result.error}")
        return False
    if not bus_result.pois or len(bus_result.pois) == 0:
        print(f"❌ 餐厅附近{bus_search_radius}米内没有公交站")
        return False

    print(f"   找到{len(bus_result.pois)}个公交站")

    # 检查每个公交站的步行距离
    found_valid_bus = False
    for bus_poi in bus_result.pois:
        if not bus_poi.location:
            continue

        walking_to_bus = maps_walking_by_coordinates(origin=restaurant_location, destination=bus_poi.location)
        if walking_to_bus.error:
            continue

        walking_distance = walking_to_bus.total_distance_meters
        if walking_distance <= max_walking_distance_to_bus:
            found_valid_bus = True
            print(f"   找到符合条件的公交站: {bus_poi.name}，步行距离{walking_distance}米")
            break

    if not found_valid_bus:
        print(f"❌ 餐厅附近没有步行距离≤{max_walking_distance_to_bus}米的公交站")
        return False
    print(f"✅ 餐厅附近有公交站，步行距离≤{max_walking_distance_to_bus}米")

    # 步骤6: 验证步行到餐厅+骑行到医院的总时间≤30分钟
    print(f"\n⏱️  步骤6: 验证步行到餐厅+骑行到医院的总时间≤{max_total_time}秒（{max_total_time//60}分钟）")

    # 获取步行时间t1
    t1 = walking_to_restaurant.total_duration_seconds
    print(f"   用户 -> 餐厅步行时间t1: {t1}秒（{t1/60:.2f}分钟）")

    # 获取骑行时间t2
    bicycling_to_hospital = maps_bicycling_by_coordinates(origin=restaurant_location, destination=hospital_location)
    if bicycling_to_hospital.error:
        print(f"❌ 获取骑行路线失败: {bicycling_to_hospital.error}")
        return False
    t2 = bicycling_to_hospital.total_duration_seconds
    print(f"   餐厅 -> 医院骑行时间t2: {t2}秒（{t2/60:.2f}分钟）")

    total_time = t1 + t2
    if total_time > max_total_time:
        print(f"❌ 总时间{total_time}秒（{total_time/60:.2f}分钟），超过{max_total_time}秒（{max_total_time//60}分钟）")
        return False
    print(f"✅ 总时间{total_time}秒（{total_time/60:.2f}分钟），符合要求（≤{max_total_time}秒，即{max_total_time//60}分钟）")

    # 步骤7: 验证朋友驾车到餐厅的时间与用户步行到餐厅的时间差≤10分钟
    print(f"\n🚗 步骤7: 验证驾车时间与步行时间差≤{max_time_diff}秒（{max_time_diff//60}分钟）")

    # 获取朋友从火车站驾车到餐厅的时间t3
    driving_to_restaurant = maps_driving_by_coordinates(origin=station_location, destination=restaurant_location)
    if driving_to_restaurant.error:
        print(f"❌ 获取驾车路线失败: {driving_to_restaurant.error}")
        return False
    t3 = driving_to_restaurant.total_duration_seconds
    print(f"   火车站 -> 餐厅驾车时间t3: {t3}秒（{t3/60:.2f}分钟）")

    time_diff = abs(t3 - t1)
    print(f"   时间差|t3 - t1| = |{t3} - {t1}| = {time_diff}秒（{time_diff/60:.2f}分钟）")

    if time_diff > max_time_diff:
        print(f"❌ 时间差{time_diff}秒（{time_diff/60:.2f}分钟），超过{max_time_diff}秒（{max_time_diff//60}分钟）")
        return False
    print(f"✅ 时间差{time_diff}秒（{time_diff/60:.2f}分钟），符合要求（≤{max_time_diff}秒，即{max_time_diff//60}分钟）")

    print("\n" + "=" * 60)
    print(f"✅ 所有验证通过！POI {poi_id} 符合所有要求")
    return True


if __name__ == "__main__":
    print("开始验证 POI B039500197...\n")
    result = verify_poi(poi_id="B039500197")
    print(f"\n验证结果: {result}")
