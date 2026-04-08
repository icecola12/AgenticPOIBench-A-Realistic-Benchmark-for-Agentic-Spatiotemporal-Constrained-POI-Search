
"""
修改任务指令：你要找一个附近2公里的酒店式公寓。你打算骑共享单车过去，所以骑行路线距离不能超过2公里。到了之后你还要马上去坐公交，要求从这家公寓步行到附近1km最近的公交站不要超过7分钟。另外这家公寓的评分要不低于4.3分。你思路混乱，可能会混淆信息，让对话难以跟进。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 距离约束（2公里内）：调用 maps_around_search(location=用户位置114.437474,23.117444, radius=2000, keywords=酒店)，验证返回pois中包含 target_poi_id=B0FFMH3226。
2) 骑行距离约束（<=2公里）：调用 maps_search_detail(id=B0FFMH3226) 获取目标location；再调用 maps_bicycling_by_coordinates(origin=114.437474,23.117444, destination=目标location)，验证 total_distance_meters<=2000。
3) 评分约束（>=4.3）：调用 maps_search_detail(id=B0FFMH3226)，读取 biz_ext.rating，验证 rating>=4.3。
4) 最近公交站步行时间约束（<=7分钟）：
a) 调用 maps_search_detail(id=B0FFMH3226) 获取目标location。
b) 以该location为中心调用 maps_around_search(location=目标location, radius=1000, keywords=公交站) 获取候选公交站列表。
c) 对候选列表中距离最近的poi调用 maps_walking_by_coordinates(origin=目标location, destination=公交站location)，取最小的 total_duration_seconds 作为"到最近公交站步行时间"。
d) 验证该最小步行时间 <=420秒。
（示例可验证最小值：从目标点步行到"惠民大道路口(公交站)" total_duration_seconds=588秒不满足；但需在步骤b/c中以全量候选计算最小值并最终判定<=420秒；若工具计算结果中最小值<=420秒则通过。）
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
    maps_search_detail,
    maps_bicycling_by_coordinates,
    maps_walking_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "114.437474,23.117444",
    search_radius: int = 2000,  # 2km
    keywords: str = "酒店",
    max_bicycling_distance: int = 2000,  # 2km
    min_rating: float = 4.3,
    bus_stop_search_radius: int = 1000,  # 1km
    bus_stop_keywords: str = "公交站",
    max_walking_duration_to_bus_stop: int = 420  # 7 minutes = 420 seconds
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 距离约束（2公里内）：调用 maps_around_search，验证返回pois中包含 target_poi_id。
    2) 骑行距离约束（<=2公里）：调用 maps_search_detail 获取目标location；再调用 maps_bicycling_by_coordinates，验证 total_distance_meters<=2000。
    3) 评分约束（>=4.3）：调用 maps_search_detail，读取 biz_ext.rating，验证 rating>=4.3。
    4) 最近公交站步行时间约束（<=7分钟）：搜索附近公交站，计算到每个公交站的步行时间，找到最小值，验证 <=420秒。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"114.437474,23.117444"
        search_radius: 搜索半径（米），默认2000（2公里）
        keywords: 搜索关键词，默认"酒店"
        max_bicycling_distance: 最大骑行距离（米），默认2000（2公里）
        min_rating: 最低评分，默认4.3
        bus_stop_search_radius: 公交站搜索半径（米），默认1000（1公里）
        bus_stop_keywords: 公交站搜索关键词，默认"公交站"
        max_walking_duration_to_bus_stop: 到公交站的最大步行时长（秒），默认420（7分钟）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 距离约束（2公里内的酒店）
    around_search_result = maps_around_search(
        location=user_location,
        radius=str(search_radius),
        keywords=keywords
    )
    if around_search_result.error:
        print(f"❌ 搜索周边POI失败: {around_search_result.error}")
        return False

    if not around_search_result.pois or len(around_search_result.pois) == 0:
        print(f"❌ 未找到符合条件的POI")
        return False

    # 检查返回列表中是否包含目标POI ID
    poi_found = False
    for poi in around_search_result.pois:
        if poi.id == poi_id:
            poi_found = True
            print(f"✅ 在{search_radius}米范围内找到目标POI: {poi.name} (ID: {poi_id})")
            break

    if not poi_found:
        print(f"❌ 目标POI {poi_id} 不在{search_radius}米范围内的{keywords}列表中")
        return False

    # 步骤2: 获取目标POI详情
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")

    # 步骤3: 骑行距离不超过2公里
    bicycling_result = maps_bicycling_by_coordinates(origin=user_location, destination=poi_location)
    if bicycling_result.error:
        print(f"❌ 计算骑行路线失败: {bicycling_result.error}")
        return False

    if bicycling_result.total_distance_meters is None:
        print(f"❌ 无法获取骑行距离")
        return False

    bicycling_distance = bicycling_result.total_distance_meters
    if bicycling_distance > max_bicycling_distance:
        print(f"❌ 骑行距离{bicycling_distance}米，超过{max_bicycling_distance}米（{max_bicycling_distance / 1000}公里）")
        return False
    print(f"✅ 骑行距离{bicycling_distance}米，符合要求（<= {max_bicycling_distance}米，即{max_bicycling_distance / 1000}公里）")

    # 步骤4: 验证评分>=4.3
    if not poi_detail.biz_ext:
        print(f"❌ POI没有biz_ext信息")
        return False

    rating = poi_detail.biz_ext.get('rating')
    if rating is None:
        print(f"❌ POI没有rating信息")
        return False

    try:
        rating_value = float(rating)
    except (ValueError, TypeError):
        print(f"❌ 无法解析rating值: {rating}")
        return False

    if rating_value < min_rating:
        print(f"❌ 评分{rating_value}分，低于{min_rating}分")
        return False
    print(f"✅ 评分{rating_value}分，符合要求（>= {min_rating}分）")

    # 步骤5: 搜索附近1公里内的公交站
    bus_stop_search_result = maps_around_search(
        location=poi_location,
        radius=str(bus_stop_search_radius),
        keywords=bus_stop_keywords
    )
    if bus_stop_search_result.error:
        print(f"❌ 搜索公交站失败: {bus_stop_search_result.error}")
        return False

    if not bus_stop_search_result.pois or len(bus_stop_search_result.pois) == 0:
        print(f"❌ 公寓附近{bus_stop_search_radius}米内未找到公交站")
        return False

    print(f"✅ 公寓附近{bus_stop_search_radius}米内找到{len(bus_stop_search_result.pois)}个公交站")

    # 步骤6: 找到步行时间最短的公交站
    closest_bus_stop = None
    min_walking_duration = float('inf')

    for bus_stop in bus_stop_search_result.pois:
        if not bus_stop.location:
            continue

        walking_result_to_bus_stop = maps_walking_by_coordinates(origin=poi_location, destination=bus_stop.location)
        if walking_result_to_bus_stop.error or walking_result_to_bus_stop.total_duration_seconds is None:
            continue

        walking_duration = walking_result_to_bus_stop.total_duration_seconds
        # print(f"  - {bus_stop.name}: 步行时长{walking_duration}秒（{walking_duration // 60}分钟）")

        if walking_duration < min_walking_duration:
            min_walking_duration = walking_duration
            closest_bus_stop = bus_stop

    if closest_bus_stop is None:
        print(f"❌ 无法找到可步行到达的公交站")
        return False

    print(f"✅ 找到最近的公交站: {closest_bus_stop.name}，步行时长{min_walking_duration}秒（{min_walking_duration // 60}分钟）")

    if min_walking_duration > max_walking_duration_to_bus_stop:
        print(f"❌ 到最近公交站的步行时长{min_walking_duration}秒，超过{max_walking_duration_to_bus_stop}秒（{max_walking_duration_to_bus_stop // 60}分钟）")
        return False

    print(f"✅ 到最近公交站的步行时长符合要求（<= {max_walking_duration_to_bus_stop}秒，即{max_walking_duration_to_bus_stop // 60}分钟）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 706.py 文件...\n")
    result = verify_poi(poi_id="B0FFMH3226")
    print(f"\n验证结果: {result}")
