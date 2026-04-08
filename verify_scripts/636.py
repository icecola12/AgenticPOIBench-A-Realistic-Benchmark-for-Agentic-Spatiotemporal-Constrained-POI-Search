
"""
修改任务指令：你要去办一件紧急的邮寄业务，想找一个附近1500米的邮政网点。你需要步行过去，步行时间不能超过20分钟，并且它的用户评分要在4.5分及以上。办完事后你还要立刻打车去北京西站，所以从这个邮政网点开车到北京西站的时间不能超过10分钟。你对服务和解决方案持怀疑态度。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 距离约束（周边搜索验证）：调用 maps_around_search(location="116.376145,39.918312", radius="1500", keywords="邮局")，验证返回的pois列表中包含 target_poi_id = "B000A7UNY9"。
2) POI属性验证（评分）：调用 maps_search_detail(id="B000A7UNY9")，读取 biz_ext.rating，验证 rating >= 4.5。
3) 步行可达性验证（<=20分钟）：从步骤2获取POI坐标 location="116.372561,39.914403"，调用 maps_walking_by_coordinates(origin="116.376145,39.918312", destination="116.372561,39.914403")，验证 total_duration_seconds <= 1200。
4) 到交通枢纽的驾车时间验证（<=10分钟）：调用 maps_text_search(keywords="北京西站", city="北京") 取 poi_id，再 maps_search_detail(id=poi_id) 获取 北京西站坐标 location_station；再调用 maps_driving_by_coordinates，验证 total_duration_seconds <= 600。
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
    maps_search_detail ,
    maps_walking_by_coordinates,
    maps_driving_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "116.376145,39.918312",
    search_radius: int = 1500,  # 1500 meters
    keywords: str = "邮局",
    min_rating: float = 4.5,
    max_walking_duration: int = 1200,  # 20 minutes = 1200 seconds
    station_address: str = "北京西站",
    station_city: str = "北京",
    max_driving_to_station: int = 600  # 10 minutes = 600 seconds
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 距离约束（周边搜索验证）：验证返回的pois列表中包含 target_poi_id
    2) POI属性验证（评分）：验证 rating >= 4.5
    3) 步行可达性验证（<=20分钟）：验证 total_duration_seconds <= 1200
    4) 到交通枢纽的驾车时间验证（<=10分钟）：验证 total_duration_seconds <= 600

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"116.376145,39.918312"
        search_radius: 搜索半径（米），默认1500
        keywords: 搜索关键词，默认"邮局"
        min_rating: 最低评分，默认4.5
        max_walking_duration: 最大步行时长（秒），默认1200（20分钟）
        station_address: 火车站地址，默认"北京西站"
        station_city: 火车站所在城市，默认"北京"
        max_driving_to_station: 到火车站的最大驾车时长（秒），默认600（10分钟）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 距离约束（周边搜索验证）
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

    # 步骤2: POI属性验证（评分）
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

    # 步骤3: 步行可达性验证（<= 20分钟）
    walking_result = maps_walking_by_coordinates(origin=user_location, destination=poi_location)
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

    # 步骤4: 到交通枢纽的驾车时间验证（<= 10分钟）（用 maps_text_search + maps_search_detail 替代 maps_geo）
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

    # 验证驾车时间（<= 10分钟）
    driving_result = maps_driving_by_coordinates(origin=poi_location, destination=station_location)
    if driving_result.error:
        print(f"❌ 计算到{station_address}驾车路线失败: {driving_result.error}")
        return False

    if driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取到{station_address}驾车时长")
        return False

    driving_duration = driving_result.total_duration_seconds
    if driving_duration > max_driving_to_station:
        print(f"❌ 到{station_address}驾车时长{driving_duration}秒，超过{max_driving_to_station}秒（{max_driving_to_station // 60}分钟）")
        return False
    print(f"✅ 到{station_address}驾车时长{driving_duration}秒，符合要求（<= {max_driving_to_station}秒，即{max_driving_to_station // 60}分钟）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 636.py 文件...\n")
    result = verify_poi(poi_id="B000A7UNY9")
    print(f"\n验证结果: {result}")
