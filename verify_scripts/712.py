
"""
修改任务指令：你要在附近找一个距离2.5公里内的商场。你打算从你这里步行过去，走路总时长不能超过25分钟。你还需要这个商场在2.5公里范围内，能步行到一个地铁站且步行时间不超过15分钟。并且从那个地铁站出站后，附近300米内必须能找到停车场，方便同事开车来接你。你有礼貌但非常坚决和不耐烦，希望尽快解决问题。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 距离约束（2.5km内的商场）：调用 maps_around_search(location='117.278957,31.87228', radius='2500', keywords='商场')，验证返回pois中包含 target_poi_id='B0FFHEN026'。
2) 步行时间约束（≤25分钟）：调用 maps_search_detail(id='B0FFHEN026') 获取目标POI坐标 destination=location；再调用 maps_walking_by_coordinates(origin='117.278957,31.87228', destination=destination)，验证 total_duration_seconds ≤ 1500。
3) 附近2.5公里商场到地铁站步行时间约束（≤15分钟）：对目标POI坐标调用 maps_around_search(location=POI.location, radius='2500', keywords='地铁站') 获取候选地铁站列表；选择其中步行时间最短的地铁站station（对每个站调用 maps_walking_by_coordinates(origin=POI.location, destination=station.location)），验证 min(total_duration_seconds) ≤ 900。
4) 地铁站300米内必须有停车场：对步骤3选出的station调用 maps_around_search(location=station.location, radius='300', keywords='停车场')，验证返回pois数量>0（至少存在一个停车场POI）。
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
    maps_walking_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "117.278957,31.87228",
    search_radius: int = 2500,  # 2.5km
    keywords: str = "商场",
    max_walking_duration_from_user: int = 1500,  # 25 minutes = 1500 seconds
    subway_search_radius: int = 2500,  # 2.5km
    subway_keywords: str = "地铁站",
    max_walking_duration_to_subway: int = 900,  # 15 minutes = 900 seconds
    parking_search_radius: int = 300,  # 300m
    parking_keywords: str = "停车场"
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 距离约束（2.5km内的商场）：调用 maps_around_search，验证返回pois中包含 target_poi_id。
    2) 步行时间约束（≤25分钟）：调用 maps_search_detail 获取目标POI坐标；再调用 maps_walking_by_coordinates，验证 total_duration_seconds ≤ 1500。
    3) 附近2.5公里商场到地铁站步行时间约束（≤15分钟）：对目标POI坐标调用 maps_around_search 获取候选地铁站列表；选择其中步行时间最短的地铁站，验证 min(total_duration_seconds) ≤ 900。
    4) 地铁站300米内必须有停车场：对步骤3选出的station调用 maps_around_search，验证返回pois数量>0。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"117.278957,31.87228"
        search_radius: 搜索半径（米），默认2500（2.5公里）
        keywords: 搜索关键词，默认"商场"
        max_walking_duration_from_user: 从用户位置到商场的最大步行时长（秒），默认1500（25分钟）
        subway_search_radius: 地铁站搜索半径（米），默认2500（2.5公里）
        subway_keywords: 地铁站搜索关键词，默认"地铁站"
        max_walking_duration_to_subway: 从商场到地铁站的最大步行时长（秒），默认900（15分钟）
        parking_search_radius: 停车场搜索半径（米），默认300
        parking_keywords: 停车场搜索关键词，默认"停车场"

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 距离约束（2.5公里内的商场）
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

    # 步骤2: 获取目标POI坐标
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")

    # 步骤3: 从用户位置到商场的步行时间≤25分钟
    walking_result_from_user = maps_walking_by_coordinates(origin=user_location, destination=poi_location)
    if walking_result_from_user.error:
        print(f"❌ 计算从用户位置到商场的步行路线失败: {walking_result_from_user.error}")
        return False

    if walking_result_from_user.total_duration_seconds is None:
        print(f"❌ 无法获取从用户位置到商场的步行时长")
        return False

    walking_duration_from_user = walking_result_from_user.total_duration_seconds
    if walking_duration_from_user > max_walking_duration_from_user:
        print(f"❌ 从用户位置到商场的步行时长{walking_duration_from_user}秒，超过{max_walking_duration_from_user}秒（{max_walking_duration_from_user // 60}分钟）")
        return False
    print(f"✅ 从用户位置到商场的步行时长{walking_duration_from_user}秒，符合要求（<= {max_walking_duration_from_user}秒，即{max_walking_duration_from_user // 60}分钟）")

    # 步骤4: 搜索商场附近2.5公里内的地铁站
    subway_search_result = maps_around_search(
        location=poi_location,
        radius=str(subway_search_radius),
        keywords=subway_keywords
    )
    if subway_search_result.error:
        print(f"❌ 搜索地铁站失败: {subway_search_result.error}")
        return False

    if not subway_search_result.pois or len(subway_search_result.pois) == 0:
        print(f"❌ 商场附近{subway_search_radius}米内未找到地铁站")
        return False

    print(f"✅ 商场附近{subway_search_radius}米内找到{len(subway_search_result.pois)}个地铁站")

    # 步骤5: 找到步行时间最短的地铁站
    closest_subway = None
    min_walking_duration = float('inf')

    for subway in subway_search_result.pois:
        if not subway.location:
            continue

        walking_result_to_subway = maps_walking_by_coordinates(origin=poi_location, destination=subway.location)
        if walking_result_to_subway.error or walking_result_to_subway.total_duration_seconds is None:
            continue

        walking_duration = walking_result_to_subway.total_duration_seconds
        # print(f"  - {subway.name}: 步行时长{walking_duration}秒（{walking_duration // 60}分钟）")

        if walking_duration < min_walking_duration:
            min_walking_duration = walking_duration
            closest_subway = subway

    if closest_subway is None:
        print(f"❌ 无法找到可步行到达的地铁站")
        return False

    print(f"✅ 找到最近的地铁站: {closest_subway.name}，步行时长{min_walking_duration}秒（{min_walking_duration // 60}分钟）")

    if min_walking_duration > max_walking_duration_to_subway:
        print(f"❌ 到最近地铁站的步行时长{min_walking_duration}秒，超过{max_walking_duration_to_subway}秒（{max_walking_duration_to_subway // 60}分钟）")
        return False

    print(f"✅ 到最近地铁站的步行时长符合要求（<= {max_walking_duration_to_subway}秒，即{max_walking_duration_to_subway // 60}分钟）")

    # 步骤6: 验证地铁站300米内有停车场
    parking_search_result = maps_around_search(
        location=closest_subway.location,
        radius=str(parking_search_radius),
        keywords=parking_keywords
    )
    if parking_search_result.error:
        print(f"❌ 搜索停车场失败: {parking_search_result.error}")
        return False

    if not parking_search_result.pois or len(parking_search_result.pois) == 0:
        print(f"❌ 地铁站附近{parking_search_radius}米内未找到停车场")
        return False

    print(f"✅ 地铁站附近{parking_search_radius}米内找到停车场: {parking_search_result.pois[0].name} (共{len(parking_search_result.pois)}个)")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 712.py 文件...\n")
    result = verify_poi(poi_id="B0FFHEN026")
    print(f"\n验证结果: {result}")
