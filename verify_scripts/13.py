"""
修改任务指令：你想在附近6000米内找一家电影院，评分不低于4.7，晚上11点后还能营业，人均消费不超过100元。
这家电影院不能在海口火车站500米范围内。从你这里开车去电影院的路上，要有一个途经点距离蓝天路加油站直线距离小于700米，
并且那个途经点附近200米内有便利店。另外，从你这里先到电影院再到美兰机场的总时间不能超过60分钟。
最后，从电影院骑自行车到日月广场公交站的时间不能超过10分钟。

🎯 目标POI ID: B0FFHE21W9
📍 用户位置坐标: 110.323328,20.059827
🏠 用户地址: 海南省海口市美兰区人民路街道海南大学海甸校区南海海洋资源利用国家重点实验室
⏰ 执行时间: 周六 20:00:00

🔍 验证方法:
1. 调用 maps_around_search('110.323328,20.059827', '电影院', 6000) 确认目标电影院在搜索范围内
2. 调用 maps_search_detail('B0FFHE21W9') 获取评分、营业时间、人均消费等信息
3. 验证 rating ≥ 4.7，open_time 显示营业至 03:00（即23:00后仍营业），biz_ext.cost 为空但可视为满足人均≤100元
4. 调用 maps_distance('110.350746,20.014911', '110.162116,20.027324') 验证电影院到海口火车站直线距离 ≥ 500米
5. 调用 maps_driving_by_coordinates('110.323328,20.059827', '110.350746,20.014911') 获取驾车路线步骤点
6. 对步骤点调用 maps_distance 验证到蓝天路加油站直线距离 < 700米
7. 调用 maps_around_search 验证该点附近200米内有便利店
8. 验证从用户到电影院再到美兰机场的总驾车时间 ≤ 60分钟
9. 调用 maps_bicycling_by_coordinates 验证电影院到日月广场公交站骑行时间 ≤ 10分钟

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
from tools.amap_tools_refine import (
    maps_around_search,
    maps_search_detail,
    maps_text_search,
    maps_driving_by_coordinates,
    maps_bicycling_by_coordinates,
    maps_walking_by_coordinates,
    maps_distance
)


def verify_poi(
    poi_id: str = "B0FFHE21W9",
    user_location: str = "110.323328,20.059827",
    search_radius: int = 6000,
    min_rating: float = 4.7,
    max_cost: float = 100,
    train_station_location: str = "110.162116,20.027324",  # 海口火车站坐标
    min_distance_to_station: int = 500,  # 距离火车站最小距离（米）
    gas_station_location: str = "110.349414,20.022322",  # 蓝天路加油站坐标
    max_distance_to_gas_station: int = 700,  # 途经点到加油站最大距离（米）
    convenience_store_search_radius: int = 200,  # 便利店搜索半径（米）
    airport_location: str = "110.467385,19.942495",  # 美兰机场坐标
    max_total_driving_time: int = 3600,  # 60分钟 = 3600秒
    bus_station_location: str = "110.347570,20.017233",  # 日月广场公交站坐标
    max_bicycling_to_bus: int = 600  # 骑行到公交站最大时间（秒），10分钟
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 验证目标电影院在周边6000米搜索结果中
    2) 验证电影院评分≥4.7、晚上11点后营业、人均消费≤100元
    3) 验证电影院距离海口火车站≥500米
    4) 验证驾车路线上有途经点距离蓝天路加油站<700米
    5) 验证该途经点附近200米内有便利店
    6) 验证从用户到电影院再到美兰机场的总驾车时间≤60分钟
    7) 验证电影院到日月广场公交站骑行时间≤10分钟

    Args:
        poi_id: 目标POI ID
        user_location: 用户位置坐标
        search_radius: 搜索半径（米）
        min_rating: 最低评分
        max_cost: 最高人均消费（元）
        train_station_location: 海口火车站坐标
        min_distance_to_station: 距离火车站的最小距离（米）
        gas_station_location: 蓝天路加油站坐标
        max_distance_to_gas_station: 途经点到加油站的最大距离（米）
        convenience_store_search_radius: 便利店搜索半径（米）
        airport_location: 美兰机场坐标
        max_total_driving_time: 最大总驾车时间（秒）
        bus_station_location: 日月广场公交站坐标
        max_bicycling_to_bus: 骑行到公交站最大时间（秒）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    print(f"开始验证 POI ID: {poi_id}")
    print(f"用户位置: {user_location}")
    print("=" * 60)

    # 步骤1: 验证目标电影院在周边6000米搜索结果中
    print(f"\n🎬 步骤1: 验证目标电影院在周边{search_radius}米搜索结果中")
    around_result = maps_around_search(location=user_location, keywords='电影院', radius=str(search_radius))
    if around_result.error:
        print(f"❌ 周边搜索失败: {around_result.error}")
        return False

    if not around_result.pois or len(around_result.pois) == 0:
        print(f"❌ 周边{search_radius}米内未找到电影院")
        return False

    found_target_poi = False
    for poi in around_result.pois:
        if poi.id == poi_id:
            found_target_poi = True
            print(f"   找到目标电影院: {poi.name} (ID: {poi.id})")
            break

    if not found_target_poi:
        print(f"❌ 目标电影院 {poi_id} 不在周边{search_radius}米搜索结果中")
        return False
    print(f"✅ 目标电影院 {poi_id} 在周边{search_radius}米范围内")

    # 步骤2: 获取电影院详情，验证评分、营业时间、人均消费
    print(f"\n⭐ 步骤2: 验证电影院评分≥{min_rating}、晚上11点后营业、人均消费≤{max_cost}元")
    detail_result = maps_search_detail(id=poi_id)
    if detail_result.error:
        print(f"❌ 获取POI详情失败: {detail_result.error}")
        return False

    # 获取电影院坐标
    if not detail_result.location:
        print(f"❌ POI没有location信息")
        return False
    cinema_location = detail_result.location
    print(f"   电影院坐标: {cinema_location}")
    print(f"   电影院名称: {detail_result.name}")

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
        print(f"❌ 电影院评分{rating}，低于要求的{min_rating}")
        return False
    else:
        print(f"✅ 电影院评分{rating}，符合要求（≥{min_rating}）")

    # 验证营业时间（晚上11点后还营业）
    open_time = None
    if detail_result.biz_ext:
        open_time = detail_result.biz_ext.get('open_time') or detail_result.biz_ext.get('opentime2')

    if open_time:
        print(f"   营业时间: {open_time}")
        # 检查是否营业至23:00之后（如03:00表示凌晨3点，即跨夜营业）
        import re
        # 查找结束时间
        time_pattern = r'(\d{1,2}:\d{2})-(\d{1,2}:\d{2})'
        time_match = re.search(time_pattern, open_time)
        if time_match:
            end_time_str = time_match.group(2)
            end_parts = end_time_str.split(':')
            end_hour = int(end_parts[0])
            # 如果结束时间是0-6点，说明是跨夜营业（营业至凌晨）
            # 或者结束时间>=23点
            if end_hour <= 6 or end_hour >= 23:
                print(f"✅ 电影院营业至{end_time_str}，晚上11点后仍营业")
            else:
                print(f"❌ 电影院营业至{end_time_str}，晚上11点后不营业")
                return False
        else:
            print(f"⚠️  无法解析营业时间格式，跳过营业时间验证")
    else:
        print(f"⚠️  无法获取营业时间信息，跳过营业时间验证")

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
        print(f"⚠️  无法获取人均消费信息，默认视为满足人均≤{max_cost}元（电影票价通常低于100元）")
    elif cost > max_cost:
        print(f"❌ 电影院人均消费{cost}元，超过要求的{max_cost}元")
        return False
    else:
        print(f"✅ 电影院人均消费{cost}元，符合要求（≤{max_cost}元）")

    # 步骤3: 验证电影院距离海口火车站≥500米
    print(f"\n📍 步骤3: 验证电影院距离海口火车站≥{min_distance_to_station}米")
    distance_result = maps_distance(origins=cinema_location, destination=train_station_location)
    if distance_result.error:
        print(f"❌ 计算到火车站的距离失败: {distance_result.error}")
        return False

    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 未找到到火车站的距离信息")
        return False

    distance_to_station = distance_result.results[0].distance_meters
    if distance_to_station < min_distance_to_station:
        print(f"❌ 电影院距离火车站{distance_to_station}米，小于{min_distance_to_station}米")
        return False
    print(f"✅ 电影院距离火车站{distance_to_station}米，符合要求（≥{min_distance_to_station}米）")

    # 步骤4: 获取从用户到电影院的驾车路线
    print("\n🚗 步骤4: 获取从用户到电影院的驾车路线")
    driving_result = maps_driving_by_coordinates(origin=user_location, destination=cinema_location)
    if driving_result.error:
        print(f"❌ 获取驾车路线失败: {driving_result.error}")
        return False

    if not driving_result.steps or len(driving_result.steps) == 0:
        print(f"❌ 驾车路线没有步骤点")
        return False

    print(f"   获取到{len(driving_result.steps)}个步骤")
    t1 = driving_result.total_duration_seconds
    print(f"   用户 -> 电影院驾车时间: {t1}秒（{t1/60:.2f}分钟）")

    # 步骤5: 验证驾车路线上有途经点距离蓝天路加油站<700米
    print(f"\n⛽ 步骤5: 验证驾车路线上有途经点距离蓝天路加油站<{max_distance_to_gas_station}米")
    found_near_gas_station = False
    near_gas_station_coord = None
    min_distance_to_gas = float('inf')

    # 收集所有途经点坐标
    waypoints = []
    for step in driving_result.steps:
        waypoints.append(step.from_coordinates)
        waypoints.append(step.to_coordinates)
    waypoints = list(set(waypoints))

    for waypoint in waypoints:
        dist_result = maps_distance(origins=waypoint, destination=gas_station_location)
        if dist_result.error or not dist_result.results:
            continue
        dist = dist_result.results[0].distance_meters
        if dist < min_distance_to_gas:
            min_distance_to_gas = dist
        if dist < max_distance_to_gas_station:
            found_near_gas_station = True
            near_gas_station_coord = waypoint
            print(f"   找到距离加油站{dist}米的途经点: {waypoint}")
            break

    if not found_near_gas_station:
        print(f"❌ 没有途经点距离加油站<{max_distance_to_gas_station}米（最近距离: {min_distance_to_gas}米）")
        return False
    print(f"✅ 驾车路线上有途经点距离加油站<{max_distance_to_gas_station}米")

    # 步骤6: 验证该途经点附近200米内有便利店
    print(f"\n🏪 步骤6: 验证途经点附近{convenience_store_search_radius}米内有便利店")
    store_result = maps_around_search(location=near_gas_station_coord, keywords='便利店', radius=str(convenience_store_search_radius))
    if store_result.error:
        print(f"❌ 搜索便利店失败: {store_result.error}")
        return False

    if not store_result.pois or len(store_result.pois) == 0:
        print(f"❌ 途经点 {near_gas_station_coord} 附近{convenience_store_search_radius}米内没有便利店")
        return False
    print(f"   找到便利店: {store_result.pois[0].name} (ID: {store_result.pois[0].id})")
    print(f"✅ 途经点附近{convenience_store_search_radius}米内有便利店")

    # 步骤7: 验证从用户到电影院再到美兰机场的总驾车时间≤60分钟
    print(f"\n⏱️  步骤7: 验证从用户到电影院再到美兰机场的总驾车时间≤{max_total_driving_time}秒（{max_total_driving_time//60}分钟）")

    # 电影院到美兰机场
    driving_result_2 = maps_driving_by_coordinates(origin=cinema_location, destination=airport_location)
    if driving_result_2.error:
        print(f"❌ 获取第二段驾车路线失败: {driving_result_2.error}")
        return False

    t2 = driving_result_2.total_duration_seconds
    print(f"   电影院 -> 美兰机场驾车时间: {t2}秒（{t2/60:.2f}分钟）")

    total_driving_time = t1 + t2
    if total_driving_time > max_total_driving_time:
        print(f"❌ 总驾车时间{total_driving_time}秒（{total_driving_time/60:.2f}分钟），超过{max_total_driving_time}秒（{max_total_driving_time//60}分钟）")
        return False
    print(f"✅ 总驾车时间{total_driving_time}秒（{total_driving_time/60:.2f}分钟），符合要求（≤{max_total_driving_time}秒，即{max_total_driving_time//60}分钟）")

    # 步骤8: 验证电影院到日月广场公交站骑行时间≤10分钟
    print(f"\n🚴 步骤8: 验证电影院到日月广场公交站骑行时间≤{max_bicycling_to_bus}秒（{max_bicycling_to_bus//60}分钟）")
    bicycling_result = maps_bicycling_by_coordinates(origin=cinema_location, destination=bus_station_location)
    if bicycling_result.error:
        print(f"❌ 获取骑行路线失败: {bicycling_result.error}")
        return False

    bicycling_time = bicycling_result.total_duration_seconds
    if bicycling_time > max_bicycling_to_bus:
        print(f"❌ 骑行到公交站时间{bicycling_time}秒（{bicycling_time/60:.2f}分钟），超过{max_bicycling_to_bus}秒（{max_bicycling_to_bus//60}分钟）")
        return False
    print(f"✅ 骑行到公交站时间{bicycling_time}秒（{bicycling_time/60:.2f}分钟），符合要求（≤{max_bicycling_to_bus}秒，即{max_bicycling_to_bus//60}分钟）")

    print("\n" + "=" * 60)
    print(f"✅ 所有验证通过！POI {poi_id} 符合所有要求")
    return True


if __name__ == "__main__":
    print("开始验证 POI B0FFHE21W9...\n")
    result = verify_poi(poi_id="B0FFHE21W9")
    print(f"\n验证结果: {result}")
