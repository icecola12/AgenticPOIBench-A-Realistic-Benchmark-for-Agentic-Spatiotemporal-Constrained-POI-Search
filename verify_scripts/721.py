
"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边范围验证：调用 maps_around_search(location="106.092395,30.779506", radius="3000", keywords="酒吧")，验证返回pois中包含 target_poi_id=B0FFJ2OJ93。
2) POI属性验证：调用 maps_search_detail(id="B0FFJ2OJ93")，验证 biz_ext.rating >= 4.5，且 biz_ext.open_time/opentime2 显示营业到 "03:00"（因此在凌晨2点之后仍营业）。同时取其 location 作为后续路由终点。
3) 用户到目标点驾车时间：调用 maps_driving_by_coordinates(origin="106.092395,30.779506", destination="106.089960,30.777786")，验证 total_duration_seconds <= 360（6分钟）。
4) 南充站到目标点驾车时间：先调用 maps_search_detail(id="B033100HZZ") 获取南充站 location="106.086011,30.807886"；再调用 maps_driving_by_coordinates(origin="106.086011,30.807886", destination="106.089960,30.777786")，验证 total_duration_seconds <= 480（8分钟）。
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
    maps_driving_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "106.092395,30.779506",
    search_radius: int = 3000,  # 3km
    keywords: str = "酒吧",
    min_rating: float = 4.5,
    required_closing_time: str = "03:00",
    max_driving_duration_from_user: int = 360,  # 6 minutes = 360 seconds
    station_poi_id: str = "B033100HZZ",
    max_driving_duration_from_station: int = 480  # 8 minutes = 480 seconds
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 周边范围验证：调用 maps_around_search，验证返回pois中包含 target_poi_id。
    2) POI属性验证：调用 maps_search_detail，验证 biz_ext.rating >= 4.5，且 biz_ext.open_time/opentime2 显示营业到 "03:00"。同时取其 location 作为后续路由终点。
    3) 用户到目标点驾车时间：调用 maps_driving_by_coordinates，验证 total_duration_seconds <= 360（6分钟）。
    4) 南充站到目标点驾车时间：先调用 maps_search_detail 获取南充站 location；再调用 maps_driving_by_coordinates，验证 total_duration_seconds <= 480（8分钟）。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"106.092395,30.779506"
        search_radius: 搜索半径（米），默认3000（3公里）
        keywords: 搜索关键词，默认"酒吧"
        min_rating: 最低评分，默认4.5
        required_closing_time: 要求的打烊时间，默认"03:00"
        max_driving_duration_from_user: 从用户位置到POI的最大驾车时长（秒），默认360（6分钟）
        station_poi_id: 火车站POI ID，默认"B033100HZZ"
        max_driving_duration_from_station: 从火车站到POI的最大驾车时长（秒），默认480（8分钟）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 周边范围验证（3公里内的酒吧）
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

    # 步骤3: 验证评分>=4.5
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

    # 步骤4: 验证营业时间（营业到03:00，即凌晨2点之后仍营业）
    open_time = poi_detail.biz_ext.get('open_time') or poi_detail.biz_ext.get('opentime2')
    if not open_time:
        print(f"❌ POI没有营业时间信息")
        return False

    print(f"✅ 获取营业时间: {open_time}")

    # 检查营业时间是否包含03:00（表示营业到凌晨3点）
    if required_closing_time not in open_time:
        print(f"❌ 营业时间{open_time}不包含{required_closing_time}，不满足营业到凌晨2点之后的要求")
        return False
    print(f"✅ 营业时间包含{required_closing_time}，满足营业到凌晨2点之后的要求")

    # 步骤5: 从用户位置到POI的驾车时间<=6分钟
    driving_result_from_user = maps_driving_by_coordinates(origin=user_location, destination=poi_location)
    if driving_result_from_user.error:
        print(f"❌ 计算从用户位置到POI的驾车路线失败: {driving_result_from_user.error}")
        return False

    if driving_result_from_user.total_duration_seconds is None:
        print(f"❌ 无法获取从用户位置到POI的驾车时长")
        return False

    driving_duration_from_user = driving_result_from_user.total_duration_seconds
    if driving_duration_from_user > max_driving_duration_from_user:
        print(f"❌ 从用户位置到POI的驾车时长{driving_duration_from_user}秒，超过{max_driving_duration_from_user}秒（{max_driving_duration_from_user // 60}分钟）")
        return False
    print(f"✅ 从用户位置到POI的驾车时长{driving_duration_from_user}秒，符合要求（<= {max_driving_duration_from_user}秒，即{max_driving_duration_from_user // 60}分钟）")

    # 步骤6: 获取南充站坐标
    station_detail = maps_search_detail(id=station_poi_id)
    if station_detail.error:
        print(f"❌ 获取南充站详情失败: {station_detail.error}")
        return False

    if not station_detail.location:
        print(f"❌ 南充站没有location信息")
        return False

    station_location = station_detail.location
    print(f"✅ 获取南充站坐标: {station_location}")

    # 步骤7: 从南充站到POI的驾车时间<=8分钟
    driving_result_from_station = maps_driving_by_coordinates(origin=station_location, destination=poi_location)
    if driving_result_from_station.error:
        print(f"❌ 计算从南充站到POI的驾车路线失败: {driving_result_from_station.error}")
        return False

    if driving_result_from_station.total_duration_seconds is None:
        print(f"❌ 无法获取从南充站到POI的驾车时长")
        return False

    driving_duration_from_station = driving_result_from_station.total_duration_seconds
    if driving_duration_from_station > max_driving_duration_from_station:
        print(f"❌ 从南充站到POI的驾车时长{driving_duration_from_station}秒，超过{max_driving_duration_from_station}秒（{max_driving_duration_from_station // 60}分钟）")
        return False
    print(f"✅ 从南充站到POI的驾车时长{driving_duration_from_station}秒，符合要求（<= {max_driving_duration_from_station}秒，即{max_driving_duration_from_station // 60}分钟）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 721.py 文件...\n")
    result = verify_poi(poi_id="B0FFJ2OJ93")
    print(f"\n验证结果: {result}")
