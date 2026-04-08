"""
验证任务：你想在附近2500米以内找一家电影院，评分不低于4.7，人均消费不超过100元，而且要有IMAX巨幕体验。
电影院不能离阜阳师范大学直线距离500米以内。电影院附近300米内得有一个公交站。你朋友从阜阳火车站骑车到电影院的距离不能超过7公里。
另外，从阜阳师范大学经过电影院到阜阳火车站的总步行时间不能超过3个小时。

🎯 目标POI ID: B0FFHNT3YD
📍 用户位置坐标: 115.808658,32.881751
🏠 用户地址: 安徽省阜阳市颍州区清河街道颍淮大道537号民航小区
⏰ 执行时间: 周六 20:00:00

🔍 验证方法:
1. 调用maps_around_search('115.808658,32.881751', '电影院', 2500)验证目标电影院在2500米范围内
2. 调用maps_search_detail('B0FFHNT3YD')获取详细信息
3. 验证biz_ext.rating ≥ 4.7
4. 验证biz_ext.cost为空或人均消费 ≤ 100元
5. 验证biz_ext.open_time显示营业至22:00之后（实际周末营业至23:30）
6. 验证name字段包含'IMAX'字样
7. 调用maps_distance('115.822570,32.898625', '115.783816,32.890879')验证电影院到阜阳师范大学距离 > 500米
8. 调用maps_around_search('115.822570,32.898625', '公交站', 300)验证300米内存在公交站（东方恒隆公交站，距离81米）
9. 调用maps_bicycling_by_coordinates('115.868250,32.914512', '115.822570,32.898625')计算阜阳火车站到电影院的骑行距离，验证 ≤ 7000米（实际4628米）
10. 调用maps_walking_by_coordinates('115.783816,32.890879', '115.822570,32.898625')计算阜阳师范大学到电影院的步行时间t1
11. 调用maps_walking_by_coordinates('115.822570,32.898625', '115.868250,32.914512')计算电影院到阜阳火车站的步行时间t2
12. 验证t1 + t2 ≤ 180分钟（实际约133分钟）

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
    poi_id: str = "B0FFHNT3YD",
    user_location: str = "115.808658,32.881751",
    search_radius: int = 2500,
    min_rating: float = 4.7,
    max_cost: float = 100,
    university_location: str = "115.783816,32.890879",  # 阜阳师范大学坐标
    min_distance_to_university: int = 500,  # 距离大学最小距离（米）
    bus_station_search_radius: int = 300,  # 公交站搜索半径（米）
    train_station_location: str = "115.868250,32.914512",  # 阜阳火车站坐标
    max_bicycling_distance: int = 7000,  # 骑行到电影院最大距离（米），7公里
    max_total_walking_time: int = 10800  # 总步行时间最大值（秒），180分钟=3小时
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 验证目标电影院在周边2500米搜索结果中
    2) 验证电影院评分≥4.7、人均消费≤100元、营业至22:00之后
    3) 验证电影院名称包含'IMAX'
    4) 验证电影院距离阜阳师范大学>500米
    5) 验证电影院附近300米内有公交站
    6) 验证阜阳火车站骑行到电影院距离≤7公里
    7) 验证从阜阳师范大学经过电影院到阜阳火车站的总步行时间≤180分钟

    Args:
        poi_id: 目标POI ID
        user_location: 用户位置坐标
        search_radius: 搜索半径（米）
        min_rating: 最低评分
        max_cost: 最高人均消费（元）
        university_location: 阜阳师范大学坐标
        min_distance_to_university: 距离大学的最小距离（米）
        bus_station_search_radius: 公交站搜索半径（米）
        train_station_location: 阜阳火车站坐标
        max_bicycling_distance: 骑行到电影院最大距离（米）
        max_total_walking_time: 总步行时间最大值（秒）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    print(f"开始验证 POI ID: {poi_id}")
    print(f"用户位置: {user_location}")
    print("=" * 60)

    # 步骤1: 验证目标电影院在周边2500米搜索结果中
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

    # 步骤2: 获取电影院详情
    print(f"\n⭐ 步骤2: 获取电影院详细信息")
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

    # 步骤3: 验证评分≥4.7
    print(f"\n⭐ 步骤3: 验证电影院评分≥{min_rating}")
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

    # 步骤4: 验证人均消费≤100元
    print(f"\n💰 步骤4: 验证人均消费≤{max_cost}元")
    cost = None
    if detail_result.biz_ext and 'cost' in detail_result.biz_ext:
        try:
            cost_str = detail_result.biz_ext['cost']
            if cost_str and cost_str != '':
                cost = float(cost_str)
        except (ValueError, TypeError):
            pass

    if cost is None:
        print(f"⚠️  无法获取人均消费信息，默认视为满足人均≤{max_cost}元")
    elif cost > max_cost:
        print(f"❌ 电影院人均消费{cost}元，超过要求的{max_cost}元")
        return False
    else:
        print(f"✅ 电影院人均消费{cost}元，符合要求（≤{max_cost}元）")

    # 步骤5: 验证营业时间（营业至22:00之后）
    print(f"\n🕐 步骤5: 验证营业至22:00之后")
    open_time = None
    if detail_result.biz_ext:
        open_time = detail_result.biz_ext.get('open_time') or detail_result.biz_ext.get('opentime2')

    if open_time:
        print(f"   营业时间: {open_time}")
        import re
        time_pattern = r'(\d{1,2}:\d{2})-(\d{1,2}:\d{2})'
        time_match = re.search(time_pattern, open_time)
        if time_match:
            end_time_str = time_match.group(2)
            end_parts = end_time_str.split(':')
            end_hour = int(end_parts[0])
            # 如果结束时间是0-6点，说明是跨夜营业
            # 或者结束时间>=22点
            if end_hour <= 6 or end_hour >= 22:
                print(f"✅ 电影院营业至{end_time_str}，符合要求（22:00之后）")
            else:
                print(f"❌ 电影院营业至{end_time_str}，不符合要求（需营业至22:00之后）")
                return False
        else:
            print(f"⚠️  无法解析营业时间格式，跳过营业时间验证")
    else:
        print(f"⚠️  无法获取营业时间信息，跳过营业时间验证")

    # 步骤6: 验证名称包含'IMAX'
    print(f"\n🎥 步骤6: 验证电影院名称包含'IMAX'")
    cinema_name = detail_result.name or ""
    if 'IMAX' in cinema_name.upper():
        print(f"✅ 电影院名称'{cinema_name}'包含'IMAX'")
    else:
        print(f"❌ 电影院名称'{cinema_name}'不包含'IMAX'")
        return False

    # 步骤7: 验证电影院距离阜阳师范大学>500米
    print(f"\n📍 步骤7: 验证电影院距离阜阳师范大学>{min_distance_to_university}米")
    distance_result = maps_distance(origins=cinema_location, destination=university_location)
    if distance_result.error:
        print(f"❌ 计算到大学的距离失败: {distance_result.error}")
        return False

    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 未找到到大学的距离信息")
        return False

    distance_to_university = distance_result.results[0].distance_meters
    if distance_to_university <= min_distance_to_university:
        print(f"❌ 电影院距离阜阳师范大学{distance_to_university}米，不大于{min_distance_to_university}米")
        return False
    print(f"✅ 电影院距离阜阳师范大学{distance_to_university}米，符合要求（>{min_distance_to_university}米）")

    # 步骤8: 验证电影院附近300米内有公交站
    print(f"\n🚌 步骤8: 验证电影院附近{bus_station_search_radius}米内有公交站")
    bus_result = maps_around_search(location=cinema_location, keywords='公交站', radius=str(bus_station_search_radius))
    if bus_result.error:
        print(f"❌ 搜索公交站失败: {bus_result.error}")
        return False

    if not bus_result.pois or len(bus_result.pois) == 0:
        print(f"❌ 电影院附近{bus_station_search_radius}米内没有公交站")
        return False
    print(f"   找到公交站: {bus_result.pois[0].name} (ID: {bus_result.pois[0].id})")
    print(f"✅ 电影院附近{bus_station_search_radius}米内有公交站")

    # 步骤9: 验证阜阳火车站骑行到电影院距离≤7公里
    print(f"\n🚴 步骤9: 验证阜阳火车站骑行到电影院距离≤{max_bicycling_distance}米（{max_bicycling_distance/1000}公里）")
    bicycling_result = maps_bicycling_by_coordinates(origin=train_station_location, destination=cinema_location)
    if bicycling_result.error:
        print(f"❌ 获取骑行路线失败: {bicycling_result.error}")
        return False

    bicycling_distance = bicycling_result.total_distance_meters
    if bicycling_distance > max_bicycling_distance:
        print(f"❌ 骑行距离{bicycling_distance}米（{bicycling_distance/1000:.2f}公里），超过{max_bicycling_distance}米（{max_bicycling_distance/1000}公里）")
        return False
    print(f"✅ 骑行距离{bicycling_distance}米（{bicycling_distance/1000:.2f}公里），符合要求（≤{max_bicycling_distance}米，即{max_bicycling_distance/1000}公里）")

    # 步骤10: 计算阜阳师范大学到电影院的步行时间t1
    print(f"\n🚶 步骤10: 计算阜阳师范大学到电影院的步行时间")
    walking_result_1 = maps_walking_by_coordinates(origin=university_location, destination=cinema_location)
    if walking_result_1.error:
        print(f"❌ 获取第一段步行路线失败: {walking_result_1.error}")
        return False

    t1 = walking_result_1.total_duration_seconds
    print(f"   阜阳师范大学 -> 电影院步行时间: {t1}秒（{t1/60:.2f}分钟）")

    # 步骤11: 计算电影院到阜阳火车站的步行时间t2
    print(f"\n🚶 步骤11: 计算电影院到阜阳火车站的步行时间")
    walking_result_2 = maps_walking_by_coordinates(origin=cinema_location, destination=train_station_location)
    if walking_result_2.error:
        print(f"❌ 获取第二段步行路线失败: {walking_result_2.error}")
        return False

    t2 = walking_result_2.total_duration_seconds
    print(f"   电影院 -> 阜阳火车站步行时间: {t2}秒（{t2/60:.2f}分钟）")

    # 步骤12: 验证t1+t2≤180分钟（10800秒）
    print(f"\n⏱️  步骤12: 验证总步行时间≤{max_total_walking_time}秒（{max_total_walking_time//60}分钟，即{max_total_walking_time//3600}小时）")
    total_walking_time = t1 + t2
    if total_walking_time > max_total_walking_time:
        print(f"❌ 总步行时间{total_walking_time}秒（{total_walking_time/60:.2f}分钟），超过{max_total_walking_time}秒（{max_total_walking_time//60}分钟）")
        return False
    print(f"✅ 总步行时间{total_walking_time}秒（{total_walking_time/60:.2f}分钟），符合要求（≤{max_total_walking_time}秒，即{max_total_walking_time//60}分钟）")

    print("\n" + "=" * 60)
    print(f"✅ 所有验证通过！POI {poi_id} 符合所有要求")
    return True


if __name__ == "__main__":
    print("开始验证 POI B0FFHNT3YD...\n")
    result = verify_poi(poi_id="B0FFHNT3YD")
    print(f"\n验证结果: {result}")
