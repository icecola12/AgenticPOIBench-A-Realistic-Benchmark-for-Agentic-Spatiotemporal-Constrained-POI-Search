"""
修改任务指令：你想在附近2000米内找一家餐厅，人均消费不超过100元，评分不低于4.4分，并且晚上11点后仍然营业。
这家餐厅不能离车陂南地铁站太近（500米以内）。你打算从当前位置步行去餐厅，步行距离不能超过1500米。
然后你需要从餐厅去广州东站，整个行程（从当前位置经餐厅到广州东站）的总时间不能超过40分钟，
而且这样绕行所增加的时间相比直接去广州东站不能超过15分钟。

🎯 目标POI ID: B0LDCDMVQS
📍 用户位置坐标: 113.426642,23.122185
🏠 用户地址: 广东省广州市天河区珠吉街道珠村东环路110号111珠园大厦(珠村东环路)

🔍 验证方法:
1. 调用maps_around_search('113.426642,23.122185','餐厅',2000)验证目标餐厅在搜索范围内
2. 调用maps_search_detail('B0LDCDMVQS')获取详情，验证biz_ext.cost≤100元（实际94元）、rating≥4.4、open_time结束时间晚于23:00
3. 调用maps_search_detail('BV10014566')获取车陂南地铁站坐标，调用maps_distance计算餐厅到车陂南地铁站直线距离，验证>500米
4. 调用maps_walking_by_coordinates计算用户位置到餐厅的步行距离，验证≤1500米
5. 调用maps_driving_by_coordinates计算餐厅到广州东站的驾车时间t1
6. 调用maps_walking_by_coordinates计算用户位置到餐厅的步行时间t2
7. 计算总行程时间t1+t2，验证≤2400秒（40分钟）
8. 调用maps_driving_by_coordinates计算用户位置直接到广州东站的驾车时间t3
9. 验证(t1+t2)-t3≤900秒（15分钟）
"""

import os
import sys
import re

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
    poi_id: str = "B0LDCDMVQS",
    user_location: str = "113.426642,23.122185",
    search_radius: int = 2000,
    max_cost: int = 100,
    min_rating: float = 4.4,
    chebeinan_metro_poi_id: str = "BV10014566",  # 车陂南地铁站POI ID
    min_distance_to_metro: int = 500,  # 距离地铁站最小距离（米）
    max_walking_distance: int = 1500,  # 步行到餐厅最大距离（米）
    guangzhou_east_station_location: str = "113.324547,23.151434",  # 广州东站坐标（需要通过搜索获取）
    max_total_time: int = 2400,  # 总行程时间最大值（秒），40分钟
    max_detour_time: int = 900  # 绕道增加时间最大值（秒），15分钟
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 验证目标餐厅在周边2000米搜索结果中
    2) 验证餐厅人均消费≤100元、评分≥4.4、晚上11点后营业
    3) 验证餐厅距离车陂南地铁站>500米
    4) 验证步行到餐厅距离≤1500米
    5) 验证从当前位置经餐厅到广州东站的总时间≤40分钟
    6) 验证绕道时间≤15分钟

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

    # 步骤2: 获取餐厅详情，验证人均消费、评分和营业时间
    print(f"\n⭐ 步骤2: 验证餐厅人均消费≤{max_cost}元、评分≥{min_rating}、晚上11点后营业")
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

    # 验证营业时间（晚上11点后还营业）
    open_time = None
    if detail_result.biz_ext:
        open_time = detail_result.biz_ext.get('open_time') or detail_result.biz_ext.get('opentime2')

    if open_time:
        print(f"   营业时间: {open_time}")
        time_pattern = r'(\d{1,2}:\d{2})-(\d{1,2}:\d{2})'
        time_match = re.search(time_pattern, open_time)
        if time_match:
            end_time_str = time_match.group(2)
            end_parts = end_time_str.split(':')
            end_hour = int(end_parts[0])
            # 如果结束时间是0-6点，说明是跨夜营业（营业至凌晨）
            # 或者结束时间>=23点
            if end_hour <= 6 or end_hour >= 23:
                print(f"✅ 餐厅营业至{end_time_str}，晚上11点后仍营业")
            else:
                print(f"❌ 餐厅营业至{end_time_str}，晚上11点后不营业")
                return False
        else:
            print(f"⚠️  无法解析营业时间格式，跳过营业时间验证")
    else:
        print(f"⚠️  无法获取营业时间信息，跳过营业时间验证")

    # 步骤3: 获取车陂南地铁站坐标，验证餐厅距离地铁站>500米
    print(f"\n🚇 步骤3: 验证餐厅距离车陂南地铁站>{min_distance_to_metro}米")
    metro_detail = maps_search_detail(id=chebeinan_metro_poi_id)
    if metro_detail.error:
        print(f"❌ 获取车陂南地铁站详情失败: {metro_detail.error}")
        return False
    if not metro_detail.location:
        print(f"❌ 车陂南地铁站没有location信息")
        return False
    metro_location = metro_detail.location
    print(f"   车陂南地铁站坐标: {metro_location}")

    distance_result = maps_distance(origins=restaurant_location, destination=metro_location)
    if distance_result.error:
        print(f"❌ 计算到车陂南地铁站的距离失败: {distance_result.error}")
        return False

    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 未找到到车陂南地铁站的距离信息")
        return False

    distance_to_metro = distance_result.results[0].distance_meters
    if distance_to_metro <= min_distance_to_metro:
        print(f"❌ 餐厅距离车陂南地铁站{distance_to_metro}米，不大于{min_distance_to_metro}米")
        return False
    print(f"✅ 餐厅距离车陂南地铁站{distance_to_metro}米，符合要求（>{min_distance_to_metro}米）")

    # 步骤4: 验证步行到餐厅距离≤1500米
    print(f"\n🚶 步骤4: 验证步行到餐厅距离≤{max_walking_distance}米")
    walking_to_restaurant = maps_walking_by_coordinates(origin=user_location, destination=restaurant_location)
    if walking_to_restaurant.error:
        print(f"❌ 获取步行路线失败: {walking_to_restaurant.error}")
        return False

    walking_distance = walking_to_restaurant.total_distance_meters
    if walking_distance > max_walking_distance:
        print(f"❌ 步行到餐厅距离{walking_distance}米，超过{max_walking_distance}米")
        return False
    print(f"✅ 步行到餐厅距离{walking_distance}米，符合要求（≤{max_walking_distance}米）")

    # 获取步行时间t2
    t2 = walking_to_restaurant.total_duration_seconds
    print(f"   步行时间t2: {t2}秒（{t2/60:.2f}分钟）")

    # 步骤5: 计算餐厅到广州东站的驾车时间t1
    print(f"\n🚗 步骤5: 计算餐厅到广州东站的驾车时间")
    driving_to_station = maps_driving_by_coordinates(origin=restaurant_location, destination=guangzhou_east_station_location)
    if driving_to_station.error:
        print(f"❌ 获取餐厅到广州东站驾车路线失败: {driving_to_station.error}")
        return False
    t1 = driving_to_station.total_duration_seconds
    print(f"   餐厅 -> 广州东站驾车时间t1: {t1}秒（{t1/60:.2f}分钟）")

    # 步骤6: 验证总行程时间≤40分钟
    print(f"\n⏱️  步骤6: 验证总行程时间≤{max_total_time}秒（{max_total_time//60}分钟）")
    total_time = t1 + t2
    print(f"   总行程时间 = t1 + t2 = {t1} + {t2} = {total_time}秒（{total_time/60:.2f}分钟）")

    if total_time > max_total_time:
        print(f"❌ 总行程时间{total_time}秒（{total_time/60:.2f}分钟），超过{max_total_time}秒（{max_total_time//60}分钟）")
        return False
    print(f"✅ 总行程时间{total_time}秒（{total_time/60:.2f}分钟），符合要求（≤{max_total_time}秒，即{max_total_time//60}分钟）")

    # 步骤7: 计算用户位置直接到广州东站的驾车时间t3
    print(f"\n🚗 步骤7: 计算用户位置直接到广州东站的驾车时间")
    driving_direct = maps_driving_by_coordinates(origin=user_location, destination=guangzhou_east_station_location)
    if driving_direct.error:
        print(f"❌ 获取用户直接到广州东站驾车路线失败: {driving_direct.error}")
        return False
    t3 = driving_direct.total_duration_seconds
    print(f"   用户 -> 广州东站直接驾车时间t3: {t3}秒（{t3/60:.2f}分钟）")

    # 步骤8: 验证绕道时间≤15分钟
    print(f"\n⏱️  步骤8: 验证绕道时间≤{max_detour_time}秒（{max_detour_time//60}分钟）")
    detour_time = total_time - t3
    print(f"   绕道时间 = (t1+t2) - t3 = {total_time} - {t3} = {detour_time}秒（{detour_time/60:.2f}分钟）")

    if detour_time > max_detour_time:
        print(f"❌ 绕道时间{detour_time}秒（{detour_time/60:.2f}分钟），超过{max_detour_time}秒（{max_detour_time//60}分钟）")
        return False
    print(f"✅ 绕道时间{detour_time}秒（{detour_time/60:.2f}分钟），符合要求（≤{max_detour_time}秒，即{max_detour_time//60}分钟）")

    print("\n" + "=" * 60)
    print(f"✅ 所有验证通过！POI {poi_id} 符合所有要求")
    return True


if __name__ == "__main__":
    print("开始验证 POI B0LDCDMVQS...\n")
    result = verify_poi(poi_id="B0LDCDMVQS")
    print(f"\n验证结果: {result}")
