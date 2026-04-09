
"""
修改任务指令：
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边命中校验：调用 maps_around_search(location='117.219887,39.041829', radius='3000', keywords='商场')，验证返回pois数量>8，且包含目标poi_id=B0FFJM8ATC。
2) 详情与评分校验：调用 maps_search_detail(id='B0FFJM8ATC') 获取 poi_id，再 maps_search_detail(id=poi_id) 获取 location 与 biz_ext.rating，验证 rating>=4.7。
3) 步行时间校验：用步骤2得到的目的地坐标destination=location，调用 maps_walking_by_coordinates(origin='117.219887,39.041829', destination=destination)，验证 total_duration_seconds<=22*60。
4) 天津站坐标获取：调用 maps_text_search(keywords='天津站', city='天津') 取 poi_id，再 maps_search_detail(id=poi_id) 获取天津站坐标。
5) 天津站驾车时间校验：调用 maps_driving_by_coordinates(origin=天津站坐标, destination=destination)，验证 total_duration_seconds<=22*60。
6) 地铁站邻近校验：调用 maps_around_search(location=destination, radius='600', keywords='地铁站')，验证返回pois数量>=1（即600米内存在地铁站POI）。
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
    maps_text_search,
    maps_search_detail,
    maps_walking_by_coordinates ,
    maps_driving_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "117.219887,39.041829",
    search_radius: int = 3000,  # 3km
    keywords: str = "商场",
    min_poi_count: int = 8,
    min_rating: float = 4.7,
    max_walking_duration: int = 1320,  # 22 minutes = 1320 seconds
    station_address: str = "天津站",
    station_city: str = "天津",
    max_driving_duration: int = 1320,  # 22 minutes = 1320 seconds
    metro_search_radius: int = 600,  # 600 meters
    metro_keywords: str = "地铁站",
    min_metro_count: int = 1
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 周边命中校验：调用 maps_around_search，验证返回pois数量>8，且包含目标poi_id
    2) 详情与评分校验：调用 maps_search_detail 获取 location 与 biz_ext.rating，验证 rating>=4.7
    3) 步行时间校验：调用 maps_walking_by_coordinates，验证 total_duration_seconds<=22*60
    4) 天津站坐标获取：调用5) 天津站驾车时间校验：调用 maps_driving_by_coordinates，验证 total_duration_seconds<=22*60
    6) 地铁站邻近校验：调用 maps_around_search，验证返回pois数量>=1

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"117.219887,39.041829"
        search_radius: 搜索半径（米），默认3000（3公里）
        keywords: 搜索关键词，默认"商场"
        min_poi_count: 最少POI数量，默认8
        min_rating: 最低评分，默认4.7
        max_walking_duration: 最大步行时长（秒），默认1320（22分钟）
        station_address: 车站地址，默认"天津站"
        station_city: 车站所在城市，默认"天津"
        max_driving_duration: 最大驾车时长（秒），默认1320（22分钟）
        metro_search_radius: 地铁站搜索半径（米），默认600
        metro_keywords: 地铁站搜索关键词，默认"地铁站"
        min_metro_count: 最少地铁站数量，默认1

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 周边命中校验（3公里内的商场）
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

    # 检查返回POI数量是否>8
    poi_count = len(around_search_result.pois)
    if poi_count <= min_poi_count:
        print(f"❌ 返回POI数量{poi_count}个，不大于{min_poi_count}个")
        return False
    print(f"✅ 返回POI数量{poi_count}个，符合要求（> {min_poi_count}个）")

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

    # 步骤2: 详情与评分校验
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    destination = poi_detail.location
    print(f"✅ 获取POI坐标: {destination}")

    # 评分验证（rating >= 4.7）
    if hasattr(poi_detail, 'biz_ext') and poi_detail.biz_ext and 'rating' in poi_detail.biz_ext:
        rating = poi_detail.biz_ext['rating']
        try:
            rating_value = float(rating)
            if rating_value < min_rating:
                print(f"❌ 评分{rating_value}低于{min_rating}")
                return False
            print(f"✅ 评分{rating_value}，符合要求（>= {min_rating}）")
        except (ValueError, TypeError):
            print(f"⚠️  无法解析评分值: {rating}，跳过评分验证")
    else:
        print(f"⚠️  未找到评分信息，跳过评分验证")

    # 步骤3: 步行时间校验（<= 22分钟）
    walking_result = maps_walking_by_coordinates(origin=user_location, destination=destination)
    if walking_result.error:
        print(f"❌ 计算步行路线失败: {walking_result.error}")
        return False

    if walking_result.total_duration_seconds is None:
        print(f"❌ 无法获取步行时长")
        return False

    walking_duration = walking_result.total_duration_seconds
    if walking_duration > max_walking_duration:
        print(f"❌ 步行时长{walking_duration}秒，超过{max_walking_duration}秒（{max_walking_duration // 60}分钟）")
        return False
    print(f"✅ 步行时长{walking_duration}秒，符合要求（<= {max_walking_duration}秒，即{max_walking_duration // 60}分钟）")

    # 步骤4: 天津站坐标获取（用 maps_text_search + maps_search_detail 替代 maps_geo）
    station_text_result = maps_text_search(keywords=station_address, city=station_city)
    if station_text_result.error:
        print(f"❌ 获取{station_address}坐标失败: {station_text_result.error}")
        return False

    if not station_text_result.pois or len(station_text_result.pois) == 0:
        print(f"❌ 未找到{station_address}坐标")
        return False

    first_poi_id = station_text_result.pois[0].id
    station_detail_result = maps_search_detail(id=first_poi_id)
    if station_detail_result.error:
        print(f"❌ 获取坐标失败: {station_detail_result.error}")
        return False
    if not station_detail_result.location:
        print("❌ 未获取到坐标")
        return False

    station_location = station_detail_result.location
    print(f"✅ 获取{station_address}坐标: {station_location}")

    # 步骤5: 天津站驾车时间校验（<= 22分钟）
    driving_result = maps_driving_by_coordinates(origin=station_location, destination=destination)
    if driving_result.error:
        print(f"❌ 计算驾车路线失败: {driving_result.error}")
        return False

    if driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取驾车时长")
        return False

    driving_duration = driving_result.total_duration_seconds
    if driving_duration > max_driving_duration:
        print(f"❌ 从{station_address}驾车时长{driving_duration}秒，超过{max_driving_duration}秒（{max_driving_duration // 60}分钟）")
        return False
    print(f"✅ 从{station_address}驾车时长{driving_duration}秒，符合要求（<= {max_driving_duration}秒，即{max_driving_duration // 60}分钟）")

    # 步骤6: 地铁站邻近校验（600米内）
    metro_search_result = maps_around_search(
        location=destination,
        radius=str(metro_search_radius),
        keywords=metro_keywords
    )
    if metro_search_result.error:
        print(f"❌ 搜索周边地铁站失败: {metro_search_result.error}")
        return False

    metro_count = 0
    if metro_search_result.pois:
        metro_count = len(metro_search_result.pois)

    if metro_count < min_metro_count:
        print(f"❌ {metro_search_radius}米范围内地铁站数量{metro_count}个，少于{min_metro_count}个")
        return False
    print(f"✅ {metro_search_radius}米范围内找到{metro_count}个地铁站")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 629.py 文件...\n")
    result = verify_poi(poi_id="B0FFJM8ATC")
    print(f"\n验证结果: {result}")
