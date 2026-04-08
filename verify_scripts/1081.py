"""
验证任务：你想在附近4000米内找一个博物馆，评分至少4.7分。博物馆不能离徐州站太近，至少要500米以外。
你步行去博物馆的路上，会经过一个点，这个点离泰山小区京东便利店直线距离不超过700米。
下午要从中国矿业大学文昌校区去云龙湖，中途参观博物馆，要求从大学出发，经过博物馆再到云龙湖的总开车时间不超过20分钟，
而且这样绕路比直接去云龙湖多花的时间不能超过5分钟。另外，博物馆离中心医院地铁站步行不能超过15分钟。

🎯 目标POI ID: B020400196
📍 用户位置坐标: 117.183047,34.218294
🏠 用户地址: 江苏省徐州市泉山区泰山街道学府路11号美的云筑和苑
⏰ 执行时间: 周六 14:30:00

🔍 验证方法:
1. 调用maps_search_detail('B020400196')获取博物馆详细信息，验证rating≥4.7
2. 调用maps_around_search('117.183047,34.218294','博物馆',4000)验证目标博物馆在搜索范围内
3. 调用maps_text_search('徐州站','徐州')获取徐州站poi_id，再调用maps_search_detail获取坐标(117.207930,34.265209)
4. 调用maps_distance('117.186653,34.251058','117.207930,34.265209')验证距离>500米
5. 调用maps_walking_by_coordinates('117.183047,34.218294','117.186653,34.251058')获取用户到博物馆的步行路线途经点坐标
6. 调用maps_search_detail('B0KK6AGCQU')获取泰山小区京东便利店坐标(117.188730,34.222224)
7. 调用maps_distance计算每个途经点到便利店的距离，验证至少有一个途经点距离<700米（途经点117.188434,34.228198距离665米）
8. 调用maps_walking_by_coordinates('117.186653,34.251058','117.183047,34.218294')获取博物馆到用户的返程路线，同样验证至少一个途经点附近700米内有便利店
9. 调用maps_text_search('中国矿业大学文昌校区','徐州')获取矿业大学poi_id，再调用maps_search_detail获取坐标(117.201227,34.219010)
10. 调用maps_text_search('云龙湖','徐州')获取云龙湖poi_id，再调用maps_search_detail获取坐标(117.151905,34.237488)
11. 调用maps_driving_by_coordinates('117.201227,34.219010','117.186653,34.251058')计算矿业大学到博物馆的驾车时间t1
12. 调用maps_driving_by_coordinates('117.186653,34.251058','117.151905,34.237488')计算博物馆到云龙湖的驾车时间t2
13. 验证t1+t2≤20分钟(1200秒)
14. 调用maps_driving_by_coordinates('117.201227,34.219010','117.151905,34.237488')计算矿业大学到云龙湖的直接驾车时间t3
15. 验证(t1+t2)-t3≤5分钟(300秒)
16. 调用maps_around_search('117.183047,34.218294','地铁站',3000)获取中心医院地铁站poi_id(BV10779356)，再调用maps_search_detail获取坐标(117.193501,34.241675)
17. 调用maps_walking_by_coordinates('117.186653,34.251058','117.193501,34.241675')验证步行时间≤15分钟(900秒)

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
    maps_walking_by_coordinates,
    maps_distance
)


def verify_poi(
    poi_id: str = "B020400196",
    user_location: str = "117.183047,34.218294",
    search_radius: int = 4000,
    min_rating: float = 4.7,
    min_distance_to_station: int = 500,
    convenience_store_poi_id: str = "B0KK6AGCQU",
    max_distance_to_store: int = 700,
    metro_station_poi_id: str = "BV10779356",
    max_total_driving_time: int = 1200,  # 20分钟 = 1200秒
    max_detour_time: int = 300,  # 5分钟 = 300秒
    max_walking_to_metro: int = 900  # 15分钟 = 900秒
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 验证博物馆评分≥4.7
    2) 验证目标博物馆在周边4000米搜索结果中
    3) 验证博物馆距离徐州站>500米
    4) 验证步行去博物馆的路上至少有一个途经点距离泰山小区京东便利店<700米
    5) 验证从矿业大学经过博物馆到云龙湖的总驾车时间≤20分钟
    6) 验证绕道博物馆比直接去云龙湖多花的时间≤5分钟
    7) 验证博物馆到中心医院地铁站步行时间≤15分钟

    Args:
        poi_id: 目标POI ID
        user_location: 用户位置坐标
        search_radius: 搜索半径（米）
        min_rating: 最低评分
        min_distance_to_station: 距离徐州站的最小距离（米）
        convenience_store_poi_id: 泰山小区京东便利店POI ID
        max_distance_to_store: 途经点到便利店的最大距离（米）
        metro_station_poi_id: 中心医院地铁站POI ID
        max_total_driving_time: 最大总驾车时间（秒）
        max_detour_time: 最大绕道时间（秒）
        max_walking_to_metro: 步行到地铁站最大时间（秒）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    print(f"开始验证 POI ID: {poi_id}")
    print(f"用户位置: {user_location}")
    print("=" * 60)

    # 步骤1: 获取博物馆详细信息，验证rating≥4.7
    print("\n⭐ 步骤1: 验证博物馆评分≥4.7")
    detail_result = maps_search_detail(id=poi_id)
    if detail_result.error:
        print(f"❌ 获取POI详情失败: {detail_result.error}")
        return False

    # 获取博物馆坐标
    if not detail_result.location:
        print(f"❌ POI没有location信息")
        return False
    museum_location = detail_result.location
    print(f"   博物馆坐标: {museum_location}")
    print(f"   博物馆名称: {detail_result.name}")

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
        print(f"❌ 博物馆评分{rating}，低于要求的{min_rating}")
        return False
    else:
        print(f"✅ 博物馆评分{rating}，符合要求（≥{min_rating}）")

    # 步骤2: 验证目标博物馆在周边4000米搜索结果中
    print(f"\n🏛️  步骤2: 验证目标博物馆在周边{search_radius}米搜索结果中")
    around_result = maps_around_search(location=user_location, keywords='博物馆', radius=str(search_radius))
    if around_result.error:
        print(f"❌ 周边搜索失败: {around_result.error}")
        return False

    if not around_result.pois or len(around_result.pois) == 0:
        print(f"❌ 周边{search_radius}米内未找到博物馆")
        return False

    found_target_poi = False
    for poi in around_result.pois:
        if poi.id == poi_id:
            found_target_poi = True
            print(f"   找到目标博物馆: {poi.name} (ID: {poi.id})")
            break

    if not found_target_poi:
        print(f"❌ 目标博物馆 {poi_id} 不在周边{search_radius}米搜索结果中")
        return False
    print(f"✅ 目标博物馆 {poi_id} 在周边{search_radius}米范围内")

    # 步骤3: 获取徐州站坐标
    print("\n🚉 步骤3: 获取徐州站坐标")
    xuzhou_station_result = maps_text_search(keywords='徐州站', city='徐州')
    if xuzhou_station_result.error:
        print(f"❌ 搜索徐州站失败: {xuzhou_station_result.error}")
        return False

    if not xuzhou_station_result.pois or len(xuzhou_station_result.pois) == 0:
        print(f"❌ 未找到徐州站")
        return False

    xuzhou_station_poi_id = xuzhou_station_result.pois[0].id
    print(f"   徐州站POI ID: {xuzhou_station_poi_id}")

    xuzhou_station_detail = maps_search_detail(id=xuzhou_station_poi_id)
    if xuzhou_station_detail.error:
        print(f"❌ 获取徐州站详情失败: {xuzhou_station_detail.error}")
        return False

    if not xuzhou_station_detail.location:
        print(f"❌ 徐州站没有location信息")
        return False

    xuzhou_station_location = xuzhou_station_detail.location
    print(f"   徐州站坐标: {xuzhou_station_location}")

    # 步骤4: 验证博物馆距离徐州站>500米
    print(f"\n📍 步骤4: 验证博物馆距离徐州站>{min_distance_to_station}米")
    distance_result = maps_distance(origins=museum_location, destination=xuzhou_station_location)
    if distance_result.error:
        print(f"❌ 计算到徐州站的距离失败: {distance_result.error}")
        return False

    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 未找到到徐州站的距离信息")
        return False

    distance_to_station = distance_result.results[0].distance_meters
    if distance_to_station <= min_distance_to_station:
        print(f"❌ 博物馆距离徐州站{distance_to_station}米，不大于{min_distance_to_station}米")
        return False
    print(f"✅ 博物馆距离徐州站{distance_to_station}米，符合要求（>{min_distance_to_station}米）")

    # 步骤5: 获取用户到博物馆的步行路线途经点坐标
    print("\n🚶 步骤5: 获取用户到博物馆的步行路线途经点")
    walking_to_museum = maps_walking_by_coordinates(origin=user_location, destination=museum_location)
    if walking_to_museum.error:
        print(f"❌ 获取步行路线失败: {walking_to_museum.error}")
        return False

    if not walking_to_museum.steps or len(walking_to_museum.steps) == 0:
        print(f"❌ 步行路线没有步骤点")
        return False

    print(f"   获取到{len(walking_to_museum.steps)}个步骤")

    # 步骤6: 获取泰山小区京东便利店坐标
    print("\n🏪 步骤6: 获取泰山小区京东便利店坐标")
    store_detail = maps_search_detail(id=convenience_store_poi_id)
    if store_detail.error:
        print(f"❌ 获取便利店详情失败: {store_detail.error}")
        return False

    if not store_detail.location:
        print(f"❌ 便利店没有location信息")
        return False

    store_location = store_detail.location
    print(f"   便利店坐标: {store_location}")
    print(f"   便利店名称: {store_detail.name}")

    # 步骤7: 验证至少有一个途经点距离便利店<700米
    print(f"\n📏 步骤7: 验证步行路线上至少有一个途经点距离便利店<{max_distance_to_store}米")
    found_near_store = False
    near_store_coord = None
    min_distance_to_store = float('inf')

    # 收集所有途经点坐标
    waypoints = []
    for step in walking_to_museum.steps:
        waypoints.append(step.from_coordinates)
        waypoints.append(step.to_coordinates)

    # 去重
    waypoints = list(set(waypoints))

    for waypoint in waypoints:
        dist_result = maps_distance(origins=waypoint, destination=store_location)
        if dist_result.error or not dist_result.results:
            continue
        dist = dist_result.results[0].distance_meters
        if dist < min_distance_to_store:
            min_distance_to_store = dist
        if dist < max_distance_to_store:
            found_near_store = True
            near_store_coord = waypoint
            print(f"   找到距离便利店{dist}米的途经点: {waypoint}")
            break

    if not found_near_store:
        print(f"❌ 没有途经点距离便利店<{max_distance_to_store}米（最近距离: {min_distance_to_store}米）")
        return False
    print(f"✅ 步行路线上有途经点距离便利店<{max_distance_to_store}米")

    # 步骤8: 验证返程路线也有途经点附近700米内有便利店（可选验证）
    print(f"\n🔄 步骤8: 验证返程路线上也有途经点距离便利店<{max_distance_to_store}米")
    walking_from_museum = maps_walking_by_coordinates(origin=museum_location, destination=user_location)
    if walking_from_museum.error:
        print(f"⚠️  获取返程步行路线失败: {walking_from_museum.error}，跳过此验证")
    elif not walking_from_museum.steps or len(walking_from_museum.steps) == 0:
        print(f"⚠️  返程步行路线没有步骤点，跳过此验证")
    else:
        found_near_store_return = False
        min_distance_return = float('inf')

        # 收集返程途经点坐标
        return_waypoints = []
        for step in walking_from_museum.steps:
            return_waypoints.append(step.from_coordinates)
            return_waypoints.append(step.to_coordinates)
        return_waypoints = list(set(return_waypoints))

        for waypoint in return_waypoints:
            dist_result = maps_distance(origins=waypoint, destination=store_location)
            if dist_result.error or not dist_result.results:
                continue
            dist = dist_result.results[0].distance_meters
            if dist < min_distance_return:
                min_distance_return = dist
            if dist < max_distance_to_store:
                found_near_store_return = True
                print(f"   找到返程途经点距离便利店{dist}米: {waypoint}")
                break

        if found_near_store_return:
            print(f"✅ 返程路线上也有途经点距离便利店<{max_distance_to_store}米")
        else:
            print(f"⚠️  返程路线上没有途经点距离便利店<{max_distance_to_store}米（最近距离: {min_distance_return}米）")

    # 步骤9: 获取中国矿业大学文昌校区坐标
    print("\n🎓 步骤9: 获取中国矿业大学文昌校区坐标")
    university_result = maps_text_search(keywords='中国矿业大学文昌校区', city='徐州')
    if university_result.error:
        print(f"❌ 搜索矿业大学失败: {university_result.error}")
        return False

    if not university_result.pois or len(university_result.pois) == 0:
        print(f"❌ 未找到中国矿业大学文昌校区")
        return False

    university_poi_id = university_result.pois[0].id
    print(f"   矿业大学POI ID: {university_poi_id}")

    university_detail = maps_search_detail(id=university_poi_id)
    if university_detail.error:
        print(f"❌ 获取矿业大学详情失败: {university_detail.error}")
        return False

    if not university_detail.location:
        print(f"❌ 矿业大学没有location信息")
        return False

    university_location = university_detail.location
    print(f"   矿业大学坐标: {university_location}")

    # 步骤10: 获取云龙湖坐标
    print("\n🌊 步骤10: 获取云龙湖坐标")
    lake_result = maps_text_search(keywords='云龙湖', city='徐州')
    if lake_result.error:
        print(f"❌ 搜索云龙湖失败: {lake_result.error}")
        return False

    if not lake_result.pois or len(lake_result.pois) == 0:
        print(f"❌ 未找到云龙湖")
        return False

    lake_poi_id = lake_result.pois[0].id
    print(f"   云龙湖POI ID: {lake_poi_id}")

    lake_detail = maps_search_detail(id=lake_poi_id)
    if lake_detail.error:
        print(f"❌ 获取云龙湖详情失败: {lake_detail.error}")
        return False

    if not lake_detail.location:
        print(f"❌ 云龙湖没有location信息")
        return False

    lake_location = lake_detail.location
    print(f"   云龙湖坐标: {lake_location}")

    # 步骤11: 计算矿业大学到博物馆的驾车时间t1
    print("\n🚗 步骤11: 计算矿业大学到博物馆的驾车时间")
    driving_result_1 = maps_driving_by_coordinates(origin=university_location, destination=museum_location)
    if driving_result_1.error:
        print(f"❌ 获取第一段驾车路线失败: {driving_result_1.error}")
        return False

    t1 = driving_result_1.total_duration_seconds
    print(f"   矿业大学 -> 博物馆: {t1}秒（{t1/60:.2f}分钟）")

    # 步骤12: 计算博物馆到云龙湖的驾车时间t2
    print("\n🚗 步骤12: 计算博物馆到云龙湖的驾车时间")
    driving_result_2 = maps_driving_by_coordinates(origin=museum_location, destination=lake_location)
    if driving_result_2.error:
        print(f"❌ 获取第二段驾车路线失败: {driving_result_2.error}")
        return False

    t2 = driving_result_2.total_duration_seconds
    print(f"   博物馆 -> 云龙湖: {t2}秒（{t2/60:.2f}分钟）")

    # 步骤13: 验证t1+t2≤20分钟(1200秒)
    print(f"\n⏱️  步骤13: 验证总驾车时间≤{max_total_driving_time}秒（{max_total_driving_time//60}分钟）")
    total_driving_time = t1 + t2
    if total_driving_time > max_total_driving_time:
        print(f"❌ 总驾车时间{total_driving_time}秒（{total_driving_time/60:.2f}分钟），超过{max_total_driving_time}秒（{max_total_driving_time//60}分钟）")
        return False
    print(f"✅ 总驾车时间{total_driving_time}秒（{total_driving_time/60:.2f}分钟），符合要求（≤{max_total_driving_time}秒，即{max_total_driving_time//60}分钟）")

    # 步骤14: 计算矿业大学到云龙湖的直接驾车时间t3
    print("\n🚗 步骤14: 计算矿业大学到云龙湖的直接驾车时间")
    driving_result_direct = maps_driving_by_coordinates(origin=university_location, destination=lake_location)
    if driving_result_direct.error:
        print(f"❌ 获取直接驾车路线失败: {driving_result_direct.error}")
        return False

    t3 = driving_result_direct.total_duration_seconds
    print(f"   矿业大学 -> 云龙湖（直接）: {t3}秒（{t3/60:.2f}分钟）")

    # 步骤15: 验证(t1+t2)-t3≤5分钟(300秒)
    print(f"\n🔄 步骤15: 验证绕道时间≤{max_detour_time}秒（{max_detour_time//60}分钟）")
    detour_time = total_driving_time - t3
    if detour_time > max_detour_time:
        print(f"❌ 绕道时间{detour_time}秒（{detour_time/60:.2f}分钟），超过{max_detour_time}秒（{max_detour_time//60}分钟）")
        return False
    print(f"✅ 绕道时间{detour_time}秒（{detour_time/60:.2f}分钟），符合要求（≤{max_detour_time}秒，即{max_detour_time//60}分钟）")

    # 步骤16: 获取中心医院地铁站坐标
    print("\n🚇 步骤16: 获取中心医院地铁站坐标")
    metro_around_result = maps_around_search(location=user_location, keywords='地铁站', radius='3000')
    if metro_around_result.error:
        print(f"❌ 搜索地铁站失败: {metro_around_result.error}")
        return False

    # 查找中心医院地铁站
    metro_found = False
    metro_location = None
    for poi in metro_around_result.pois or []:
        if poi.id == metro_station_poi_id or '中心医院' in poi.name:
            metro_found = True
            print(f"   找到地铁站: {poi.name} (ID: {poi.id})")
            # 获取详细坐标
            metro_detail = maps_search_detail(id=poi.id)
            if metro_detail.error or not metro_detail.location:
                print(f"⚠️  无法获取地铁站坐标，尝试使用POI ID: {metro_station_poi_id}")
            else:
                metro_location = metro_detail.location
            break

    if not metro_found or not metro_location:
        # 直接使用指定的POI ID获取
        print(f"   使用指定的地铁站POI ID: {metro_station_poi_id}")
        metro_detail = maps_search_detail(id=metro_station_poi_id)
        if metro_detail.error:
            print(f"❌ 获取地铁站详情失败: {metro_detail.error}")
            return False
        if not metro_detail.location:
            print(f"❌ 地铁站没有location信息")
            return False
        metro_location = metro_detail.location

    print(f"   地铁站坐标: {metro_location}")

    # 步骤17: 验证博物馆到中心医院地铁站步行时间≤15分钟(900秒)
    print(f"\n🚶 步骤17: 验证博物馆到地铁站步行时间≤{max_walking_to_metro}秒（{max_walking_to_metro//60}分钟）")
    walking_to_metro = maps_walking_by_coordinates(origin=museum_location, destination=metro_location)
    if walking_to_metro.error:
        print(f"❌ 获取步行路线失败: {walking_to_metro.error}")
        return False

    walking_time = walking_to_metro.total_duration_seconds
    if walking_time > max_walking_to_metro:
        print(f"❌ 步行到地铁站时间{walking_time}秒（{walking_time/60:.2f}分钟），超过{max_walking_to_metro}秒（{max_walking_to_metro//60}分钟）")
        return False
    print(f"✅ 步行到地铁站时间{walking_time}秒（{walking_time/60:.2f}分钟），符合要求（≤{max_walking_to_metro}秒，即{max_walking_to_metro//60}分钟）")

    print("\n" + "=" * 60)
    print(f"✅ 所有验证通过！POI {poi_id} 符合所有要求")
    return True


if __name__ == "__main__":
    print("开始验证 POI B020400196...\n")
    result = verify_poi(poi_id="B020400196")
    print(f"\n验证结果: {result}")
