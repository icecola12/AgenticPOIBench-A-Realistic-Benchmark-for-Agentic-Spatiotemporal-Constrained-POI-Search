
"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 附近1500米内：调用 maps_around_search(location='116.359104,39.90506', radius='1500', keywords='邮局')，验证返回结果中包含 target_poi_id='B0FFLKM3QA'。
2) 用户到邮局最大步行距离：调用 maps_walking_by_coordinates(origin='116.359104,39.90506', destination='116.359659,39.906347')，验证 total_distance_meters ≤ 1500。
3) 用户到邮局最大骑行距离：调用 maps_bicycling_by_coordinates(origin='116.359104,39.90506', destination='116.359659,39.906347')，验证 total_distance_meters ≤ 1500。
4) 邮局附近1200米内地铁站集合：调用 maps_around_search(location='116.359659,39.906347', radius='1200', keywords='地铁站') 获取候选地铁站列表。
5) 邮局到最近地铁站最短步行距离≤500米且最短步行时间≤8分钟：对第4步返回的每个地铁站，调用 maps_walking_by_coordinates(origin='116.359659,39.906347', destination=station.location)，取 total_distance_meters 的最小值，验证最小 total_distance_meters ≤ 500 且这个地铁站对应的 total_duration_seconds ≤ 480。
6) 邮局到指定公交站点（复兴门地铁站）直线距离≤700米：调用 maps_text_search(keywords='复兴门(地铁站)', city='北京', citylimit='true') 获取复兴门地铁站坐标；再调用 maps_distance(origins=target_poi.location, destination=fuxingmen.location)，验证 distance_meters ≤ 700。
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
    maps_walking_by_coordinates,
    maps_bicycling_by_coordinates,
    maps_text_search,
    maps_distance,
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "116.359104,39.90506",
    target_poi_location: str = "116.359659,39.906347",
    around_search_radius: int = 1500,
    around_search_keywords: str = "邮局",
    max_walking_distance_to_poi: int = 1500,
    max_bicycling_distance_to_poi: int = 1500,
    metro_around_radius: int = 1200,
    metro_keywords: str = "地铁站",
    max_walking_distance_to_nearest_metro: int = 500,
    max_walking_duration_to_nearest_metro: int = 480,
    fuxingmen_keywords: str = "复兴门(地铁站)",
    fuxingmen_city: str = "北京",
    fuxingmen_citylimit: str = "true",
    max_distance_to_fuxingmen: int = 700,
) -> bool:
    """
    根据给定的验证方法验证POI是否符合要求。
    
    Args:
        poi_id: 目标邮局 POI ID
        user_location: 用户坐标
        target_poi_location: 目标邮局坐标
        around_search_radius: 搜索邮局半径（米）
        around_search_keywords: 搜索邮局关键词
        max_walking_distance_to_poi: 用户到邮局最大步行距离（米）
        max_bicycling_distance_to_poi: 用户到邮局最大骑行距离（米）
        metro_around_radius: 邮局附近地铁站搜索半径（米）
        metro_keywords: 地铁站搜索关键词
        max_walking_distance_to_nearest_metro: 邮局到最近地铁站最大步行距离（米）
        max_walking_duration_to_nearest_metro: 邮局到最近地铁站最大步行时间（秒）
        fuxingmen_keywords: 复兴门地铁站搜索关键词
        fuxingmen_city: 复兴门地铁站所在城市
        fuxingmen_citylimit: 城市限制参数
        max_distance_to_fuxingmen: 邮局到复兴门地铁站最大直线距离（米）
    
    Returns:
        bool: True 表示验证通过，False 表示验证失败
    """
    # 步骤1: 附近1500米内包含目标邮局
    around_result = maps_around_search(
        location=user_location,
        radius=str(around_search_radius),
        keywords=around_search_keywords,
    )
    if around_result.error:
        print(f"❌ 周边搜索邮局失败: {around_result.error}")
        return False

    if not around_result.pois or len(around_result.pois) == 0:
        print("❌ 周边未找到任何邮局")
        return False

    poi_found = False
    for poi in around_result.pois:
        if poi.id == poi_id:
            poi_found = True
            print(f"✅ 在{around_search_radius}米范围内找到目标邮局: {poi.name} (ID: {poi_id})")
            break

    if not poi_found:
        print(f"❌ 目标邮局 {poi_id} 不在{around_search_radius}米范围内的邮局列表中")
        return False

    # 获取目标邮局详情以获得其坐标（供后续步骤使用）
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取目标邮局详情失败: {poi_detail.error}")
        return False
    if not poi_detail.location:
        print("❌ 目标邮局缺少坐标信息")
        return False
    target_location = poi_detail.location
    print(f"✅ 目标邮局坐标: {target_location}")

    # 步骤2: 用户到邮局最大步行距离
    walking_result = maps_walking_by_coordinates(
        origin=user_location,
        destination=target_poi_location,
    )
    if walking_result.error:
        print(f"❌ 计算用户到邮局的步行路线失败: {walking_result.error}")
        return False
    if walking_result.total_distance_meters is None:
        print("❌ 无法获取用户到邮局的步行距离")
        return False

    walking_distance = walking_result.total_distance_meters
    if walking_distance > max_walking_distance_to_poi:
        print(
            f"❌ 用户到邮局步行距离{walking_distance}米，超过{max_walking_distance_to_poi}米"
        )
        return False
    print(
        f"✅ 用户到邮局步行距离{walking_distance}米，符合要求（<= {max_walking_distance_to_poi}米）"
    )

    # 步骤3: 用户到邮局最大骑行距离
    bicycling_result = maps_bicycling_by_coordinates(
        origin=user_location,
        destination=target_poi_location,
    )
    if bicycling_result.error:
        print(f"❌ 计算用户到邮局的骑行路线失败: {bicycling_result.error}")
        return False
    if bicycling_result.total_distance_meters is None:
        print("❌ 无法获取用户到邮局的骑行距离")
        return False

    bicycling_distance = bicycling_result.total_distance_meters
    if bicycling_distance > max_bicycling_distance_to_poi:
        print(
            f"❌ 用户到邮局骑行距离{bicycling_distance}米，超过{max_bicycling_distance_to_poi}米"
        )
        return False
    print(
        f"✅ 用户到邮局骑行距离{bicycling_distance}米，符合要求（<= {max_bicycling_distance_to_poi}米）"
    )

    # 步骤4: 邮局附近1200米内地铁站集合
    metro_around_result = maps_around_search(
        location=target_poi_location,
        radius=str(metro_around_radius),
        keywords=metro_keywords,
    )
    if metro_around_result.error:
        print(f"❌ 搜索邮局附近地铁站失败: {metro_around_result.error}")
        return False

    if not metro_around_result.pois or len(metro_around_result.pois) == 0:
        print(f"❌ 邮局附近{metro_around_radius}米内未找到任何地铁站")
        return False

    print(
        f"✅ 邮局附近{metro_around_radius}米内找到地铁站{len(metro_around_result.pois)}个"
    )

    # 步骤5: 邮局到最近地铁站最短步行距离≤500米且最短步行时间≤8分钟
    min_distance = None
    min_distance_duration = None

    for station in metro_around_result.pois:
        if not station.location:
            continue
        walk_to_station = maps_walking_by_coordinates(
            origin=target_poi_location,
            destination=station.location,
        )
        if walk_to_station.error:
            print(f"⚠️ 计算到地铁站 {station.name} 的步行路线失败: {walk_to_station.error}")
            continue
        if walk_to_station.total_distance_meters is None:
            print(f"⚠️ 无法获取到地铁站 {station.name} 的步行距离")
            continue

        distance = walk_to_station.total_distance_meters
        duration = walk_to_station.total_duration_seconds

        if min_distance is None or distance < min_distance:
            min_distance = distance
            min_distance_duration = duration

    if min_distance is None:
        print("❌ 无法获取任何地铁站的步行距离")
        return False

    if min_distance > max_walking_distance_to_nearest_metro:
        print(
            f"❌ 邮局到最近地铁站的最短步行距离{min_distance}米，超过{max_walking_distance_to_nearest_metro}米"
        )
        return False

    if min_distance_duration is None:
        print("❌ 最近地铁站的步行时长信息缺失")
        return False

    if min_distance_duration > max_walking_duration_to_nearest_metro:
        print(
            f"❌ 邮局到最近地铁站的步行时间{min_distance_duration}秒，超过{max_walking_duration_to_nearest_metro}秒"
        )
        return False

    print(
        f"✅ 邮局到最近地铁站的最短步行距离{min_distance}米，"
        f"步行时间{min_distance_duration}秒，均符合要求"
    )

    # 步骤6: 邮局到指定公交站点（复兴门地铁站）直线距离≤700米
    fuxingmen_search = maps_text_search(
        keywords=fuxingmen_keywords,
        city=fuxingmen_city,
        citylimit=fuxingmen_citylimit,
    )
    if fuxingmen_search.error:
        print(f"❌ 搜索复兴门地铁站失败: {fuxingmen_search.error}")
        return False

    if not fuxingmen_search.pois or len(fuxingmen_search.pois) == 0:
        print("❌ 未搜索到复兴门地铁站")
        return False

    # 取搜索到的第一个复兴门地铁站结果，再通过详情接口获取坐标
    fuxingmen_poi_id = fuxingmen_search.pois[0].id
    fuxingmen_detail = maps_search_detail(id=fuxingmen_poi_id)
    if fuxingmen_detail.error:
        print(f"❌ 获取复兴门地铁站详情失败: {fuxingmen_detail.error}")
        return False
    if not fuxingmen_detail.location:
        print("❌ 复兴门地铁站缺少坐标信息")
        return False

    fuxingmen_location = fuxingmen_detail.location
    print(f"✅ 复兴门地铁站坐标: {fuxingmen_location} (ID: {fuxingmen_poi_id})")

    # 目标邮局坐标使用 target_location（通过详情接口获取）
    distance_result = maps_distance(
        origins=target_location,
        destination=fuxingmen_location,
    )
    if distance_result.error:
        print(f"❌ 计算到复兴门地铁站的直线距离失败: {distance_result.error}")
        return False
    if not distance_result.results or len(distance_result.results) == 0:
        print("❌ 未获得到复兴门地铁站的距离结果")
        return False

    distance_to_fuxingmen = distance_result.results[0].distance_meters
    if distance_to_fuxingmen > max_distance_to_fuxingmen:
        print(
            f"❌ 邮局到复兴门地铁站直线距离{distance_to_fuxingmen}米，超过{max_distance_to_fuxingmen}米"
        )
        return False

    print(
        f"✅ 邮局到复兴门地铁站直线距离{distance_to_fuxingmen}米，符合要求（<= {max_distance_to_fuxingmen}米）"
    )

    print("✅ 所有验证通过！")
    return True


if __name__ == "__main__":
    print("开始验证 788.py 文件...\n")
    result = verify_poi(poi_id="B0FFLKM3QA")
    print(f"\n验证结果: {result}")