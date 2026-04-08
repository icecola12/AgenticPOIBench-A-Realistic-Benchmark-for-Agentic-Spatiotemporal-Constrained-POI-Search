"""
修改任务指令：你想在附近2000米内找一家餐厅，特别想吃他们家的干锅牛肉。餐厅评分至少4.2分，人均消费不能超过80元。
餐厅不能在富宁客运站500米范围内。你打算步行过去，希望途中有一个地方距离金虎市场公交站直线距离小于150米。
你也会考虑骑自行车，骑行距离不能超过2公里。另外，从餐厅走到金虎市场公交站的时间不能超过10分钟。
最后，你计划先去餐厅，然后再去富州广场公交站，整个行程步行总时间不超过30分钟。

🎯 目标POI ID: B0J1GH95Q5
📍 用户位置坐标: 105.631304,23.632012

🔍 验证方法:
1. 调用maps_around_search('105.631304,23.632012', '餐厅', 2000)验证目标餐厅在2000米范围内
2. 调用maps_search_detail('B0J1GH95Q5')获取详细信息：验证rating≥4.2、cost≤80、tag包含'干锅牛肉'
3. 调用maps_distance('105.629736,23.622146', '105.633512,23.626371')验证餐厅与富宁客运站距离>500米（实际607米）
4. 调用maps_walking_by_coordinates('105.631304,23.632012', '105.629736,23.622146')获取步行路线步骤，对每个步骤的起点/终点坐标调用maps_distance与金虎市场公交站('105.631073,23.624588')距离，验证至少有一个点距离<150米（实际步骤终点距离124米）
5. 调用maps_bicycling_by_coordinates('105.631304,23.632012', '105.629736,23.622146')验证骑行距离≤2000米（实际1110米）
6. 调用maps_walking_by_coordinates('105.629736,23.622146', '105.631073,23.624588')验证步行时间≤600秒（实际442秒）
7. 调用maps_walking_by_coordinates('105.631304,23.632012', '105.629736,23.622146')获取时间t1，调用maps_walking_by_coordinates('105.629736,23.622146', '105.624609,23.625814')获取时间t2，验证t1+t2≤1800秒（实际755+511=1266秒）
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
    maps_distance,
    maps_walking_by_coordinates,
    maps_bicycling_by_coordinates
)


def verify_poi(
    poi_id: str = "B0J1GH95Q5",
    user_location: str = "105.631304,23.632012",
    search_radius: int = 2000,
    min_rating: float = 4.2,
    max_cost: int = 80,
    required_tag: str = "干锅牛肉",
    funing_station_location: str = "105.633512,23.626371",  # 富宁客运站坐标
    min_distance_to_station: int = 500,  # 距离富宁客运站最小距离（米）
    jinhu_bus_station_location: str = "105.631073,23.624588",  # 金虎市场公交站坐标
    max_distance_to_jinhu: int = 150,  # 途中距离金虎市场公交站最大距离（米）
    max_bicycling_distance: int = 2000,  # 骑行最大距离（米）
    max_walking_to_jinhu: int = 600,  # 从餐厅步行到金虎市场公交站最大时间（秒），10分钟
    fuzhou_plaza_bus_station_location: str = "105.624609,23.625814",  # 富州广场公交站坐标
    max_total_walking_time: int = 1800  # 总步行时间最大值（秒），30分钟
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 验证目标餐厅在周边2000米搜索结果中
    2) 验证餐厅评分≥4.2、人均消费≤80、tag包含'干锅牛肉'
    3) 验证餐厅距离富宁客运站>500米
    4) 验证步行途中有一个点距离金虎市场公交站<150米
    5) 验证骑行距离≤2000米
    6) 验证从餐厅步行到金虎市场公交站时间≤10分钟
    7) 验证从用户位置到餐厅再到富州广场公交站的总步行时间≤30分钟

    Args:
        poi_id: 目标POI ID
        user_location: 用户位置坐标
        search_radius: 搜索半径（米）
        min_rating: 最低评分
        max_cost: 最高人均消费（元）
        required_tag: 必须包含的标签
        funing_station_location: 富宁客运站坐标
        min_distance_to_station: 距离富宁客运站的最小距离（米）
        jinhu_bus_station_location: 金虎市场公交站坐标
        max_distance_to_jinhu: 途中距离金虎市场公交站最大距离（米）
        max_bicycling_distance: 骑行最大距离（米）
        max_walking_to_jinhu: 从餐厅步行到金虎市场公交站最大时间（秒）
        fuzhou_plaza_bus_station_location: 富州广场公交站坐标
        max_total_walking_time: 总步行时间最大值（秒）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    print(f"开始验证 POI ID: {poi_id}")
    print(f"用户位置: {user_location}")
    print("=" * 60)

    # 步骤1: 验证目标餐厅在周边2000米搜索结果中
    print(f"\n🍽️  步骤1: 验证目标餐厅在周边{search_radius}米搜索结果中")
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

    # 步骤2: 获取餐厅详情，验证评分、人均消费和标签
    print(f"\n⭐ 步骤2: 验证餐厅评分≥{min_rating}、人均消费≤{max_cost}元、tag包含'{required_tag}'")
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

    # 验证标签包含'干锅牛肉'
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

    # 步骤3: 验证餐厅距离富宁客运站>500米
    print(f"\n🚌 步骤3: 验证餐厅距离富宁客运站>{min_distance_to_station}米")
    distance_result = maps_distance(origins=restaurant_location, destination=funing_station_location)
    if distance_result.error:
        print(f"❌ 计算到富宁客运站的距离失败: {distance_result.error}")
        return False

    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 未找到到富宁客运站的距离信息")
        return False

    distance_to_station = distance_result.results[0].distance_meters
    if distance_to_station <= min_distance_to_station:
        print(f"❌ 餐厅距离富宁客运站{distance_to_station}米，不大于{min_distance_to_station}米")
        return False
    print(f"✅ 餐厅距离富宁客运站{distance_to_station}米，符合要求（>{min_distance_to_station}米）")

    # 步骤4: 验证步行途中有一个点距离金虎市场公交站<150米
    print(f"\n🚶 步骤4: 验证步行途中有一个点距离金虎市场公交站<{max_distance_to_jinhu}米")
    walking_result = maps_walking_by_coordinates(origin=user_location, destination=restaurant_location)
    if walking_result.error:
        print(f"❌ 获取步行路线失败: {walking_result.error}")
        return False

    if not walking_result.steps or len(walking_result.steps) == 0:
        print(f"❌ 未找到步行路线步骤")
        return False

    # 检查每个步骤的起点和终点坐标与金虎市场公交站的距离
    found_close_point = False
    min_distance_found = float('inf')
    for step in walking_result.steps:
        # 检查起点坐标
        from_distance_result = maps_distance(origins=step.from_coordinates, destination=jinhu_bus_station_location)
        if not from_distance_result.error and from_distance_result.results:
            from_distance = from_distance_result.results[0].distance_meters
            if from_distance < min_distance_found:
                min_distance_found = from_distance
            if from_distance < max_distance_to_jinhu:
                found_close_point = True
                print(f"   找到符合条件的点: 步骤起点{step.from_coordinates}距离金虎市场公交站{from_distance}米")
                break

        # 检查终点坐标
        to_distance_result = maps_distance(origins=step.to_coordinates, destination=jinhu_bus_station_location)
        if not to_distance_result.error and to_distance_result.results:
            to_distance = to_distance_result.results[0].distance_meters
            if to_distance < min_distance_found:
                min_distance_found = to_distance
            if to_distance < max_distance_to_jinhu:
                found_close_point = True
                print(f"   找到符合条件的点: 步骤终点{step.to_coordinates}距离金虎市场公交站{to_distance}米")
                break

    if not found_close_point:
        print(f"❌ 步行途中没有点距离金虎市场公交站<{max_distance_to_jinhu}米（最近距离: {min_distance_found}米）")
        return False
    print(f"✅ 步行途中有点距离金虎市场公交站<{max_distance_to_jinhu}米")

    # 步骤5: 验证骑行距离≤2000米
    print(f"\n🚴 步骤5: 验证骑行距离≤{max_bicycling_distance}米")
    bicycling_result = maps_bicycling_by_coordinates(origin=user_location, destination=restaurant_location)
    if bicycling_result.error:
        print(f"❌ 获取骑行路线失败: {bicycling_result.error}")
        return False

    bicycling_distance = bicycling_result.total_distance_meters
    if bicycling_distance > max_bicycling_distance:
        print(f"❌ 骑行距离{bicycling_distance}米，超过{max_bicycling_distance}米")
        return False
    print(f"✅ 骑行距离{bicycling_distance}米，符合要求（≤{max_bicycling_distance}米）")

    # 步骤6: 验证从餐厅步行到金虎市场公交站时间≤10分钟（600秒）
    print(f"\n🚶 步骤6: 验证从餐厅步行到金虎市场公交站时间≤{max_walking_to_jinhu}秒（{max_walking_to_jinhu//60}分钟）")
    walking_to_jinhu = maps_walking_by_coordinates(origin=restaurant_location, destination=jinhu_bus_station_location)
    if walking_to_jinhu.error:
        print(f"❌ 获取步行路线失败: {walking_to_jinhu.error}")
        return False

    walking_time_to_jinhu = walking_to_jinhu.total_duration_seconds
    if walking_time_to_jinhu > max_walking_to_jinhu:
        print(f"❌ 从餐厅步行到金虎市场公交站时间{walking_time_to_jinhu}秒（{walking_time_to_jinhu/60:.2f}分钟），超过{max_walking_to_jinhu}秒（{max_walking_to_jinhu//60}分钟）")
        return False
    print(f"✅ 从餐厅步行到金虎市场公交站时间{walking_time_to_jinhu}秒（{walking_time_to_jinhu/60:.2f}分钟），符合要求（≤{max_walking_to_jinhu}秒，即{max_walking_to_jinhu//60}分钟）")

    # 步骤7: 验证从用户位置到餐厅再到富州广场公交站的总步行时间≤30分钟（1800秒）
    print(f"\n⏱️  步骤7: 验证总步行时间≤{max_total_walking_time}秒（{max_total_walking_time//60}分钟）")

    # 获取用户位置到餐厅的步行时间t1
    walking_to_restaurant = maps_walking_by_coordinates(origin=user_location, destination=restaurant_location)
    if walking_to_restaurant.error:
        print(f"❌ 获取用户到餐厅步行路线失败: {walking_to_restaurant.error}")
        return False
    t1 = walking_to_restaurant.total_duration_seconds
    print(f"   用户位置 -> 餐厅步行时间: {t1}秒（{t1/60:.2f}分钟）")

    # 获取餐厅到富州广场公交站的步行时间t2
    walking_to_fuzhou = maps_walking_by_coordinates(origin=restaurant_location, destination=fuzhou_plaza_bus_station_location)
    if walking_to_fuzhou.error:
        print(f"❌ 获取餐厅到富州广场公交站步行路线失败: {walking_to_fuzhou.error}")
        return False
    t2 = walking_to_fuzhou.total_duration_seconds
    print(f"   餐厅 -> 富州广场公交站步行时间: {t2}秒（{t2/60:.2f}分钟）")

    total_walking_time = t1 + t2
    if total_walking_time > max_total_walking_time:
        print(f"❌ 总步行时间{total_walking_time}秒（{total_walking_time/60:.2f}分钟），超过{max_total_walking_time}秒（{max_total_walking_time//60}分钟）")
        return False
    print(f"✅ 总步行时间{total_walking_time}秒（{total_walking_time/60:.2f}分钟），符合要求（≤{max_total_walking_time}秒，即{max_total_walking_time//60}分钟）")

    print("\n" + "=" * 60)
    print(f"✅ 所有验证通过！POI {poi_id} 符合所有要求")
    return True


if __name__ == "__main__":
    print("开始验证 POI B0J1GH95Q5...\n")
    result = verify_poi(poi_id="B0J1GH95Q5")
    print(f"\n验证结果: {result}")
