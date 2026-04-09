
"""
修改任务指令：你要在附近3000米以内找一家酒吧。你打算步行过去，所以你走到酒吧的步行距离不能超过2000米；同时你也可能骑车去，骑行距离要在1800米以内；如果临时改成打车，开车距离要在2公里以内。酒吧的评分要至少4.7分。另外你希望酒吧到附近1200米范围内的地铁站里，走到最近一个地铁站的步行时间不超过12分钟。还有一个取现需求：你希望从你出发去酒吧的路上，沿途途径点500米范围内能找到ATM。你健谈外向，乐观，乐于合作。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 距离周边约束（附近3000米）：调用maps_around_search(location='125.267857,43.864558', radius='3000', keywords='酒吧')，验证返回pois中包含target_poi_id='B0ID377ITT'。
2) 酒吧评分：调用maps_search_detail(id='B0ID377ITT')，读取biz_ext.rating，验证rating>=4.7。
3) 起点到酒吧步行距离：从maps_search_detail获得酒吧坐标destination=location；调用maps_walking_by_coordinates(origin='125.267857,43.864558', destination=destination)，验证total_distance_meters<=2000。
4) 起点到酒吧骑行距离：调用maps_bicycling_by_coordinates(origin='125.267857,43.864558', destination=destination)，验证total_distance_meters<=1800。
5) 起点到酒吧驾车距离：调用maps_driving_by_coordinates(origin='125.267857,43.864558', destination=destination)，验证total_distance_meters<=2000。
6) 酒吧到附近1200米内地铁站的最小步行时间：以酒吧坐标为中心调用maps_around_search(location=destination, radius='1200', keywords='地铁站')获取候选地铁站列表；对每个地铁站调用maps_walking_by_coordinates(origin=destination, destination=station.location)，取total_duration_seconds最小值t_min，验证t_min<=720秒(12分钟)。
7) 途径点附近有ATM（用"酒吧到最近地铁站"路径上的一个途径点近似验证）：在步骤6中找到使t_min最小的地铁站（本数据中为"宽平桥(地铁站)"）；取酒吧到该地铁站步行路线steps中所有起始点、终点和中间途径点作为to_coordinates（例如'125.275500,43.861500'，由路线步骤坐标确定）；调用maps_around_search(location=P, radius='500', keywords='ATM')，验证存在一个点返回的pois数量>=1。
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
    maps_driving_by_coordinates,
    maps_bicycling_by_coordinates,
    maps_walking_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "125.267857,43.864558",
    search_radius: int = 3000,
    keywords: str = "酒吧",
    min_rating: float = 4.7,
    max_walking_distance: int = 2000,  # 2000 meters
    max_bicycling_distance: int = 1800,  # 1800 meters
    max_driving_distance: int = 2000,  # 2 km = 2000 meters
    subway_search_radius: int = 1200,
    subway_keywords: str = "地铁站",
    max_subway_walking_duration: int = 720,  # 12 minutes = 720 seconds
    waypoint_atm_radius: int = 500,
    atm_keywords: str = "ATM"
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 距离周边约束（附近3000米）：调用 maps_around_search，验证返回pois中包含target_poi_id。
    2) 酒吧评分：调用 maps_search_detail，读取 biz_ext.rating，验证rating>=4.7。
    3) 起点到酒吧步行距离：调用 maps_walking_by_coordinates，验证 total_distance_meters<=2000。
    4) 起点到酒吧骑行距离：调用 maps_bicycling_by_coordinates，验证 total_distance_meters<=1800。
    5) 起点到酒吧驾车距离：调用 maps_driving_by_coordinates，验证 total_distance_meters<=2000。
    6) 酒吧到附近1200米内地铁站的最小步行时间：调用 maps_around_search 获取地铁站列表，对每个地铁站调用 maps_walking_by_coordinates，取最小值，验证<=720秒。
    7) 途径点附近有ATM：取酒吧到最近地铁站步行路线steps中所有途径点，调用 maps_around_search，验证存在一个点返回的pois数量>=1。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"125.267857,43.864558"
        search_radius: 搜索半径（米），默认3000
        keywords: 搜索关键词，默认"酒吧"
        min_rating: 最低评分，默认4.7
        max_walking_distance: 最大步行距离（米），默认2000
        max_bicycling_distance: 最大骑行距离（米），默认1800
        max_driving_distance: 最大驾车距离（米），默认2000
        subway_search_radius: 地铁站搜索半径（米），默认1200
        subway_keywords: 地铁站搜索关键词，默认"地铁站"
        max_subway_walking_duration: 到地铁站最大步行时长（秒），默认720（12分钟）
        waypoint_atm_radius: 途经点ATM搜索半径（米），默认500
        atm_keywords: ATM搜索关键词，默认"ATM"

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 距离周边约束（附近3000米）
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

    # 步骤2: 获取目标POI详情（包括坐标和评分）
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")

    # 验证评分
    if poi_detail.biz_ext and 'rating' in poi_detail.biz_ext:
        rating = float(poi_detail.biz_ext['rating'])
        if rating < min_rating:
            print(f"❌ POI评分{rating}分，低于{min_rating}分")
            return False
        print(f"✅ POI评分{rating}分，符合要求（>= {min_rating}分）")
    else:
        print(f"❌ POI没有评分信息")
        return False

    # 步骤3: 起点到酒吧步行距离<=2000米
    walking_result = maps_walking_by_coordinates(origin=user_location, destination=poi_location)
    if walking_result.error:
        print(f"❌ 计算步行路线失败: {walking_result.error}")
        return False

    if walking_result.total_distance_meters is None:
        print(f"❌ 无法获取步行距离")
        return False

    walking_distance = walking_result.total_distance_meters
    if walking_distance > max_walking_distance:
        print(f"❌ 步行距离{walking_distance}米，超过{max_walking_distance}米")
        return False
    print(f"✅ 步行距离{walking_distance}米，符合要求（<= {max_walking_distance}米）")

    # 步骤4: 起点到酒吧骑行距离<=1800米
    bicycling_result = maps_bicycling_by_coordinates(origin=user_location, destination=poi_location)
    if bicycling_result.error:
        print(f"❌ 计算骑行路线失败: {bicycling_result.error}")
        return False

    if bicycling_result.total_distance_meters is None:
        print(f"❌ 无法获取骑行距离")
        return False

    bicycling_distance = bicycling_result.total_distance_meters
    if bicycling_distance > max_bicycling_distance:
        print(f"❌ 骑行距离{bicycling_distance}米，超过{max_bicycling_distance}米")
        return False
    print(f"✅ 骑行距离{bicycling_distance}米，符合要求（<= {max_bicycling_distance}米）")

    # 步骤5: 起点到酒吧驾车距离<=2000米
    driving_result = maps_driving_by_coordinates(origin=user_location, destination=poi_location)
    if driving_result.error:
        print(f"❌ 计算驾车路线失败: {driving_result.error}")
        return False

    if driving_result.total_distance_meters is None:
        print(f"❌ 无法获取驾车距离")
        return False

    driving_distance = driving_result.total_distance_meters
    if driving_distance > max_driving_distance:
        print(f"❌ 驾车距离{driving_distance}米，超过{max_driving_distance}米")
        return False
    print(f"✅ 驾车距离{driving_distance}米，符合要求（<= {max_driving_distance}米）")

    # 步骤6: 酒吧到附近1200米内地铁站的最小步行时间
    subway_search_result = maps_around_search(
        location=poi_location,
        radius=str(subway_search_radius),
        keywords=subway_keywords
    )
    if subway_search_result.error:
        print(f"❌ 搜索地铁站失败: {subway_search_result.error}")
        return False

    if not subway_search_result.pois or len(subway_search_result.pois) == 0:
        print(f"❌ 未找到地铁站")
        return False

    print(f"✅ 找到{len(subway_search_result.pois)}个地铁站")

    # 计算到每个地铁站的步行时间，找到最小值及对应的地铁站
    min_subway_walking_duration = None
    nearest_subway_location = None
    nearest_subway_walking_result = None
    for subway in subway_search_result.pois:
        if not subway.location:
            continue

        subway_walking_result = maps_walking_by_coordinates(
            origin=poi_location,
            destination=subway.location
        )
        if subway_walking_result.error or subway_walking_result.total_duration_seconds is None:
            continue

        duration = subway_walking_result.total_duration_seconds
        if min_subway_walking_duration is None or duration < min_subway_walking_duration:
            min_subway_walking_duration = duration
            nearest_subway_location = subway.location
            nearest_subway_walking_result = subway_walking_result

    if min_subway_walking_duration is None:
        print(f"❌ 无法计算到地铁站的步行时间")
        return False

    if min_subway_walking_duration > max_subway_walking_duration:
        print(f"❌ 到最近地铁站步行时长{min_subway_walking_duration}秒，超过{max_subway_walking_duration}秒（{max_subway_walking_duration // 60}分钟）")
        return False
    print(f"✅ 到最近地铁站步行时长{min_subway_walking_duration}秒，符合要求（<= {max_subway_walking_duration}秒，即{max_subway_walking_duration // 60}分钟）")

    # 步骤7: 途径点附近有ATM（用"酒吧到最近地铁站"路径上的途径点验证）
    if not nearest_subway_walking_result or not nearest_subway_walking_result.steps or len(nearest_subway_walking_result.steps) == 0:
        print(f"❌ 酒吧到最近地铁站的步行路线没有步骤信息")
        return False

    print(f"✅ 酒吧到最近地铁站的步行路线共有{len(nearest_subway_walking_result.steps)}个步骤")

    # 检查每个途经点周围是否有ATM
    atm_found = False
    for i, step in enumerate(nearest_subway_walking_result.steps):
        waypoint_location = step.to_coordinates
        atm_search_result = maps_around_search(
            location=waypoint_location,
            radius=str(waypoint_atm_radius),
            keywords=atm_keywords
        )

        if atm_search_result.error:
            continue

        if atm_search_result.pois and len(atm_search_result.pois) > 0:
            atm_found = True
            print(f"✅ 在途经点{i+1}（坐标: {waypoint_location}）周围{waypoint_atm_radius}米内找到{len(atm_search_result.pois)}个ATM")
            print(f"   示例ATM: {atm_search_result.pois[0].name} (ID: {atm_search_result.pois[0].id})")
            break

    if not atm_found:
        print(f"❌ 所有途经点周围{waypoint_atm_radius}米内都没有找到ATM")
        return False

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 794.py 文件...\n")
    result = verify_poi(poi_id="B0ID377ITT")
    print(f"\n验证结果: {result}")
