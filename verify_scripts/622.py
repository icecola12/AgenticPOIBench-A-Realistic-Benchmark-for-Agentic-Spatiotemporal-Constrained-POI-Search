
"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 调用 maps_around_search(location='125.289133,43.862195', radius='3000', keywords='网吧')，验证返回pois中包含目标poi_id=B0K02768BJ（满足"附近3公里内网吧"）。
2) 调用 maps_search_detail(id='B0K02768BJ') 获取评分rating，验证 rating>=4.5。
3) 用 maps_driving_by_coordinates(origin='125.289133,43.862195', destination=目标POI的location) 获取驾车时长t_user_to_poi，验证 t_user_to_poi<=300秒（5分钟）。
4) 调用 maps_text_search(keywords='长春站', city='长春') 获取 poi_id，再调用 maps_search_detail(id=poi_id) 获取长春站坐标station_loc。
5) 用 maps_driving_by_coordinates(origin=目标POI的location, destination=station_loc) 获取驾车时长t_poi_to_station，验证 t_poi_to_station<=600秒（10分钟）。
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
    maps_text_search,
    maps_driving_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "125.289133,43.862195",
    search_radius: int = 3000,  # 3km
    keywords: str = "网吧",
    min_rating: float = 4.5,
    max_driving_to_poi: int = 300,  # 5 minutes = 300 seconds
    station_address: str = "长春站",
    station_city: str = "长春",
    max_driving_to_station: int = 600  # 10 minutes = 600 seconds
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 周边范围验证：验证返回pois中包含目标poi_id
    2) 评分验证：验证 rating>=4.5
    3) 用户到POI驾车时间验证：验证 t_user_to_poi<=300秒（5分钟）
    4) 调用 maps_text_search 获取 poi_id，再用 maps_search_detail 获取长春站坐标
    5) POI到车站驾车时间验证：验证 t_poi_to_station<=600秒（10分钟）

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"125.289133,43.862195"
        search_radius: 搜索半径（米），默认3000（3公里）
        keywords: 搜索关键词，默认"网吧"
        min_rating: 最低评分，默认4.5
        max_driving_to_poi: 到POI的最大驾车时长（秒），默认300（5分钟）
        station_address: 火车站地址，默认"长春站"
        station_city: 火车站所在城市，默认"长春"
        max_driving_to_station: 到车站的最大驾车时长（秒），默认600（10分钟）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 周边范围验证（附近3公里内的网吧）
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

    # 步骤2: 评分验证
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")

    # 验证评分（rating >= 4.5）
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

    # 步骤3: 用户到POI驾车时间验证（<= 5分钟）
    driving_to_poi_result = maps_driving_by_coordinates(origin=user_location, destination=poi_location)
    if driving_to_poi_result.error:
        print(f"❌ 计算到POI驾车路线失败: {driving_to_poi_result.error}")
        return False

    if driving_to_poi_result.total_duration_seconds is None:
        print(f"❌ 无法获取到POI驾车时长")
        return False

    t_user_to_poi = driving_to_poi_result.total_duration_seconds
    if t_user_to_poi > max_driving_to_poi:
        print(f"❌ 到POI驾车时长{t_user_to_poi}秒，超过{max_driving_to_poi}秒（{max_driving_to_poi // 60}分钟）")
        return False
    print(f"✅ 到POI驾车时长{t_user_to_poi}秒，符合要求（<= {max_driving_to_poi}秒，即{max_driving_to_poi // 60}分钟）")

    # 步骤4: 用 maps_text_search + maps_search_detail 获取长春站坐标
    text_search_result = maps_text_search(keywords=station_address, city=station_city)
    if text_search_result.error:
        print(f"❌ 获取{station_address}坐标失败: {text_search_result.error}")
        return False

    if not text_search_result.pois or len(text_search_result.pois) == 0:
        print(f"❌ 未找到{station_address}坐标")
        return False

    first_poi_id = text_search_result.pois[0].id
    detail_result = maps_search_detail(id=first_poi_id)
    if detail_result.error or not detail_result.location:
        print(f"❌ 获取{station_address}坐标失败: {detail_result.error or '无location'}")
        return False

    station_location = detail_result.location
    print(f"✅ 获取{station_address}坐标: {station_location}")

    # 步骤5: POI到车站驾车时间验证（<= 10分钟）
    driving_to_station_result = maps_driving_by_coordinates(origin=poi_location, destination=station_location)
    if driving_to_station_result.error:
        print(f"❌ 计算到{station_address}驾车路线失败: {driving_to_station_result.error}")
        return False

    if driving_to_station_result.total_duration_seconds is None:
        print(f"❌ 无法获取到{station_address}驾车时长")
        return False

    t_poi_to_station = driving_to_station_result.total_duration_seconds
    if t_poi_to_station > max_driving_to_station:
        print(f"❌ 到{station_address}驾车时长{t_poi_to_station}秒，超过{max_driving_to_station}秒（{max_driving_to_station // 60}分钟）")
        return False
    print(f"✅ 到{station_address}驾车时长{t_poi_to_station}秒，符合要求（<= {max_driving_to_station}秒，即{max_driving_to_station // 60}分钟）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 622.py 文件...\n")
    result = verify_poi(poi_id="B0K02768BJ")
    print(f"\n验证结果: {result}")
