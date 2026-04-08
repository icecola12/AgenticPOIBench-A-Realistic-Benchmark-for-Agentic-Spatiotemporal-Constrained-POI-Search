"""
输入：B0FFMHY9TB
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边酒店约束：调用 maps_around_search(location='118.878919,42.25805', radius='3000', keywords='酒店')，验证返回pois中包含 target_poi_id='B0FFMHY9TB'。
2) 评分约束：调用 maps_search_detail(id='B0FFMHY9TB')，读取 biz_ext.rating，验证 rating >= 4.8。
3) 最大骑行时间：从 maps_search_detail 取酒店坐标 destination=location='118.885019,42.255044'，调用 maps_bicycling_by_coordinates(origin='118.878919,42.25805', destination=destination)，验证 total_duration_seconds <= 300。
4) 最大驾车距离：调用 maps_driving_by_coordinates(origin='118.878919,42.25805', destination=destination)，验证 total_distance_meters <= 2000。
5) 附近政务服务中心：以酒店坐标为中心调用 maps_around_search(location=destination, radius='800', keywords='政务服务中心')，从返回pois中任选一个POI，取其location并用 maps_distance(origins=destination, destination=poi.location) 复核直线距离 <= 800 米（例如：赤峰市政务服务和数据管理局 location='118.884574,42.251113'，直线距离约439米）。
"""
import sys
import os
from typing import List, Dict

# 将 src 加入 sys.path，以便从 src/tools/amap_tools 导入
_current_file_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_file_dir)
_src_dir = os.path.join(_project_root, "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from tools.amap_tools import (
    maps_search_detail,
    maps_distance,
    maps_driving_by_coordinates ,
    maps_walking_by_coordinates,
    maps_text_search,
    maps_bicycling_by_coordinates
)
from tools.amap_tools import maps_around_search

"""
POI验证函数
用于验证POI ID是否符合给定的验证条件
"""
def verify_poi(
    target_poi_id: str = "B0FFMHY9TB",
    user_location: str = "118.878919,42.25805",
    hotel_radius_meters: str = "3000",
    hotel_keywords: str = "酒店",
    min_rating: float = 4.8,
    expected_hotel_location: str = "118.885019,42.255044",
    max_bicycling_seconds: int = 300,
    max_driving_distance_meters: int = 2000,
    gov_service_radius_meters: str = "800",
    gov_service_keywords: str = "政务服务中心",
    max_gov_service_air_distance_meters: int = 800,
) -> bool:
    """
    按给定验证步骤验证 POI 是否符合要求。

    验证步骤（严格按题面）：
    1) 周边酒店约束：调用 maps_around_search(location=user_location, radius=3000, keywords="酒店")，
       验证返回pois中包含 target_poi_id。
    2) 评分约束：调用 maps_search_detail(id=target_poi_id)，读取 biz_ext.rating，验证 rating >= 4.8。
    3) 最大骑行时间：从 maps_search_detail 取 destination=location，且应为 expected_hotel_location；
       调用 maps_bicycling_by_coordinates(origin=user_location, destination=destination)，验证 total_duration_seconds <= 300。
    4) 最大驾车距离：调用 maps_driving_by_coordinates(origin=user_location, destination=destination)，验证 total_distance_meters <= 2000。
    5) 附近政务服务中心：以酒店坐标为中心调用 maps_around_search(location=destination, radius=800, keywords="政务服务中心")，
       从返回pois中任选一个POI，取其location并用 maps_distance(origins=destination, destination=poi.location)
       复核直线距离 <= 800 米。

    Returns:
        bool: True表示全部验证通过，否则False（包含部分满足的情况）。
    """
    all_passed = True

    # 步骤1) 周边酒店约束
    print("验证步骤1: 周边酒店约束 - 在用户位置周边搜索“酒店”，检查是否包含目标POI")
    around_hotels = maps_around_search(location=user_location, radius=hotel_radius_meters, keywords=hotel_keywords)
    if around_hotels.error:
        print(f"验证步骤1失败: 周边搜索返回错误: {around_hotels.error}")
        all_passed = False
    elif not around_hotels.pois:
        print("验证步骤1失败: 周边搜索未返回任何POI")
        all_passed = False
    else:
        found = any(poi.id == target_poi_id for poi in around_hotels.pois)
        if found:
            print(f"验证步骤1通过: 在{hotel_radius_meters}米内“{hotel_keywords}”结果中找到了目标POI {target_poi_id}")
        else:
            print(f"验证步骤1失败: 在{hotel_radius_meters}米内“{hotel_keywords}”结果中未找到目标POI {target_poi_id}")
            all_passed = False

    # 步骤2) 评分约束 + 获取坐标
    print(f"验证步骤2: 评分约束 - 获取POI详情并验证评分 >= {min_rating}")
    poi_detail = maps_search_detail(id=target_poi_id)
    if poi_detail.error:
        print(f"验证步骤2失败: 获取POI详情返回错误: {poi_detail.error}")
        return False
    if not poi_detail.location:
        print("验证步骤2失败: POI详情中未获取到location")
        return False

    destination = poi_detail.location

    rating = None
    if poi_detail.biz_ext and isinstance(poi_detail.biz_ext, dict):
        rating_str = poi_detail.biz_ext.get("rating")
        if rating_str is not None and rating_str != "":
            try:
                rating = float(rating_str)
            except (TypeError, ValueError):
                rating = None

    if rating is None:
        print("验证步骤2失败: 未获取到POI评分(biz_ext.rating)")
        all_passed = False
    elif rating >= min_rating:
        print(f"验证步骤2通过: 评分 {rating} >= {min_rating}")
    else:
        print(f"验证步骤2失败: 评分 {rating} < {min_rating}")
        all_passed = False

    # 步骤3) 最大骑行时间（并校验题面给定 destination 坐标一致）
    print(f"验证步骤3: 最大骑行时间 - 骑行时长 <= {max_bicycling_seconds}秒")
    if expected_hotel_location and destination != expected_hotel_location:
        print(
            "验证步骤3失败: maps_search_detail 返回的酒店坐标与验证步骤给定值不一致: "
            f"实际={destination}，期望={expected_hotel_location}"
        )
        all_passed = False
    else:
        print(f"验证步骤3: 成功获取酒店坐标 destination={destination}")

    bicycling = maps_bicycling_by_coordinates(origin=user_location, destination=destination)
    if bicycling.error:
        print(f"验证步骤3失败: 骑行路径计算返回错误: {bicycling.error}")
        all_passed = False
    elif bicycling.total_duration_seconds is None:
        print("验证步骤3失败: 骑行路径计算未返回 total_duration_seconds")
        all_passed = False
    else:
        s = bicycling.total_duration_seconds
        if s <= max_bicycling_seconds:
            print(f"验证步骤3通过: 骑行时长 {s}秒 <= {max_bicycling_seconds}秒")
        else:
            print(f"验证步骤3失败: 骑行时长 {s}秒 > {max_bicycling_seconds}秒")
            all_passed = False

    # 步骤4) 最大驾车距离
    print(f"验证步骤4: 最大驾车距离 - 驾车距离 <= {max_driving_distance_meters}米")
    driving = maps_driving_by_coordinates(origin=user_location, destination=destination)
    if driving.error:
        print(f"验证步骤4失败: 驾车路径计算返回错误: {driving.error}")
        all_passed = False
    elif driving.total_distance_meters is None:
        print("验证步骤4失败: 驾车路径计算未返回 total_distance_meters")
        all_passed = False
    else:
        d = driving.total_distance_meters
        if d <= max_driving_distance_meters:
            print(f"验证步骤4通过: 驾车距离 {d}米 <= {max_driving_distance_meters}米")
        else:
            print(f"验证步骤4失败: 驾车距离 {d}米 > {max_driving_distance_meters}米")
            all_passed = False

    # 步骤5) 附近政务服务中心（around_search + distance 复核）
    print("验证步骤5: 附近政务服务中心 - 周边搜索并用直线距离复核 <= 800米")
    around_gov = maps_around_search(location=destination, radius=gov_service_radius_meters, keywords=gov_service_keywords)
    if around_gov.error:
        print(f"验证步骤5失败: 周边搜索返回错误: {around_gov.error}")
        all_passed = False
    elif not around_gov.pois:
        print(f"验证步骤5失败: 酒店周边{gov_service_radius_meters}米内未找到“{gov_service_keywords}”")
        all_passed = False
    else:
        chosen = None
        for p in around_gov.pois:
            if p and p.location:
                chosen = p
                break

        if chosen is None:
            print(f"验证步骤5失败: 找到了“{gov_service_keywords}”POI，但都没有可用的location字段")
            all_passed = False
        else:
            print(f"验证步骤5: 选取POI用于复核: {chosen.name} (id={chosen.id}, location={chosen.location})")
            dist = maps_distance(origins=destination, destination=chosen.location)
            if dist.error:
                print(f"验证步骤5失败: 直线距离复核返回错误: {dist.error}")
                all_passed = False
            elif not dist.results:
                print("验证步骤5失败: 直线距离复核未返回结果")
                all_passed = False
            else:
                air_m = dist.results[0].distance_meters
                if air_m <= max_gov_service_air_distance_meters:
                    print(f"验证步骤5通过: 直线距离 {air_m}米 <= {max_gov_service_air_distance_meters}米")
                else:
                    print(f"验证步骤5失败: 直线距离 {air_m}米 > {max_gov_service_air_distance_meters}米")
                    all_passed = False

    return all_passed


def main():
    result = verify_poi()
    print(f"\n最终验证结果: {'通过' if result else '失败'}")
    return result  


if __name__ == "__main__":
    main()
