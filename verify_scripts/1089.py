"""
修改任务指令：你想在附近1500米以内找一家餐厅，评分大于4.2，特色菜是羊蝎子火锅，人均消费不超过60元。
这家餐厅要离济宁市政府至少500米远。你开车去餐厅的路上，得有一个途经点距离中国农业银行金城支行不到400米。
然后你从餐厅骑行到济宁汽车总站不能超过15分钟。你从当前位置开车先去餐厅，然后再去济宁火车站，
整个行程时间不能超过15分钟，而且绕道去餐厅相比直接去火车站增加的时间不能超过5分钟。

🎯 目标POI ID: B0FFK4JXLQ
📍 用户位置坐标: 116.570179,35.413814
🏠 用户地址: 山东省济宁市任城区金城街道阳光花园东区

🔍 验证方法:
1. 调用maps_search_detail('B0FFK4JXLQ')获取餐厅详细信息，验证rating≥4.3（>4.2），tag字段包含'羊蝎子火锅'，biz_ext.cost字段中人均消费≤60元（实际44元）。
2. 调用maps_around_search('116.570179,35.413814','餐厅',1500)验证目标餐厅在1500米范围内。
3. 调用maps_distance计算餐厅与济宁市政府(116.587116,35.415117)的直线距离，验证>500米（实际1717米）。
4. 调用maps_driving_by_coordinates('116.570179,35.413814','116.568183,35.415222')获取驾车路线，提取所有途经点坐标（steps中的from_coordinates和to_coordinates），对每个途经点调用maps_distance计算其与中国农业银行金城支行(116.571709,35.415469)的直线距离，验证是否存在距离<400米的点（实际途经点116.572827,35.418524距离约354米）。
5. 调用maps_bicycling_by_coordinates('116.568183,35.415222','116.599175,35.397945')计算餐厅到济宁汽车总站的骑行时间，验证total_duration_seconds≤900秒（15分钟）（实际876秒）。
6. 调用maps_driving_by_coordinates('116.570179,35.413814','116.568183,35.415222')获取用户到餐厅驾车时间t1（实际185秒），调用maps_driving_by_coordinates('116.568183,35.415222','116.600756,35.392521')获取餐厅到火车站驾车时间t2（实际469秒），计算总行程时间T1 = t1 + t2，验证T1≤900秒（15分钟）（实际654秒）。
7. 调用maps_driving_by_coordinates('116.570179,35.413814','116.600756,35.392521')获取用户直接到火车站驾车时间T0（实际500秒），计算绕道增加时间ΔT = T1 - T0，验证ΔT≤300秒（5分钟）（实际154秒）。
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
    maps_driving_by_coordinates,
    maps_bicycling_by_coordinates
)


def verify_poi(
    poi_id: str = "B0FFK4JXLQ",
    user_location: str = "116.570179,35.413814",
    search_radius: int = 1500,
    min_rating: float = 4.2,
    max_cost: int = 60,
    required_tag: str = "羊蝎子火锅",
    jining_gov_location: str = "116.587116,35.415117",  # 济宁市政府坐标
    min_distance_to_gov: int = 500,  # 距离济宁市政府最小距离（米）
    abc_bank_location: str = "116.571709,35.415469",  # 中国农业银行金城支行坐标
    max_distance_to_bank: int = 400,  # 途经点距离银行最大距离（米）
    jining_bus_station_location: str = "116.599175,35.397945",  # 济宁汽车总站坐标
    max_bicycling_time_to_bus: int = 900,  # 骑行到汽车总站最大时间（秒），15分钟
    jining_train_station_location: str = "116.600756,35.392521",  # 济宁火车站坐标
    max_total_driving_time: int = 900,  # 总驾车时间最大值（秒），15分钟
    max_detour_time: int = 300  # 绕道增加时间最大值（秒），5分钟
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 验证餐厅评分>4.2、tag包含'羊蝎子火锅'、人均消费≤60元
    2) 验证目标餐厅在周边1500米搜索结果中
    3) 验证餐厅距离济宁市政府>500米
    4) 验证驾车途中有一个点距离中国农业银行金城支行<400米
    5) 验证餐厅骑行到济宁汽车总站时间≤15分钟
    6) 验证用户到餐厅再到火车站的总驾车时间≤15分钟
    7) 验证绕道去餐厅相比直接去火车站增加的时间≤5分钟

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    print(f"开始验证 POI ID: {poi_id}")
    print(f"用户位置: {user_location}")
    print("=" * 60)

    # 步骤1: 获取餐厅详情，验证评分、标签和人均消费
    print(f"\n⭐ 步骤1: 验证餐厅评分>{min_rating}、tag包含'{required_tag}'、人均消费≤{max_cost}元")
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
    elif rating <= min_rating:
        print(f"❌ 餐厅评分{rating}，不大于要求的{min_rating}")
        return False
    else:
        print(f"✅ 餐厅评分{rating}，符合要求（>{min_rating}）")

    # 验证标签包含'羊蝎子火锅'
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

    # 步骤3: 验证餐厅距离济宁市政府>500米
    print(f"\n🏛️  步骤3: 验证餐厅距离济宁市政府>{min_distance_to_gov}米")
    distance_result = maps_distance(origins=restaurant_location, destination=jining_gov_location)
    if distance_result.error:
        print(f"❌ 计算到济宁市政府的距离失败: {distance_result.error}")
        return False

    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 未找到到济宁市政府的距离信息")
        return False

    distance_to_gov = distance_result.results[0].distance_meters
    if distance_to_gov <= min_distance_to_gov:
        print(f"❌ 餐厅距离济宁市政府{distance_to_gov}米，不大于{min_distance_to_gov}米")
        return False
    print(f"✅ 餐厅距离济宁市政府{distance_to_gov}米，符合要求（>{min_distance_to_gov}米）")

    # 步骤4: 验证驾车途中有一个点距离中国农业银行金城支行<400米
    print(f"\n🚗 步骤4: 验证驾车途中有一个点距离中国农业银行金城支行<{max_distance_to_bank}米")
    driving_to_restaurant = maps_driving_by_coordinates(origin=user_location, destination=restaurant_location)
    if driving_to_restaurant.error:
        print(f"❌ 获取驾车路线失败: {driving_to_restaurant.error}")
        return False

    if not driving_to_restaurant.steps or len(driving_to_restaurant.steps) == 0:
        print(f"❌ 未找到驾车路线步骤")
        return False

    # 检查每个步骤的起点和终点坐标与银行的距离
    found_close_point = False
    min_distance_found = float('inf')
    for step in driving_to_restaurant.steps:
        # 检查起点坐标
        from_distance_result = maps_distance(origins=step.from_coordinates, destination=abc_bank_location)
        if not from_distance_result.error and from_distance_result.results:
            from_distance = from_distance_result.results[0].distance_meters
            if from_distance < min_distance_found:
                min_distance_found = from_distance
            if from_distance < max_distance_to_bank:
                found_close_point = True
                print(f"   找到符合条件的点: 步骤起点{step.from_coordinates}距离银行{from_distance}米")
                break

        # 检查终点坐标
        to_distance_result = maps_distance(origins=step.to_coordinates, destination=abc_bank_location)
        if not to_distance_result.error and to_distance_result.results:
            to_distance = to_distance_result.results[0].distance_meters
            if to_distance < min_distance_found:
                min_distance_found = to_distance
            if to_distance < max_distance_to_bank:
                found_close_point = True
                print(f"   找到符合条件的点: 步骤终点{step.to_coordinates}距离银行{to_distance}米")
                break

    if not found_close_point:
        print(f"❌ 驾车途中没有点距离中国农业银行金城支行<{max_distance_to_bank}米（最近距离: {min_distance_found}米）")
        return False
    print(f"✅ 驾车途中有点距离中国农业银行金城支行<{max_distance_to_bank}米")

    # 步骤5: 验证餐厅骑行到济宁汽车总站时间≤15分钟
    print(f"\n🚴 步骤5: 验证餐厅骑行到济宁汽车总站时间≤{max_bicycling_time_to_bus}秒（{max_bicycling_time_to_bus//60}分钟）")
    bicycling_to_bus = maps_bicycling_by_coordinates(origin=restaurant_location, destination=jining_bus_station_location)
    if bicycling_to_bus.error:
        print(f"❌ 获取骑行路线失败: {bicycling_to_bus.error}")
        return False

    bicycling_time_to_bus = bicycling_to_bus.total_duration_seconds
    if bicycling_time_to_bus > max_bicycling_time_to_bus:
        print(f"❌ 餐厅骑行到济宁汽车总站时间{bicycling_time_to_bus}秒（{bicycling_time_to_bus/60:.2f}分钟），超过{max_bicycling_time_to_bus}秒（{max_bicycling_time_to_bus//60}分钟）")
        return False
    print(f"✅ 餐厅骑行到济宁汽车总站时间{bicycling_time_to_bus}秒（{bicycling_time_to_bus/60:.2f}分钟），符合要求（≤{max_bicycling_time_to_bus}秒，即{max_bicycling_time_to_bus//60}分钟）")

    # 步骤6: 验证用户到餐厅再到火车站的总驾车时间≤15分钟
    print(f"\n🚗 步骤6: 验证总驾车时间≤{max_total_driving_time}秒（{max_total_driving_time//60}分钟）")

    # 获取用户到餐厅的驾车时间t1
    t1 = driving_to_restaurant.total_duration_seconds
    print(f"   用户 -> 餐厅驾车时间t1: {t1}秒（{t1/60:.2f}分钟）")

    # 获取餐厅到火车站的驾车时间t2
    driving_to_train = maps_driving_by_coordinates(origin=restaurant_location, destination=jining_train_station_location)
    if driving_to_train.error:
        print(f"❌ 获取餐厅到火车站驾车路线失败: {driving_to_train.error}")
        return False
    t2 = driving_to_train.total_duration_seconds
    print(f"   餐厅 -> 火车站驾车时间t2: {t2}秒（{t2/60:.2f}分钟）")

    T1 = t1 + t2
    if T1 > max_total_driving_time:
        print(f"❌ 总驾车时间T1={T1}秒（{T1/60:.2f}分钟），超过{max_total_driving_time}秒（{max_total_driving_time//60}分钟）")
        return False
    print(f"✅ 总驾车时间T1={T1}秒（{T1/60:.2f}分钟），符合要求（≤{max_total_driving_time}秒，即{max_total_driving_time//60}分钟）")

    # 步骤7: 验证绕道增加时间≤5分钟
    print(f"\n⏱️  步骤7: 验证绕道增加时间≤{max_detour_time}秒（{max_detour_time//60}分钟）")

    # 获取用户直接到火车站的驾车时间T0
    driving_direct = maps_driving_by_coordinates(origin=user_location, destination=jining_train_station_location)
    if driving_direct.error:
        print(f"❌ 获取用户直接到火车站驾车路线失败: {driving_direct.error}")
        return False
    T0 = driving_direct.total_duration_seconds
    print(f"   用户直接到火车站驾车时间T0: {T0}秒（{T0/60:.2f}分钟）")

    delta_T = T1 - T0
    print(f"   绕道增加时间ΔT = T1 - T0 = {T1} - {T0} = {delta_T}秒（{delta_T/60:.2f}分钟）")

    if delta_T > max_detour_time:
        print(f"❌ 绕道增加时间{delta_T}秒（{delta_T/60:.2f}分钟），超过{max_detour_time}秒（{max_detour_time//60}分钟）")
        return False
    print(f"✅ 绕道增加时间{delta_T}秒（{delta_T/60:.2f}分钟），符合要求（≤{max_detour_time}秒，即{max_detour_time//60}分钟）")

    print("\n" + "=" * 60)
    print(f"✅ 所有验证通过！POI {poi_id} 符合所有要求")
    return True


if __name__ == "__main__":
    print("开始验证 POI B0FFK4JXLQ...\n")
    result = verify_poi(poi_id="B0FFK4JXLQ")
    print(f"\n验证结果: {result}")
