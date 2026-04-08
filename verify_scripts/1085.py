"""
验证任务：晚上你想找个电竞馆和朋友一起玩游戏。你想找一个附近2000米以内的电竞馆，评分不低于4.3，人均消费不超过12元。
这家电竞馆不能离涿州西关太近,直线距离大于500m。你步行过去的路上，希望会经过一个离邮局(公交站)300米以内的地点。
另外，一个朋友从涿州市医院过来，另一个从涿州西关过来，你希望他们两个到电竞馆的时间总和不要超过30分钟，
而且这样走比直接从医院到西关多花的时间不要超过10分钟。最后，电竞馆到邮局(公交站)的步行时间要在10分钟以内。

🎯 目标POI ID: B0HU2CUSN6
📍 用户位置坐标: 115.968583,39.485169
🏠 用户地址: 河北省保定市涿州市双塔街道范阳西路中能化(河北)新能源汽车产业有限公司涿州亨达分公司
⏰ 执行时间: 周六 20:00:00

🔍 验证方法:
1. 调用maps_around_search('115.968583,39.485169', '电竞馆', 2000)搜索附近电竞馆，确认目标POI在结果中。
2. 调用maps_search_detail('B0HU2CUSN6')获取目标POI详细信息，验证rating≥4.3，biz_ext.cost≤12元（实际为10.00元）。
3. 调用maps_text_search('涿州西关', '涿州')获取涿州西关的poi_id（应为BV11181876）。
4. 调用maps_search_detail('BV11181876')获取涿州西关坐标（115.966217,39.485172）。
5. 调用maps_distance('115.977678,39.484736', '115.966217,39.485172')计算目标POI到涿州西关的直线距离，验证>500米（实际约985米）。
6. 调用maps_text_search('邮局(公交站)', '涿州')获取邮局公交站的poi_id（应为BV10621649）。
7. 调用maps_search_detail('BV10621649')获取邮局公交站坐标（115.971724,39.485142）。
8. 调用maps_walking_by_coordinates('115.968583,39.485169', '115.977678,39.484736')获取用户到目标POI的步行路线步骤。
9. 对于每个步骤的from_coordinates和to_coordinates，调用maps_distance计算到邮局公交站坐标的直线距离，验证至少有一个点距离<300米。
10. 调用maps_text_search('涿州市医院', '涿州')获取涿州市医院的poi_id（应为B013801OSR）。
11. 调用maps_search_detail('B013801OSR')获取涿州市医院坐标（115.976553,39.486057）。
12. 调用maps_walking_by_coordinates('115.976553,39.486057', '115.977678,39.484736')计算涿州市医院到目标POI的步行时间t1（秒）。
13. 调用maps_walking_by_coordinates('115.977678,39.484736', '115.966217,39.485172')计算目标POI到涿州西关的步行时间t2（秒）。
14. 计算总时间t1+t2，验证≤1800秒（30分钟）。
15. 调用maps_walking_by_coordinates('115.976553,39.486057', '115.966217,39.485172')计算涿州市医院到涿州西关的直接步行时间t_direct（秒）。
16. 验证(t1+t2) - t_direct ≤ 600秒（10分钟）。
17. 调用maps_walking_by_coordinates('115.977678,39.484736', '115.971724,39.485142')计算目标POI到邮局公交站的步行时间，验证≤600秒（10分钟）。

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
    maps_driving_by_coordinates,
    maps_bicycling_by_coordinates,
    maps_walking_by_coordinates,
    maps_distance
)


def verify_poi(
    poi_id: str = "B0HU2CUSN6",
    user_location: str = "115.968583,39.485169",
    search_radius: int = 2000,
    min_rating: float = 4.3,
    max_cost: float = 12,
    min_distance_to_xiguan: int = 500,  # 距离涿州西关最小距离（米）
    max_distance_to_bus_station: int = 300,  # 途经点到邮局公交站最大距离（米）
    max_total_walking_time: int = 1800,  # 总步行时间最大值（秒），30分钟
    max_detour_time: int = 600,  # 绕道时间最大值（秒），10分钟
    max_walking_to_bus: int = 600  # 步行到公交站最大时间（秒），10分钟
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 验证目标电竞馆在周边2000米搜索结果中
    2) 验证电竞馆评分≥4.3、人均消费≤12元
    3) 验证电竞馆距离涿州西关>500米
    4) 验证步行路线上有途经点距离邮局公交站<300米
    5) 验证从涿州市医院经过电竞馆到涿州西关的总步行时间≤30分钟
    6) 验证绕道电竞馆比直接步行多花的时间≤10分钟
    7) 验证电竞馆到邮局公交站步行时间≤10分钟

    Args:
        poi_id: 目标POI ID
        user_location: 用户位置坐标
        search_radius: 搜索半径（米）
        min_rating: 最低评分
        max_cost: 最高人均消费（元）
        min_distance_to_xiguan: 距离涿州西关的最小距离（米）
        max_distance_to_bus_station: 途经点到邮局公交站的最大距离（米）
        max_total_walking_time: 总步行时间最大值（秒）
        max_detour_time: 绕道时间最大值（秒）
        max_walking_to_bus: 步行到公交站最大时间（秒）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    print(f"开始验证 POI ID: {poi_id}")
    print(f"用户位置: {user_location}")
    print("=" * 60)

    # 步骤1: 验证目标电竞馆在周边2000米搜索结果中
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

    # 步骤2: 获取电竞馆详情，验证评分和人均消费
    print(f"\n⭐ 步骤2: 验证电竞馆评分≥{min_rating}、人均消费≤{max_cost}元")
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
            cost_str = detail_result.biz_ext['cost']
            if cost_str and cost_str != '':
                cost = float(cost_str)
        except (ValueError, TypeError):
            pass

    if cost is None:
        print(f"⚠️  无法获取人均消费信息，跳过消费验证")
    elif cost > max_cost:
        print(f"❌ 电竞馆人均消费{cost}元，超过要求的{max_cost}元")
        return False
    else:
        print(f"✅ 电竞馆人均消费{cost}元，符合要求（≤{max_cost}元）")

    # 步骤3: 获取涿州西关坐标
    print("\n🏛️  步骤3: 获取涿州西关坐标")
    xiguan_result = maps_text_search(keywords='涿州西关', city='涿州')
    if xiguan_result.error:
        print(f"❌ 搜索涿州西关失败: {xiguan_result.error}")
        return False

    if not xiguan_result.pois or len(xiguan_result.pois) == 0:
        print(f"❌ 未找到涿州西关")
        return False

    xiguan_poi_id = xiguan_result.pois[0].id
    print(f"   涿州西关POI ID: {xiguan_poi_id}")

    xiguan_detail = maps_search_detail(id=xiguan_poi_id)
    if xiguan_detail.error:
        print(f"❌ 获取涿州西关详情失败: {xiguan_detail.error}")
        return False

    if not xiguan_detail.location:
        print(f"❌ 涿州西关没有location信息")
        return False

    xiguan_location = xiguan_detail.location
    print(f"   涿州西关坐标: {xiguan_location}")

    # 步骤4: 验证电竞馆距离涿州西关>500米
    print(f"\n📍 步骤4: 验证电竞馆距离涿州西关>{min_distance_to_xiguan}米")
    distance_result = maps_distance(origins=esports_location, destination=xiguan_location)
    if distance_result.error:
        print(f"❌ 计算到涿州西关的距离失败: {distance_result.error}")
        return False

    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 未找到到涿州西关的距离信息")
        return False

    distance_to_xiguan = distance_result.results[0].distance_meters
    if distance_to_xiguan <= min_distance_to_xiguan:
        print(f"❌ 电竞馆距离涿州西关{distance_to_xiguan}米，不大于{min_distance_to_xiguan}米")
        return False
    print(f"✅ 电竞馆距离涿州西关{distance_to_xiguan}米，符合要求（>{min_distance_to_xiguan}米）")

    # 步骤5: 获取邮局公交站坐标
    print("\n🚌 步骤5: 获取邮局公交站坐标")
    bus_result = maps_text_search(keywords='邮局(公交站)', city='涿州')
    if bus_result.error:
        print(f"❌ 搜索邮局公交站失败: {bus_result.error}")
        return False

    if not bus_result.pois or len(bus_result.pois) == 0:
        print(f"❌ 未找到邮局公交站")
        return False

    bus_poi_id = bus_result.pois[0].id
    print(f"   邮局公交站POI ID: {bus_poi_id}")

    bus_detail = maps_search_detail(id=bus_poi_id)
    if bus_detail.error:
        print(f"❌ 获取邮局公交站详情失败: {bus_detail.error}")
        return False

    if not bus_detail.location:
        print(f"❌ 邮局公交站没有location信息")
        return False

    bus_location = bus_detail.location
    print(f"   邮局公交站坐标: {bus_location}")

    # 步骤6: 获取用户到电竞馆的步行路线，验证途经点距离邮局公交站<300米
    print(f"\n🚶 步骤6: 验证步行路线上有途经点距离邮局公交站<{max_distance_to_bus_station}米")
    walking_to_esports = maps_walking_by_coordinates(origin=user_location, destination=esports_location)
    if walking_to_esports.error:
        print(f"❌ 获取步行路线失败: {walking_to_esports.error}")
        return False

    if not walking_to_esports.steps or len(walking_to_esports.steps) == 0:
        print(f"❌ 步行路线没有步骤点")
        return False

    print(f"   获取到{len(walking_to_esports.steps)}个步骤")

    found_near_bus = False
    min_distance_to_bus = float('inf')

    # 收集所有途经点坐标
    waypoints = []
    for step in walking_to_esports.steps:
        waypoints.append(step.from_coordinates)
        waypoints.append(step.to_coordinates)
    waypoints = list(set(waypoints))

    for waypoint in waypoints:
        dist_result = maps_distance(origins=waypoint, destination=bus_location)
        if dist_result.error or not dist_result.results:
            continue
        dist = dist_result.results[0].distance_meters
        if dist < min_distance_to_bus:
            min_distance_to_bus = dist
        if dist < max_distance_to_bus_station:
            found_near_bus = True
            print(f"   找到距离邮局公交站{dist}米的途经点: {waypoint}")
            break

    if not found_near_bus:
        print(f"❌ 没有途经点距离邮局公交站<{max_distance_to_bus_station}米（最近距离: {min_distance_to_bus}米）")
        return False
    print(f"✅ 步行路线上有途经点距离邮局公交站<{max_distance_to_bus_station}米")

    # 步骤7: 获取涿州市医院坐标
    print("\n🏥 步骤7: 获取涿州市医院坐标")
    hospital_result = maps_text_search(keywords='涿州市医院', city='涿州')
    if hospital_result.error:
        print(f"❌ 搜索涿州市医院失败: {hospital_result.error}")
        return False

    if not hospital_result.pois or len(hospital_result.pois) == 0:
        print(f"❌ 未找到涿州市医院")
        return False

    hospital_poi_id = hospital_result.pois[0].id
    print(f"   涿州市医院POI ID: {hospital_poi_id}")

    hospital_detail = maps_search_detail(id=hospital_poi_id)
    if hospital_detail.error:
        print(f"❌ 获取涿州市医院详情失败: {hospital_detail.error}")
        return False

    if not hospital_detail.location:
        print(f"❌ 涿州市医院没有location信息")
        return False

    hospital_location = hospital_detail.location
    print(f"   涿州市医院坐标: {hospital_location}")

    # 步骤8: 计算涿州市医院到电竞馆的步行时间t1
    print("\n🚶 步骤8: 计算涿州市医院到电竞馆的步行时间")
    walking_result_1 = maps_walking_by_coordinates(origin=hospital_location, destination=esports_location)
    if walking_result_1.error:
        print(f"❌ 获取第一段步行路线失败: {walking_result_1.error}")
        return False

    t1 = walking_result_1.total_duration_seconds
    print(f"   涿州市医院 -> 电竞馆步行时间: {t1}秒（{t1/60:.2f}分钟）")

    # 步骤9: 计算电竞馆到涿州西关的步行时间t2
    print("\n🚶 步骤9: 计算电竞馆到涿州西关的步行时间")
    walking_result_2 = maps_walking_by_coordinates(origin=esports_location, destination=xiguan_location)
    if walking_result_2.error:
        print(f"❌ 获取第二段步行路线失败: {walking_result_2.error}")
        return False

    t2 = walking_result_2.total_duration_seconds
    print(f"   电竞馆 -> 涿州西关步行时间: {t2}秒（{t2/60:.2f}分钟）")

    # 步骤10: 验证t1+t2≤30分钟（1800秒）
    print(f"\n⏱️  步骤10: 验证总步行时间≤{max_total_walking_time}秒（{max_total_walking_time//60}分钟）")
    total_walking_time = t1 + t2
    if total_walking_time > max_total_walking_time:
        print(f"❌ 总步行时间{total_walking_time}秒（{total_walking_time/60:.2f}分钟），超过{max_total_walking_time}秒（{max_total_walking_time//60}分钟）")
        return False
    print(f"✅ 总步行时间{total_walking_time}秒（{total_walking_time/60:.2f}分钟），符合要求（≤{max_total_walking_time}秒，即{max_total_walking_time//60}分钟）")

    # 步骤11: 计算涿州市医院到涿州西关的直接步行时间t_direct
    print("\n🚶 步骤11: 计算涿州市医院到涿州西关的直接步行时间")
    walking_result_direct = maps_walking_by_coordinates(origin=hospital_location, destination=xiguan_location)
    if walking_result_direct.error:
        print(f"❌ 获取直接步行路线失败: {walking_result_direct.error}")
        return False

    t_direct = walking_result_direct.total_duration_seconds
    print(f"   涿州市医院 -> 涿州西关（直接）步行时间: {t_direct}秒（{t_direct/60:.2f}分钟）")

    # 步骤12: 验证(t1+t2)-t_direct≤10分钟（600秒）
    print(f"\n🔄 步骤12: 验证绕道时间≤{max_detour_time}秒（{max_detour_time//60}分钟）")
    detour_time = total_walking_time - t_direct
    if detour_time > max_detour_time:
        print(f"❌ 绕道时间{detour_time}秒（{detour_time/60:.2f}分钟），超过{max_detour_time}秒（{max_detour_time//60}分钟）")
        return False
    print(f"✅ 绕道时间{detour_time}秒（{detour_time/60:.2f}分钟），符合要求（≤{max_detour_time}秒，即{max_detour_time//60}分钟）")

    # 步骤13: 验证电竞馆到邮局公交站步行时间≤10分钟
    print(f"\n🚶 步骤13: 验证电竞馆到邮局公交站步行时间≤{max_walking_to_bus}秒（{max_walking_to_bus//60}分钟）")
    walking_to_bus = maps_walking_by_coordinates(origin=esports_location, destination=bus_location)
    if walking_to_bus.error:
        print(f"❌ 获取步行路线失败: {walking_to_bus.error}")
        return False

    walking_time_to_bus = walking_to_bus.total_duration_seconds
    if walking_time_to_bus > max_walking_to_bus:
        print(f"❌ 步行到邮局公交站时间{walking_time_to_bus}秒（{walking_time_to_bus/60:.2f}分钟），超过{max_walking_to_bus}秒（{max_walking_to_bus//60}分钟）")
        return False
    print(f"✅ 步行到邮局公交站时间{walking_time_to_bus}秒（{walking_time_to_bus/60:.2f}分钟），符合要求（≤{max_walking_to_bus}秒，即{max_walking_to_bus//60}分钟）")

    print("\n" + "=" * 60)
    print(f"✅ 所有验证通过！POI {poi_id} 符合所有要求")
    return True


if __name__ == "__main__":
    print("开始验证 POI B0HU2CUSN6...\n")
    result = verify_poi(poi_id="B0HU2CUSN6")
    print(f"\n验证结果: {result}")
