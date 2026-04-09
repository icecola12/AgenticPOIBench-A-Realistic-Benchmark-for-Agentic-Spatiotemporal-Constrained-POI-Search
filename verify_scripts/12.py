"""
验证任务：你想在附近3000米以内找一家电竞馆，评分不低于4.3，人均消费不超过30元。
电竞馆不能在济宁火车站500米范围内。你有一个朋友从济宁市政府过来，你们计划先到电竞馆玩，然后朋友要去济宁火车站。
所以从市政府骑自行车到电竞馆，再从电竞馆到火车站的总时间不能超过40分钟，而且这样走比直接从市政府到火车站增加的时间不能超过15分钟。
另外，电竞馆到某个公交站的步行时间要在10分钟以内。

🎯 目标POI ID: B0JU59DEVD
📍 用户位置坐标: 116.56541,35.393637
🏠 用户地址: 山东省济宁市任城区南苑街道济安桥南路
⏰ 执行时间: 周六 15:30:00

🔍 验证方法:
1. 调用 maps_around_search('116.56541,35.393637', '电竞馆', 3000) 获取附近电竞馆列表
2. 对每个候选电竞馆调用 maps_search_detail 获取详情，筛选评分≥4.3 且 biz_ext.cost≤30 的 POI（目标 POI 评分为4.4，人均21元）
3. 调用 maps_distance('116.589865,35.406083', '116.600756,35.392521') 验证目标电竞馆到济宁站的直线距离＞500米（实际约1804米）
4. 调用 maps_text_search('济宁市政府', '济宁') 获取朋友出发地 poi_id
5. 调用 maps_search_detail 获取市政府坐标（116.587116,35.415117）
6. 调用 maps_bicycling_by_coordinates('116.587116,35.415117', '116.589865,35.406083') 计算市政府到电竞馆骑行时间 t1（约290秒）
7. 调用 maps_bicycling_by_coordinates('116.589865,35.406083', '116.600756,35.392521') 计算电竞馆到火车站骑行时间 t2（约571秒）
8. 验证 t1 + t2 ≤ 40分钟（实际约14.35分钟）
9. 调用 maps_bicycling_by_coordinates('116.587116,35.415117', '116.600756,35.392521') 计算直接骑行时间 t_direct（约650秒）
10. 验证 (t1 + t2) - t_direct ≤ 15分钟（实际约3.52分钟）
11. 调用 maps_around_search('116.589865,35.406083', '公交站', 500) 获取附近公交站列表
12. 对每个公交站调用 maps_walking_by_coordinates 计算电竞馆到该站的步行时间，验证至少有一个≤10分钟（如东大寺公交站约6.07分钟）

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
    maps_bicycling_by_coordinates,
    maps_walking_by_coordinates,
    maps_distance
)


def verify_poi(
    poi_id: str = "B0JU59DEVD",
    user_location: str = "116.56541,35.393637",
    search_radius: int = 3000,
    min_rating: float = 4.3,
    max_cost: float = 30,
    train_station_location: str = "116.600756,35.392521",  # 济宁火车站坐标
    min_distance_to_station: int = 500,  # 距离火车站最小距离（米）
    max_total_bicycling_time: int = 2400,  # 40分钟 = 2400秒
    max_detour_time: int = 900,  # 15分钟 = 900秒
    bus_station_search_radius: int = 500,  # 公交站搜索半径（米）
    max_walking_to_bus: int = 600  # 步行到公交站最大时间（秒），10分钟
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 验证目标电竞馆在周边3000米搜索结果中
    2) 验证电竞馆评分≥4.3 且人均消费≤30元
    3) 验证电竞馆距离济宁火车站>500米
    4) 验证从市政府骑行到电竞馆再到火车站的总时间≤40分钟
    5) 验证绕道电竞馆比直接去火车站多花的时间≤15分钟
    6) 验证电竞馆到某个公交站的步行时间≤10分钟

    Args:
        poi_id: 目标POI ID
        user_location: 用户位置坐标
        search_radius: 搜索半径（米）
        min_rating: 最低评分
        max_cost: 最高人均消费（元）
        train_station_location: 济宁火车站坐标
        min_distance_to_station: 距离火车站的最小距离（米）
        max_total_bicycling_time: 最大总骑行时间（秒）
        max_detour_time: 最大绕道时间（秒）
        bus_station_search_radius: 公交站搜索半径（米）
        max_walking_to_bus: 步行到公交站最大时间（秒）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    print(f"开始验证 POI ID: {poi_id}")
    print(f"用户位置: {user_location}")
    print("=" * 60)

    # 步骤1: 验证目标电竞馆在周边3000米搜索结果中
    print(f"\n🎮 步骤1: 验证目标电竞馆在周边{search_radius}米搜索结果中")
    around_result = maps_around_search(location=user_location, keywords='电竞馆', radius=str(search_radius))
    if around_result.error:
        print(f"❌ 周边搜索失败: {around_result.error}")
        return False

    if not around_result.pois or len(around_result.pois) == 0:
        print(f"❌ 周边{search_radius}米内未找到电竞馆")
        return False

    found_target_poi = False
    for poi in around_result.pois:
        if poi.id == poi_id:
            found_target_poi = True
            print(f"   找到目标电竞馆: {poi.name} (ID: {poi.id})")
            break

    if not found_target_poi:
        print(f"❌ 目标电竞馆 {poi_id} 不在周边{search_radius}米搜索结果中")
        return False
    print(f"✅ 目标电竞馆 {poi_id} 在周边{search_radius}米范围内")

    # 步骤2: 获取电竞馆详情，验证评分≥4.3 且人均消费≤30元
    print(f"\n⭐ 步骤2: 验证电竞馆评分≥{min_rating} 且人均消费≤{max_cost}元")
    detail_result = maps_search_detail(id=poi_id)
    if detail_result.error:
        print(f"❌ 获取POI详情失败: {detail_result.error}")
        return False

    # 获取电竞馆坐标
    if not detail_result.location:
        print(f"❌ POI没有location信息")
        return False
    esports_location = detail_result.location
    print(f"   电竞馆坐标: {esports_location}")
    print(f"   电竞馆名称: {detail_result.name}")

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
        print(f"❌ 电竞馆评分{rating}，低于要求的{min_rating}")
        return False
    else:
        print(f"✅ 电竞馆评分{rating}，符合要求（≥{min_rating}）")

    # 验证人均消费
    cost = None
    if detail_result.biz_ext and 'cost' in detail_result.biz_ext:
        try:
            cost = float(detail_result.biz_ext['cost'])
        except (ValueError, TypeError):
            pass

    if cost is None:
        print(f"⚠️  无法获取人均消费信息，跳过消费验证")
    elif cost > max_cost:
        print(f"❌ 电竞馆人均消费{cost}元，超过要求的{max_cost}元")
        return False
    else:
        print(f"✅ 电竞馆人均消费{cost}元，符合要求（≤{max_cost}元）")

    # 步骤3: 验证电竞馆距离济宁火车站>500米
    print(f"\n📍 步骤3: 验证电竞馆距离济宁火车站>{min_distance_to_station}米")
    distance_result = maps_distance(origins=esports_location, destination=train_station_location)
    if distance_result.error:
        print(f"❌ 计算到火车站的距离失败: {distance_result.error}")
        return False

    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 未找到到火车站的距离信息")
        return False

    distance_to_station = distance_result.results[0].distance_meters
    if distance_to_station <= min_distance_to_station:
        print(f"❌ 电竞馆距离火车站{distance_to_station}米，不大于{min_distance_to_station}米")
        return False
    print(f"✅ 电竞馆距离火车站{distance_to_station}米，符合要求（>{min_distance_to_station}米）")

    # 步骤4: 获取济宁市政府坐标
    print("\n🏛️  步骤4: 获取济宁市政府坐标")
    gov_result = maps_text_search(keywords='济宁市政府', city='济宁')
    if gov_result.error:
        print(f"❌ 搜索济宁市政府失败: {gov_result.error}")
        return False

    if not gov_result.pois or len(gov_result.pois) == 0:
        print(f"❌ 未找到济宁市政府")
        return False

    gov_poi_id = gov_result.pois[0].id
    print(f"   市政府POI ID: {gov_poi_id}")

    gov_detail = maps_search_detail(id=gov_poi_id)
    if gov_detail.error:
        print(f"❌ 获取市政府详情失败: {gov_detail.error}")
        return False

    if not gov_detail.location:
        print(f"❌ 市政府没有location信息")
        return False

    gov_location = gov_detail.location
    print(f"   市政府坐标: {gov_location}")

    # 步骤5: 计算市政府到电竞馆的骑行时间t1
    print("\n🚴 步骤5: 计算市政府到电竞馆的骑行时间")
    bicycling_result_1 = maps_bicycling_by_coordinates(origin=gov_location, destination=esports_location)
    if bicycling_result_1.error:
        print(f"❌ 获取第一段骑行路线失败: {bicycling_result_1.error}")
        return False

    t1 = bicycling_result_1.total_duration_seconds
    print(f"   市政府 -> 电竞馆: {t1}秒（{t1/60:.2f}分钟）")

    # 步骤6: 计算电竞馆到火车站的骑行时间t2
    print("\n🚴 步骤6: 计算电竞馆到火车站的骑行时间")
    bicycling_result_2 = maps_bicycling_by_coordinates(origin=esports_location, destination=train_station_location)
    if bicycling_result_2.error:
        print(f"❌ 获取第二段骑行路线失败: {bicycling_result_2.error}")
        return False

    t2 = bicycling_result_2.total_duration_seconds
    print(f"   电竞馆 -> 火车站: {t2}秒（{t2/60:.2f}分钟）")

    # 步骤7: 验证t1+t2≤40分钟(2400秒)
    print(f"\n⏱️  步骤7: 验证总骑行时间≤{max_total_bicycling_time}秒（{max_total_bicycling_time//60}分钟）")
    total_bicycling_time = t1 + t2
    if total_bicycling_time > max_total_bicycling_time:
        print(f"❌ 总骑行时间{total_bicycling_time}秒（{total_bicycling_time/60:.2f}分钟），超过{max_total_bicycling_time}秒（{max_total_bicycling_time//60}分钟）")
        return False
    print(f"✅ 总骑行时间{total_bicycling_time}秒（{total_bicycling_time/60:.2f}分钟），符合要求（≤{max_total_bicycling_time}秒，即{max_total_bicycling_time//60}分钟）")

    # 步骤8: 计算市政府到火车站的直接骑行时间t_direct
    print("\n🚴 步骤8: 计算市政府到火车站的直接骑行时间")
    bicycling_result_direct = maps_bicycling_by_coordinates(origin=gov_location, destination=train_station_location)
    if bicycling_result_direct.error:
        print(f"❌ 获取直接骑行路线失败: {bicycling_result_direct.error}")
        return False

    t_direct = bicycling_result_direct.total_duration_seconds
    print(f"   市政府 -> 火车站（直接）: {t_direct}秒（{t_direct/60:.2f}分钟）")

    # 步骤9: 验证(t1+t2)-t_direct≤15分钟(900秒)
    print(f"\n🔄 步骤9: 验证绕道时间≤{max_detour_time}秒（{max_detour_time//60}分钟）")
    detour_time = total_bicycling_time - t_direct
    if detour_time > max_detour_time:
        print(f"❌ 绕道时间{detour_time}秒（{detour_time/60:.2f}分钟），超过{max_detour_time}秒（{max_detour_time//60}分钟）")
        return False
    print(f"✅ 绕道时间{detour_time}秒（{detour_time/60:.2f}分钟），符合要求（≤{max_detour_time}秒，即{max_detour_time//60}分钟）")

    # 步骤10: 获取电竞馆附近500米内的公交站
    print(f"\n🚌 步骤10: 获取电竞馆附近{bus_station_search_radius}米内的公交站")
    bus_around_result = maps_around_search(location=esports_location, keywords='公交站', radius=str(bus_station_search_radius))
    if bus_around_result.error:
        print(f"❌ 搜索公交站失败: {bus_around_result.error}")
        return False

    if not bus_around_result.pois or len(bus_around_result.pois) == 0:
        print(f"❌ 电竞馆附近{bus_station_search_radius}米内未找到公交站")
        return False

    print(f"   找到{len(bus_around_result.pois)}个公交站")

    # 步骤11: 验证至少有一个公交站步行时间≤10分钟
    print(f"\n🚶 步骤11: 验证至少有一个公交站步行时间≤{max_walking_to_bus}秒（{max_walking_to_bus//60}分钟）")
    found_near_bus = False
    min_walking_time = float('inf')

    for bus_poi in bus_around_result.pois:
        # 获取公交站坐标
        if bus_poi.location:
            bus_location = bus_poi.location
        else:
            # 如果没有location，尝试获取详情
            bus_detail = maps_search_detail(id=bus_poi.id)
            if bus_detail.error or not bus_detail.location:
                continue
            bus_location = bus_detail.location

        # 计算步行时间
        walking_result = maps_walking_by_coordinates(origin=esports_location, destination=bus_location)
        if walking_result.error or walking_result.total_duration_seconds is None:
            continue

        walking_time = walking_result.total_duration_seconds
        if walking_time < min_walking_time:
            min_walking_time = walking_time

        if walking_time <= max_walking_to_bus:
            found_near_bus = True
            print(f"   找到公交站: {bus_poi.name}，步行时间{walking_time}秒（{walking_time/60:.2f}分钟）")
            break

    if not found_near_bus:
        print(f"❌ 没有公交站步行时间≤{max_walking_to_bus}秒（最短步行时间: {min_walking_time}秒）")
        return False
    print(f"✅ 电竞馆附近有公交站步行时间≤{max_walking_to_bus}秒（{max_walking_to_bus//60}分钟）")

    print("\n" + "=" * 60)
    print(f"✅ 所有验证通过！POI {poi_id} 符合所有要求")
    return True


if __name__ == "__main__":
    print("开始验证 POI B0JU59DEVD...\n")
    result = verify_poi(poi_id="B0JU59DEVD")
    print(f"\n验证结果: {result}")
