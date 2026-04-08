"""
修改任务指令：你想在附近2000米以内找一家餐厅，评分至少4.7分，人均消费不超过80元。
这家餐厅不能在离西单地铁站500米的范围内。你从北京南站过来，要去天安门广场，
所以从北京南站到餐厅再到天安门广场的总驾车时间不能超过30分钟。
餐厅到甘石桥公交站的步行距离不能超过1000米。
另外，从你当前位置到餐厅的路线中，起点附近300米内要有银行。
最后，餐厅到灵境胡同地铁站的步行时间要在20分钟以内。

🎯 目标POI ID: B0FFJHY67L
📍 用户位置坐标: 116.372673,39.917582
🏠 用户地址: 北京市西城区金融街街道粉子胡同10号粉子胡同7号院

🔍 验证方法:
1. 调用maps_around_search('116.372673,39.917582', '餐厅', 2000)验证目标餐厅在搜索范围内
2. 调用maps_search_detail('B0FFJHY67L')获取详细信息，验证rating≥4.7，biz_ext.cost≤80元
3. 调用maps_search_detail('BV10006791')获取西单地铁站坐标
4. 调用maps_distance('116.375178,39.913936', '116.374276,39.907379')计算餐厅到西单地铁站直线距离，验证>500米
5. 调用maps_search_detail('B000A83AJN')获取北京南站坐标
6. 调用maps_search_detail('B000A83C1S')获取天安门广场坐标
7. 调用maps_driving_by_coordinates('116.378517,39.865246', '116.375178,39.913936')计算北京南站到餐厅驾车时间t1
8. 调用maps_driving_by_coordinates('116.375178,39.913936', '116.397755,39.903182')计算餐厅到天安门广场驾车时间t2
9. 验证t1+t2≤30分钟（1800秒）
10. 调用maps_search_detail('BV10006760')获取甘石桥公交站坐标
11. 调用maps_walking_by_coordinates('116.375178,39.913936', '116.373744,39.915486')计算餐厅到甘石桥公交站步行距离，验证≤1000米
12. 调用maps_around_search('116.372673,39.917582', '银行', 300)验证起点附近300米内有银行
13. 调用maps_search_detail('BV10008400')获取灵境胡同地铁站坐标
14. 调用maps_walking_by_coordinates('116.375178,39.913936', '116.373696,39.916055')计算餐厅到灵境胡同地铁站步行时间，验证≤20分钟（1200秒）
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
    poi_id: str = "B0FFJHY67L",
    user_location: str = "116.372673,39.917582",
    search_radius: int = 2000,
    min_rating: float = 4.7,
    max_cost: int = 80,
    xidan_metro_poi_id: str = "BV10006791",  # 西单地铁站POI ID
    min_distance_to_xidan: int = 500,  # 距离西单地铁站最小距离（米）
    beijing_south_poi_id: str = "B000A83AJN",  # 北京南站POI ID
    tiananmen_poi_id: str = "B000A83C1S",  # 天安门广场POI ID
    max_total_driving_time: int = 1800,  # 总驾车时间最大值（秒），30分钟
    ganshiqiao_bus_poi_id: str = "BV10006760",  # 甘石桥公交站POI ID
    max_walking_distance_to_ganshiqiao: int = 1000,  # 到甘石桥公交站最大步行距离（米）
    bank_search_radius: int = 300,  # 银行搜索半径（米）
    lingjing_metro_poi_id: str = "BV10008400",  # 灵境胡同地铁站POI ID
    max_walking_time_to_lingjing: int = 1200  # 到灵境胡同地铁站最大步行时间（秒），20分钟
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 验证目标餐厅在周边2000米搜索结果中
    2) 验证餐厅评分≥4.7、人均消费≤80元
    3) 验证餐厅距离西单地铁站>500米
    4) 验证从北京南站到餐厅再到天安门广场的总驾车时间≤30分钟
    5) 验证餐厅到甘石桥公交站的步行距离≤1000米
    6) 验证起点附近300米内有银行
    7) 验证餐厅到灵境胡同地铁站的步行时间≤20分钟

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

    # 步骤2: 获取餐厅详情，验证评分和人均消费
    print(f"\n⭐ 步骤2: 验证餐厅评分≥{min_rating}、人均消费≤{max_cost}元")
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

    # 步骤3: 获取西单地铁站坐标
    print(f"\n🚇 步骤3: 获取西单地铁站坐标")
    xidan_detail = maps_search_detail(id=xidan_metro_poi_id)
    if xidan_detail.error:
        print(f"❌ 获取西单地铁站详情失败: {xidan_detail.error}")
        return False
    if not xidan_detail.location:
        print(f"❌ 西单地铁站没有location信息")
        return False
    xidan_location = xidan_detail.location
    print(f"   西单地铁站坐标: {xidan_location}")

    # 步骤4: 验证餐厅距离西单地铁站>500米
    print(f"\n📏 步骤4: 验证餐厅距离西单地铁站>{min_distance_to_xidan}米")
    distance_result = maps_distance(origins=restaurant_location, destination=xidan_location)
    if distance_result.error:
        print(f"❌ 计算到西单地铁站的距离失败: {distance_result.error}")
        return False

    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 未找到到西单地铁站的距离信息")
        return False

    distance_to_xidan = distance_result.results[0].distance_meters
    if distance_to_xidan <= min_distance_to_xidan:
        print(f"❌ 餐厅距离西单地铁站{distance_to_xidan}米，不大于{min_distance_to_xidan}米")
        return False
    print(f"✅ 餐厅距离西单地铁站{distance_to_xidan}米，符合要求（>{min_distance_to_xidan}米）")

    # 步骤5: 获取北京南站坐标
    print(f"\n🚉 步骤5: 获取北京南站坐标")
    beijing_south_detail = maps_search_detail(id=beijing_south_poi_id)
    if beijing_south_detail.error:
        print(f"❌ 获取北京南站详情失败: {beijing_south_detail.error}")
        return False
    if not beijing_south_detail.location:
        print(f"❌ 北京南站没有location信息")
        return False
    beijing_south_location = beijing_south_detail.location
    print(f"   北京南站坐标: {beijing_south_location}")

    # 步骤6: 获取天安门广场坐标
    print(f"\n🏛️  步骤6: 获取天安门广场坐标")
    tiananmen_detail = maps_search_detail(id=tiananmen_poi_id)
    if tiananmen_detail.error:
        print(f"❌ 获取天安门广场详情失败: {tiananmen_detail.error}")
        return False
    if not tiananmen_detail.location:
        print(f"❌ 天安门广场没有location信息")
        return False
    tiananmen_location = tiananmen_detail.location
    print(f"   天安门广场坐标: {tiananmen_location}")

    # 步骤7: 计算北京南站到餐厅的驾车时间t1
    print(f"\n🚗 步骤7: 计算北京南站到餐厅的驾车时间")
    driving_result_1 = maps_driving_by_coordinates(origin=beijing_south_location, destination=restaurant_location)
    if driving_result_1.error:
        print(f"❌ 获取北京南站到餐厅驾车路线失败: {driving_result_1.error}")
        return False
    t1 = driving_result_1.total_duration_seconds
    print(f"   北京南站 -> 餐厅驾车时间: {t1}秒（{t1/60:.2f}分钟）")

    # 步骤8: 计算餐厅到天安门广场的驾车时间t2
    print(f"\n🚗 步骤8: 计算餐厅到天安门广场的驾车时间")
    driving_result_2 = maps_driving_by_coordinates(origin=restaurant_location, destination=tiananmen_location)
    if driving_result_2.error:
        print(f"❌ 获取餐厅到天安门广场驾车路线失败: {driving_result_2.error}")
        return False
    t2 = driving_result_2.total_duration_seconds
    print(f"   餐厅 -> 天安门广场驾车时间: {t2}秒（{t2/60:.2f}分钟）")

    # 步骤9: 验证t1+t2≤30分钟（1800秒）
    print(f"\n⏱️  步骤9: 验证总驾车时间≤{max_total_driving_time}秒（{max_total_driving_time//60}分钟）")
    total_driving_time = t1 + t2
    if total_driving_time > max_total_driving_time:
        print(f"❌ 总驾车时间{total_driving_time}秒（{total_driving_time/60:.2f}分钟），超过{max_total_driving_time}秒（{max_total_driving_time//60}分钟）")
        return False
    print(f"✅ 总驾车时间{total_driving_time}秒（{total_driving_time/60:.2f}分钟），符合要求（≤{max_total_driving_time}秒，即{max_total_driving_time//60}分钟）")

    # 步骤10: 获取甘石桥公交站坐标
    print(f"\n🚌 步骤10: 获取甘石桥公交站坐标")
    ganshiqiao_detail = maps_search_detail(id=ganshiqiao_bus_poi_id)
    if ganshiqiao_detail.error:
        print(f"❌ 获取甘石桥公交站详情失败: {ganshiqiao_detail.error}")
        return False
    if not ganshiqiao_detail.location:
        print(f"❌ 甘石桥公交站没有location信息")
        return False
    ganshiqiao_location = ganshiqiao_detail.location
    print(f"   甘石桥公交站坐标: {ganshiqiao_location}")

    # 步骤11: 验证餐厅到甘石桥公交站的步行距离≤1000米
    print(f"\n🚶 步骤11: 验证餐厅到甘石桥公交站步行距离≤{max_walking_distance_to_ganshiqiao}米")
    walking_to_ganshiqiao = maps_walking_by_coordinates(origin=restaurant_location, destination=ganshiqiao_location)
    if walking_to_ganshiqiao.error:
        print(f"❌ 获取步行路线失败: {walking_to_ganshiqiao.error}")
        return False
    walking_distance_to_ganshiqiao = walking_to_ganshiqiao.total_distance_meters
    if walking_distance_to_ganshiqiao > max_walking_distance_to_ganshiqiao:
        print(f"❌ 餐厅到甘石桥公交站步行距离{walking_distance_to_ganshiqiao}米，超过{max_walking_distance_to_ganshiqiao}米")
        return False
    print(f"✅ 餐厅到甘石桥公交站步行距离{walking_distance_to_ganshiqiao}米，符合要求（≤{max_walking_distance_to_ganshiqiao}米）")

    # 步骤12: 验证起点附近300米内有银行
    print(f"\n🏦 步骤12: 验证起点附近{bank_search_radius}米内有银行")
    bank_result = maps_around_search(location=user_location, keywords='银行', radius=str(bank_search_radius))
    if bank_result.error:
        print(f"❌ 搜索银行失败: {bank_result.error}")
        return False
    if not bank_result.pois or len(bank_result.pois) == 0:
        print(f"❌ 起点附近{bank_search_radius}米内没有银行")
        return False
    print(f"✅ 起点附近{bank_search_radius}米内有银行: {bank_result.pois[0].name}（共{len(bank_result.pois)}个）")

    # 步骤13: 获取灵境胡同地铁站坐标
    print(f"\n🚇 步骤13: 获取灵境胡同地铁站坐标")
    lingjing_detail = maps_search_detail(id=lingjing_metro_poi_id)
    if lingjing_detail.error:
        print(f"❌ 获取灵境胡同地铁站详情失败: {lingjing_detail.error}")
        return False
    if not lingjing_detail.location:
        print(f"❌ 灵境胡同地铁站没有location信息")
        return False
    lingjing_location = lingjing_detail.location
    print(f"   灵境胡同地铁站坐标: {lingjing_location}")

    # 步骤14: 验证餐厅到灵境胡同地铁站的步行时间≤20分钟（1200秒）
    print(f"\n🚶 步骤14: 验证餐厅到灵境胡同地铁站步行时间≤{max_walking_time_to_lingjing}秒（{max_walking_time_to_lingjing//60}分钟）")
    walking_to_lingjing = maps_walking_by_coordinates(origin=restaurant_location, destination=lingjing_location)
    if walking_to_lingjing.error:
        print(f"❌ 获取步行路线失败: {walking_to_lingjing.error}")
        return False
    walking_time_to_lingjing = walking_to_lingjing.total_duration_seconds
    if walking_time_to_lingjing > max_walking_time_to_lingjing:
        print(f"❌ 餐厅到灵境胡同地铁站步行时间{walking_time_to_lingjing}秒（{walking_time_to_lingjing/60:.2f}分钟），超过{max_walking_time_to_lingjing}秒（{max_walking_time_to_lingjing//60}分钟）")
        return False
    print(f"✅ 餐厅到灵境胡同地铁站步行时间{walking_time_to_lingjing}秒（{walking_time_to_lingjing/60:.2f}分钟），符合要求（≤{max_walking_time_to_lingjing}秒，即{max_walking_time_to_lingjing//60}分钟）")

    print("\n" + "=" * 60)
    print(f"✅ 所有验证通过！POI {poi_id} 符合所有要求")
    return True


if __name__ == "__main__":
    print("开始验证 POI B0FFJHY67L...\n")
    result = verify_poi(poi_id="B0FFJHY67L")
    print(f"\n验证结果: {result}")
