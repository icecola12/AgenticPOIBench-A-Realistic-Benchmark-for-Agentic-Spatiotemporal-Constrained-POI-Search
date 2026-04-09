"""
修改任务指令：你想在附近1500米内找一家餐厅，评分不低于4.7，人均消费不超过120元。
餐厅不能离赤峰火车站500米以内。你从家步行到餐厅的路上，需要经过一个离海贝尔游乐场公交站500米以内的点，
并且这个点附近500米内要有一个广场。餐厅到长安小区公交站的直线距离要小于300米，并且步行过去不超过10分钟。
另外，你朋友从赤峰玉龙机场开车过来，你们在餐厅会合后一起去赤峰博物馆，整个行程的开车时间不能超过50分钟，
而且比直接从机场到博物馆的时间最多只能多5分钟。

🎯 目标POI ID: B0H015NRX9
📍 用户位置坐标: 118.887055,42.263364
🏠 用户地址: 内蒙古自治区赤峰市松山区玉龙街道王府大街王府花园

🔍 验证方法:
1. 调用maps_search_detail('B0H015NRX9')获取餐厅详细信息，验证rating≥4.7，biz_ext.cost≤120元（实际为103元）
2. 调用maps_around_search('118.887055,42.263364','餐厅',1500)验证目标餐厅在搜索范围内
3. 调用maps_distance('118.886578,42.269402','118.901624,42.275612')验证餐厅到赤峰火车站直线距离>500米
4. 调用maps_walking_by_coordinates('118.887055,42.263364','118.886578,42.269402')获取步行路线步骤，检查每个步骤点的坐标，计算到海贝尔游乐场公交站(118.887553,42.267561)的直线距离，确认存在一个点距离<500米（如步骤点118.883237,42.265830距离404米）
5. 对上述步骤点调用maps_around_search('118.883237,42.265830','广场',500)验证附近存在广场（和谐广场，距离143米）
6. 调用maps_distance('118.886578,42.269402','118.884863,42.270313')验证餐厅到长安小区公交站直线距离<300米（实际173米）
7. 调用maps_walking_by_coordinates('118.886578,42.269402','118.884863,42.270313')验证步行时间≤10分钟（实际200秒，约3.33分钟）
8. 调用maps_driving_by_coordinates('118.846896,42.159804','118.886578,42.269402')获取机场到餐厅驾车时间t1（1252秒）
9. 调用maps_driving_by_coordinates('118.886578,42.269402','118.899671,42.247180')获取餐厅到博物馆驾车时间t2（278秒）
10. 计算总时间t1+t2=1530秒（25.5分钟），验证≤50分钟
11. 调用maps_driving_by_coordinates('118.846896,42.159804','118.899671,42.247180')获取机场到博物馆直接驾车时间t3（1461秒）
12. 验证(t1+t2)-t3=69秒（1.15分钟）≤5分钟
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
    maps_driving_by_coordinates
)


def verify_poi(
    poi_id: str = "B0H015NRX9",
    user_location: str = "118.887055,42.263364",
    search_radius: int = 1500,
    min_rating: float = 4.7,
    max_cost: int = 120,
    train_station_location: str = "118.901624,42.275612",  # 赤峰火车站坐标
    min_distance_to_station: int = 500,  # 距离火车站最小距离（米）
    haibei_bus_location: str = "118.887553,42.267561",  # 海贝尔游乐场公交站坐标
    max_distance_to_haibei: int = 500,  # 途经点距离海贝尔游乐场公交站最大距离（米）
    square_search_radius: int = 500,  # 广场搜索半径（米）
    changan_bus_location: str = "118.884863,42.270313",  # 长安小区公交站坐标
    max_distance_to_changan: int = 300,  # 餐厅到长安小区公交站最大直线距离（米）
    max_walking_time_to_changan: int = 600,  # 步行到长安小区公交站最大时间（秒），10分钟
    airport_location: str = "118.846896,42.159804",  # 赤峰玉龙机场坐标
    museum_location: str = "118.899671,42.247180",  # 赤峰博物馆坐标
    max_total_driving_time: int = 3000,  # 总驾车时间最大值（秒），50分钟
    max_detour_time: int = 300  # 绕道增加时间最大值（秒），5分钟
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 验证餐厅评分≥4.7、人均消费≤120元
    2) 验证目标餐厅在周边1500米搜索结果中
    3) 验证餐厅距离赤峰火车站>500米
    4) 验证步行途中有一个点距离海贝尔游乐场公交站<500米
    5) 验证该途经点附近500米内有广场
    6) 验证餐厅到长安小区公交站直线距离<300米
    7) 验证餐厅步行到长安小区公交站时间≤10分钟
    8) 验证机场到餐厅再到博物馆的总驾车时间≤50分钟
    9) 验证绕道时间≤5分钟

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    print(f"开始验证 POI ID: {poi_id}")
    print(f"用户位置: {user_location}")
    print("=" * 60)

    # 步骤1: 获取餐厅详情，验证评分和人均消费
    print(f"\n⭐ 步骤1: 验证餐厅评分≥{min_rating}、人均消费≤{max_cost}元")
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

    # 步骤2: 验证目标餐厅在周边1500米搜索结果中
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

    # 步骤3: 验证餐厅距离赤峰火车站>500米
    print(f"\n🚉 步骤3: 验证餐厅距离赤峰火车站>{min_distance_to_station}米")
    distance_result = maps_distance(origins=restaurant_location, destination=train_station_location)
    if distance_result.error:
        print(f"❌ 计算到赤峰火车站的距离失败: {distance_result.error}")
        return False

    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 未找到到赤峰火车站的距离信息")
        return False

    distance_to_station = distance_result.results[0].distance_meters
    if distance_to_station <= min_distance_to_station:
        print(f"❌ 餐厅距离赤峰火车站{distance_to_station}米，不大于{min_distance_to_station}米")
        return False
    print(f"✅ 餐厅距离赤峰火车站{distance_to_station}米，符合要求（>{min_distance_to_station}米）")

    # 步骤4: 验证步行途中有一个点距离海贝尔游乐场公交站<500米
    print(f"\n🚶 步骤4: 验证步行途中有一个点距离海贝尔游乐场公交站<{max_distance_to_haibei}米")
    walking_to_restaurant = maps_walking_by_coordinates(origin=user_location, destination=restaurant_location)
    if walking_to_restaurant.error:
        print(f"❌ 获取步行路线失败: {walking_to_restaurant.error}")
        return False

    if not walking_to_restaurant.steps or len(walking_to_restaurant.steps) == 0:
        print(f"❌ 未找到步行路线步骤")
        return False

    # 检查每个步骤的起点和终点坐标与海贝尔游乐场公交站的距离
    found_close_point = False
    close_point_location = None
    min_distance_found = float('inf')
    for step in walking_to_restaurant.steps:
        # 检查起点坐标
        from_distance_result = maps_distance(origins=step.from_coordinates, destination=haibei_bus_location)
        if not from_distance_result.error and from_distance_result.results:
            from_distance = from_distance_result.results[0].distance_meters
            if from_distance < min_distance_found:
                min_distance_found = from_distance
            if from_distance < max_distance_to_haibei:
                found_close_point = True
                close_point_location = step.from_coordinates
                print(f"   找到符合条件的点: 步骤起点{step.from_coordinates}距离海贝尔游乐场公交站{from_distance}米")
                break

        # 检查终点坐标
        to_distance_result = maps_distance(origins=step.to_coordinates, destination=haibei_bus_location)
        if not to_distance_result.error and to_distance_result.results:
            to_distance = to_distance_result.results[0].distance_meters
            if to_distance < min_distance_found:
                min_distance_found = to_distance
            if to_distance < max_distance_to_haibei:
                found_close_point = True
                close_point_location = step.to_coordinates
                print(f"   找到符合条件的点: 步骤终点{step.to_coordinates}距离海贝尔游乐场公交站{to_distance}米")
                break

    if not found_close_point:
        print(f"❌ 步行途中没有点距离海贝尔游乐场公交站<{max_distance_to_haibei}米（最近距离: {min_distance_found}米）")
        return False
    print(f"✅ 步行途中有点距离海贝尔游乐场公交站<{max_distance_to_haibei}米")

    # 步骤5: 验证该途经点附近500米内有广场
    print(f"\n🏛️  步骤5: 验证途经点附近{square_search_radius}米内有广场")
    square_result = maps_around_search(location=close_point_location, keywords='广场', radius=str(square_search_radius))
    if square_result.error:
        print(f"❌ 搜索广场失败: {square_result.error}")
        return False
    if not square_result.pois or len(square_result.pois) == 0:
        print(f"❌ 途经点附近{square_search_radius}米内没有广场")
        return False
    print(f"✅ 途经点附近{square_search_radius}米内有广场: {square_result.pois[0].name}（共{len(square_result.pois)}个）")

    # 步骤6: 验证餐厅到长安小区公交站直线距离<300米
    print(f"\n🚌 步骤6: 验证餐厅到长安小区公交站直线距离<{max_distance_to_changan}米")
    distance_to_changan = maps_distance(origins=restaurant_location, destination=changan_bus_location)
    if distance_to_changan.error:
        print(f"❌ 计算到长安小区公交站的距离失败: {distance_to_changan.error}")
        return False

    if not distance_to_changan.results or len(distance_to_changan.results) == 0:
        print(f"❌ 未找到到长安小区公交站的距离信息")
        return False

    changan_distance = distance_to_changan.results[0].distance_meters
    if changan_distance >= max_distance_to_changan:
        print(f"❌ 餐厅到长安小区公交站直线距离{changan_distance}米，不小于{max_distance_to_changan}米")
        return False
    print(f"✅ 餐厅到长安小区公交站直线距离{changan_distance}米，符合要求（<{max_distance_to_changan}米）")

    # 步骤7: 验证餐厅步行到长安小区公交站时间≤10分钟
    print(f"\n🚶 步骤7: 验证餐厅步行到长安小区公交站时间≤{max_walking_time_to_changan}秒（{max_walking_time_to_changan//60}分钟）")
    walking_to_changan = maps_walking_by_coordinates(origin=restaurant_location, destination=changan_bus_location)
    if walking_to_changan.error:
        print(f"❌ 获取步行路线失败: {walking_to_changan.error}")
        return False

    walking_time_to_changan = walking_to_changan.total_duration_seconds
    if walking_time_to_changan > max_walking_time_to_changan:
        print(f"❌ 餐厅步行到长安小区公交站时间{walking_time_to_changan}秒（{walking_time_to_changan/60:.2f}分钟），超过{max_walking_time_to_changan}秒（{max_walking_time_to_changan//60}分钟）")
        return False
    print(f"✅ 餐厅步行到长安小区公交站时间{walking_time_to_changan}秒（{walking_time_to_changan/60:.2f}分钟），符合要求（≤{max_walking_time_to_changan}秒，即{max_walking_time_to_changan//60}分钟）")

    # 步骤8: 计算机场到餐厅的驾车时间t1
    print(f"\n🚗 步骤8: 计算机场到餐厅的驾车时间")
    driving_to_restaurant = maps_driving_by_coordinates(origin=airport_location, destination=restaurant_location)
    if driving_to_restaurant.error:
        print(f"❌ 获取机场到餐厅驾车路线失败: {driving_to_restaurant.error}")
        return False
    t1 = driving_to_restaurant.total_duration_seconds
    print(f"   机场 -> 餐厅驾车时间t1: {t1}秒（{t1/60:.2f}分钟）")

    # 步骤9: 计算餐厅到博物馆的驾车时间t2
    print(f"\n🚗 步骤9: 计算餐厅到博物馆的驾车时间")
    driving_to_museum = maps_driving_by_coordinates(origin=restaurant_location, destination=museum_location)
    if driving_to_museum.error:
        print(f"❌ 获取餐厅到博物馆驾车路线失败: {driving_to_museum.error}")
        return False
    t2 = driving_to_museum.total_duration_seconds
    print(f"   餐厅 -> 博物馆驾车时间t2: {t2}秒（{t2/60:.2f}分钟）")

    # 步骤10: 验证总驾车时间≤50分钟
    print(f"\n⏱️  步骤10: 验证总驾车时间≤{max_total_driving_time}秒（{max_total_driving_time//60}分钟）")
    total_driving_time = t1 + t2
    if total_driving_time > max_total_driving_time:
        print(f"❌ 总驾车时间{total_driving_time}秒（{total_driving_time/60:.2f}分钟），超过{max_total_driving_time}秒（{max_total_driving_time//60}分钟）")
        return False
    print(f"✅ 总驾车时间{total_driving_time}秒（{total_driving_time/60:.2f}分钟），符合要求（≤{max_total_driving_time}秒，即{max_total_driving_time//60}分钟）")

    # 步骤11: 计算机场直接到博物馆的驾车时间t3
    print(f"\n🚗 步骤11: 计算机场直接到博物馆的驾车时间")
    driving_direct = maps_driving_by_coordinates(origin=airport_location, destination=museum_location)
    if driving_direct.error:
        print(f"❌ 获取机场直接到博物馆驾车路线失败: {driving_direct.error}")
        return False
    t3 = driving_direct.total_duration_seconds
    print(f"   机场 -> 博物馆直接驾车时间t3: {t3}秒（{t3/60:.2f}分钟）")

    # 步骤12: 验证绕道时间≤5分钟
    print(f"\n⏱️  步骤12: 验证绕道时间≤{max_detour_time}秒（{max_detour_time//60}分钟）")
    detour_time = total_driving_time - t3
    print(f"   绕道时间 = (t1+t2) - t3 = {total_driving_time} - {t3} = {detour_time}秒（{detour_time/60:.2f}分钟）")

    if detour_time > max_detour_time:
        print(f"❌ 绕道时间{detour_time}秒（{detour_time/60:.2f}分钟），超过{max_detour_time}秒（{max_detour_time//60}分钟）")
        return False
    print(f"✅ 绕道时间{detour_time}秒（{detour_time/60:.2f}分钟），符合要求（≤{max_detour_time}秒，即{max_detour_time//60}分钟）")

    print("\n" + "=" * 60)
    print(f"✅ 所有验证通过！POI {poi_id} 符合所有要求")
    return True


if __name__ == "__main__":
    print("开始验证 POI B0H015NRX9...\n")
    result = verify_poi(poi_id="B0H015NRX9")
    print(f"\n验证结果: {result}")
